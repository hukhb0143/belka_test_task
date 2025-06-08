import traceback
import jwt

from loguru import logger
from typing import Optional
from asyncpg import Record
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from config import SECRET_KEY, ALGORITHM
from db_service.database_api import PostgreSQLService
from exceptions.auth_exceptions import CredentialsException, CorruptedTokenException
from model.concentrate_models import TokenData
from patterns.singleton import Singleton


class Authenticator(Singleton):
    def __init__(self):
        try:
            super().__init__()
            self.pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__ident="2b", deprecated="auto")
            self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
            self.db_service = PostgreSQLService()
        except:
            logger.error(f"Ошибка при инициализации класса Authenticator - {traceback.format_exc()}")

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Создаем access-токен.

        :param data: Данные токена.
        :param expires_delta: Дельта истечения токена.
        :return:
        """

        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def authenticate_user(self, username: str, password: str) -> Optional[Record]:
        """
        Аутентификация пользователя.

        :param username: Логин пользователя
        :param password: Пароль пользователя
        :return:
        """
        user = await self.db_service.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user["hashed_password"]):
            return None
        return user

    async def get_current_user(self, token: str) -> Record:
        """
        Получаем пользователя из токена.

        :param token: Токен
        :return:
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise CredentialsException

            token_data = TokenData(username=username)
        except jwt.PyJWTError as e:
            logger.error(f"Ошибка JWT: {e}")
            raise CredentialsException

        user = await self.db_service.get_user(username=token_data.username)
        if user is None:
            raise CredentialsException
        return user

    async def get_user_from_request(self, request):
        """
        Получаем пользователя из запроса.

        :param request: Запрос FastAPI
        :return:
        """
        auth_header: str = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise CorruptedTokenException

        token = auth_header.split(" ")[1]
        current_user = await self.get_current_user(token)
        return current_user

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Верификация пароля.

        :param plain_password: Пароль
        :param hashed_password: Хэшированный пароль
        :return:
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Формирует хэш пароля.

        :param password: Пароль
        :return:
        """
        return self.pwd_context.hash(password)