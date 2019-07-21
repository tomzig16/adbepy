from subprocess import Popen, PIPE
import re
import os
from platform import system
from modules.deviceInfoFormat import PrintError

resFolder = os.path.join(os.path.dirname(__file__), "../res/")
configFileName = "adbepy.config"
configFilePath = os.path.join(resFolder, configFileName)

def GetDefaultSDKPath():
    try:
        proc = Popen(["adb"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = proc.communicate(input=None, timeout=None)
        if err.decode("UTF-8"): # TODO test if this is needed
            # if adb is not added to PATH env variables
            userPath = os.path.expanduser("~")
            pathToSDK = "Library/Android/sdk"
            if system() == "Windows":
                pathToSDK = "AppData\\Local\\Android\\Sdk"
            return os.path.join(userPath, pathToSDK)
        else:
            matchObj = re.search(r"Installed as (.+(?=\n))", output.decode("ascii"), flags=0)
            return os.path.abspath(os.path.join(matchObj.group(1), "../../"))
    except FileNotFoundError:
        PrintError("adb command was not found.")
        PrintError("Make sure that Android SDK is installed correctly and adb is added to the PATH environmental variable.")
        PrintError("ADB Extension is a simply an extenion and it can not run without adb.")
        return ""      


class ConfigDataFields:
    sdk_location = "SDK_FOLDER"
    screenshot_location = "SCREENSHOT_LOC"
    recorded_video_location = "RECVID_LOC"

defaultConfigValues = {
    ConfigDataFields.sdk_location:{
        "value": GetDefaultSDKPath(),
        "description": "SDK folder location"
    },
    ConfigDataFields.screenshot_location: {
        "value": os.path.abspath(os.path.join(resFolder, "../../screenshots/")),
        "description": "Default screenshot location"
    },
    ConfigDataFields.recorded_video_location: {
        "value": os.path.abspath(os.path.join(resFolder, "../../videos/")),
        "description": "Default path for recorded videos"
    }
}


def GetFieldData(field):
    """
    field - expected any field from ConfigDataFields class. You can send a simple
    string with property name from adbepy.config file (useful if using custom added
    fields) but it is highly recommended to use ConfigDataFields in order to
    prevent mistakes and stay consistent
    """
    try:
        f = open(configFilePath, mode='r', buffering=-1)
    except FileNotFoundError:
        GenerateConfigFile("")
        return defaultConfigValues[field]["value"]
    for line in f:
        if line[0] == "#": continue
        if field in line: 
            value = line.split('=', 1)[1].rstrip()
            if not value: return defaultConfigValues[field]["value"]
            else: return value

def GetConfigs():
    """
    Returns whole config file as a dictionary. Use ConfigDataFields variables
    as keys for returned dictionary
    """
    output = {}
    try:
        f = open(configFilePath, mode='r', buffering=-1)
        # if file is found
        for line in f:
            if line[0] == "#": continue
            if "=" in line: 
                configProps = line.split('=', 1)
                output[configProps[0]] = configProps[1].rstrip()
                if not output[configProps[0]]:
                    output[configProps[0]] = defaultConfigValues[configProps[0]]["value"]
    except FileNotFoundError:
        GenerateConfigFile("")
        for defKey in defaultConfigValues:
            output[defKey] = defaultConfigValues[defKey]["value"]
    return output

def GenerateConfigFile(args):
    """
    Generates new adbepy.config file (overwrites if such file already exists!)
    """
    if not os.path.exists(resFolder):
        os.mkdir(resFolder)
    f = open(configFilePath, mode='w')
    for defKey in defaultConfigValues:
        f.write("# " + defaultConfigValues[defKey]["description"] + "\n")
        f.write(defKey + "=" + defaultConfigValues[defKey]["value"] + "\n")
    print("New adbepy.config file has been generated. Path: %s" % (os.path.abspath(configFilePath)))
