import importlib.util
import io
import json
import pickle
import runpy
import tempfile

#import cv2
import numpy as np
import requests
from PIL import Image

from datatypes import DATATYPE
from grpc_infer import TrtGrpcInference


class InferenceService(object):

    def __init__(self):
        #self.trt_url = os.environ['TRITON_URL']
        #self.onm_url = os.environ['ONM_URL']
        self.trt_url = 'localhost:8001'
        self.onm_url = 'localhost:8005'
        self.models = dict()

        try:
            res = requests.get(url=f'http://{self.onm_url}/models/loaded')
            res = res.json()
            for r in res:
                uuid = r['uuid']
                if r['has_process_file']:
                    r = requests.get(
                        url=f"http://{self.onm_url}/models/file/process/{uuid}")
                    self.create(uuid, r.content)
                else:
                    self.create(uuid, None)
        except:
            print("Server is not running.")

    def create(self, uuid: str, module: bytes):
        if uuid not in self.models:
            model = TrtGrpcInference(url=self.trt_url)
            model.set_metadata(uuid)
            if module:
                module = load_module_from_file(module)
                model.preprocess = module.get('preprocess', None)
                model.postprocess = module.get('postprocess', None)
            else:
                model.preprocess = None
                model.postprocess = None

            self.models[uuid] = model


def image2numpy(data, datatype):
    return np.array(
        Image.open(io.BytesIO(data)), dtype=DATATYPE[datatype])[:, :, :3]


def parse_string(data, datatype=None):
    try:
        data = json.loads(data)
        if datatype:
            data = np.array(data, dtype=DATATYPE[datatype])
    except:
        pass
    return data


def to_image(data, format: str = 'JPEG'):
    ## cv2
    #_, img = cv2.imencode('.png', data[0])
    #return io.BytesIO(img.tobytes())
    # PIL
    if np.ndim(data) == 4:
        data = data[0]
    buf = io.BytesIO()
    image = Image.fromarray(data)
    image.save(buf, format)
    return buf


def to_pickle(data):
    return io.BytesIO(pickle.dumps(data))


def load_module_from_file(module: bytes):
    module = importlib.util.decode_source(module)
    with tempfile.NamedTemporaryFile(suffix='.py', delete=True) as tmpfile:
        tmpfile.write(module.encode('utf8'))
        tmpfile.flush()
        module = runpy.run_path(tmpfile.name)
    return module
