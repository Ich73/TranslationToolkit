""" Author: Dominik Beese
>>> Translation Toolkit
<<<
"""

from os import system, listdir, getenv, name as os_name
from os.path import join, splitext, exists, isfile, isdir
from shutil import rmtree
from tempfile import mkdtemp
import json
import webbrowser
from urllib.request import urlopen
import platform
import ssl
import re

from TranslationPatcher import applyPatches, createPatches, distribute, createSaves
from SendViaFTP import sendFiles as sendFilesViaFTP
from SendToCitra import sendFiles as sendFilesToCitra
from FileReplacer import replaceFiles
from WorkspaceManager import downloadAndExtractPatches, extractPatches, doUpdateActions, copyOriginalFiles
from WorkspaceManager import copyPatchedFiles, prepareReleasePatches, createReleasePatches
from WorkspaceManager import checkTool, downloadTool
from GameManager import extractGame, rebuildGame

CONFIG_FILE = 'tt-config.json'

VERSION = 'v2.7.1'
REPOSITORY = r'Ich73/TranslationToolkit'

TOOLS = {
	'xdelta': {
		'version': '3.1.0',
		'win64': {'url': r'https://github.com/jmacd/xdelta-gpl/releases/download/v3.1.0/xdelta3-3.1.0-x86_64.exe.zip', 'exe': 'xdelta.exe'},
		'win32': {'url': r'https://github.com/jmacd/xdelta-gpl/releases/download/v3.1.0/xdelta3-3.1.0-i686.exe.zip', 'exe': 'xdelta.exe'},
		'linux64': {'url': r'https://github.com/Ich73/xdelta-LinuxBuilds/releases/download/v3.1.0/xdelta3-linux_x86_64.zip', 'exe': 'xdelta'},
	},
	'3dstool': {
		'version': '1.1.0',
		'win64': {'url': r'https://github.com/dnasdw/3dstool/releases/download/v1.1.0/3dstool.zip', 'exe': '3dstool.exe'},
		'win32': {'url': r'https://github.com/dnasdw/3dstool/releases/download/v1.1.0/3dstool.zip', 'exe': '3dstool.exe'},
		'linux64': {'url': r'https://github.com/dnasdw/3dstool/releases/download/v1.1.0/3dstool_linux_x86_64.tar.gz', 'exe': '3dstool'},
	},
	'ctrtool': {
		'version': '0.7',
		'win64': {'url': r'https://github.com/3DSGuy/Project_CTR/releases/download/ctrtool-v0.7/ctrtool-v0.7-win_x86_64.zip', 'exe': 'ctrtool.exe'},
		'win32': {'url': r'https://github.com/Ich73/Project-CTR-WindowsBuilds/releases/download/ctrtool-v0.7/ctrtool-v0.7-win_i686.zip', 'exe': 'ctrtool.exe'},
		'linux64': {'url': r'https://github.com/3DSGuy/Project_CTR/releases/download/ctrtool-v0.7/ctrtool-v0.7-ubuntu_x86_64.zip', 'exe': 'ctrtool'},
	},
	'makerom': {
		'version': '0.17',
		'win64': {'url': r'https://github.com/3DSGuy/Project_CTR/releases/download/makerom-v0.17/makerom-v0.17-win_x86_64.zip', 'exe': 'makerom.exe'},
		'win32': {'url': r'https://github.com/Ich73/Project-CTR-WindowsBuilds/releases/download/makerom-v0.17/makerom-v0.17-win_i686.zip', 'exe': 'makerom.exe'},
		'linux64': {'url': r'https://github.com/3DSGuy/Project_CTR/releases/download/makerom-v0.17/makerom-v0.17-ubuntu_x86_64.zip', 'exe': 'makerom'},
	}
}


###########
## Setup ##
###########

# check os
if 'windows' in platform.system().lower(): opSys = 'win'
else: opSys = 'linux'
if '64' in platform.machine(): opSys += '64'
else: opSys += '32'

# set windows taskbar icon
try:
	from ctypes import windll
	appid = 'translationtoolkit.' + VERSION
	windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
except: pass

