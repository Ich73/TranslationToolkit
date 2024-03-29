[![](https://img.shields.io/github/v/release/Ich73/TranslationToolkit?include_prereleases&label=Release)](https://github.com/Ich73/TranslationToolkit/releases/latest)
[![](https://img.shields.io/github/downloads/Ich73/TranslationToolkit/total?label=Downloads)](https://github.com/Ich73/TranslationToolkit/releases)
[![](https://img.shields.io/github/license/Ich73/TranslationToolkit?label=License)](/LICENSE)
# Translation Toolkit
Translation Toolkit is a command line interface to simplify the workflow for translating 3DS games and releasing patches. A lite version without built-in support for `.binJ` and `.e` files can be found at [Ich73/TranslationToolkitLite](https://github.com/Ich73/TranslationToolkitLite).  
  
It uses the following tools:
  * [xdelta](https://github.com/jmacd/xdelta-gpl) ([v3.1.0](https://github.com/jmacd/xdelta-gpl/releases/tag/v3.1.0))
  * [3dstool](https://github.com/dnasdw/3dstool) ([v1.1.0](https://github.com/dnasdw/3dstool/releases/tag/v1.1.0))
  * [ctrtool](https://github.com/3DSGuy/Project_CTR) ([v0.7](https://github.com/3DSGuy/Project_CTR/releases/tag/ctrtool-v0.7))
  * [makerom](https://github.com/3DSGuy/Project_CTR) ([v0.17](https://github.com/3DSGuy/Project_CTR/releases/tag/makerom-v0.17))

## Using Translation Toolkit
You can download the newest version as an executable from the [Release Page](https://github.com/Ich73/TranslationToolkit/releases/latest). Extract the archive and copy `TranslationToolkit.exe` to the root of your translation directory and run it.


## Scripts
### Apply Patches (AP)
This script is used to apply `.xdelta`, `.patJ` and `.patE` patches to all files from the original game.  
  
It searches internally specified folders using the naming scheme `<folder>_<language>` (e.g. `Layout_EN`) for patches and applies them to the files with matching names from the folder `<folder>_<originalLanguage>` (e.g. `Layout_JA`).  
A `<file>.<ext>.xdelta` patch will create `<file>.<ext>`, a `<file>.patJ` patch will create `<file>.binJ` and update `<file>.savJ` if found and a `<file>.patE` patch will create `<file>.e` and update `<file>.savE` if found.  
Only files with a different hash will be overriden by default. The default original language is `JA`.  
  
_Options:_
  * `-f`: Force overriding all files even if their hashes match (e.g. `AP -f`).
  * `-o=<XY>`: Set the original language to `<XY>` (e.g. `AP -o=JA`).

### Create Patches (CP)
This script is used to create `.xdelta`, `.patJ` and `.patE` patches for all edited game files.  
  
It searches internally specified folders using the naming scheme `<folder>_<language>` (e.g. `Layout_EN`) for edited files and creates patches using the files with matching names from the folder `<folder>_<originalLanguage>` (e.g. `Layout_JA`).  
A `<file>.<ext>` file will create a `<file>.<ext>.xdelta` patch, a `<file>.savJ` project file will create a `<file>.patJ` patch and a `<file>.savE` project file will create a `<file>.patE` patch. If no `<file>.savJ` or `<file>.savE` project file is found `<file>.binJ` and `<file>.e` files are used to create the patch.  
Only patches with a different hash will be overriden by default. The default original language is `JA`.  

_Options:_
  * `-f`: Force overriding all patches even if their hashes match (e.g. `CP -f`).
  * `-o=<XY>`: Set the original language to `<XY>` (e.g. `CP -o=JA`).

### Distribute (D)
This script is used to copy all edited game files to a folder that matches the file structure of an extracted `.cia` or `.3ds` file. You can use this to either copy it to your extracted game to create a patched `.cia` or `.3ds` file, or use the `S` script to send the files to your 3DS so [Luma](https://github.com/LumaTeam/Luma3DS) can patch them.  
  
The script requires you to specify a single language (e.g.`EN`) or multiple languages (e.g. `DE,EN`) to distribute. If you specify multiple languages the translations of the first language are used whenever possible. The other languages are used when translations are missing. This works line-by-line for `.binJ` files (if `.patJ` files are found) and file-by-file for all other file types.  
Additionally you need to specify a version. If you choose the original version (`v1.0`) only those files are being distributed. If you chose an updated version (e.g. `v1.1`) the files from the original version and the updated files will be distributed.  
The third value is the directory you want the files to be distributed to.  
  
The script only overrides files with a different hash by default. The default original language is `JA`.

_Options:_
  * `-f`: Force overriding all files even if their hashes match (e.g. `D -f`).
  * `-o=<XY>`: Set the original language to `<XY>` (e.g. `D -o=JA`).

### Send via FTP (S)
This script is used to send the with the `D` script generated folder to 3DS so [Luma](https://github.com/LumaTeam/Luma3DS) can patch the game. For this to work your 3DS needs a FTP Server application, for example [FTPD](https://github.com/mtheall/ftpd), and your 3DS and your PC need to be connected to the same network.  
  
The script requires you to specify the following values to properly send the files:
  * `Folder`: The folder generated by the `D` script.
  * `Title ID`: The ID of the game you want to patch.
  * `3DS IP`: The local IP address of your 3DS. FTPD displays it on the top screen (e.g. **[192.168.1.1]**:5000).
  * `Port`: The port the FTP Server is listening. FTPD displays it on the top screen (e.g. [192.168.1.1]:**5000**).
  * `User`: The registered username. In FTPD you can configure this in the settings by opening the Menu (Y) and selecting Settings. (This can be left blank to connect unauthorized.)
  * `Password`: The registered password. This value can be configured the same way as the username can. (This can be left blank to connect unauthorized.)

The script only overrides files when they are newer than the files on the 3DS by default. Make sure your computer and the 3DS are set to the same time and date.  
  
_Options:_
  * `-f`: Force overriding all files even if the timestamp is newer (e.g. `S -f`).

### Send to Citra (SC)
This script is used to send the with the `D` script generated folder to [Citra](https://citra-emu.org/)'s mod folder.   
  
The script requires you to specify the following values to properly send the files:
  * `Folder`: The folder generated by the `D` script.
  * `Title ID`: The ID of the game you want to patch.

_Options:_
  * `-f`: Force overriding all files even if their hashes match (e.g. `SC -f`).

### Setup Workspace (SW)
This script is used to download the latest patches from the repository, copy the required original files from the extracted CIA and run the `AP` script.
  
The script requires you to specify the following values:
  * `Download URL or Zip File`: The url for downloading all patches as a zip file, or the full path to a local zip file.
  * `CIA Folder`: The folder containing the extracted CIA file.

_Options:_
  * `-f`: Force overriding all files even if their hashes match (e.g. `SW -f`).
  * `-o=<XY>`: Set the original language to `<XY>` (e.g. `SW -o=JA`).

### Update Workspace (UW)
This script is used to download the latest patches from the repository and run the `AP` script.
  
The script requires you to specify the following values:
  * `Download URL or Zip File`: The url for downloading all patches as a zip file, or the full path to a local zip file.

_Options:_
  * `-f`: Force overriding all files even if their hashes match (e.g. `UW -f`).
  * `-o=<XY>`: Set the original language to `<XY>` (e.g. `UW -o=JA`).

### Release Patches (RP)
This script is used to create `banner.xdelta`, `code.xdelta` and `RomFS.xdelta` patches by distributing the files for a given language and version and rebuilding the banner and romFS files.

The script requires you to specify the following values:
  * `Language`: A single language (e.g.`EN`) or multiple languages (e.g. `DE,EN`) to distribute. More information can be found in the details of the `D` script.
  * `Version`: The version to release patches for (e.g. `v1.0`, `v1.1`).
  * `CIA Folder`: The folder containing the extracted CIA file to override. Do _not_ use the folder you used for the `SW` script, but a copy of it.
  * `Patches File`: The archive file to write the patches to.

_Options:_
  * `-o=<XY>`: Set the original language to `<XY>` (e.g. `RP -o=JA`).

### Replace Files (RF)
This script searches the given destination folder for files with the same name as the files in the given source folder and replaces them. This can be used to update multiple `.bclim` files at once when editing `.arc` files.

### Create Saves (CS)
This script is used to apply `.patJ` and `.patE` patches to all files from the original game in order to create `.savJ` and `.savE` files.  
It can also be used to update the decoding tables used in those files by enabling the `-f` option.  
  
It searches internally specified folders using the naming scheme `<folder>_<language>` (e.g. `Message_EN`) for patches and applies them to the files with matching names from the folder `<folder>_<originalLanguage>` (e.g. `Message_JA`).  
A `<file>.patJ` patch will create `<file>.savJ` and a `<file>.patE` patch will `<file>.savE`.  
No files will be overwritten by default. The default original language is `JA`.  
  
The script requires you to specify the following values:
  * `Table File`: The filename of the updated decoding table. This table will be stored inside the save files.
  
_Options:_
  * `-f`: Force overriding all files even if they exist (e.g. `CS -f`).
  * `-o=<XY>`: Set the original language to `<XY>` (e.g. `CS -o=JA`).

### Extract Game (EG)
This script is used to extract a `.cia` or `.3ds` file in order to use the extracted folder for the `SW` script.

The script requires you to specify the following values:
  * `Game File`: The full path to the `.cia` or `.3ds` to extract.
  * `Game Folder`: The full path to the folder the game should be extracted to. This folder can then be used by the `SW` script.

### Rebuild Game (RG)
This script is used to rebuild a `.cia` or `.3ds` file after using the `RP` script.

The script requires you to specify the following values:
  * `Game Folder`: The full path to the folder containing the game files. The folder from the `RP` script can be used for it.
  * `Game File`: The full path to the destination `.cia` or `.3ds` file to create.
  * `CIA Version`: If you want to rebuild a `.cia` file you need to specify a version as a string (e.g. `v1.0.0`) or integer (e.g. `1024`).

### Distribute & Send via FTP (DS)
This script combines the `D` and `S` scripts.

### Distribute & Send to Citra (DSC)
This script combines the `D` and `SC` scripts.


## Configuring Translation Toolkit
When starting the program it searches for a file named `.ttparams` which defines the file structure of the game and the repository. If the file is missing default values will be used. It is a json file with the following, optional parameters:
  * `SEP`: The separator token used in `.binJ` and `.e` files as a string of hexadecimal digits. More information can be found in [BinJ Format](https://github.com/Ich73/BinJEditor/wiki/BinJ-Format) and [E Format](https://github.com/Ich73/BinJEditor/wiki/E-Format).  
    Example: `"E31B"`
  * `XDELTA`: The base names of the folders in the repository and the corresponding file extensions of game files inside those folders for which `.xdelta` patches should be used as an object from string to list of strings.  
    Example: `"Banner": [".bcwav", ".cbmd", ".cgfx"]`
  * `PAT`: The base names of the folders in the repository and the corresponding type of file (`binJ` or `e`), game file extension, save file extension and patch file extension for which `.patJ` or `.patE` patches should be used as an object from string to list of strings.  
    Example: `"Message": ["binJ", ".binJ", ".savJ", ".patJ"]`
  * `PARENT`: The base names of the folders in the repository mapped to the directories in the game files as an object from string to string.  
    Example: `"Banner": "ExtractedBanner"`
  * `UPDATE_ACTIONS`: A list of operations that should be executed when the `UW` or `SW` script is called as a list of lists. Valid actions are:
    * `rename-folder`: Rename the folders with the first argument as the base name to folders with the second argument as the base name.  
      Example: `["rename-folder", ["Code", "ExeFS"]]`
    * `delete-folder`: Delete the folders with the argument as the base name.  
      Example: `["delete-folder", "Code"]`


## For Developers
### Setup
This program is written using [Python 3.10.2](https://www.python.org/downloads/release/python-3102/). Addionally you need [`JTools.py`](https://github.com/Ich73/BinJEditor/blob/master/JTools.py) found in [BinJ Editor](https://github.com/Ich73/BinJEditor).

### Running
You can run the program by using the command `python TranslationToolkit.py`.

### Distributing
To pack the program into a single executable file, [pyinstaller](http://www.pyinstaller.org/) is needed. Simply run the command `pyinstaller TranslationToolkit.spec --noconfirm` and the executable will be created in the `dist` folder.
