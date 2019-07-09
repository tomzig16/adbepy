from subprocess import Popen, PIPE, signal
import os
import re

from modules.webrequests import GetCPUHardwareData, UpdateSupportedDevices
from modules.deviceCacher import GetCachedDeviceData, CacheDevice
from modules.deviceInfoFormat import PrintError

CPUHardwareData = {}


def SetCPUHardwareData():
    global CPUHardwareData
    CPUHardwareData = GetCPUHardwareData()


class Amazon:
    """
    Since Amazon devices are not in the 'supported 
    Google Play Store devices' list (supported-devices.csv)
    a seperate dictionary just for these devices is needed

    Dictionary key is 'model_code' and value is 'market_name'
    """
    devices = {
        'KFOT': 'Kindle Fire (2012)',
        'KFJWI': 'Kindle Fire HD 8.9" (2012)',
        'KFTT': 'Kindle Fire HD 7" (2012)',
        'KFTBWI': 'Kindle Fire HD 10 (2015)',
        'KFTHWI': 'Kindle Fire HDX 7" (2013)',
        'KFAPWI': 'Kindle Fire HDX 8.9" (2013)',
        'KFFOWI': 'Fire (2015)',
        'KFMEWI': 'Fire HD 8 (2015)',
        'KFSAWA': 'Fire HDX 8.9 (2014)',
        'SD4930UR': 'Fire Phone',
    }


