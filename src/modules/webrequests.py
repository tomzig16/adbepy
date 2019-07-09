from os import path
import urllib
import urllib.error
import urllib.request
import json
from modules.configs import ConfigDataFields, GetFieldData

def UpdateSupportedDevices(args):
    url = "http://storage.googleapis.com/play_public/supported_devices.csv"
    resPath = "../res/"
    scriptPath = path.dirname(__file__)
    targetPath = path.join(scriptPath, resPath)
    try:
        urllib.request.urlretrieve(url, targetPath + "supported_devices.csv")
    except FileNotFoundError:
        import os
        os.makedirs(targetPath)
        urllib.request.urlretrieve(url, targetPath + "supported_devices.csv")
    except urllib.error.URLError:
        print("Can't connect to supported_devices.csv source. Please, check internet connection.")
            
def GetCPUHardwareData():
    """
    Sends GET web request to seperate database and returns CPU hardware info.
    https://github.com/xTheEc0/Android-Device-Hardware-Specs-Database
    """
    f = urllib.request.urlopen("https://raw.githubusercontent.com/xTheEc0/Android-Device-Hardware-Specs-Database/master/database.json")
    return json.loads(f.read())
