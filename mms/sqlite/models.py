from sqlalchemy import Boolean, Column, Integer, String

from .database import Base


class Model(Base):
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    state = Column(String)


class Info(Base):
    __tablename__ = 'infos'

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    model_description = Column(String, nullable=True)
    version = Column(Integer)
    model_state = Column(String, nullable=True)
    state_reason = Column(String, nullable=True)
    save_path = Column(String)
    model_filename = Column(String)
    process_filename = Column(String, nullable=True)
    has_process_file = Column(Boolean)
    project_id = Column(Integer, nullable=True)
    uuid = Column(String, unique=True, index=True)