class DeviceData:
    __serial = ""
    # General
    __manuf = ""
    __model_code = ""
    __market_name = ""
    __os_ver = ""
    __fingerprint = ""

    __battery_level = ""
    __battery_temp = ""
    # GPU info
    __gpu_renderer = ""
    __gpu_manufacturer = ""
    __gpu_gles = ""
    # CPU info
    __cpu_abi = ""
    __cpu_soc = ""
    __cpu_hardware = ""


    def __ExecuteCommand(self, command):
        proc = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = proc.communicate(input=None, timeout=None)

        if "Permission denied" in err.decode("utf-8"):
            raise Exception("Permission denied", err.decode("utf-8"))
        elif "Failure" in err.decode("utf-8"): # in case error is printed in err (most of the time it is printed in output too)
            return err.decode("utf-8").rstrip()
        try:
            return output.decode("utf-8").rstrip()
        except UnicodeDecodeError:
            try:
                return output.decode("windows-1258").rstrip()
            except UnicodeDecodeError:
                return output.decode("ibm866").rstrip()

    def __ExecuteCommandInterruptible(self, command):
        proc = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

        try:
            proc.communicate(input=None, timeout=None)
        except KeyboardInterrupt:
            proc.terminate()

    def __SetGPU(self):
        data = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "dumpsys", "SurfaceFlinger"])
        matchObj = re.search(r"(GLES: )(.+ [\w+-]+ .\..)", data, flags=0)
        # Expected output: "GLES: Qualcomm, Adreno (TM) 540, OpenGL ES 3.2"
        # "GLES: " is in the first group, everything else belongs to second
        elements = matchObj.group(2).split(", ")
        self.__gpu_manufacturer = elements[0]
        self.__gpu_renderer = elements[1]
        self.__gpu_gles = elements[2]

    def __SetCPUHardware(self):
        getprop = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "getprop", "ro.product.board"])
        procCpuInfo = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "cat", "/proc/cpuinfo"])
        matchObj = re.search(r"Hardware.+ ([\w\-]+)", procCpuInfo, flags=0)
        hardwareLine = ""
        if matchObj:
            hardwareLine = matchObj.group(1)
        # hardwareLine = cpuinfo
        # getprop = board

        realBoard = ""
        if getprop in hardwareLine:
            realBoard = hardwareLine
        else:
            realBoard = getprop
        # if CPU Data is not set yet - download it
        if len(CPUHardwareData) == 0:
            SetCPUHardwareData()
        if realBoard.lower() in CPUHardwareData:
            self.__cpu_soc = CPUHardwareData[realBoard.lower()]["SoC"]
            self.__cpu_hardware = CPUHardwareData[realBoard.lower()]["CPU"]
        else:
            self.__cpu_soc = "NOT FOUND"
            self.__cpu_hardware = "NOT FOUND"

    def __SetCPU(self):
        self.__SetCPUHardware()
        self.__cpu_abi = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "getprop", "ro.product.cpu.abi"])

    def __SetDeviceNames(self):
        self.__manuf = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "getprop", "ro.product.manufacturer"]).title()
        self.__model_code = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "getprop", "ro.product.model"])
        if self.__manuf.lower() == 'amazon':
            try:
                self.__market_name = Amazon.devices[self.__model_code]
                return  # Early return for amazon devices since they are not in csv
            except KeyError:
                self.__market_name = "UNKNOWN"
                return

        tProductName = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "getprop", "ro.product.name"])
        tProductDevice = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "getprop", "ro.product.device"])
        
        self.__SetMarketName(tProductName, tProductDevice)
        if(self.__market_name == "-"):
            # If failed to set the name, update CSV file and check if it exists by then
            print("Certain device name was not found, updating supported devices list")
            UpdateSupportedDevices(None)
            self.__SetMarketName(tProductDevice, tProductDevice)



    def __SetMarketName(self, tProductName, tProductDevice):
        supportedDevicesPth = "../res/supported_devices.csv"
        scriptPath = os.path.dirname(__file__)
        targetPath = os.path.join(scriptPath, supportedDevicesPth)
        checkDeviceRange = False
        try:
            f = open(targetPath, mode='r', buffering=-1, encoding="UTF-16")
        except FileNotFoundError:
            from modules.webrequests import UpdateSupportedDevices
            UpdateSupportedDevices("")
            f = open(targetPath, mode='r', buffering=-1, encoding="UTF-16")
        for line in f:
            # Cache the line split since we use it a few times
            splitLine = line.split(",")
            tempName = '-'
            if self.__manuf.lower() in splitLine[0].lower():
                checkDeviceRange = True
                if self.__model_code.lower() == splitLine[3].strip().lower():
                    if(splitLine[1]):
                        self.__market_name = splitLine[1]
                        break
                if self.__model_code.lower() in splitLine[3].lower():
                    tempName = splitLine[1]
                if tProductName.lower() in line.lower():
                    tempName = splitLine[1]
                if tProductDevice.lower() == splitLine[2].lower():
                    tempName = splitLine[1]
            if checkDeviceRange and not self.__manuf.lower() in splitLine[0].lower():
                self.__market_name = tempName
                break
        f.close()


    def __SetDataFromDictionary(self, dictData):
        self.__serial = dictData["serial"]
        self.__manuf = dictData["manufa"]
        self.__model_code = dictData["model_code"]
        self.__market_name = dictData["market_name"]
        self.__os_ver = dictData["os"]
        self.__fingerprint = dictData["fingerprint"]
        self.__gpu_renderer = dictData["gpu_renderer"]
        self.__gpu_manufacturer = dictData["gpu_manufa"]
        self.__gpu_gles = dictData["gpu_gles"]
        self.__cpu_abi = dictData["cpu_abi"]
        self.__cpu_soc = dictData["cpu_soc"]
        self.__cpu_hardware = dictData["cpu_hardware"]


    def __CheckDynamicFields(self, isIndepthInfo):
        """
        Checks if dynamic fields are still up to date. Dynamic fields are:
        * Android OS version
        * Fingerprint
        """
        os_ver = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "getprop", "ro.build.version.release"])
        fingerprint = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "getprop", "ro.build.fingerprint"])
        dataWasChanged = False
        if self.__os_ver != os_ver: 
            self.__os_ver = os_ver
            dataWasChanged = True
        if self.__fingerprint != fingerprint:
            self.__fingerprint = fingerprint
            dataWasChanged = True

        if dataWasChanged:
            CacheDevice(self.GetFullDeviceData(), isIndepthInfo)


    def __SetBatteryData(self):
        batterydump = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "dumpsys", "battery"])
        matchObj = re.search(r"level: (\d+)", batterydump, flags=0)
        self.__battery_level = matchObj.group(1)
        matchObj = re.search(r"temperature: (\d+)", batterydump, flags=0)
        # whole codebase works with strings, so after multiplying, I am converting value back to string
        batteryTemp = round(float(matchObj.group(1)) * 0.1, 1)
        self.__battery_temp = str(batteryTemp) 


    def __LoadTestData(self, testingData):
        self.__manuf = testingData["manufacturer"]
        self.__model_code = testingData["model"]

        self.__SetMarketName(testingData["name"], testingData["device"])


    def __init__(self, deviceID, isIndepthInfo, isForTests=False, testDictData={}):
        """
        Constructor requires deviceID and a boolean if it should go for indepth information
        If isIndepthInfo is true - adbepy will run several shell commands and gather more information about the device itself
        """
        if isForTests:
            self.__LoadTestData(testDictData)
            return

        cachedDeviceData = GetCachedDeviceData(deviceID)
        if cachedDeviceData is not None:
            if cachedDeviceData["isFullData"] == True or isIndepthInfo == cachedDeviceData["isFullData"]:
                self.__SetDataFromDictionary(cachedDeviceData["deviceData"])
                self.__SetBatteryData()
                self.__CheckDynamicFields(isIndepthInfo)
                return
        # If device is not cached or cached version != isIndepthInfo
        self.__serial = deviceID
        self.__SetDeviceNames()
        self.__os_ver = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "getprop", "ro.build.version.release"])
        if isIndepthInfo == True:
            self.__SetBatteryData()
            self.__SetGPU()
            self.__SetCPU()
            self.__fingerprint = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "getprop", "ro.build.fingerprint"])
        CacheDevice(self.GetFullDeviceData(), isIndepthInfo)


