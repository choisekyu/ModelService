import os
import shutil
import uuid
from typing import List, Union

import requests
from fastapi import Depends, FastAPI, File, Form, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import FileResponse, PlainTextResponse

import utils
from datatypes import DATATYPES
from models import frameworks
from sqlite import crud, models, schemas


#TRITON_TEST_URL = os.environ['TRITON_TEST_URL']
TRITON_TEST_URL = 'localhost:8000'
app = FastAPI()
mms = utils.ModelManagementService(app)


@app.post('/models', response_class=PlainTextResponse, summary='모델 등록')
async def upload_model(
        framework: str = Form(),
        model_name: str = Form(),
        model_desc: str = Form(None),
        model_files: List[UploadFile] = File(...),
        process_file: UploadFile = File(None),
        inputs = Form(None),
        outputs = Form(None),
        load: Union[bool, None] = Form(True),
        db: Session = Depends(utils.get_db)):
    #id = utils.get_uuid([r.uuid for r in crud.get_infos(db, 0, None)])
    id = str(uuid.uuid4())
    print(id)
    # 1. save model_files, process_file in test repository
    info = mms.set_files(
        id, framework, inputs, outputs, model_files, process_file)

    # 2. load model at test trtis
    res = utils.load_model(TRITON_TEST_URL, id)
    if res.status_code != 200:
        print('STATUS CODE:', res.status_code)
        print(res.text)
        mms.delete_file(id)
        return 'ERROR'
    cfg = utils.get_config(TRITON_TEST_URL, id)
    _ = utils.unload_model(TRITON_TEST_URL, id)
    
    # 3. save info in db
    result = crud.get_info_by_model_name(db, model_name)
    version = len(result) + 1

    info['model_name'] = model_name
    info['model_description'] = model_desc
    info['version'] = version
    crud.create_info(db=db, info=schemas.InfoCreate(**info))

    if load:
        # 4. load model
        _ = mms.load_model(id)
        crud.update_state(db, id, 'READY')

        # 5. send info to inference service
        res = mms.send_to_is(id, info['process_filename'])

    return f'uuid: {id}'


@app.post('/models/load/{uuid}', summary='Triton에 모델 load')
def load_model(uuid: str, db: Session = Depends(utils.get_db)):
    _ = mms.load_model(uuid)
    crud.update_state(db, uuid, 'READY')
    info = crud.get_info_by_uuid(db, uuid)
    mms.send_to_is(uuid, info.process_filename)
    return 'OK'


@app.post('/models/unload/{uuid}', summary='Triton에 모델 unload')
def unload_model(uuid: str, db: Session = Depends(utils.get_db)):
    _ = mms.unload_model(uuid)
    crud.update_state(db, uuid, 'UNAVAILABLE')
    mms.send_to_is(uuid, type='delete')
    return 'OK'


@app.delete('/models/{uuid}', summary='모델 삭제')
def delete_model(uuid: str, db: Session = Depends(utils.get_db)):
    _ = mms.unload_model(uuid)
    crud.delete_info(db, uuid)
    #mms.rmtree(uuid)
    return f'{uuid} is deleted.'


@app.get('/models/loaded',
         response_model=List[schemas.Info],
         summary='Triton에 로드된 모델 정보')
def get_loaded_models_info(db: Session = Depends(utils.get_db)):
    result = crud.get_info_by_state(db, 'READY')
    return result


@app.get('/models',
         response_model=List[schemas.Info],
         summary='등록된 모델 정보')
def get_models_info(db: Session = Depends(utils.get_db)):
    result = crud.get_infos(db, 0, None)
    return result


@app.get('/models/{uuid}', response_model=schemas.Info, summary='모델 정보')
def get_model_info(uuid: str, db: Session = Depends(utils.get_db)):
    return crud.get_info_by_uuid(db, uuid)


@app.get('/models/file/model/{uuid}', summary='모델 다운로드')
def get_model_file(uuid: str, db: Session = Depends(utils.get_db)):
    return FileResponse(mms.get_model_path(db, uuid))


@app.get('/models/file/process/{uuid}', summary='프로세스(전처리) 다운로드')
def get_process_file(uuid: str, db: Session = Depends(utils.get_db)):
    info = crud.get_info_by_uuid(db, uuid)
    if info.process_filename is not None:
        return FileResponse(mms.get_process_path(db, uuid))
    else:
        return PlainTextResponse('OK')


@app.get('/models/metadata/{uuid}', summary='모델 입출력 정보')
def get_model_metadata(uuid: str):
    return mms.get_metadata(uuid)


@app.get('/models/info', summary='프론트 용')
def get_info():
    return {
        'frameworks': list(frameworks.keys()),
        'datatypes': list(DATATYPES.keys()),
        }


@app.post('/test')
def test(uuid: str = Form(),
         model_name: str = Form(),
         model_filename: str = Form(),
         process_filename: str = Form(None),
         db: Session = Depends(utils.get_db)):
    
    if uuid in os.listdir(f'{TRITON_PATH}'):
        result = crud.get_info_by_model_name(db, model_name)
        version = len(result) + 1
        info = {
            'model_name': model_name,
            'model_description': '',
            'version': version,
            'model_state': None,
            'state_reason': None,
            'save_path': f'{TRITON_PATH}/{uuid}',
            'model_filename': model_filename,
            'process_filename': process_filename,
            'has_process_file': process_filename is not None,
            'project_id': 1,
            'uuid': uuid,
        }
        crud.create_info(db=db, info=schemas.InfoCreate(**info))
        _ = mms.load_model(uuid)
        crud.update_state(db, uuid, 'READY')
        res = mms.send_to_is(uuid, info['process_filename'])

        return f'uuid: {uuid}'
    else:
        return f'{uuid} does not exist.'
