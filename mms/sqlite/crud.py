from sqlalchemy.orm import Session
from . import models, schemas


def get_models(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Model).offset(skip).limit(limit).all()


def create_model(db: Session, model: schemas.ModelCreate):
    db_model = models.Model(uuid=model.uuid)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


def create_info(db: Session, info: schemas.InfoCreate):
    db_info = models.Info(**info.dict())
    db.add(db_info)
    db.commit()
    db.refresh(db_info)
    return db_info


def get_infos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Info).offset(skip).limit(limit).all()


def get_info_by_model_name(db: Session, model_name: str):
    return (db.query(models.Info)
              .filter(models.Info.model_name == model_name)
              .all())

def get_info_by_uuid(db: Session, uuid: str):
    return db.query(models.Info).filter(models.Info.uuid == uuid).first()


def get_info_by_state(db: Session, state: str):
    return db.query(models.Info).filter(models.Info.model_state == state).all()


def update_state(db: Session, uuid: str, state: str):
    info = get_info_by_uuid(db, uuid)
    info.model_state = state
    db.commit()


def delete_info(db: Session, uuid: str):
    info = get_info_by_uuid(db, uuid)
    db.delete(info)
    db.commit()