# config
class Config:
	cfg = None
	
	def loadConfig():
		if Config.cfg is not None: return
		if not exists(CONFIG_FILE):
			Config.cfg = dict()
			return
		try:
			with open(CONFIG_FILE, 'r') as file:
				Config.cfg = json.load(file)
		except:
			Config.cfg = dict()
	
	def saveConfig():
		with open(CONFIG_FILE, 'w') as file:
			json.dump(Config.cfg, file)
	
	def get(key, default = None):
		Config.loadConfig()
		value = Config.cfg.get(key)
		if value is None:
			Config.set(key, default)
			return default
		return value
	
	def set(key, value):
		Config.cfg[key] = value
		Config.saveConfig()


#############
## Updates ##
#############

def checkUpdates():
	try:
		# query api
		latest = r'https://api.github.com/repos/%s/releases/latest' % REPOSITORY
		with urlopen(latest, timeout = 1, context=ssl._create_unverified_context()) as url:
			data = json.loads(url.read().decode())
		tag = data['tag_name']
		link = data['html_url']
		
		# compare versions
		def ver2int(s):
			if s[0] == 'v': s = s[1:]
			v = s.split('.')
			return sum([int(k) * 100**(len(v)-i) for i, k in enumerate(v)])
		current_version = ver2int(VERSION)
		tag_version     = ver2int(tag)
		ignore_version  = ver2int(Config.get('ignoreVersion', 'v0.0.0'))
		if current_version >= tag_version or ignore_version >= tag_version: return
		
		# show message
		printTitleBox()
		print(' '*m + 'A new version of Translation Toolkit is available.')
		print()
		print(' '*m + 'Current Version: %s' % VERSION)
		print(' '*m + 'New Version:     %s' % tag)
		print()
		printCategory('Options')
		printOption('D', 'Download the latest release')
		printOption('C', 'Continue with the current version')
		printOption('I', 'Ignore version %s' % tag)
		print()
		print('_'*(w+m+4+m))
		print()
		
		# parse command
		print('Enter command:')
		command = input('>> ').strip()
		script = command.upper() if command else ''
		
		if script == 'D': webbrowser.open(link)
		elif script == 'C': pass
		elif script == 'I': Config.set('ignoreVersion', tag)
	except Exception: pass

def checkTools():
	# check xdelta
	version, url = Config.get('xdelta', (TOOLS['xdelta']['version'], TOOLS['xdelta'][opSys]['url']))
	if not checkTool(TOOLS['xdelta'][opSys]['exe'], version, args = '-V'):
		downloadTool(url, TOOLS['xdelta'][opSys]['exe'])
	
	# check 3dstool
	version, url = Config.get('3dstool', (TOOLS['3dstool']['version'], TOOLS['3dstool'][opSys]['url']))
	if not checkTool(TOOLS['3dstool'][opSys]['exe'], version):
		downloadTool(url, TOOLS['3dstool'][opSys]['exe'])
	
	# check ctrtool
	version, url = Config.get('ctrtool', (TOOLS['ctrtool']['version'], TOOLS['ctrtool'][opSys]['url']))
	if not checkTool(TOOLS['ctrtool'][opSys]['exe'], version):
		downloadTool(url, TOOLS['ctrtool'][opSys]['exe'])
	
	# check makerom
	version, url = Config.get('makerom', (TOOLS['makerom']['version'], TOOLS['makerom'][opSys]['url']))
	if not checkTool(TOOLS['makerom'][opSys]['exe'], version):
		downloadTool(url, TOOLS['makerom'][opSys]['exe'])


#############
## Scripts ##
#############

def verifyStart():
	command = 'n'
	while command != 'y':
		command = input('Start script? [y/n] ')
		if command == 'n':
			menu()
			return False
	print()
	return True

def showEnd():
	print()
	input('Press Enter to return to menu...')
	menu()

def askParamter(name, key, default = '', description = None, hide_fallback = False, fallback = None):
	print('~', ' '.join(w.capitalize() if w[0].islower() else w for w in name.split()), '~')
	if key is not None: fallback = Config.get(key, default)
	for line in description: print(line)
	print('Enter %s [%s]:' % (name, fallback if not hide_fallback else '***'))
	command = input('>> ').strip() or fallback
	if key is not None: Config.set(key, command)
	print()
	return command

