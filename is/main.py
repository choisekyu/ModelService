import os

import requests
from fastapi import FastAPI, File, Form, Request, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import UploadFile as UFile
from starlette.responses import StreamingResponse

import utils


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
_is = utils.InferenceService()


@app.post('/models', summary='Inference Object 생성')
async def create_model(uuid: str = Form(), process_file: UploadFile = None):
    if process_file is not None:
        process_file = await process_file.read()
    _is.create(uuid, process_file)
    return f"{uuid} is built."


@app.delete('/models/{uuid}', summary='Inference Object 삭제')
def delete_model(uuid: str):
    if uuid in _is.models:
        del _is.models[uuid]
    return f'{uuid} is destroyed.'


@app.get('/models', summary='Inference Object 목록')
def show_object_list():
    return list(_is.models.keys())


@app.post('/inference', description='infer', summary='Infer')
async def infer(request: Request):
    request = await request.form()
    request: dict = request._dict
    uuid: str = request.pop('uuid')
    if uuid not in _is.models:
        raise HTTPException(status_code=400, detail="uuid is wrong")
    process = request.pop('process_file', None)
    preprocess = request.pop('preprocess', False)
    postprocess = request.pop('postprocess', False)
    return_type = request.pop('return_type', None)
    img_type = request.pop('image_type', 'jpeg')  # jpeg, png
    model = _is.models[uuid]

    for k, v in request.items():
        if isinstance(v, UFile):
            v = utils.image2numpy(
                await v.read(),
                model.inputs[k].datatype if k in model.inputs else None)
        else:
            v = utils.parse_string(
                v,
                model.inputs[k].datatype if k in model.inputs else None)
        request[k] = v

    #try:
    if process is None:
        result = model.run(request,
                           process=None,
                           with_pre=preprocess=='True',
                           with_post=postprocess=='True',
        )
    else:
        result = model.run(request, await process.read())
    #except Exception as e:
    #    return str(e)

    if return_type is None or return_type in ['pkl', 'pickle']:
        return StreamingResponse(utils.to_pickle(result))
    elif return_type == 'list':
        return {k: v.tolist() for k, v in result.items()}
    elif isinstance(return_type, str):
        buf = utils.to_image(result[return_type], img_type.upper())
        buf.seek(0)
        return StreamingResponse(content=buf, media_type=f'image/{img_type}')
