from fastapi import HTTPException, status


class CredentialsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Валидация прошла с ошибкой",
            headers={"WWW-Authenticate": "Bearer"},
        )


class WrongCredentialsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )


class CorruptedTokenException(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="Невалидный заголовок аутентификации")
