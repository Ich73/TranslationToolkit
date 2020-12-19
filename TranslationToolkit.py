""" Author: Dominik Beese
>>> Translation Toolkit
<<<
"""

from os import system, listdir, getenv
from os.path import join, exists, isfile, isdir
from shutil import rmtree
from tempfile import mkdtemp
import json
import webbrowser
from urllib.request import urlopen

from TranslationPatcher import applyPatches, createPatches, distribute
from SendViaFTP import sendFiles as sendFilesViaFTP
from SendToCitra import sendFiles as sendFilesToCitra
from FileReplacer import replaceFiles
from SaveChanger import updateTableInSave
from WorkspaceManager import downloadAndExtractPatches, copyOriginalFiles, copyPatchedFiles, prepareReleasePatches, createReleasePatches
from WorkspaceManager import checkTool, downloadExe

CONFIG_FILE = 'tt-config.json'

VERSION = 'v2.3.0'
REPOSITORY = r'Ich73/TranslationToolkit'


###########
## Setup ##
###########

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
		with urlopen(latest, timeout = 1) as url:
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
	version, url = Config.get('xdelta', ('3.1.0', r'https://github.com/jmacd/xdelta-gpl/releases/download/v3.1.0/xdelta3-3.1.0-x86_64.exe.zip'))
	if not checkTool('xdelta -V', version):
		downloadExe(url, 'xdelta.exe')
	
	# check 3dstool
	version, url = Config.get('3dstool', ('1.1.0', r'https://github.com/dnasdw/3dstool/releases/download/v1.1.0/3dstool.zip'))
	if not checkTool('3dstool', version):
		downloadExe(url, '3dstool.exe')


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
	system('cls')
	if not verifyStart(): return
	applyPatches(original_language=original_language, force_override=force_override)
	showEnd()

def CP(original_language, force_override):
	system('cls')
	if not verifyStart(): return
	createPatches(original_language=original_language, force_override=force_override)
	showEnd()

def D(original_language, force_override):
	system('cls')
	
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
	
	print('Language:', ', '.join(languages))
	print('Version:', version)
	print('Destination Folder:', destination_dir)
	print()
	
	if not verifyStart(): return
	distribute(languages=languages, version=version, version_only=False, original_language=original_language, destination_dir=destination_dir, force_override=force_override)
	showEnd()

def S(force_override):
	system('cls')
	
	while True:
		source_dir = askParamter(
			name = 'folder',
			description = ['The folder to send. This is the folder generated by the \'D\' script.'],
			key = 'S.source',
			default = '_dist'
		)
		if isdir(source_dir): break
	
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
	
	print('Folder:', source_dir)
	print('Title ID:', title_id)
	print()
	
	if not verifyStart(): return
	sendFilesViaFTP(source_dir=source_dir, title_id=title_id, ip=ip, port=port, user=user, passwd=passwd, force_override=force_override)
	showEnd()

def SC(force_override):
	system('cls')
	
	while True:
		source_dir = askParamter(
			name = 'folder',
			description = ['The folder to send. This is the folder generated by the \'D\' script.'],
			key = 'SC.source',
			default = '_dist'
		)
		if isdir(source_dir): break
	
	title_id = askParamter(
		name = 'title ID',
		description = ['The title ID of the game to patch.'],
		key = 'SC.titleid',
		default = '00040000000cf500'
	)
	
	user_dir = join(getenv('PROGRAMFILES'), 'Citra', 'user')
	appdata_dir = join(getenv('APPDATA'), 'Citra')
	while True:
		citra_dir = askParamter(
			name = 'Citra folder',
			description = ['Citra\'s mod folder to which the patched files should be copied.'],
			key = 'SC.citra',
			default = appdata_dir if not exists(user_dir) else user_dir
		)
		if isdir(citra_dir): break
	
	print('Folder:', source_dir)
	print('Title ID:', title_id)
	print('Citra Folder:', citra_dir)
	print()
	
	if not verifyStart(): return
	sendFilesToCitra(source_dir=source_dir, title_id=title_id, citra_dir=citra_dir, force_override=force_override)
	showEnd()

def RF():
	system('cls')
	
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

def UD():
	system('cls')
	
	while True:
		source_dir = askParamter(
			name = 'save folder',
			description = ['The folder containing the save files to update.'],
			key = 'UD.source',
			default = '.'
		)
		if isdir(source_dir): break
	
	while True:
		table_file = askParamter(
			name = 'table file',
			description = ['The updated decoding table file.'],
			key = 'UD.table'
		)
		if isfile(table_file): break
	
	print('Save Folder:', source_dir)
	print('Table File:', table_file)
	print()
	
	if not verifyStart(): return
	updateTableInSave(save_dir=source_dir, table_file=table_file)
	showEnd()

def SW(original_language, force_override):
	system('cls')
	
	download_url = askParamter(
		name = 'download URL',
		description = ['The url for downloading all patches as a zip file.'],
		key = 'UW.url'
	)
	
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
		update_cia_dir = askParamter(
			name = 'update CIA folder',
			description = ['The full path to the folder containing the extracted update CIA file.'],
			key = None,
			fallback = fallbacks[len(updates)][1] if len(fallbacks) > len(updates) else ''
		)
		updates.append((update_ver, update_cia_dir))
	Config.set('SW.updates', updates)
	
	print('CIA Folder:', cia_dir)
	print('Download URL:', download_url)
	for ver, dir in updates:
		print('Update %s Folder:' % ver, dir)
	print()
	
	if not verifyStart(): return
	
	print('~~ Download Patches ~~')
	if not downloadAndExtractPatches(download_url):
		showEnd()
		return
	
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
	applyPatches(original_language=original_language, force_override=force_override)
	
	showEnd()

def UW(original_language, force_override):
	system('cls')
	
	download_url = askParamter(
		name = 'download URL',
		description = ['The url for downloading all patches as a zip file.'],
		key = 'UW.url'
	)
	
	print('Download URL:', download_url)
	print()
	
	if not verifyStart(): return
	
	print('~~ Download Patches ~~')
	if not downloadAndExtractPatches(download_url):
		showEnd()
		return
	
	print()
	print()
	print('~~ Apply Patches ~~')
	applyPatches(original_language=original_language, force_override=force_override)
	
	showEnd()

def RP(original_language):
	system('cls')
	
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
	createReleasePatches(cia_dir, patches_filename, original_language=original_language)
	
	rmtree(temp_dir)
	showEnd()


##########
## Menu ##
##########

m = 2 # left margin
w = 96 # width of title box

def printTitleBox():
	system('cls')
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

def printOption(cmd, text):
	print(' '*m + '*', cmd, ':', text)

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
	printOption('RF', 'Replace Files')
	printOption('UD', 'Update Decoding Tables')
	printOption('SW', 'Setup Workspace')
	printOption('UW', 'Update Workspace')
	printOption('RP', 'Release Patches')
	
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
	elif script == 'RF': RF()
	elif script == 'UD': UD()
	elif script == 'SW': SW(original_language, force_override)
	elif script == 'UW': UW(original_language, force_override)
	elif script == 'RP': RP(original_language)
	elif script in ['EXIT', 'CLOSE', 'QUIT', ':Q']: return
	else: menu()

def main():
	try:
		system('cls')
		system('mode con: cols=%d lines=%d' % (w+m+4+m, 41)) # SCREEN WIDTH AND HEIGHT
		checkUpdates()
		checkTools()
		menu()
	except Exception:
		import traceback
		traceback.print_exc()
		print()
		input('Press Enter to exit...')

if __name__ == '__main__':
	main()