def AP(original_language, force_override):
	cls()
	if not verifyStart(): return
	applyPatches(xdelta=TOOLS['xdelta'][opSys]['exe'], original_language=original_language, force_override=force_override)
	showEnd()

def CP(original_language, force_override):
	cls()
	if not verifyStart(): return
	createPatches(xdelta=TOOLS['xdelta'][opSys]['exe'], original_language=original_language, force_override=force_override)
	showEnd()

def _D():
	languages = askParamter(
		name = 'language',
		description = [
			'You can enter a single language (e.g. \'EN\') or multiple languages (e.g. \'DE,EN\').',
			'Translations of additionally languages are used when translations of the first language are missing.'
		],
		key = 'D.lang',
		default = 'EN'
	)
	languages = tuple(languages.split(','))
	
	version = askParamter(
		name = 'version',
		description = [
			'The version of the game you want to play.',
			'You can enter an updated version (e.g. \'v1.1\') or the original version (e.g. \'v1.0\').'
		],
		key = 'D.ver',
		default = 'v1.0'
	)
	
	lang_ver = '%s::%s' % ('-'.join(languages), version)
	destination_dirs = Config.get('D.dests', dict())
	destination_dir = askParamter(
		name = 'destination folder',
		description = ['This folder will contain all edited files with the correct file structure.'],
		key = None,
		fallback = destination_dirs.get(lang_ver, '_dist_%s_%s' % (version, '_'.join(languages)))
	)
	destination_dirs[lang_ver] = destination_dir
	Config.set('D.dests', destination_dirs)
	
	return (languages, version, destination_dir)

def D(original_language, force_override):
	cls()
	
	languages, version, destination_dir = _D()
	
	print('Language:', ', '.join(languages))
	print('Version:', version)
	print('Destination Folder:', destination_dir)
	print()
	
	if not verifyStart(): return
	distribute(languages=languages, version=version, version_only=False, original_language=original_language, destination_dir=destination_dir, force_override=force_override)
	showEnd()

def _S():
	title_id = askParamter(
		name = 'title ID',
		description = ['The title ID of the game to patch.'],
		key = 'S.titleid',
		default = '00040000000cf500'
	)
	
	ip = askParamter(
		name = '3DS IP',
		description = ['The IP address of the 3DS for the FTP connection.'],
		key = 'S.ip',
		default = '192.168.1.1',
	)
	
	port = int(askParamter(
		name = 'port',
		description = ['The port for the FTP connection.'],
		key = 'S.port',
		default = '5000'
	))
	
	user = askParamter(
		name = 'user',
		description = ['The username for the FTP connection.'],
		key = 'S.user'
	)
	
	passwd = askParamter(
		name = 'password',
		description = ['The password for the FTP connection.'],
		key = 'S.passwd',
		hide_fallback = True
	)
	
	return (title_id, ip, port, user, passwd)

def S(force_override):
	cls()
	
	while True:
		source_dir = askParamter(
			name = 'folder',
			description = ['The folder to send. This is the folder generated by the \'D\' script.'],
			key = 'S.source',
			default = '_dist'
		)
		if isdir(source_dir): break
	
	title_id, ip, port, user, passwd = _S()
	
	print('Folder:', source_dir)
	print('Title ID:', title_id)
	print()
	
	if not verifyStart(): return
	sendFilesViaFTP(source_dir=source_dir, title_id=title_id, ip=ip, port=port, user=user, passwd=passwd, force_override=force_override)
	showEnd()

def DS(original_language, force_override):
	cls()
	
	languages, version, destination_dir = _D()
	title_id, ip, port, user, passwd = _S()
	
	print('Language:', ', '.join(languages))
	print('Version:', version)
	print('Destination Folder:', destination_dir)
	print('Title ID:', title_id)
	print()
	
	if not verifyStart(): return
	
	print('~~ Distribute ~~')
	distribute(languages=languages, version=version, version_only=False, original_language=original_language, destination_dir=destination_dir, force_override=force_override)
	
	print()
	print()
	print('~~ Send via FTP ~~')
	sendFilesViaFTP(source_dir=destination_dir, title_id=title_id, ip=ip, port=port, user=user, passwd=passwd, force_override=force_override)
	
	showEnd()

