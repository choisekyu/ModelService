from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from fastapi import File, Form, UploadFile
from pydantic import BaseModel

from datatypes import DATATYPES


class Upload(BaseModel):
    framework: str = Form()
    model_name: str = Form()
    model_desc: Optional[str] = Form(None)
    #model_files: List[UploadFile] = File(...)
    model_files: UploadFile = File(...)
    #process_files: Optional[UploadFile] = File(None)
    #inputs: str = Form(None)
    #outputs: str = Form(None)
    #load: Union[bool, None] = Form(True)


class Data(BaseModel):
    name: str
    shape: List[int]
    datatype: str


@dataclass
class Info:
    platform: str
    filename: str


frameworks = {
    'ONNX': Info('onnxruntime_onnx', 'model.onnx'),
    'PyTorch': Info('pytorch_libtorch', 'model.pt'),
    'TensorRT': Info('tensorrt_plan', 'model.plan'),
    'TF-graph': Info('tensorflow_graphdef', 'model.graphdef'),
    'TF-saved': Info('tensorflow_savedmodel', 'model.savedmodel'),
}


class Config(object):

    def __init__(self, framework: str, path: str):
        self.path = path
        if framework == 'TF-saved':
            self.model_path = f'{path}/1/model.savedmodel'
            self.variable_path = f'{path}/1/model.savedmodel/variables'
            Path(self.variable_path).mkdir(parents=True)
        else:
            self.model_path = f'{path}/1'
            Path(self.model_path).mkdir(parents=True)

        self.framework: str = framework
        # 1보다 크거나 같아야 하고, batching을 지원하지 않는 모델에 대해서는 0으로 설정한다.
        self.max_batch_size: int = 0
        framework = frameworks[framework]
        self.platform: str = framework.platform
        self.filename: str = framework.filename

    def set_name(self, name: str):
        self.name = name

    def set_data(self, name: str, data: list) -> None:
        result = list()
        result.append(f'{name} [')
        for d in data:
            result.append('  {')
            result.append(f'    name: "{d["name"]}"')
            result.append(f'    data_type: {DATATYPES[d["datatype"]]}')
            shape = str(d['shape']).replace('[', '[ ').replace(']', ' ]')
            result.append(f'    dims: {shape}')
            result.append('  },')
        result.append(']')
        result[-2] = result[-2].rstrip(',')
        self.__setattr__(name, result)

    def make_pbtxt(self) -> None:
        with open(f'{self.path}/config.pbtxt', 'w') as pbtxt:
            #pbtxt.write(f'{self.result["name"]}\n')
            pbtxt.write(f'{self.platform}\n')
            pbtxt.write(f'{self.max_batch_size}\n')
            inputs = '\n'.join(self.input)
            pbtxt.write(f'{inputs}\n')
            outputs = '\n'.join(self.output)
            pbtxt.write(f'{outputs}\n')
