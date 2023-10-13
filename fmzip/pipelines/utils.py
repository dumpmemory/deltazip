import os
from pynvml import nvmlInit, nvmlDeviceGetCount
from loguru import logger

nvml_is_initialized = False


def initialize():
    global nvml_is_initialized
    if not nvml_is_initialized:
        # respect CUDA_VISIBLE_DEVICES: https://github.com/gpuopenanalytics/pynvml/issues/28
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        nvmlInit()
        nvml_is_initialized = True
    else:
        pass

def _get_gpu_count():
    initialize()
    return nvmlDeviceGetCount()


def get_gpu_count():
    return len(get_available_gpus())


def get_available_gpus():
    gpus = os.environ.get("CUDA_VISIBLE_DEVICES", None)
    if gpus is None:
        return list(range(_get_gpu_count()))
    else:
        total_gpus = len([x for x in gpus.split(",")])
        return list(range(total_gpus))


def get_submodules(model, key):
    parent = model.get_submodule(".".join(key.split(".")[:-1]))
    target_name = key.split(".")[-1]
    target = model.get_submodule(key)
    return parent, target, target_name