def _SC():
	title_id = askParamter(
		name = 'title ID',
		description = ['The title ID of the game to patch.'],
		key = 'SC.titleid',
		default = '00040000000cf500'
	)
	
	user_dir = join(getenv('PROGRAMFILES'), 'Citra', 'user') if getenv('PROGRAMFILES') is not None else ''
	appdata_dir = join(getenv('APPDATA'), 'Citra') if getenv('APPDATA') is not None else ''
	while True:
		citra_dir = askParamter(
			name = 'Citra folder',
			description = ['Citra\'s mod folder to which the patched files should be copied.'],
			key = 'SC.citra',
			default = appdata_dir if not exists(user_dir) else user_dir
		)
		if isdir(citra_dir): break
	
	return (title_id, citra_dir)

def SC(force_override):
	cls()
	
	while True:
		source_dir = askParamter(
			name = 'folder',
			description = ['The folder to send. This is the folder generated by the \'D\' script.'],
			key = 'SC.source',
			default = '_dist'
		)
		if isdir(source_dir): break
	
	title_id, citra_dir = _SC()
	
	print('Folder:', source_dir)
	print('Title ID:', title_id)
	print('Citra Folder:', citra_dir)
	print()
	
	if not verifyStart(): return
	sendFilesToCitra(source_dir=source_dir, title_id=title_id, citra_dir=citra_dir, force_override=force_override)
	showEnd()

def DSC(original_language, force_override):
	cls()
	
	languages, version, destination_dir = _D()
	title_id, citra_dir = _SC()
	
	print('Language:', ', '.join(languages))
	print('Version:', version)
	print('Destination Folder:', destination_dir)
	print('Title ID:', title_id)
	print('Citra Folder:', citra_dir)
	print()
	
	if not verifyStart(): return
	
	print('~~ Distribute ~~')
	distribute(languages=languages, version=version, version_only=False, original_language=original_language, destination_dir=destination_dir, force_override=force_override)
	
	print()
	print()
	print('~~ Send to Citra ~~')
	sendFilesToCitra(source_dir=destination_dir, title_id=title_id, citra_dir=citra_dir, force_override=force_override)
	
	showEnd()

def SW(original_language, force_override):
	cls()
	
	download_url_or_zip_file = askParamter(
		name = 'download URL or zip file',
		description = ['The url for downloading all patches as a zip file, or the full path to a local zip file.'],
		key = 'UW.url'
	)
	is_download_url = not exists(download_url_or_zip_file)
	
	while True:
		cia_dir = askParamter(
			name = 'CIA folder',
			description = ['The full path to the folder containing the extracted CIA file.'],
			key = 'SW.cia'
		)
		if isdir(cia_dir): break
	
	updates = list()
	fallbacks = Config.get('SW.updates', list())
	while True:
		print('Do you wish to add an update? [y/n]')
		fallback = 'y' if len(fallbacks) > len(updates) else 'n'
		print('Enter your choice [%s]:' % fallback)
		command = input('>> ')
		print()
		if not command: command = fallback
		if command != 'y': break
		update_ver = askParamter(
			name = 'update version',
			description = ['The update version you want to add (e.g. \'v1.1\').'],
			key = None,
			fallback = fallbacks[len(updates)][0] if len(fallbacks) > len(updates) else ''
		)
		while True:
			update_cia_dir = askParamter(
				name = 'update CIA folder',
				description = ['The full path to the folder containing the extracted update CIA file.'],
				key = None,
				fallback = fallbacks[len(updates)][1] if len(fallbacks) > len(updates) else ''
			)
			if isdir(update_cia_dir): break
		updates.append((update_ver, update_cia_dir))
	Config.set('SW.updates', updates)
	
	print('CIA Folder:', cia_dir)
	if is_download_url: print('Download URL:', download_url_or_zip_file)
	else: print('Zip File:', download_url_or_zip_file)
	for ver, dir in updates:
		print('Update %s Folder:' % ver, dir)
	print()
	
	if not verifyStart(): return
	
	if is_download_url:
		print('~~ Download Patches ~~')
		if not downloadAndExtractPatches(download_url_or_zip_file):
			showEnd()
			return
	else:
		print('~~ Extract Patches ~~')
		if not extractPatches(download_url_or_zip_file):
			showEnd()
			return
	
	print()
	print()
	print('~~ Update Actions ~~')
	doUpdateActions()
	
	print()
	print()
	print('~~ Copy Original Files ~~')
	if not copyOriginalFiles(cia_dir, version=None, original_language=original_language):
		showEnd()
		return
	
	for ver, dir in updates:
		print()
		print()
		print('~~ Copy Update %s Files ~~' % ver)
		if not copyOriginalFiles(dir, version=ver, original_language=original_language):
			showEnd()
			return
	
	print()
	print()
	print('~~ Apply Patches ~~')
	applyPatches(xdelta=TOOLS['xdelta'][opSys]['exe'], original_language=original_language, force_override=force_override)
	
	showEnd()

