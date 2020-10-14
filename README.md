# Translation Toolkit
Translation Toolkit is a command line interface to simplify the workflow for translating games.  
It is especially designed for the [DQM2-FanTranslation](https://github.com/Ich73/DQM2-FanTranslation) project.

## Using Translation Toolkit
You can download the newest version as an executable from the [Release Page](https://github.com/Ich73/TranslationToolkit/releases/latest). Copy `TranslationToolkit.exe` to the root of your translation directory.  

Addionally you need `xdelta.exe` which is included in [xdelta UI](http://www.romhacking.net/utilities/598/). Copy this file to the same folder.
  
You can now run `TranslationToolkit.exe` by double clicking it.


## Scripts
### Apply Patches (AP)
This scripts is used to apply `.xdelta`, `.patJ` and `.patE` patches to all files from the original game.  
  
It searches internally specified folders using the naming scheme `<folder>_<language>` (e.g. `Layout_EN`) for patches and applies them to the files with matching names from the folder `<folder>_<originalLanguage>` (e.g. `Layout_JA`).  
A `<file>.<ext>.xdelta` patch will create `<file>.<ext>`, a `<file>.patJ` patch will create `<file>.binJ` and update `<file>.savJ` if found and a `<file>.patE` patch will create `<file>.e` and update `<file>.savE` if found.  
Only files with a different hash will be overriden by default. The default original language is `JA`.  
  
_Options:_
  * `-f`: Force overriding all files even if their hashes match (e.g. `AP -f`).
  * `-o=<XY>`: Set the original language to `<XY>` (e.g. `AP -o=JA`).

### Create Patches (CP)
This script is used to create `.xdelta`, `.patJ` and `.patE` patches for all edited game files.  
  
It searches internally specified folders using the naming scheme `<folder>_<language>` (e.g. `Layout_EN`) for edited files and creates patches using the files with matching names from the folder `<folder>_<originalLanguage>` (e.g. `Layout_JA`).  
A `<file>.<ext>` file will create a `<file>.<ext>.xdelta` patch, a `<file>.savJ` project file will create a `<file>.patJ` patch and a `<file>.savE` project file will create a `<file>.patE` patch.  
Only patches with a different hash will be overriden by default. The default original language is `JA`.  

_Options:_
  * `-f`: Force overriding all patches even if their hashes match (e.g. `CP -f`).
  * `-o=<XY>`: Set the original language to `<XY>` (e.g. `CP -o=JA`).

### Distribute (D)
This script is used to copy all edited game files to a folder that matches the file structure of an extracted `.cia` or `.3ds` file. You can use this to either copy it to your extracted game to create a patched `.cia` or `.3ds` file, or use the [S](#send-via-ftp-s) script to send the files to your 3DS so [Luma](https://github.com/LumaTeam/Luma3DS) can patch them.  
  
The script requires you to specify a single language (e.g.`EN`) or multiple languages (e.g. `DE,EN`) to distribute. If you specify multiple languages the translations of the first language are used whenever possible. The other languages are used when translations are missing. This works line-by-line for `.binJ` files (if `.patJ` files are found) and file-by-file for all other file types.  
  
The script only overrides files with a different hash by default. The default original language is `JA`.

_Options:_
  * `-f`: Force overriding all files even if their hashes match (e.g. `D -f`).
  * `-o=<XY>`: Set the original language to `<XY>` (e.g. `D -o=JA`).

### Send via FTP (S)
This script is used to send the with the [D](#distribute-d) script generated folder to 3DS so [Luma](https://github.com/LumaTeam/Luma3DS) can patch the game. For this to work your 3DS needs a FTP Server application, for example [FTPD](https://github.com/mtheall/), and your 3DS and your PC need to be connected to the same network.  
  
The script requires you to specify the following values to properly send the files:
  * `Title ID`: The ID of the game you want to patch.
  * `3DS IP`: The local IP address of your 3DS. FTPD displays it on the top screen (e.g. **[192.168.1.1]**:5000).
  * `Port`: The port the FTP Server is listening. FTPD displays it on the top screen (e.g. [192.168.1.1]:**5000**).
  * `User`: The registered username. In FTPD you can configure this in the settings by opening the Menu (Y) and selecting Settings. (This can be left blank to connect unauthorized.)
  * `Password`: The registered password. This value can be configured the same way as the username can. (This can be left blank to connect unauthorized.)

The script only overrides files when they are newer than the files on the 3DS by default. Make sure your computer and the 3DS are set to the same time and date.  
  
_Options:_
  * `-f`: Force overriding all files even if their hashes match (e.g. `D -f`).

### Replace Files (RF)
This script searches the given destination folder for files with the same name as the files in the given source folder and replaces them. This can be used to update multiple `.bclim` files at once when editing `.arc` files.


## For Developers
### Setup
This program is written using [Python 3.8](https://www.python.org/downloads/release/python-383/). Addionally you need `JTools.py` found in [BinJ Editor](https://github.com/Ich73/BinJEditor).

### Running
You can run the program by using the command `python TranslationToolkit.py`.

### Distributing
To pack the program into a single executable file, [pyinstaller](http://www.pyinstaller.org/) is needed. Simply run the command `pyinstaller TranslationToolkit.spec --noconfirm` and the executable will be created in the `dist` folder.
