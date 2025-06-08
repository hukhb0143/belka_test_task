import json
import os
import traceback
import asyncpg

from contextlib import asynccontextmanager
from asyncpg import Record
from datetime import timedelta
from typing import Annotated
from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from auth.auth_api import Authenticator
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from db_service.database_api import PostgreSQLService
from exceptions.app_exceptions import NoDataException, UserAlreadyExistException
from exceptions.auth_exceptions import WrongCredentialsException
from model.concentrate_models import Token, MonthData, ConcentrateRecord, SummaryResponse, User, UserCreate
from utils.stat_utils import calculate_stats


# Инициализация приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    До старта приложения создаем таблицы и вставляем дефолтных пользователей из initial_users.json

    :param app: Основное приложение.
    :type app: FastAPI
    :return:
    """
    await db_service.create_tables()

    file_path = os.path.join(os.path.dirname(__file__), "initial_users.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            default_users = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка создания дефолтных пользователей: {e}")
        return

    for user in default_users:
        try:
            await db_service.insert_user(user['username'], auth_service.get_password_hash(user['password']))
        except asyncpg.exceptions.UniqueViolationError:
            # Дефолтные пользователи уже в бд
            pass

    logger.info(f"Дефолтные пользователи были созданы")

    yield

# Настройка логгирования
logger.add("logs/concentrate_api.log", rotation="10 MB", retention="10 days", level="INFO")

app = FastAPI(
    title="API данных железного концентрата",
    description="API системы добавления данных о качественных показателях железорудного концентрата и просмотра "
        "сводной информации по всем концентратам. Качественные показатели железорудного концентрата: содержание железа, "
        "содержание кремния, содержание алюминия, содержание кальция, содержание серы",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8000",
        "http://172.20.0.4:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация нужных сервисов
auth_service = Authenticator()
db_service = PostgreSQLService()


@app.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    Аутентификация пользователя.

    :param form_data: Модель данных
    :return:
    """
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Ошибка аутентификации пользователя {form_data.username}")
        raise WrongCredentialsException

    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = auth_service.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    logger.info(f"Пользователь {user['username']} успешно прошел аутентификацию")
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/concentrate-quality")
async def save_concentrate_data(
        month_data: MonthData,
        request: Request
):
    """
    Сохраняем данные концентратов.

    :param month_data: Модель данных
    :param request: запрос FastAPI
    :return:
    """
    try:
        current_user = await auth_service.get_user_from_request(request)
        if not current_user:
            return RedirectResponse('/')

        logger.info(f"Пользователь {current_user['username']} сохраняет данные за {month_data.month}/{month_data.year}")
        await db_service.set_concentrate_data(month_data, current_user)

        logger.info(f"Данные за {month_data.month}/{month_data.year} успешно сохранены")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Данные за {month_data.month}/{month_data.year} не были сохранены: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}


@app.get("/api/concentrate-quality", response_model=MonthData)
async def get_concentrate_data(
        month: Annotated[int, Query(..., gt=0, le=12)],
        year: Annotated[int, Query(..., gt=2000)],
        request: Request
):
    """
    Получение данных за конкретный месяц и год. На фронте не используется.

    :param month: Месяц
    :param year: Год
    :param request: Запрос FastAPI
    :return:
    """
    current_user = await auth_service.get_user_from_request(request)
    if not current_user:
        return RedirectResponse('/')

    logger.info(f"Пользователь {current_user['username']} запросил данные за {month}/{year}")
    records = await db_service.get_concentrate_data(month, year, current_user['id'])

    if not records:
        logger.info(f"Нет данных за {month}/{year}")
        return MonthData(month=month, year=year, data=[])

    data = [ConcentrateRecord(**record) for record in records]
    return MonthData(month=month, year=year, data=data)


@app.get("/api/concentrate-quality/summary", response_model=SummaryResponse)
async def get_concentrate_summary(
        month: Annotated[int, Query(..., gt=0, le=12)],
        year: Annotated[int, Query(..., gt=2000)],
        request: Request
):
    """
    Получаем отчет за выбранный месяц и год.

    :param month: Месяц
    :param year: Год
    :param request: Запрос FastAPI
    :return:
    """
    current_user = await auth_service.get_user_from_request(request)
    if not current_user:
        return RedirectResponse('/')

    logger.info(f"Пользователь {current_user['username']} запросил отчет за {month}/{year}")
    records = await db_service.get_concentrate_data(month, year, current_user['id'])

    if not records:
        logger.warning(f"Нет данных для отчета за {month}/{year}")
        raise NoDataException

    # Подготовка данных для статистики
    iron_vals = [record["iron"] for record in records]
    silicon_vals = [record["silicon"] for record in records]
    aluminum_vals = [record["aluminum"] for record in records]
    calcium_vals = [record["calcium"] for record in records]
    sulfur_vals = [record["sulfur"] for record in records]

    logger.info(f"Отчет за {month}/{year} успешно сформирован")

    return SummaryResponse(
        month=month,
        year=year,
        count=len(records),
        iron=calculate_stats(iron_vals),
        silicon=calculate_stats(silicon_vals),
        aluminum=calculate_stats(aluminum_vals),
        calcium=calculate_stats(calcium_vals),
        sulfur=calculate_stats(sulfur_vals)
    )


@app.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    """
    Начал писать API для регистрации и понял, что это не требуется для тестового задания, а удалять жалко
    :param user: Данные пользователя
    :type user: UserCreate
    :return:
    """
    try:
        logger.info(f"Создаем нового пользователя: {user.username}")
        db_user = await db_service.insert_user(user.username,
            auth_service.get_password_hash(user.password))
    except asyncpg.exceptions.UniqueViolationError:
        logger.warning(f"Пользователь {user.username} уже существует")
        raise UserAlreadyExistException

    logger.info(f"Пользователь {user.username} успешно создан")
    return User(**db_user)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="172.20.0.3", port=8000)
