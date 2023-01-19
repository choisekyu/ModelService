import dataclasses
from dataclasses import dataclass

import tritonclient.grpc as client

import utils
from datatypes import DATATYPE


@dataclass
class Data:
    name: str
    shape: list
    datatype: str


class TrtGrpcInference(object):

    def __init__(self, **kwargs):
        self.client = client.InferenceServerClient(**kwargs)

    def set_metadata(self, model_name: str):
        self.model_name = model_name
        metadata = self.client.get_model_metadata(model_name)
        inputs = {d.name: Data(d.name, d.shape, d.datatype)
                  for d in metadata.inputs}
        outputs = {d.name: Data(d.name, d.shape, d.datatype)
                   for d in metadata.outputs}
        self.inputs = inputs
        self.outputs = outputs

    def infer(self, data):
        inputs = []
        for k, v in self.inputs.items():
            if -1 in v.shape:
                inputs.append(
                    client.InferInput(v.name, data[k].shape, v.datatype))
            else:
                inputs.append(client.InferInput(*dataclasses.astuple(v)))
            inputs[-1].set_data_from_numpy(data[k])

        outputs = [client.InferRequestedOutput(k) for k in self.outputs]

        results = self.client.infer(
            model_name=self.model_name,
            inputs=inputs,
            outputs=outputs,
            client_timeout=None,
            compression_algorithm=None)

        output_data = {k: results.as_numpy(k) for k in self.outputs}
        return output_data

    def run(self, data, process, *, with_pre=False, with_post=False):
        if process is None:
            if with_pre and self.preprocess:
                data = self.preprocess(data)
            data = self.infer(data)
            if with_post and self.postprocess:
                data = self.postprocess(data)
        else:
            process = utils.load_module_from_file(process)
            if process.get('preprocess', None) is not None:
                data = process['preprocess'](data)
            data = self.infer(data)
            if process.get('postprocess', None) is not None:
                data = process['postprocess'](data)
        return data
