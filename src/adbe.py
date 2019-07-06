import sys
import argparse

from modules.commands import *
from modules.webrequests import UpdateSupportedDevices
from modules.configs import GenerateConfigFile

version = "1.0.0"

def PrintVersion(args):
    print("ADBEpy version: %s" % version)


helpList = 'Prints package names (bundle identifiers) of all Unity apps installed on a device.'
helpPurge = 'Removes all third party apps from the device.'
helpUpdate = '''As new devices are comming out quite often, supported devices file is changing a lot as well.
If you can not find your brand new device name when you have connected it to pc, please run update-supported-devices command and it will update the list for you.'''

# Main function.
if __name__ == '__main__':

    # Common parser to get device list
    parserDeviceList = argparse.ArgumentParser(add_help=False)
    parserDeviceListGroup = parserDeviceList.add_mutually_exclusive_group()
    parserDeviceListGroup.add_argument('-s', '--specific', nargs='+', help='To specific listed devices', dest='devices')

    # Main arguments parser
    parserMain = argparse.ArgumentParser()
    subCommands = parserMain.add_subparsers(title='subcommands')

    parserInstall = subCommands.add_parser('install', aliases=['ins'], parents=[parserDeviceList], help='Install application (given via path to .apk file) to device(s)')
    parserInstall.set_defaults(func=Install)
    parserInstall.add_argument('apkPath', help='Path to .APK package')
    parserInstall.add_argument('-nl', '--no-launch', action='store_true', help='Doesnt launch application after installing it on a device')

    parserPurge = subCommands.add_parser('purge', parents=[parserDeviceList], help=helpPurge)
    parserPurge.set_defaults(func=PurgeApps)
    parserPurge.add_argument('-w', '--whitelist', nargs='+', help='White listed apps identifiers')

    parserCopyDevices = subCommands.add_parser('copy-devices', aliases=['dc', 'dce'], parents=[parserDeviceList], help='Copy connected device information to clipboard. Available modes: minimal (or min or m) prints only copies minimal info (name, android version);' + 
        ' standard (or std or s) copies standard device info (what minimal does + CPU and GPU); full (or f) copies full info (same as standard + ABI, Hardware and fingerprint)')
    parserCopyDevices.set_defaults(func=CopyDeviceInfo)
    parserCopyDevices.add_argument('-m', '--mode', help='Copying mode. Available modes: minimal, standard and full. For more info check help', default='std')
    parserCopyDevices.add_argument('-ut', '--use-tabs', action='store_true',  help='replaces separator with tabs and ommits field labels. Good for pasting in spreadsheets')
    # if "dce" alias was used lets set -ut flag
    if len(sys.argv) > 1 and sys.argv[1] == "dce":
        parserCopyDevices.set_defaults(use_tabs=True)

    printDevices = subCommands.add_parser('print-devices', aliases=['d'], help='Prints general information about connected devices in a table form')
    printDevices.add_argument('-b', '--battery', action='store_true', help="Include battery data: it's level and temperature")
    printDevices.set_defaults(func=PrintDevices)
    
    excelDevices = subCommands.add_parser('excel-devices', help='Prints general information about connected devices in Excel table string.')
    excelDevices.add_argument('-b', '--battery', action='store_true', help="Include battery data: it's level and temperature")
    excelDevices.set_defaults(func=PrintDevicesInExcelFormat)

    parserScreenshot = subCommands.add_parser('take-screenshot', aliases=['screen'], parents=[parserDeviceList], help='Take a screenshot')
    parserScreenshot.set_defaults(func=TakeScreenshot)
    parserScreenshot.add_argument('-o', '--output', nargs=1, default=GetFieldData(ConfigDataFields.screenshot_location) , dest='saveLocation', help="Path where the image is going to be saved. Can be left empty in order to save to default location") 
    parserScreenshot.add_argument('imageName', help="Name of the screenshot. It will be saved as 'name_deviceSerial'")

    parserVideo = subCommands.add_parser('record-video', aliases=['record'], parents=[parserDeviceList], help='Record a video (only on a single device)')
    parserVideo.set_defaults(func=RecordVideo)
    parserVideo.add_argument('-o', '--output', nargs=1, default=GetFieldData(ConfigDataFields.recorded_video_location), dest='saveLocation', help="Path where the video is going to be saved. Can be left empty in order to save to default location")
    parserVideo.add_argument('videoName', help="Name of the video. It will be saved as 'name_deviceSerial'")
    parserVideo.add_argument('-r', '--orientation', nargs=1, choices={'land', 'port'}, default='port', dest='orientation', help='Recording orientation. Landscape (1280x720) or Portrait (720x1280)')

    openDir = subCommands.add_parser('open-dir', aliases=['opendir'], help='Opens ADBEpy directory')
    openDir.set_defaults(func=OpenRootFolder)
    openDir.add_argument('-d','--dir', '--directory', nargs=1, choices={'screen', 'video'}, default='root', dest='directory', help='Choose to open screenshots or video directory. If not specified opens ADBEpy root folder')

    clearCache = subCommands.add_parser('clear-device-cache', aliases=['clear-cache', 'clear', 'cc'], help="Clears cached devices")
    clearCache.set_defaults(func=ClearDeviceCache)
    clearCache.add_argument('-s', '--serial', nargs='?', default='newest', dest='serial', help="Device serial number (can be truncated)")

    subCommands.add_parser('update-supported-devices', aliases=['usd'], help=helpUpdate).set_defaults(func=UpdateSupportedDevices)
    subCommands.add_parser('generate-new-config', aliases=['config'], help="Generates new adbepy.config file. If it already exists - overrides all it's saved data").set_defaults(func=GenerateConfigFile)
    subCommands.add_parser('list', parents=[parserDeviceList], help=helpList).set_defaults(func=ListApps)
    subCommands.add_parser('shutdown', aliases=['off'], parents=[parserDeviceList], help='Power off devices').set_defaults(func=TurnOff)
    subCommands.add_parser('version', aliases=['v'], help='Displays ADBEpy version').set_defaults(func=PrintVersion)


    if len(sys.argv) > 1:
        args = parserMain.parse_args()
        args.func(args)
    else:
        PrintVersion(None)
        parserMain.print_help()

