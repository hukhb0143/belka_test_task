import asyncpg

from contextlib import asynccontextmanager
from loguru import logger
from config import DATABASE_URL
from asyncpg import Record
from typing import Optional

from model.concentrate_models import MonthData
from patterns.singleton import Singleton


class PostgreSQLService(Singleton):
    def __init__(self):
        super().__init__()

    @asynccontextmanager
    async def connect(self, dsn: str):
        """
        Асинхронный контекстный менедежер обращения к БД.

        :param dsn: Строка обращения к БД
        :return:
        """
        conn = await asyncpg.connect(dsn)
        try:
            yield conn
        finally:
            await conn.close()

    async def create_tables(self):
        """
        Создаем необходимые дефолтные таблицы.

        :return:
        """
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        );
        """

        create_concentrate_table = """
        CREATE TABLE IF NOT EXISTS concentrate_quality (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            iron NUMERIC(5,2) NOT NULL,
            silicon NUMERIC(5,2) NOT NULL,
            aluminum NUMERIC(5,2) NOT NULL,
            calcium NUMERIC(5,2) NOT NULL,
            sulfur NUMERIC(5,2) NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER REFERENCES users(id)
        );
        """

        async with self.connect(DATABASE_URL) as con:
            await con.execute(create_users_table)
            await con.execute(create_concentrate_table)
            logger.info("Таблицы были созданы")

    async def get_user(self, username: str) -> Optional[Record]:
        """
        Проверка наличия пользователя в БД.

        :param username: Логин пользователя
        :return:
        """
        async with self.connect(DATABASE_URL) as con:
            return await con.fetchrow("SELECT * FROM users WHERE username = $1;", username)

    async def set_concentrate_data(self, month_data: MonthData, current_user: str, replace_data: bool =False):
        """
        Запись в БД информации по концентрату.

        :param month_data: Модель данных
        :param current_user: Логин пользователя
        :param replace_data: Переменная, отвечающая за замену данных в БД. Если True, то данные за выбранные месяц будут
            перезаписаны.
        :return:
        """
        async with self.connect(DATABASE_URL) as con:
            async with con.transaction():
                # Удаляем старые данные за этот месяц
                if replace_data:
                    await con.execute(
                        "DELETE FROM concentrate_quality WHERE month = $1 AND year = $2;",
                        month_data.month, month_data.year
                    )

                # Сохраняем новые данные
                for record in month_data.data:
                    await con.execute(
                        """INSERT INTO concentrate_quality 
                        (name, iron, silicon, aluminum, calcium, sulfur, month, year, created_by)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);""",
                        record.name, record.iron, record.silicon,
                        record.aluminum, record.calcium, record.sulfur,
                        month_data.month, month_data.year, current_user["id"]
                    )

    async def get_concentrate_data(self, month: str, year: str, user_id: int):
        """
        Получает данные для конкретного пользователя за представленный год и месяц.

        :param month: Месяц
        :param year: Год
        :param user_id: Id пользователя в БД
        :return:
        """
        async with self.connect(DATABASE_URL) as con:
            records = await con.fetch(
                """SELECT name, iron, silicon, aluminum, calcium, sulfur 
                FROM concentrate_quality 
                WHERE month = $1 AND year = $2 AND created_by = $3;""",
                month, year, user_id
            )
            return records

    async def insert_user(self, username, hashed_password):
        """
        Добавляем нового пользователя в БД.

        :param username: Логин пользователя
        :param hashed_password: Хешированный пароль
        :return:
        """
        async with self.connect(DATABASE_URL) as con:
            async with con.transaction():
                db_user = await con.fetchrow(
                    """INSERT INTO users (username, hashed_password)
                    VALUES ($1, $2) RETURNING id, username, is_active;""",
                    username, hashed_password
                )
                return db_user
