import json
import os
import shutil

import requests
from fastapi.middleware.cors import CORSMiddleware

from datatypes import DATATYPES, DATATYPE_META
from models import frameworks, Config, Data, Info, Upload
from sqlite import crud
from sqlite.database import Base, SessionLocal, engine


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ModelManagementService(object):

    def __init__(self, app):
        origins = [
            #"http://192.168.1.101:8088"
            #"http://localhost:8088"
            '*'
        ]
        #self.trt_url = os.environ['TRITON_MAIN_URL']
        #self.is_url = os.environ['IS_URL']
        #self.trt_path = os.environ['TRITON_PATH']
        self.trt_url = 'localhost:8000'
        self.is_url = 'localhost:8006'
        self.trt_path = '/models'

        app.add_middleware(CORSMiddleware,
                           allow_origins=origins,
                           allow_credentials=True,
                           allow_methods=['*'],
                           allow_headers=['*'],
        )
        Base.metadata.create_all(bind=engine)

        res = requests.post(f"http://{self.trt_url}/v2/repository/index")
        db = SessionLocal()
        for d in res.json():
            info = crud.get_info_by_uuid(db, d['name'])
            if info:
                state = d.get('state', None)
                if state == 'READY':
                    crud.update_state(db, d['name'], 'READY')
                else:
                    crud.upadte_state(db, d['name'], 'UNAVAILABLE')

    def get_model_path(self, db, uuid: str) -> str:
        info = crud.get_info_by_uuid(db, uuid)
        return f"{self.trt_path}/{uuid}/{info.version}/{info.model_filename}"

    def get_process_path(self, db, uuid: str) -> str:
        info = crud.get_info_by_uuid(db, uuid)
        return f"{self.trt_path}/{uuid}/process/{info.process_filename}"

    def get_metadata(self, uuid: str) -> dict:
        res = requests.get(f'http://{self.trt_url}/v2/models/{uuid}').json()
        inputs = [
            {'name': d['name'],
             'shape': d['shape'],
             'dtype': DATATYPE_META[d['datatype']]} for d in res['inputs']]
        outputs = [
            {'name': d['name'],
             'shape': d['shape'],
             'dtype': DATATYPE_META[d['datatype']]} for d in res['outputs']]
        return {'inputs': inputs, 'outputs': outputs}

    def load_model(self, uuid: str):
        res = requests.post(
            f'http://{self.trt_url}/v2/repository/models/{uuid}/load')
        return res

    def unload_model(self, uuid: str):
        res = requests.post(
            f'http://{self.trt_url}/v2/repository/models/{uuid}/unload')
        return res.status_code

    def get_process_file(self, uuid: str, process_file: str):
        try:
            process_file = self.get_process_path(uuid, process_file)
            return open(process_file, 'rb')
        except:
            return None

    def send_to_is(
            self, uuid: str, process_file: str = None, type: str = 'post'):
        if type == 'post':
            res = requests.post(
                f'http://{self.is_url}/models',
                data={'uuid': uuid},
                files={'process_file': self.get_process_file(uuid, process_file)}
            )
        elif type == 'delete':
            res = requests.delete(f'http://{self.is_url}/models/{uuid}')
        return res

    def set_files(self,
                  uuid: str,
                  framework: str,
                  inputs: str,
                  outputs: str,
                  model_files: list,
                  process_file) -> dict:
        config = Config(framework, f'{self.trt_path}/{uuid}')

        if config.framework == 'TF-saved':
            for file in model_files:
                filename = file.filename.split('/')[-1]
                if '.pb' in filename:
                    with open(f'{config.model_path}/{filename}', 'wb') as buf:
                        shutil.copyfileobj(file.file, buf)
                else:
                    with open(f'{config.variable_path}/{filename}', 'wb') as buf:
                        shutil.copyfileobj(file.file, buf)
        else:
            with open(f'{config.model_path}/{config.filename}', 'wb') as buf:
                shutil.copyfileobj(model_files[0].file, buf)

            if config.framework == 'PyTorch':
                #inputs = [Data(**d) for d in json.loads(inputs)]
                #outputs = [Data(**d) for d in json.loads(outputs)]
                inputs = json.loads(inputs)
                outputs = json.loads(outputs)
                config.set_data('input', inputs)
                config.set_data('output', outputs)
                config.make_pbtxt()

        if process_file is not None:
            process_path = f'{config.path}/process'
            os.mkdir(process_path)
            with open(f'{process_path}/{process_file.filename}', 'wb') as buf:
                shutil.copyfileobj(process_file.file, buf)

        return {
            'model_name': '',
            'model_description': '',
            'version': None,
            'model_state': None,
            'state_reason': None,
            'save_path': f'{self.trt_path}/{uuid}',
            'model_filename': model_files[0].filename,
            'process_filename': process_file.filename if process_file else None,
            'has_process_file': process_file is not None,
            'project_id': 1,
            'uuid': uuid,
        }

    def delete_file(self, uuid: str) -> None:
        shutil.rmtree(f"{self.trt_path}/{uuid}")


def get_loaded_models(url: str) -> list:
    res = requests.post(f'http://{url}/v2/repository/index')
    res = list(filter(lambda x: x.get('state') == 'READY', res.json()))
    return res


def load_model(url: str, uuid: str) -> int:
    res = requests.post(f'http://{url}/v2/repository/models/{uuid}/load')
    return res


def unload_model(url: str, uuid: str) -> int:
    res = requests.post(f'http://{url}/v2/repository/models/{uuid}/unload')
    return res.status_code


def get_config(url: str, uuid: str) -> json:
    res = requests.get(f'http://{url}/v2/models/{uuid}/config')
    return res.json()


def get_metadata(url: str, uuid: str) -> dict:
    res = requests.get(f'http://{url}/v2/models/{uuid}').json()
    inputs = [
        {'name': d['name'],
         'shape': d['shape'],
         'dtype': DATATYPE_META[d['datatype']]} for d in res['inputs']]
    outputs = [
        {'name': d['name'],
         'shape': d['shape'],
         'dtype': DATATYPE_META[d['datatype']]} for d in res['outputs']]
    return {'inputs': inputs, 'outputs': outputs}