def UW(original_language, force_override):
	cls()
	
	download_url_or_zip_file = askParamter(
		name = 'download URL or zip file',
		description = ['The url for downloading all patches as a zip file, or the full path to a local zip file.'],
		key = 'UW.url'
	)
	is_download_url = not exists(download_url_or_zip_file)
	
	if is_download_url: print('Download URL:', download_url_or_zip_file)
	else: print('Zip File:', download_url_or_zip_file)
	print()
	
	if not verifyStart(): return
	
	if is_download_url:
		print('~~ Download Patches ~~')
		if not downloadAndExtractPatches(download_url_or_zip_file):
			showEnd()
			return
	else:
		print('~~ Extract Patches ~~')
		if not extractPatches(zip_file=download_url_or_zip_file):
			showEnd()
			return
	
	print()
	print()
	print('~~ Update Actions ~~')
	doUpdateActions()
	
	print()
	print()
	print('~~ Apply Patches ~~')
	applyPatches(xdelta=TOOLS['xdelta'][opSys]['exe'], original_language=original_language, force_override=force_override)
	
	showEnd()

def RP(original_language):
	cls()
	
	languages = askParamter(
		name = 'language',
		description = [
			'You can enter a single language (e.g. \'EN\') or multiple languages (e.g. \'DE,EN\').',
			'Translations of additionally languages are used when translations of the first language are missing.'
		],
		key = 'RP.lang',
		default = 'EN'
	)
	languages = tuple(languages.split(','))
	
	version = askParamter(
		name = 'version',
		description = ['You can enter an updated version (e.g. \'v1.1\') or the original version (e.g. \'v1.0\').'],
		key = 'RP.ver',
		default = 'v1.0'
	)
	
	lang_ver = '%s::%s' % ('-'.join(languages), version)
	cia_dirs = Config.get('RP.cias', dict())
	while True:
		cia_dir = askParamter(
			name = 'CIA folder',
			description = ['The full path to the folder containing the extracted CIA file',
							'you want to update and create patches for.'],
			key = None,
			fallback = cia_dirs.get(lang_ver, '')
		)
		if not isdir(cia_dir): continue
		cia_dirs[lang_ver] = cia_dir
		break
	Config.set('RP.cias', cia_dirs)
	
	patches_filenames = Config.get('RP.patchfiles', dict())
	patches_filename = askParamter(
		name = 'patches file',
		description = ['The filename for the archive containing the patches.'],
		key = None,
		fallback = patches_filenames.get(lang_ver, join('_release', 'Patches-%s-%s.zip' % (version, '-'.join(languages))))
	)
	patches_filenames[lang_ver] = patches_filename
	Config.set('RP.patchfiles', patches_filenames)
	
	print('Language:', ', '.join(languages))
	print('Version:', version)
	print('CIA Folder:', cia_dir)
	print('Patches File:', patches_filename)
	print()
	
	if not verifyStart(): return
	
	print('~~ Prepare Release Patches ~~')
	prepareReleasePatches(cia_dir, original_language=original_language)
	
	print()
	print()
	print('~~ Distribute Patches ~~')
	temp_dir = mkdtemp()
	distribute(languages=languages, version=version, version_only=True, original_language=original_language, destination_dir=temp_dir, force_override=True, verbose=1)
	
	print()
	print()
	print('~~ Copy Patched Files ~~')
	if not copyPatchedFiles(temp_dir, cia_dir):
		showEnd()
		return
	
	print()
	print()
	print('~~ Create Release Patches ~~')
	createReleasePatches(cia_dir, patches_filename, xdelta=TOOLS['xdelta'][opSys]['exe'], dstool=TOOLS['3dstool'][opSys]['exe'], original_language=original_language)
	
	rmtree(temp_dir)
	showEnd()

