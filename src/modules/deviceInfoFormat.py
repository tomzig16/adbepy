import sys
from colorama import init, AnsiToWin32, Fore, Back, Style


def FormatEssentialDeviceInfo(device, includeBatteryInfo):
    """
    Formats given device information into one array for printing.\n
    It contains device info as follows:\n
    [Device manufacturer + market name], [OS version], [CPU SoC], [GPU renderer], [GLES version], [device id]\n
    [ 'Samsung Galaxy S5', '6.0.1', 'Snapdragon 801 MSM8974AC', 'Adreno 420', 'GLES 3.0', '12345deviceId' ]
    """
    deviceInfo = device.GetFullDeviceData()
    output = []
    output.append(deviceInfo["manufa"] + " " + deviceInfo["market_name"])
    output.append(deviceInfo["os"])
    output.append(deviceInfo["cpu_soc"])
    output.append(deviceInfo["gpu_renderer"])
    output.append(deviceInfo["gpu_gles"])
    output.append(deviceInfo["serial"])
    if includeBatteryInfo:
        output.append(deviceInfo["battery_level"])
        output.append(deviceInfo["battery_temp"])
    return output


def FormatEssentialDeviceInfoInExcelFormat(device, includeBatteryInfo):
    """
    Formats given device information into one string for copying.\n
    It contains device info as follows:\n
    Device manufacturer + market name\tOS version\tCPU SoC\tGPU renderer\tGLES version\tdevice id\n
    'Samsung Galaxy S5'\t '6.0.1'\t 'Snapdragon 801 MSM8974AC'\t 'Adreno 420'\t 'GLES 3.0'\t '12345deviceId'
    """
    deviceInfo = device.GetFullDeviceData()
    output = ""
    output += deviceInfo["manufa"] + " " + deviceInfo["market_name"] + "\t"
    output += deviceInfo["os"] + "\t"
    output += deviceInfo["cpu_soc"] + "\t"
    output += deviceInfo["gpu_renderer"] + "\t"
    output += deviceInfo["gpu_gles"] + "\t"
    output += deviceInfo["serial"] 
    if includeBatteryInfo:
        output += "\t" + deviceInfo["battery_level"]
        output += "\t" + deviceInfo["battery_temp"]
    output += "\n"
    
    return output


def PrintInfoTable(deviceInfo, columnTitles):
    """
    Prints given info in colored table format. Colors are picked automatically from the list,
    just supply column titles and values.\n
    If amount of column titles is bigger than actual info fields per deviceInfo - last fields will be left empty  
    If amount of fields per device info is bigger than actual amount of column titles, exception is risen 
    """
    # Calculating how much space each column would need
    spacePerColumn = {}
    additionalSpace = 1
    for columnTitle in columnTitles:
        spacePerColumn[columnTitle] = len(columnTitle) + additionalSpace

    for infoLineEntry in deviceInfo:
        i = 0
        for infoEntry in infoLineEntry:
            if(len(infoEntry) + additionalSpace > spacePerColumn[columnTitles[i]]):
                spacePerColumn[columnTitles[i]] = len(
                    infoEntry) + additionalSpace
            i += 1

    init(wrap=False)
    stream = AnsiToWin32(sys.stdout).stream

    colorSelection = [
        [Back.LIGHTYELLOW_EX, Fore.YELLOW],
        [Back.LIGHTGREEN_EX, Fore.GREEN],
        [Back.LIGHTBLUE_EX, Fore.BLUE],
        [Back.LIGHTCYAN_EX, Fore.CYAN],
        [Back.LIGHTMAGENTA_EX, Fore.MAGENTA],
        [Back.LIGHTRED_EX, Fore.RED],
        [Back.LIGHTWHITE_EX, Fore.WHITE]
    ]

    bgID = 0
    print(Fore.BLACK + Style.BRIGHT, sep=" ", end="", file=stream)
    # Printing column names
    for title in columnTitles:
        print("%s%*s%s" % (colorSelection[bgID][0], -spacePerColumn[title],
                           title, Back.RESET), sep=" ", end=" ", file=stream)
        bgID += 1
        if len(colorSelection) == bgID:
            bgID = 0
    print()

    # Sort devices by 'Device name' before printing
    deviceInfo = sorted(deviceInfo, key=lambda x: x[1])

    # Printing device info
    for infoLineEntry in deviceInfo:
        index = 0
        fgID = 0
        for infoEntry in infoLineEntry:
            print("%s%*s%s" % (colorSelection[fgID][1], -spacePerColumn[columnTitles[index]],
                               infoEntry, Fore.RESET), sep=" ", end=" ", file=stream)
            index += 1
            fgID += 1
            if len(colorSelection) == fgID:
                fgID = 0
        print()
    print(Style.RESET_ALL, file=stream, end="")
    print("  => " + str(len(deviceInfo)) + " devices connected\n")


def PrintError(message):
    init(wrap=False)
    stream = AnsiToWin32(sys.stdout).stream
    print("%s%s%s" % (Fore.RED, message, Fore.RESET), file=stream)

