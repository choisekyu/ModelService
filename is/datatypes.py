from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from fastapi import Form, UploadFile
from pydantic import BaseModel, Field


DATATYPE = {
    'UINT8': np.uint8,
    'INT16': np.int16,
    'INT32': np.int32,
    'INT64': np.int64,
    'FP16': np.float16,
    'FP32': np.float32,
    'FP64': np.float64,
    }


class InferInfo(BaseModel):
    uuid: str
    #return_type: str = Field('pickle', title="111", description="33")
    return_type: str = 'pickle'
    process: Optional[UploadFile] = None
    preprocess: Optional[bool] = False
    postprocess: Optional[bool] = False


@dataclass
class ModelInfo:
    name: str
    version: str
    description: str
    has_process: bool