def RF():
	cls()
	
	while True:
		source_dir = askParamter(
			name = 'source folder',
			description = ['The folder containing the files to be copied.'],
			key = 'RF.source'
		)
		if not isdir(source_dir): continue
		source_files = [join(source_dir, f) for f in listdir(source_dir)]
		break
	
	while True:
		destination_dir = askParamter(
			name = 'destination folder',
			description = ['The folder in which to replace the files.'],
			key = 'RF.dest'
		)
		if isdir(destination_dir): break
	
	print('Source Folder:', source_dir)
	print('Destination Folder:', destination_dir)
	print()
	
	if not verifyStart(): return
	replaceFiles(source_files=source_files, destination_dir=destination_dir)
	showEnd()

def CS(original_language, force_override):
	cls()
	
	while True:
		table_file = askParamter(
			name = 'table file',
			description = ['The decoding table file.'],
			key = 'CS.table'
		)
		if isfile(table_file): break
	
	print('Table File:', table_file)
	print()
	
	if not verifyStart(): return
	createSaves(table_file=table_file, original_language=original_language, force_override=force_override)
	showEnd()

def EG():
	cls()
	
	while True:
		game_file = askParamter(
			name = 'game file',
			description = ['The full path to the CIA or 3DS file to extract.'],
			key = 'EG.gamefile'
		)
		if isfile(game_file): break
	
	game_dir = askParamter(
		name = 'game folder',
		description = ['The full path to the folder the game should be extracted to.'],
		key = 'EG.gamedir'
	)
	
	print('Game File:', game_file)
	print('Game Folder:', game_dir)
	print()
	
	if not verifyStart(): return
	extractGame(game_file=game_file, game_dir=game_dir, dstool=TOOLS['3dstool'][opSys]['exe'], ctrtool=TOOLS['ctrtool'][opSys]['exe'])
	showEnd()

def RG():
	cls()
	
	while True:
		game_dir = askParamter(
			name = 'game folder',
			description = ['The full path to the folder containing the game files.'],
			key = 'RG.gamedir'
		)
		if isdir(game_dir): break
	
	game_file = askParamter(
		name = 'game file',
		description = ['The full path to the destination CIA or 3DS file.'],
		key = 'RG.gamefile'
	)
	
	def version2int(s):
		s = s[1:] # remove v
		v = [int(x) for x in s.split('.')] # split into parts
		v += [0]*(3-len(v)) # add missing parts
		return v[0]*2**10 + v[1]*2**4 + v[2] # convert to number
	
	mode = splitext(game_file)[1][1:].lower()
	if mode != '3ds':
		while True:
			version = askParamter(
				name = 'CIA version',
				description = ['The version of the rebuilt CIA as a string (v1.0.0) or integer (1024).'],
				key = 'RG.version'
			)
			if re.match('^v\d\.\d(\.\d)?$', version) or version.isdigit(): break
		version = int(version) if version.isdigit() else version2int(version)
	else: version = 0
	
	print('Game Folder:', game_dir)
	print('Game File:', game_file)
	if mode != '3ds': print('CIA Version:', version)
	print()
	
	if not verifyStart(): return
	rebuildGame(game_dir=game_dir, game_file=game_file, version=version, dstool=TOOLS['3dstool'][opSys]['exe'], makerom=TOOLS['makerom'][opSys]['exe'])
	showEnd()


##########
## Menu ##
##########

m = 2 # left margin
w = 96 # width of title box

def cls():
	""" Clears the screen. """
	system('cls' if os_name in ['nt', 'dos'] else 'clear')

def rzs(width = w+m+4+m, height = 41):
	""" Sets the width and height of the screen. """
	system('mode con: cols=%d lines=%d' % (width, height) if os_name in ['nt', 'dos'] else 'printf "\033[8;%d;%dt"' % (height, width))

