from typing import Optional, Dict, List

from pydantic import BaseModel, field_validator, confloat, constr


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ConcentrateRecord(BaseModel):
    name: str
    iron: confloat(ge=0, le=100)
    silicon: confloat(ge=0, le=100)
    aluminum: confloat(ge=0, le=100)
    calcium: confloat(ge=0, le=100)
    sulfur: confloat(ge=0, le=100)

    @field_validator('*')
    def round_values(cls, value, field):
        if field.field_name == 'name':
            return value
        return round(value, 2)


class MonthData(BaseModel):
    month: int
    year: int
    data: List[ConcentrateRecord]


class SummaryResponse(BaseModel):
    month: int
    year: int
    count: int
    iron: Dict[str, float]
    silicon: Dict[str, float]
    aluminum: Dict[str, float]
    calcium: Dict[str, float]
    sulfur: Dict[str, float]