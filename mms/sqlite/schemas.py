from typing import Optional
from pydantic import BaseModel


class ModelBase(BaseModel):
    uuid: str
    state: str


class ModelCreate(ModelBase):
    pass


class Model(ModelBase):
    id: int

    class Config:
        orm_mode = True


class InfoBase(BaseModel):
    model_name: str
    model_description: Optional[str]
    version: int
    model_state: Optional[str]
    state_reason: Optional[str]
    has_process_file: bool
    project_id: Optional[int]
    uuid: str


class InfoCreate(InfoBase):
    save_path: str
    model_filename: str
    process_filename: Optional[str]


class Info(InfoBase):
    id: int

    class Config:
        orm_mode = True
