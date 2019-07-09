# Welcome to ADBEpy repository. 

## What is ADBEpy

ADBEpy is simply a tool which helps in development and testing with lots of devices. With this tool you can run different commands on one, specific group or all devices at once.

## Prerequisites and installation

In order to successfully run ADBEpy you must have [Python 3](https://www.python.org/downloads/) and additional python modules installed.

You will need [colorama](https://pypi.org/project/colorama/) (for colorful device output) and [pyperclip](https://pypi.org/project/pyperclip/) (in order to copy device data to clipboard). Feel free to install these packages manually, or you can simply install from `pipreq.txt` given requirements:
```
pip install -r ./pipreq.txt
```
After installing these modules you are ready to run `src/adbe.py` and work, but we made things simplier and added small wrappers which will let you call ADBE from anywhere, by simply writing `adbe [command]`. You can ignore further instructions, but if you want to avoid typing all the paths or aliases yourself follow the steps below (under your OS)

<hr />

### [Windows] Adding adbe.bat to PATH env. variable

Adding `adbe.bat` file to PATH environment variable will let you to call `adbe` command from command line regardless of the path it is open in. To do so, follow these instructions:

* Open _start_ menu and start typing `environment variables`
* Click on "Edit the system environment variables" option
* Press on `Environment variables...` button
* From the `System variables` (or in case you prefer adding ADBE path only for the current user, use table with `User variables for <name>` title) table select `Path` row and press `Edit button`
* In opened window press `New` and write path to the `adbe.bat` file (it is inside downloaded `adbe` folder)
* Save and close all the opened windows and restart command line
* Check if it works by writing `adbe` - ADBEpy help should be printed

### [macOS] Creating adbe.sh alias

Shell aliases are shortcut names for commands. Each alias consists of one word (or even one letter) that you can use instead of a longer command line. 

Here are simple steps on how to add alias on your macOS system. Also, small heads up - I am writing instructions for `bash`. If you are using other shell interpretor (say `tcsh` or `csh` etc) your profile file will be different. So here are instructions for **bash** interpretor on macOS:

* Open `~/.bash_profile` file with any text editor
  * Open terminal
  * Type `open ~/` 
  * Locate `.bash_profile` file (it is hidden or even doesn't exist by default)
    * if `.bash_profile` doesn't exist - create it
* Type `alias adbe='/Path/To/ADBEpy/adbe.sh'`
* Save `.bash_profile`
* Restart terminal
* Check if it has loaded by typing `alias` and checking if alias exists in there or simply by writing `adbe` - ADBEpy help should be printed

<hr />

## Usage

Here's a quick cheatsheet of available commands and their description:

| Command | Description | Short command |
| -------------------------- | -------------------------- | -------------------------- |
| version | prints adbe version | v |
| print-devices | prints devices in table form | d |
| excel-devices | prints devices in string form which is ready to be copied to a google sheet | _None_ |
| copy-devices | copies connected device info to clipboard | dc |
| install | installs application | ins |
| update-supported-devices | updates supported-devices.csv | update |
| list | prints all apps installed on device | _None_ |
| purge | removes all third party apps from device | _None_ |
| turnoff | turns off device | off |
| take-screenshot | takes a screenshot of device's screen | screen |
| record-screen | records the device's display and then saves it as a video | record |
| clear-cache | deletes cached device info. Use if bad information was cached | clear |
| open-dir| opens adbe's directory | opendir |

Each command also accepts `-h` parameter which tells about the command in more in depth info

<hr />

##### If you have any questions regarding ADBEpy feel free to contact me (Tomas - tzigmantavicius@gmail.com) or create an issue/discussion.

