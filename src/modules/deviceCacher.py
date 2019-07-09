import pickle
import os
from os import path

dcachePath = "../res/dcache/"
scriptPath = path.dirname(__file__)
dcachePath = path.join(scriptPath, dcachePath)

class SerializedDeviceData:
    isFullData = False
    serial = ""
    # General
    manuf = ""
    model_code = ""
    market_name = ""
    os_ver = ""
    fingerprint = ""
    # GPU info
    gpu_renderer = ""
    gpu_manufacturer = ""
    gpu_gles = ""
    # CPU info
    cpu_abi = ""
    cpu_soc = ""
    cpu_hardware = ""
    

def GetCachedDeviceData(fname):
    """
    Gets cached device and returns as a deserialized dictionary with isFullData and actual device data (example is given below). 
    All serialized data is expected to be saved inside /src/res/dcache/ folder (folder is created when saving first object). 
    If object does not exist, this function returns `None`
    fname - file name. by default, device names are device serial numbers (without any extension)

    Example of returned device data:
    ```
    {
        "isFullData": True,
        "deviceData": {
            "serial": "someSerialNumber",
            "manufa": "dummyManufacturer",
            ...
        }
    }
    ```
    """
    try:
        with open(path.join(dcachePath, fname), mode="rb") as binaryFile:
            deserializedObj = pickle.load(binaryFile)
            return {
                "isFullData": deserializedObj.isFullData,
                "deviceData": {
                    "serial": deserializedObj.serial,
                    "manufa": deserializedObj.manuf,
                    "model_code": deserializedObj.model_code,
                    "market_name": deserializedObj.market_name,
                    "os": deserializedObj.os_ver,
                    "fingerprint": deserializedObj.fingerprint,
                    "gpu_renderer": deserializedObj.gpu_renderer,
                    "gpu_manufa": deserializedObj.gpu_manufacturer,
                    "gpu_gles": deserializedObj.gpu_gles,
                    "cpu_abi": deserializedObj.cpu_abi,
                    "cpu_soc": deserializedObj.cpu_soc,
                    "cpu_hardware": deserializedObj.cpu_hardware
                }
            }
    except IOError:
        return None
    except pickle.UnpicklingError:
        return None


def SaveCachedDevice(objToSerialize, fname):
    """
    Saves `objToSerialize` with `fname` into /src/res/dcache/fname file
    If folder does not exist - this function will create it
    """
    if not os.path.exists(dcachePath):
        os.makedirs(dcachePath)
    with open(path.join(dcachePath, fname), mode="wb") as dataFile:
        dataFile = pickle.dump(objToSerialize, dataFile)
    

def DeleteCachedDevice(toDelete):
    files = os.listdir(path.abspath(dcachePath))
    filePath = path.abspath(path.join(dcachePath, toDelete))

    for fileName in files:
        if fileName.startswith(toDelete):
            filePath = path.abspath(path.join(dcachePath, fileName))
            os.remove(filePath)
            return "Deleted " + fileName + " from the cache"
    
    return "File " + toDelete + " does not exist in cache directory so nothing was deleted."


def DeleteCacheDir():
    import shutil
    cachePath = path.abspath(dcachePath)
    if path.exists(cachePath):
        shutil.rmtree(cachePath)
        return "Deleted cache directory " + cachePath
    else:
        return "Directory " + cachePath + " does not exist so nothing was deleted."


def CacheDevice(deviceData, isFullData):
    """
    Generates data to serialize and saves it as byte array in a file
    deviceData - dictionary with device data (expected `DeviceData.GetFullDeviceData()`)
    isFullData - is data sent via deviceData variable full (all fields are written).
    """
    dataToSerialize = SerializedDeviceData()
    # set data fields
    dataToSerialize.isFullData = isFullData
    dataToSerialize.serial = deviceData["serial"]
    dataToSerialize.manuf = deviceData["manufa"]
    dataToSerialize.model_code = deviceData["model_code"]
    dataToSerialize.market_name = deviceData["market_name"]
    dataToSerialize.os_ver = deviceData["os"]
    dataToSerialize.fingerprint = deviceData["fingerprint"]
    dataToSerialize.gpu_renderer = deviceData["gpu_renderer"]
    dataToSerialize.gpu_manufacturer = deviceData["gpu_manufa"]
    dataToSerialize.gpu_gles = deviceData["gpu_gles"]
    dataToSerialize.cpu_abi = deviceData["cpu_abi"]
    dataToSerialize.cpu_soc = deviceData["cpu_soc"]
    dataToSerialize.cpu_hardware = deviceData["cpu_hardware"]
    SaveCachedDevice(dataToSerialize, dataToSerialize.serial)

