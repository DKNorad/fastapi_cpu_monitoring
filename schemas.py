from typing import TypeVar, Generic
from fastapi import Query
from fastapi_pagination.default import Page as BasePage, Params as BaseParams
from pydantic import BaseModel


class HostBase(BaseModel):
    ip: str

    class Config:
        orm_mode = True


class HostCreate(HostBase):
    pass


class CpuDataBase(BaseModel):
    host_id: int
    cpu_util: int
    time: str


class CpuDataDetailedOut(CpuDataBase):
    class Config:
        orm_mode = True


class CpuDataThresholdOut(CpuDataBase):
    class Config:
        orm_mode = True


class HostsRead(BaseModel):
    ip: str
    id: int

    class Config:
        orm_mode = True


class DummyCreate(BaseModel):
    entries_num: int
    hosts_num: int

    class Config:
        orm_mode = True


T = TypeVar("T")


class Params(BaseParams):
    size: int = Query(100, ge=1, le=100, description="Page size")


class Page(BasePage[T], Generic[T]):
    __params_type__ = Params