def printTitleBox():
	cls()
	def title(msg=''): print(' '*m + '║ ' + ' '*int((w-len(msg))/2) + msg + ' '*(w-len(msg)-int((w-len(msg))/2)) + ' ║')
	print()
	print(' '*m + '╔' + '═'*(w+2) + '╗')
	title('Translation Toolkit ' + VERSION)
	title('(https://github.com/%s)' % REPOSITORY)
	print(' '*m + '╚' + '═'*(w+2) + '╝')
	print()

def printCategory(text):
	print(' '*m + '~ ' + text + ' ~')
	print()

def printOption(cmd, text, cmd2=None, text2=None):
	print(' '*m + '*', cmd, ':', text, end='')
	if cmd2 and text2: print(' '*(w//2-len(cmd)-len(text)-4), '*', cmd2, ':', text2)
	else: print()

def printInfo(text):
	print(' '*(m+4), end=' ')
	c = 0
	for word in text.split():
		if c + len(word) > w-m-2:
			c = 0
			print()
			print(' '*(m+4), end=' ')
		print(word, end=' ')
		c += len(word) + 1
	print()
	print()

def menu():
	## Print Title and Options ##
	
	printTitleBox()
	
	printCategory('Scripts')
	printOption('AP', 'Apply Patches')
	printInfo('Uses xdelta patches to patch files from the original game. Applies .patJ patches to .binJ and .savJ files. Applies .patE patches to .e and .savE files.')
	printOption('CP', 'Create Patches')
	printInfo('Creates xdelta patches for all edited game files. Creates .patJ patches from .savJ or .binJ files. Creates .patE patches from .savE or .e files.')
	printOption('D', 'Distribute')
	printInfo('Copies all edited game files to a folder. The folder can be used by the \'S\' and \'SC\' script for a LayeredFS patch. Or you can copy it to your extracted cia to create a translated cia.')
	printOption('S', 'Send via FTP')
	printInfo('Sends the folder from the \'D\' script to the 3DS for Luma\'s LayeredFS patching.')
	printOption('SC', 'Send to Citra')
	printInfo('Sends the folder from the \'D\' script to Citra\'s mod folder for LayeredFS patching.')
	printOption('SW', 'Setup Workspace', 'EG', 'Extract Game')
	printOption('UW', 'Update Workspace', 'RG', 'Rebuild Game')
	printOption('RP', 'Release Patches')
	printOption('RF', 'Replace Files', 'DS', 'Distribute & Send via FTP')
	printOption('CS', 'Create Saves', 'DSC', 'Distribute & Send to Citra')
	
	print()
	printCategory('Options')
	printOption('-f', 'Force Override All Files (e.g. \'AP -f\')')
	printOption('-o=<XY>', 'Override Original Language (e.g. \'AP -o=JA\')')
	
	#print()
	print('_'*(w+m+4+m))
	print()
	
	## Parse Command ##
	
	print('Enter command:')
	command = input('>> ').split()
	
	script = command[0].upper() if command else ''
	
	force_override = False
	original_language = 'JA'
	for option in command[1:]:
		if option == '-f': force_override = True
		elif option.startswith('-o='): original_language = option[3:]
	
	## Call Script ##
	
	if script == 'AP': AP(original_language, force_override)
	elif script == 'CP': CP(original_language, force_override)
	elif script == 'D': D(original_language, force_override)
	elif script == 'S': S(force_override)
	elif script == 'SC': SC(force_override)
	elif script == 'SW': SW(original_language, force_override)
	elif script == 'UW': UW(original_language, force_override)
	elif script == 'RP': RP(original_language)
	elif script == 'RF': RF()
	elif script == 'CS': CS(original_language, force_override)
	elif script == 'EG': EG()
	elif script == 'RG': RG()
	elif script == 'DS': DS(original_language, force_override)
	elif script == 'DSC': DSC(original_language, force_override)
	elif script in ['EXIT', 'CLOSE', 'QUIT', ':Q']: return
	else: menu()

def main():
	try:
		cls()
		rzs()
		checkUpdates()
		checkTools()
		menu()
	except KeyboardInterrupt as e:
		print('KeyboardInterrupt')
		print()
		input('Press Enter to exit...')
	except Exception:
		import traceback
		traceback.print_exc()
		print()
		input('Press Enter to exit...')

if __name__ == '__main__':
	main()
