""" Author: Dominik Beese
>>> Translation Toolkit
<<<
"""

from os import system, listdir
from os.path import join, exists, isfile
import json
import webbrowser
from urllib.request import urlopen

from TranslationPatcher import applyPatches, createPatches, distribute
from SendViaFTP import sendRomFiles
from FileReplacer import replaceFiles
from SaveChanger import updateTableInSave
from WorkspaceManager import downloadAndExtractPatches

CONFIG_FILE = 'tt-config.json'

VERSION = 'v1.1.0'
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
		with open(CONFIG_FILE, 'r') as file:
			Config.cfg = json.load(file)
	
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
		print('-'*(w+m+4+m))
		print()
		
		# parse command
		print('Enter command:')
		command = input('>> ').strip()
		script = command.upper() if command else ''
		
		if script == 'D': webbrowser.open(link)
		elif script == 'C': pass
		elif script == 'I': Config.set('ignoreVersion', tag)
	except Exception: pass


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

def askParamter(name, key, default = '', description = None, hide_fallback = False):
	print('~', ' '.join(w.capitalize() if w[0].islower() else w for w in name.split()), '~')
	fallback = Config.get(key, default)
	for line in description: print(line)
	print('Enter %s [%s]:' % (name, fallback if not hide_fallback else '***'))
	command = input('>> ').strip() or fallback
	Config.set(key, command)
	print()
	return command

def AP(original_language, force_override):
	system('clear')
	if not verifyStart(): return
	applyPatches(original_language=original_language, force_override=force_override)
	showEnd()

def CP(original_language, force_override):
	system('clear')
	if not verifyStart(): return
	createPatches(original_language=original_language, force_override=force_override)
	showEnd()

def D(original_language, force_override):
	system('clear')
	
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
	
	destination_dir = askParamter(
		name = 'destination folder',
		description = ['This folder will contain all edited files with the correct file structure.'],
		key = 'D.dest',
		default = '_dist'
	)
	
	print('Language:', ', '.join(languages))
	print('Destination Folder:', destination_dir)
	print()
	
	if not verifyStart(): return
	distribute(languages=languages, original_language=original_language, destination_dir=destination_dir, force_override=force_override)
	showEnd()

def S(force_override):
	system('clear')
	
	source_dir = askParamter(
		name = 'folder',
		description = ['The folder to send. This is the folder generated by the \'D\' script.'],
		key = 'S.source',
		default = '_dist'
	)
	
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
	sendRomFiles(source_dir=source_dir, title_id=title_id, ip=ip, port=port, user=user, passwd=passwd, force_override=force_override)
	showEnd()

def RF():
	system('clear')
	
	source_dir = askParamter(
		name = 'source folder',
		description = ['The folder containing the files to be copied.'],
		key = 'RF.source'
	)
	source_files = [join(source_dir, f) for f in listdir(source_dir)]
	
	destination_dir = askParamter(
		name = 'destination folder',
		description = ['The folder in which to replace the files.'],
		key = 'RF.dest'
	)
	
	print('Source Folder:', source_dir)
	print('Destination Folder:', destination_dir)
	print()
	
	if not verifyStart(): return
	replaceFiles(source_files=source_files, destination_dir=destination_dir)
	showEnd()

def UD():
	system('clear')
	
	source_dir = askParamter(
		name = 'save folder',
		description = ['The folder containing the save files to update.'],
		key = 'UD.source'
	)
	
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

def UW(original_language, force_override):
	system('clear')
	if not verifyStart(): return
	print('~~ Download Patches ~~')
	download_url = Config.get('UW.url', r'https://github.com/Ich73/DQM2-FanTranslation/archive/master.zip')
	if downloadAndExtractPatches(download_url):
		print()
		print()
		print('~~ Apply Patches ~~')
		applyPatches(original_language=original_language, force_override=force_override)
	showEnd()


##########
## Menu ##
##########

m = 2 # left margin
w = 100 # width of title box

def printTitleBox():
	system('clear')
	def title(msg=''): print(' '*m + '##' + ' '*int((w-len(msg))/2) + msg + ' '*(w-len(msg)-int((w-len(msg))/2)) + '##')
	print()
	title('#'*w)
	title()
	title('Translation Toolkit ' + VERSION)
	title('(https://github.com/%s)' % REPOSITORY)
	title()
	title('#'*w)
	print()

def printCategory(text):
	print(' '*m + '~ ' + text + ' ~')
	print()

def printOption(cmd, text):
	print(' '*m + '*', cmd, ':', text)

def printInfo(text, width=90):
	print(' '*(m+4), end=' ')
	c = 0
	for word in text.split():
		if c + len(word) > width-m-1:
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
	printInfo('Uses xdelta patches to patch files from the original game. Applies .patJ patches to .binJ files and updates .savJ files. Applies .patE patches to .e files and updates .savE files.')
	printOption('CP', 'Create Patches')
	printInfo('Creates xdelta patches for all edited game files. Creates .patJ patches from .savJ files. Creates .patE patches from .savE files.')
	printOption('D', 'Distribute')
	printInfo('Copies all edited game files to a given folder. The folder can then be used by the \'S\' script to send the files to the 3DS so luma can patch them. Or you can copy the folder to your extracted cia folder to create a translated cia file.')
	printOption('S', 'Send via FTP')
	printInfo('Sends the contents of the in the \'D\' script generated folder to the 3DS so luma can patch them. Only updated files are sent.')
	printOption('RF', 'Replace Files')
	printInfo('Searches the given destination folder for files with the same name as the files in the given source folder and replaces them. This can be used to update multiple .bclim files at once when editing .arc files.')
	
	printCategory('Options')
	printOption('-f', 'Force Override All Files (e.g. \'AP -f\')')
	printOption('-o=<XY>', 'Override Original Language (e.g. \'AP -o=JA\')')
	
	print()
	print('-'*(w+m+4+m))
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
	elif script == 'RF': RF()
	elif script == 'UD': UD()
	elif script == 'UW': UW(original_language, force_override)
	elif script in ['EXIT', 'CLOSE', 'QUIT', ':Q']: return
	else: menu()

def main():
	system('clear')
	system('mode con: cols=%d lines=%d' % (w+m+4+m, 43)) # SCREEN WIDTH AND HEIGHT
	checkUpdates()
	menu()

if __name__ == '__main__':
	main()
