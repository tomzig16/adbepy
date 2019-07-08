from subprocess import Popen, PIPE
from os import path, listdir
from platform import system
import re
import pyperclip
import threading
from modules.device import DeviceData
from modules.configs import ConfigDataFields, GetFieldData
from modules.deviceInfoFormat import FormatEssentialDeviceInfo, FormatEssentialDeviceInfoInExcelFormat, PrintInfoTable
from modules.deviceCacher import DeleteCachedDevice, DeleteCacheDir


defaultWhitelistedApps = [
    "com.finalwire.aida64", # AIDA64
    "com.android.vending", # Google play store for Xiaomi from here
    "com.google.android.syncadapters.contacts",
    "com.google.android.gms",
    "com.google.android.gsf",
    "com.google.android.syncadapters.calendar",
    "com.google.android.gsf.login" # To here
]

class CopyDeviceInfoModes:
    minimal = 0
    standard = 1
    full = 2


def GetConnectedDevices(isFullInfo):
    """
    Gets all connected devices. if isFullInfo is set to True it loads all additional device info as well.
    This is optional because sometimes you may not want to do that (for example when removing apps from device)
    """
    proc = Popen(["adb", "devices"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = proc.communicate(input=None, timeout=None)
    daemonStartMessage = "daemon not running; starting now"
    if(err and daemonStartMessage not in err.decode("ascii")):
        print(err)
        return []
    devices = []
    unauthorized = False
    for line in (output.decode("ascii")).splitlines():
        if "\tdevice" in line:
            devData = DeviceData(line.split('\t')[0], isFullInfo)
            devices.append(devData)
        if "\tunauthorized" in line:
            print("Device " + line.split('\t')[0] + " unauthorized")
            unauthorized = True
    if len(devices) == 0:
        if not unauthorized:
            print("There are no devices connected")
            return None
        return None
    return devices

def GetAPKDumpBadging(apkPath):
    """
    Returns dump from .apk file. This dump contains apk badging information - min/recommented OS versions,
    main activity name, bundle id etc.
    """
    try:
        proc = Popen(["aapt", "dump", "badging", apkPath], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = proc.communicate(input=None, timeout=None)
        return output.decode("utf-8")
    except FileNotFoundError:
        sdkLocation = GetFieldData(ConfigDataFields.sdk_location)
        if not sdkLocation:
            print("'aapt' is not recognized command by your system. Here are solutions for this issue:")
            print(" * Add 'aapt' path (usually located in AndroidSDK/build-tools/version/) to environmental PATH variable")
            print(" * Add Android SDK path inside adbepy.config file (write it in '%s' line after equals sign)" % (ConfigDataFields.sdk_location))
            return
        buildToolsFolder = path.join(sdkLocation, "build-tools")
        if not path.exists(buildToolsFolder):
            print("Can't find build-tools folder")
            return None
        directories = listdir(buildToolsFolder)
        directories.sort(reverse=True)
        for btoolsVersion in directories:
            aaptPath = path.join(buildToolsFolder, btoolsVersion + "/aapt")
            if system() == "Windows":
                # if user is on Windows OS
                aaptPath = aaptPath + ".exe"
            if path.isfile(aaptPath):
                proc = Popen([aaptPath, "dump", "badging", apkPath], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                output, err = proc.communicate(input=None, timeout=None)
                if err:
                    print("Error occured: %s" % (err.decode("utf-8").rstrip()))
                    return None
                return output.decode("utf-8")
        print("Can't find 'aapt'. Make sure you have Android build-tools installed.")
        return None

def GetBundleIDFromDump(dump):
    matchObj = re.search(r"package: name='([\w.]*)'", dump, flags=0)
    return matchObj.group(1)

def GetLaunchableActivityFromDump(dump):
    matchObj = re.search(r"launchable-activity: name='([\w.]*)'", dump, flags=0)
    return matchObj.group(1)

def GetDevicesFromNameList(allDevices, neededDevices):
    """
    Takes list of devices and names of needed devices. Scans through allDevices and picks only those with
    elements from neededDevices and returns them.  
    NeededDevices should be device name, model code or serial number. Can be several values separated with a single comma   
    returns list of devices
    """
    output = []
    for deviceName in neededDevices:
        for device in allDevices:
            formattedDName = deviceName.strip().lower()
            if (formattedDName in device.GetPrintableDeviceName().lower()) or (formattedDName == device.GetDeviceID().lower()):
                if device not in output:
                    output.append(device)
    return output

def PrintDevices(args):
    connectedDevices = GetConnectedDevices(True)
    if connectedDevices == None:
        return

    deviceInfo = []
    for device in connectedDevices:
        deviceInfo.append(FormatEssentialDeviceInfo(device, args.battery))
    
    tableLabels = ["Device name", "OS version",
                    "CPU SoC", "GPU renderer", "GLES version", "Serial number"]
    if args.battery:
        tableLabels.append("Bat. %")
        tableLabels.append("Bat. °C")
    PrintInfoTable(deviceInfo, tableLabels)

def PrintDevicesInExcelFormat(args):
    connectedDevices = GetConnectedDevices(True)
    if connectedDevices == None:
        return
    else:
        deviceInfo = "Device name\tOS version\tCPU SoC\tGPU renderer\tGLES version\tSerial number"
        if args.battery:
            deviceInfo += "\tBat. level\tBat. temp."
        deviceInfo += "\n"
        for device in connectedDevices:
            deviceInfo += FormatEssentialDeviceInfoInExcelFormat(device, args.battery)
        print(deviceInfo)

def SingleThread_Install(device, apkPath, shouldLaunch, bundleID, mainActivity):
    isInstalled = device.InstallApk(apkPath)
    if shouldLaunch and isInstalled:
        print("Launching installed application on %s" % (device.GetPrintableDeviceName()) )
        device.LaunchApk(bundleID, mainActivity)

def Install(args):
    """
    Installs application on devices.  
    deviceParam - should be -a, for all connected devices or -s for specific ones  
    targetDevices - if deviceParam is -s then this parameter should tell what devices application should be installed on.
    Otherwise, this parameter can be left empty (application wont use it at all)
    apkPath - path to the apk file. 
    """
    if not path.isfile(args.apkPath) or args.apkPath[-4:] != ".apk":
        print("Given path does not include an .apk file.")
        return
        
    connectedDevices = GetConnectedDevices(False)
    if connectedDevices == None:
        return
    if args.devices:
        connectedDevices = GetDevicesFromNameList(connectedDevices, args.devices)
        if len(connectedDevices) == 0:
            print("Targeted device names are missing.")
            return

    mainActivity = ""
    bundleID = ""
    if not args.no_launch:
        dump = GetAPKDumpBadging(args.apkPath)
        if not dump:
            print("Due to mentioned problems, ADBEpy won't be able to run apk on connected devices...")
            print("However, application will still be installed")
            # "mentioned problems" are printed if any issues occure in GetAPKDumpBadging function
        else:
            bundleID = GetBundleIDFromDump(dump)
            mainActivity = GetLaunchableActivityFromDump(dump)

    installThreads = []
    installingOnDevices = []
    nOfDevices = len(connectedDevices)
    for device in connectedDevices:
        installThreads.append( threading.Thread(target=SingleThread_Install, 
            args=[device, args.apkPath, not args.no_launch, bundleID, mainActivity]) )
        installingOnDevices.append(device)
    print("Starting app installation process on %s devices:" % (nOfDevices))
    for i in range(nOfDevices):
        installThreads[i].start()
        print("%s: %s" % (i+1, installingOnDevices[i].GetPrintableDeviceName()))    

    print("Waiting for threads to finish assigned tasks\n")
    for thrd in installThreads:
        thrd.join()

def ListApps(args):
    """
    List all installed third party apps  
    deviceParam - -a for all devices, -s for specific
    lineWithNames - if deviceParam is -s then this parameter should tell what devices are targeted
    Device names, id or market name should be separated with a single comma. if deviceParam -a then
    this parameter is not used

    As Android 8.0+ denies permission to application path, it will scan it's main activity and that
    process takes some time (per app).
    """
    connectedDevices = GetConnectedDevices(False)
    if connectedDevices == None:
        return
    if args.devices:
        connectedDevices = GetDevicesFromNameList(connectedDevices, args.devices)
        if len(connectedDevices) == 0:
            print("Targeted device names are missing.")
            return

    print("Here are installed third party apps")
    for device in connectedDevices:
        print(device.GetPrintableDeviceName())
        apps = device.GetThirdPartyApps()
        for app in apps:
            print(" * %s" % (app))
        print("")

def SingleThread_PurgeApps(device):
    apps = device.GetThirdPartyApps()
    apps = [singleApp for singleApp in apps if singleApp not in defaultWhitelistedApps]
    for app in apps:
        device.RemoveApp(app)
    print(" * %s - Finished" % (device.GetPrintableDeviceName()))

def PurgeApps(args):
    """
    Purges all third party apps from the device
    This function contains white list and accepts additional bundle ids which will not be removed

    deviceParam - accepts two parameters: -a for all devices and -s for specific device (with device names)
    lineWithNames - string line with devices which should be affected (separate with a single comma)
    whitelistedApps - Additional whitelisted apps
    """
    connectedDevices = GetConnectedDevices(False)
    if connectedDevices == None:
        return
    if args.whitelist:
        defaultWhitelistedApps.extend(args.whitelist)
    if args.devices:
        connectedDevices = GetDevicesFromNameList(connectedDevices, args.devices)
        if len(connectedDevices) == 0:
            print("Targeted device names are missing.")
            return

    print("Removing third party apps from %s devices..." % (len(connectedDevices)))

    purgeThreads = []
    for device in connectedDevices:
        purgeThreads.append( threading.Thread(target=SingleThread_PurgeApps, args=[device]) )

    for i in range( len(purgeThreads) ):
        purgeThreads[i].start()  

    for thrd in purgeThreads:
        thrd.join()

def TurnOff(args):
    """
    Turn off connected devices.  
    deviceParam - -a for all devices, -s for specific
    lineWithNames - if deviceParam is -s then this parameter should tell what devices are targeted
    Device names, id or market name should be separated with a single comma. if deviceParam -a then
    this parameter is not used
    """
    connectedDevices = GetConnectedDevices(False)
    if connectedDevices == None:
        return
    if args.devices:
        connectedDevices = GetDevicesFromNameList(connectedDevices, args.devices)
        if len(connectedDevices) == 0:
            print("Targeted device names are missing.")
            return

    for device in connectedDevices:
        print(device.TurnOff())

def ClearDeviceCache(args):
    """
    Clear device cache in 'adbe/src/res/' (or user defined location)
    With no arguments delets the whole 'dcache' directory
    if '-s serial(s)' is provided (even partly, but from beginning) finds the full cached file(s)
    User needs to confirm the deletion action by entering 'Y' into the CLI
    """
    if args.serial:
        inp = input("You're attempting to delete " +  str(len(args.serial)) + " cached devices. Are you sure? (Y/N) ")
        if inp.upper() == "Y":
            for serial in args.serial:
                print(DeleteCachedDevice(serial))
    else:
        inp = input("You're about to delete all cached devices. Are you sure? (Y/N) ")
        if inp.upper() == "Y":
            print(DeleteCacheDir())

def CopyDeviceInfo(args):
    mode = 0
    if args.mode in ["minimal", "min", "m"]:
        mode = CopyDeviceInfoModes.minimal
    elif args.mode in ["standard", "std", "s"]:
        mode = CopyDeviceInfoModes.standard
    elif args.mode in ["full", "f"]:
        mode = CopyDeviceInfoModes.full
    else:
        print("Given mode not found. Make sure to supply one of existing modes (minimal, standard or full).")
        print("Please, check copy-devices -h for more information")
        return
    connectedDevices = []
    if mode == CopyDeviceInfoModes.minimal:
        connectedDevices = GetConnectedDevices(False)
    else:
        connectedDevices = GetConnectedDevices(True)
    if connectedDevices == None:
        return
    if args.devices:
        connectedDevices = GetDevicesFromNameList(connectedDevices, args.devices)
        if len(connectedDevices) == 0:
            print("Targeted device names are missing.")
            return

    stringForClipboard = ""
    separator = ", "
    if args.use_tabs: separator = "\t"
    counter = 0
    for device in connectedDevices:
        devdata = device.GetFullDeviceData()
        stringForClipboard += devdata["manufa"] + " " + devdata["market_name"] + " (" + devdata["model_code"] + ")" + separator
        if not args.use_tabs: stringForClipboard += "Android "
        stringForClipboard += devdata["os"]
        if mode == CopyDeviceInfoModes.standard or mode == CopyDeviceInfoModes.full:
            stringForClipboard += separator
            if not args.use_tabs: stringForClipboard += "CPU: "
            stringForClipboard += devdata["cpu_soc"] + separator
            if not args.use_tabs: stringForClipboard += "GPU: "
            stringForClipboard += devdata["gpu_renderer"]
        if mode == CopyDeviceInfoModes.full:
            stringForClipboard += separator
            if not args.use_tabs: stringForClipboard += "ABI: "
            stringForClipboard += devdata["cpu_abi"] + separator
            if not args.use_tabs: stringForClipboard += "\nHardware: "
            stringForClipboard += devdata["cpu_hardware"] + separator
            if not args.use_tabs: stringForClipboard += "Fingerprint: "
            stringForClipboard += devdata["fingerprint"]
        stringForClipboard += "\n"
        counter += 1
    pyperclip.copy(stringForClipboard)
    print("Data for %s devices was copied" % (counter))

def GetSavePath(saveLocation):
    if isinstance(saveLocation, list):
        return saveLocation[0]
    else:
        return saveLocation

def TakeScreenshot(args):
    connectedDevices = GetConnectedDevices(False)
    if connectedDevices == None:
        return

    saveLocation = GetSavePath(args.saveLocation)

    if args.devices:
        connectedDevices = GetDevicesFromNameList(connectedDevices, args.devices)
        if len(connectedDevices) == 0:
            print("Targeted device names are missing.")
            return
        
    for device in connectedDevices:
        print(device.TakeScreenshot(args.imageName, saveLocation))

def RecordVideo(args):
    connectedDevices = GetConnectedDevices(False)
    if connectedDevices == None:
        return
    if args.devices:
        connectedDevices = GetDevicesFromNameList(connectedDevices, args.devices)
        if len(connectedDevices) == 0:
            print("Targeted device names are missing.")
            return
    if len(connectedDevices) > 1:
        print("More than one device selected. Recording is available only to one device at the time.")
        return
        
    saveLocation = GetSavePath(args.saveLocation)
    recordingResolution = "720x1280"
    if args.orientation[0] == "land":
        recordingResolution = "1280x720"
    print(connectedDevices[0].RecordVideo(args.videoName, saveLocation, recordingResolution))

def OpenRootFolder(args):
    """
    Opens root directory of ADBEpy
    """
    
    pathToOpen = ''
    if args.directory == 'root':
        pathToOpen = path.abspath(path.join(path.dirname(__file__), '..', '..'))
    elif args.directory[0] == 'screen':
        pathToOpen = path.abspath(GetFieldData(ConfigDataFields.screenshot_location))
    elif args.directory[0] == 'video':
        pathToOpen = path.abspath(GetFieldData(ConfigDataFields.recorded_video_location))
    
    OpenDir(pathToOpen)
    
def OpenDir(dir):
    import os
    PathExists(dir)
    if system() == "Windows":
        os.system('start ' + dir)
    else:
        os.system('open ' + dir)

def PathExists(dir):
    import os
    if not os.path.exists(dir):
        os.makedirs(dir)
        print("Created folder " + os.path.abspath(dir))