# public methods


    def GetFullDeviceData(self):
        """
        Returns dictionary with device's values. Dictionary keys:\n
        serial       - serial device number (ID, same as adb devices prints)  
        manufa       - manufacturer (ex. Samsung)  
        model_code   - ex. GT-I880  
        market_name  - readable name (ex. Galaxy S8)  
        os           - OS version (prints only number: 6.0.1)  
        fingerprint  - device fingerprint  
        gpu_renderer - GPU Renderer, ex. Adreno 420  
        gpu_manufa   - GPU Manufacturer, ex. Qualcomm  
        gpu_gles     - GPU Gles version, ex. GLES 3.0  
        cpu_abi      - CPU ABI version ex. ARMv7-A  
        cpu_soc      - SOC family, ex. Snapdragon 880 MSM8996  
        cpu_hardware - Detailed hardware info (4x FancyKortex A53 @ 5GHz HP and same for LP)
        battery_level- Battery level in percentage
        battery_temp - Battery temperature
        """
        return {
            "serial": self.__serial,
            "manufa": self.__manuf,
            "model_code": self.__model_code,
            "market_name": self.__market_name,
            "os": self.__os_ver,
            "fingerprint": self.__fingerprint,
            "gpu_renderer": self.__gpu_renderer,
            "gpu_manufa": self.__gpu_manufacturer,
            "gpu_gles": self.__gpu_gles,
            "cpu_abi": self.__cpu_abi,
            "cpu_soc": self.__cpu_soc,
            "cpu_hardware": self.__cpu_hardware,
            "battery_level": self.__battery_level,
            "battery_temp": self.__battery_temp
        }

    def InstallApk(self, apkPath):
        """
        Installs an apk from apkPath on a device.
        If installation fails, message with an error is printed and function returns "False"
        otherwise, if installation succeeds - return "True"
        """
        isInstalled = True
        res = self.__ExecuteCommand(["adb", "-s", self.__serial, "install", "-r", apkPath])
        matchObj = re.search(r"Failure ([*[A-Z_0-9]+])", res, flags=0)
        if matchObj is not None:
            # If an error occured - print it to the user
            message = "Failed installing app on %s. Reason: %s" % (self.GetPrintableDeviceName(), matchObj.group(1))
            if "NO_MATCHING_ABIS" in matchObj.group(1):
                message += "\n\t* Make sure you are not building x86 for ARM architecture or vice versa."
            PrintError(message)
            isInstalled = False
        return isInstalled

    def LaunchApk(self, bundleID, mainActivity):
        self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "am", "start", "-n", bundleID + "/" + mainActivity])

    def GetThirdPartyApps(self):
        apps = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "pm", "list", "packages", "-3"]).split("package:")
        del apps[0]
        output = []
        for app in apps:
            output.append(app.rstrip())
        return output

    def TurnOff(self):
        cachedName = self.GetPrintableDeviceName()
        output = self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "reboot", "-p"])
        if "reboot" in output:
            return "Failed to turn off " + cachedName
        else:
            return cachedName + " turned off"

    def RemoveApp(self, appBundleID):
        """
        Uninstall specific application
        """
        self.__ExecuteCommand(["adb", "-s", self.__serial, "uninstall", appBundleID])

    def GetDeviceID(self):
        return self.__serial

    def GetDeviceSerial(self):
        return self.GetDeviceID()

    def GetDeviceName(self):
        return [self.__manuf, self.__market_name, self.__model_code]

    def GetPrintableDeviceName(self):
        return self.__manuf + " " + self.__market_name + " (" + self.__model_code + ")"

    def __PathExists(self, saveLocation):
        if not os.path.exists(saveLocation):
            os.makedirs(saveLocation)
            print("Created folder " + os.path.abspath(saveLocation))

    def TakeScreenshot(self, screenshotName, saveLocation):
        self.__PathExists(saveLocation)

        screenshotName = screenshotName + "_" + self.__serial + ".png"
        self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "screencap", "-p", "/sdcard/screen.png"])
        self.__ExecuteCommand(["adb", "-s", self.__serial, "pull", "/sdcard/screen.png", os.path.join(saveLocation, screenshotName)])
        self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "rm", "/sdcard/screen.png"])
        return "Screenshot saved as: " + os.path.abspath(os.path.join(saveLocation, screenshotName))

    def RecordVideo(self, videoName, saveLocation, recordingResolution):
        self.__PathExists(saveLocation)

        # Xiaomi workaround. It doesn't like naming the files the same way every time.
        import random
        saveName = str(random.randrange(50))
        
        videoName = videoName + "_" + self.__serial + ".mp4"
        print("\nRecording. Press CTRL+C to stop and save the video.\n")
        self.__ExecuteCommandInterruptible(["adb", "-s", self.__serial, "shell", "screenrecord", "--bugreport", "--size " + recordingResolution, "/sdcard/" + saveName + ".mp4"])
        print("Saving.. Please wait.")
        from time import sleep
        sleep(5)  # Sleeping before pulling is needed so that the video is created
        self.__ExecuteCommand(["adb", "-s", self.__serial, "pull", "/sdcard/" + saveName +".mp4", os.path.join(saveLocation, videoName)])
        self.__ExecuteCommand(["adb", "-s", self.__serial, "shell", "rm", "/sdcard/" + saveName + ".mp4"])
        return "Video saved as: " + os.path.abspath(os.path.join(saveLocation, videoName))
