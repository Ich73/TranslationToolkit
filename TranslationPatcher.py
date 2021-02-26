""" Author: Dominik Beese
>>> Translation Patcher
	createPatches():
		*.*    -> *.*.xdelta
		*.savJ -> *.patJ

	applyPatches():
		*.*.xdelta -> *.*
		*.patJ     -> *.binJ (& .savJ)
	
	distribute():
		*.*                      -> copy if different
		*.savJ / *.patJ / *.binJ -> merge and copy
<<<
"""

from os import listdir, walk, sep, remove, rename, makedirs
from os.path import join, exists, isdir, splitext, dirname, basename, normpath
from shutil import copyfile
from hashlib import md5
import re
from zipfile import ZipFile
from gzip import GzipFile
import json
from BinJEditor.JTools import parseBinJ, createBinJ, parseE, createE, parseDatJ, createDatJ, parseDatE, parseTabE, parseSpt
from tempfile import gettempdir as tempdir
from subprocess import run

PARAMS_FILE = '.ttparams'

# 0: nothing, 1: minimal, 2: default, 3: all
VERBOSE = 2


############
## Params ##
############

class Params:
	prms = None
	
	def loadParams(force_reload = False):
		if not force_reload and Params.prms is not None: return
		try:
			with open(PARAMS_FILE, 'r') as file:
				Params.prms = json.load(file)
		except:
			Params.loadDefaults()
		Params.parseParams()
	
	def _get(key, default = None):
		Params.loadParams()
		return Params.prms.get(key, default)
	
	def SEP(): return Params._get('SEP', b'\xe3\x1b')
	def xdeltaFolders(): return Params._get('XDELTA', dict())
	def patFolders(): return Params._get('PAT', dict())
	def parentFolders(): return Params._get('PARENT', dict())
	def updateActions(): return Params._get('UPDATE_ACTIONS', list())
	
	def loadDefaults():
		Params.prms = dict()
		# separator token
		Params.prms['SEP'] = 'E31B'
		# folders to search for files
		Params.prms['XDELTA'] = {
			'Banner': ['.bcwav', '.cbmd', '.cgfx'],
			'Code': ['.bin'],
			'ExeFS': ['.bin'],
			'Manual': ['.bcma'],
			'Battle': ['.bcres', '.nut'],
			'Debug': ['.bin'],
			'Effect': ['.bcres'],
			'Event': ['.gz'],
			'ExtSaveData': ['.icn'],
			'Field': ['.bcres', '.nut', '.gz', '.xbb'],
			'Flash': ['.flb'],
			'Font': ['.bcfnt'],
			'KeyImage': ['.bclim'],
			'Layout': ['.arc', '.nut'],
			'Menu': ['.nut'],
			'Menu3D': ['.bcres', '.bcenv'],
			'Model': ['.bcres', '.bcenv', '.bcmdl', '.xbb'],
			'MonsterIcon': ['.bclim'],
			'NaviMap': ['.arc'],
			'NetworkIcon': ['.ctpk'],
			'Npc': ['.nut'],
			'Param': ['.bin', '.gz'],
			'PartsIcon': ['.bclim'],
			'PresentCode': ['.bin'],
			'Test': ['.txt', '.bin', '.nut', '.gz'],
			'Title': ['.bcres'],
			'WiFi': ['.nut']
		}
		# folders to search for files, patches and saves
		Params.prms['PAT'] = {
			# folder: (mode, original, save, patch)
			'Message': ['binJ', '.binJ', '.savJ', '.patJ'],
			'Event': ['e', '.e', '.savE', '.patE']
		}
		# where to put the folders when distributing
		Params.prms['PARENT'] = {
			'Banner': 'ExtractedBanner',
			'Code': 'ExtractedExeFS',
			'ExeFS': 'ExtractedExeFS',
			'Manual': 'ExtractedManual',
			'Battle': 'ExtractedRomFS/data/Battle',
			'Debug': 'ExtractedRomFS/data/Debug',
			'Effect': 'ExtractedRomFS/data/Effect',
			'Event': 'ExtractedRomFS/data/Event',
			'ExtSaveData': 'ExtractedRomFS/data/ExtSaveData',
			'Field': 'ExtractedRomFS/data/Field',
			'Flash': 'ExtractedRomFS/data/Flash',
			'Font': 'ExtractedRomFS/data/Font',
			'KeyImage': 'ExtractedRomFS/data/KeyImage',
			'Layout': 'ExtractedRomFS/data/Layout',
			'Menu': 'ExtractedRomFS/data/Menu',
			'Menu3D': 'ExtractedRomFS/data/Menu3D',
			'Message': 'ExtractedRomFS/data/Message',
			'Model': 'ExtractedRomFS/data/Model',
			'MonsterIcon': 'ExtractedRomFS/data/MonsterIcon',
			'NaviMap': 'ExtractedRomFS/data/NaviMap',
			'NetworkIcon': 'ExtractedRomFS/data/NetworkIcon',
			'Npc': 'ExtractedRomFS/data/Npc',
			'Param': 'ExtractedRomFS/data/Param',
			'PartsIcon': 'ExtractedRomFS/data/PartsIcon',
			'PresentCode': 'ExtractedRomFS/data/PresentCode',
			'Test': 'ExtractedRomFS/data/Test',
			'Title': 'ExtractedRomFS/data/Title',
			'WiFi': 'ExtractedRomFS/data/WiFi'
		}
	
	def parseParams():
		def hex2bytes(s): return bytes([int(s[i:i+2], 16) for i in range(0, len(s), 2)])
		if 'SEP' in Params.prms: Params.prms['SEP'] = hex2bytes(Params.prms['SEP'])
		def parseDir(d): return join(*d.split('/'))
		if 'PARENT' in Params.prms: Params.prms['PARENT'] = {folder: parseDir(dir) for folder, dir in Params.prms['PARENT'].items()}


############
## Helper ##
############

def hash(file):
	""" Calculates the MD5 hash of the given file. """
	hasher = md5()
	with open(file, 'rb') as f: hasher.update(f.read())
	return hasher.digest()

def hashZip(zipfile):
	hasher = md5()
	with ZipFile(zipfile, 'r') as zip:
		for filename in sorted([info.filename for info in zip.infolist()]):
			hasher.update(filename.encode())
			hasher.update(zip.read(filename))
	return hasher.digest()

def extpath(path):
	return normpath(path).split(sep)[1:]

def splitFolder(folder):
		a = folder.split('_')
		parts = {'folder': a[0]}
		if len(a) > 1:
			if re.match('^v\d(\.\d+)*$', a[1]): parts['version'] = a[1]
			else: parts['lang'] = a[1]
		if len(a) > 2: parts['lang'] = a[2]
		return parts

def joinFolder(folder, language, version = None):
	name = folder
	if version: name += '_' + version
	if language: name += '_' + language
	return name

def loopFiles(folders, original_language = None):
	""" Loops over the files in the folders with the given names that
		match the given file types.
		It returns tuples of the folder and edit filename.
		If original_language is given, it addionally returns the
		corresponding original folder.
	"""
	if original_language:
		directories = [splitFolder(dir) for dir in listdir('.') if isdir(dir)]
		# iterate over all defined folders
		for folder, types in folders.items():
			versions = {dir.get('version') for dir in directories if dir['folder'] == folder and dir.get('lang') == original_language}
			if not versions: continue
			
			# iterate over all languages found
			for version, language in [(dir.get('version'), dir.get('lang')) for dir in directories if dir['folder'] == folder and dir.get('version') in versions and dir.get('lang') != original_language]:
				edit_folder = joinFolder(folder, language, version)
				orig_folder = joinFolder(folder, original_language, version)
				if VERBOSE >= 1: print(edit_folder, end=' ', flush=True)
				
				# iterate over all files with a valid file extension
				files = [join(dp, f) for dp, dn, fn in walk(edit_folder) for f in [n for n in fn if splitext(n)[1] in types]]
				if VERBOSE >= 1: print('[%s]' % len(files))
				for edit_file in files:
					yield (folder, edit_file, orig_folder)
	
	else:
		for folder, types in folders.items():
			# iterate over all languages found
			for edit_folder in [dir for dir in listdir('.') if isdir(dir) and splitFolder(dir)['folder'] == folder]:
				if VERBOSE >= 1: print(edit_folder, end=' ', flush=True)
				
				# iterate over all files with a valid file extension
				files = [join(dp, f) for dp, dn, fn in walk(edit_folder) for f in [n for n in fn if splitext(n)[1] in types]]
				if VERBOSE >= 1: print('[%s]' % len(files))
				for edit_file in files:
					yield (folder, edit_file)


###########
## Apply ##
###########

def applyPatches(original_language = 'JA', force_override = False):
	ctr  = applyPatPatches(original_language, force_override)
	ctr2 = applyXDeltaPatches(original_language, force_override)
	for k, v in ctr2.items(): ctr[k] = ctr.get(k, 0) + v
	print()
	if VERBOSE >= 1 and ctr.get('create', 0) > 0 or VERBOSE >= 3: print('Created %d files.' % ctr.get('create', 0))
	if VERBOSE >= 1: print('Updated %d files.' % ctr.get('update', 0))
	if VERBOSE >= 3: print('Kept %d files.' % ctr.get('keep',   0))

def applyPatPatches(original_language, force_override):
	""" Creates .binJ files from .patJ patches and the original .binJ file.
		Creates .e    files from .patE patches and the original .e    file.
		Creates .savJ files from .patJ patches and the old .savJ save file.
		Creates .savE files from .patE patches and the old .savE save file.
	"""
	
	def applyPatToFile(orig_file, patch_file, output_file, mode):
		# read original file
		try:
			if mode == 'binJ':
				with open(orig_file, 'rb') as file: bin = file.read()
				orig_data, extra = parseBinJ(bin, Params.SEP())
			elif mode == 'e':
				with GzipFile(orig_file, 'r') as file: bin = file.read()
				orig_data, extra = parseE(bin, Params.SEP())
		except:
			print(' !', 'Error: Parsing %s file failed:' % mode, join(*extpath(orig_file)))
			return
		# read patch file
		with open(patch_file, 'r', encoding = 'ANSI') as file: patj = file.read()
		edit_data = parseDatJ(patj)
		# check if compatible
		if len(edit_data) != len(orig_data):
			print(' !', 'Warning: Lengths of original file and patch differ:', join(*extpath(orig_file)))
			if len(edit_data) > len(orig_data): edit_data = edit_data[:len(orig_data)]
			else: edit_data = edit_data + [b'']*(len(orig_data) - len(edit_data))
		# patch data
		output_data = [v if v else orig_data[i] for i, v in enumerate(edit_data)]
		# save output file
		if mode == 'binJ':
			bin = createBinJ(output_data, Params.SEP(), extra)
			with open(output_file, 'wb') as file: file.write(bin)
		elif mode == 'e':
			bin = createE(output_data, Params.SEP(), extra)
			with open(output_file, 'wb') as file:
				with GzipFile(fileobj=file, mode='w', filename='', mtime=0) as gzipFile: gzipFile.write(bin)
	
	def applyPatToSav(save_file, patch_file, output_file):
		# read save file
		with ZipFile(save_file, 'r') as zip:
			origj = zip.read('orig.datJ').decode('ANSI')
			sep_from_save = zip.read('SEP.bin')
			specialj = zip.read('special.tabJ')
			decodej = zip.read('decode.tabJ')
			encodej = zip.read('encode.tabJ')
			extra_files = sorted({info.filename for info in zip.infolist()} - {'orig.datJ', 'edit.datJ', 'SEP.bin', 'special.tabJ', 'decode.tabJ', 'encode.tabJ'})
			extra = [zip.read(file) for file in extra_files]
		orig_data = parseDatJ(origj)
		# read patch file and override edit_data
		with open(patch_file, 'r', encoding = 'ANSI') as file: patj = file.read()
		edit_data = parseDatJ(patj)
		# check if compatible
		if len(edit_data) != len(orig_data):
			print(' !', 'Warning: Lengths of original file and patch differ:', join(*extpath(orig_file)))
			if len(edit_data) > len(orig_data): edit_data = edit_data[:len(orig_data)]
			else: edit_data = edit_data + [b'']*(len(orig_data) - len(edit_data))
		# save output file
		origj = createDatJ(orig_data)
		editj = createDatJ(edit_data)
		orig_filename = join(tempdir(), 'orig.datJ')
		with open(orig_filename, 'w', encoding = 'ANSI', newline = '\n') as file: file.write(origj)
		edit_filename = join(tempdir(), 'edit.datJ')
		with open(edit_filename, 'w', encoding = 'ANSI', newline = '\n') as file: file.write(editj)
		sep_filename = join(tempdir(), 'SEP.bin')
		with open(sep_filename, 'wb') as file: file.write(sep_from_save)
		special_filename = join(tempdir(), 'special.tabJ')
		with open(special_filename, 'wb') as file: file.write(specialj)
		decode_filename = join(tempdir(), 'decode.tabJ')
		with open(decode_filename, 'wb') as file: file.write(decodej)
		encode_filename = join(tempdir(), 'encode.tabJ')
		with open(encode_filename, 'wb') as file: file.write(encodej)
		extra_filenames = [join(tempdir(), file) for file in extra_files]
		for i, extra_filename in enumerate(extra_filenames):
			with open(extra_filename, 'wb') as file: file.write(extra[i])
		with ZipFile(output_file, 'w') as file:
			file.write(orig_filename, arcname=basename(orig_filename))
			file.write(edit_filename, arcname=basename(edit_filename))
			file.write(sep_filename, arcname=basename(sep_filename))
			file.write(special_filename, arcname=basename(special_filename))
			file.write(decode_filename, arcname=basename(decode_filename))
			file.write(encode_filename, arcname=basename(encode_filename))
			for extra_filename in extra_filenames:
				file.write(extra_filename, arcname=basename(extra_filename))
		remove(orig_filename)
		remove(edit_filename)
		remove(sep_filename)
		remove(special_filename)
		remove(decode_filename)
		remove(encode_filename)
		for extra_filename in extra_filenames:
			remove(extra_filename)
	
	ctr = dict()
	folders = {k: v[3] for k, v in Params.patFolders().items()}
	for folder, patch_file, orig_folder in loopFiles(folders, original_language):
		simplename = extpath(patch_file)
		mode, ext_orig, ext_save, ext_patch = Params.patFolders()[folder]
		msg_prefix = ' * %s:' % join(*simplename[:-1], splitext(simplename[-1])[0] + ext_orig)
		
		# find corresponding original file
		orig_file = join(orig_folder, *simplename[:-1], splitext(simplename[-1])[0] + ext_orig)
		if not exists(orig_file):
			if VERBOSE >= 2: print(' !', 'Warning: Original file not found:', join(*extpath(orig_file)))
			continue
		
		# define output file
		output_file = patch_file[:-len(ext_patch)] + ext_orig
		
		# check if output file already exists
		if exists(output_file):
			# create temporary output file
			temp_output_file = output_file + '.temp'
			applyPatToFile(orig_file, patch_file, temp_output_file, mode)
			# compare output files
			if not force_override and hash(output_file) == hash(temp_output_file):
				# equal -> keep old output file
				if VERBOSE >= 3: print(msg_prefix, 'keep')
				ctr['keep'] = ctr.get('keep', 0) + 1
				remove(temp_output_file)
			else:
				# new -> update output file
				if VERBOSE >= 2: print(msg_prefix, 'update')
				ctr['update'] = ctr.get('update', 0) + 1
				remove(output_file)
				rename(temp_output_file, output_file)
		else:
			# create new output file
			if VERBOSE >= 2: print(msg_prefix, 'create')
			ctr['create'] = ctr.get('create', 0) + 1
			applyPatToFile(orig_file, patch_file, output_file, mode)
		
		# define output save file
		msg_prefix = ' * %s:' % join(*simplename[:-1], splitext(simplename[-1])[0] + ext_save)
		output_save_file = patch_file[:-len(ext_patch)] + ext_save
		
		# check if output save file exists
		if exists(output_save_file):
			# create temporary output save file
			temp_output_save_file = output_save_file + '.temp'
			applyPatToSav(output_save_file, patch_file, temp_output_save_file)
			# compare save files
			if not force_override and hashZip(output_save_file) == hashZip(temp_output_save_file):
				# equal -> keep old save file
				if VERBOSE >= 3: print(msg_prefix, 'keep')
				ctr['keep'] = ctr.get('keep', 0) + 1
				remove(temp_output_save_file)
			else:
				# new -> update save file
				if VERBOSE >= 2: print(msg_prefix, 'update')
				ctr['update'] = ctr.get('update', 0) + 1
				remove(output_save_file)
				rename(temp_output_save_file, output_save_file)
	return ctr

def applyXDeltaPatches(original_language, force_override):
	""" Creates .* files from .*.xdelta patches and the original .* files. """
	
	def applyXDelta(orig_file, patch_file, output_file):
		run(['xdelta', '-f', '-d', '-s', orig_file, patch_file, output_file])
	
	ctr = dict()
	folders = dict(zip(Params.xdeltaFolders().keys(), ['.xdelta']*len(Params.xdeltaFolders())))
	for _, patch_file, orig_folder in loopFiles(folders, original_language):
		simplename = extpath(patch_file)
		simplename[-1] = simplename[-1][:-len('.xdelta')]
		msg_prefix = ' * %s:' % join(*simplename)
		
		# find corresponding original file
		orig_file = join(orig_folder, *simplename)
		if not exists(orig_file):
			print(' !', 'Warning: Original file not found:', join(*simplename))
			continue
		
		# define output file
		output_file = patch_file[:-len('.xdelta')]
		
		# check if output file already exists
		if exists(output_file):
			# create temporary output file
			temp_output_file = output_file + '.temp'
			applyXDelta(orig_file, patch_file, temp_output_file)
			# compare output files
			if not force_override and hash(output_file) == hash(temp_output_file):
				# equal -> keep old output file
				if VERBOSE >= 3: print(msg_prefix, 'keep')
				ctr['keep'] = ctr.get('keep', 0) + 1
				remove(temp_output_file)
			else:
				# new -> update output file
				if VERBOSE >= 2: print(msg_prefix, 'update')
				ctr['update'] = ctr.get('update', 0) + 1
				remove(output_file)
				rename(temp_output_file, output_file)
		else:
			# create new output file
			if VERBOSE >= 2: print(msg_prefix, 'create')
			ctr['create'] = ctr.get('create', 0) + 1
			applyXDelta(orig_file, patch_file, output_file)
	return ctr


############
## Create ##
############

def createPatches(original_language = 'JA', force_override = False):
	ctr  = createPatPatches(original_language, force_override)
	ctr2 = createXDeltaPatches(original_language, force_override)
	for k, v in ctr2.items(): ctr[k] = ctr.get(k, 0) + v
	print()
	if VERBOSE >= 1 and ctr.get('create', 0) > 0 or VERBOSE >= 3: print('Created %d patches.' % ctr.get('create', 0))
	if VERBOSE >= 1: print('Updated %d patches.' % ctr.get('update', 0))
	if VERBOSE >= 1 and ctr.get('delete', 0) > 0 or VERBOSE >= 3: print('Deleted %d patches.' % ctr.get('delete', 0))
	if VERBOSE >= 3: print('Kept %d patches.' % ctr.get('keep',   0))
	if VERBOSE >= 3: print('Skipped %d files.' % ctr.get('skip',   0))

def createPatPatches(original_language, force_override):
	""" Creates .patJ patches from .savJ files or pairs of .binJ files.
		Creates .patE patches from .savE files or pairs of .e files.
	"""
	
	def createPatFromSav(save_file, patch_file):
		# read edit data from save
		with ZipFile(save_file, 'r') as zip:
			data = zip.read('edit.datJ').decode('ANSI')
		# correct newlines
		data = createDatJ(parseDatJ(data))
		# save patch file
		with open(patch_file, 'w', encoding = 'ANSI', newline = '\n') as file:
			file.write(data)
	
	def createPatFromOrigAndEdit(orig_file, edit_file, patch_file, mode):
		def readFile(file):
			try:
				if mode == 'binJ':
					with open(file, 'rb') as file: bin = file.read()
					return parseBinJ(bin, Params.SEP())
				elif mode == 'e':
					with GzipFile(file, 'r') as file: bin = file.read()
					return parseE(bin, Params.SEP())
			except:
				print(' !', 'Error: Parsing %s file failed:' % mode, join(*extpath(file)))
				return None, None
		# read original file
		orig_data, orig_extra = readFile(orig_file)
		if orig_data is None: return
		# read edit file
		edit_data, edit_extra = readFile(edit_file)
		if edit_data is None: return
		# check if compatible
		if len(edit_data) != len(orig_data): # check data length
			print(' !', 'Warning: Lengths of original and edited file differ:', join(*extpath(orig_file)))
			if len(edit_data) > len(orig_data): edit_data = edit_data[:len(orig_data)]
			else: edit_data = edit_data + [b'']*(len(orig_data) - len(edit_data))
		# check if compatible for binJ
		if mode == 'binJ':
			if edit_extra['prefix'] != orig_extra['prefix']:
				print(' !', 'Warning: Prefixes of original and edited file differ.')
		# check if compatible for e
		elif mode == 'e':
			if edit_extra['prefix'] != orig_extra['prefix']:
				print(' !', 'Warning: Prefixes of original and edited file differ.')
			if edit_extra['header'] != orig_extra['header']:
				print(' !', 'Warning: Headers of original and edited file differ.')
			if edit_extra['scripts'] != orig_extra['scripts']:
				print(' !', 'Warning: Scripts of original and edited file differ.')
			if edit_extra['links'] != orig_extra['links']:
				print(' !', 'Warning: Links of original and edited file differ.')
		# create patch
		patch = createDatJ([edit if edit != orig else b'' for orig, edit in zip(orig_data, edit_data)])
		# save patch file
		with open(patch_file, 'w', encoding = 'ASCII', newline = '\n') as file:
			file.write(patch)
	
	def collectFiles(folder, ext_orig, ext_save):
		# find directories matching the given folder
		directories = [splitFolder(dir) for dir in listdir('.') if isdir(dir)]
		versions = {dir.get('version') for dir in directories if dir['folder'] == folder and dir.get('lang') == original_language}
		if not versions: return
		
		# iterate over all languages found
		for version, language in [(dir.get('version'), dir.get('lang')) for dir in directories if dir['folder'] == folder and dir.get('version') in versions and dir.get('lang') != original_language]:
			edit_folder = joinFolder(folder, language, version)
			orig_folder = joinFolder(folder, original_language, version)
			if VERBOSE >= 1: print(edit_folder, end=' ', flush=True)
			
			# collect all files by priority type
			files = dict() # dict of shortname (no first folder, no ext) -> ext
			for type in [ext_orig, ext_save]: # reverse priority
				for file in [join(dp, f) for dp, dn, fn in walk(edit_folder) for f in [n for n in fn if splitext(n)[1] == type]]:
					shortname = join(*extpath(splitext(file)[0]))
					files[shortname] = type # override files of worse priority
			if VERBOSE >= 1: print('[%s]' % len(files))
			
			# yield all values of the current folders
			for shortname, type in files.items():
				yield (edit_folder, shortname, type, orig_folder)
	
	# iterate over all pat folders
	ctr = dict()
	for folder, (mode, ext_orig, ext_save, ext_patch) in Params.patFolders().items():
		# iterate over all files
		for folder, shortname, type, orig_folder in collectFiles(folder, ext_orig, ext_save):
			msg_prefix = ' * %s:' % join(shortname + ext_patch)
			edit_file = join(folder, shortname + type)
			
			# define patch file
			patch_file = join(folder, shortname + ext_patch)
			
			if type == ext_orig:
				# define orig file
				orig_file = join(orig_folder, shortname + type)
				if not exists(orig_file):
					if VERBOSE >= 2: print(' !', 'Warning: Original file not found:', shortname + type)
					return
				
				# compare files
				if hash(orig_file) == hash(edit_file):
					# check if patch exists
					if exists(patch_file):
						if VERBOSE >= 2: print(msg_prefix, 'delete patch')
						ctr['delete'] = ctr.get('delete', 0) + 1
						remove(patch_file)
					else:
						if VERBOSE >= 3: print(msg_prefix, 'skip')
						ctr['skip'] = ctr.get('skip', 0) + 1
					continue
			
			def createPat(patch_file):
				# savJ/savE -> create from sav
				if type == ext_save:
					createPatFromSav(edit_file, patch_file)
				# binJ/e -> create from edit and orig
				elif type == ext_orig:
					createPatFromOrigAndEdit(orig_file, edit_file, patch_file, mode)
			
			# check if patch already exists
			if exists(patch_file):
				# create temporary patch
				temp_patch_file = patch_file + '.temp'
				createPat(temp_patch_file)
				# compare patches
				if not force_override and hash(patch_file) == hash(temp_patch_file):
					# equal -> keep old patch
					if VERBOSE >= 3: print(msg_prefix, 'keep')
					ctr['keep'] = ctr.get('keep', 0) + 1
					remove(temp_patch_file)
				else:
					# new -> update patch
					if VERBOSE >= 2: print(msg_prefix, 'update')
					ctr['update'] = ctr.get('update', 0) + 1
					remove(patch_file)
					rename(temp_patch_file, patch_file)
			else:
				# create new patch
				if VERBOSE >= 2: print(msg_prefix, 'create')
				ctr['create'] = ctr.get('create', 0) + 1
				createPat(patch_file)
	return ctr

def createXDeltaPatches(original_language, force_override):
	""" Creates .*.xdelta patches from pairs of .* files. """
	
	def createXDelta(orig_file, edit_file, patch_file):
		run(['xdelta', '-f', '-s', orig_file, edit_file, patch_file])
	
	ctr = dict()
	for _, edit_file, orig_folder in loopFiles(Params.xdeltaFolders(), original_language):
		simplename = extpath(edit_file)
		msg_prefix = ' * %s:' % join(*simplename[:-1], simplename[-1]+'.xdelta')
		
		# find corresponding original file
		orig_file = join(orig_folder, *simplename)
		if not exists(orig_file):
			if VERBOSE >= 2: print(' !', 'Warning: Original file not found:', join(*simplename))
			continue
		
		# define patch file
		patch_file = edit_file + '.xdelta'
		
		# compare files
		if hash(orig_file) == hash(edit_file):
			# check if patch exists
			if exists(patch_file):
				if VERBOSE >= 2: print(msg_prefix, 'delete patch')
				ctr['delete'] = ctr.get('delete', 0) + 1
				remove(patch_file)
			else:
				if VERBOSE >= 3: print(msg_prefix, 'skip')
				ctr['skip'] = ctr.get('skip', 0) + 1
			continue
		
		# check if patch already exists
		if exists(patch_file):
			# create temporary patch
			temp_patch_file = patch_file + '.temp'
			createXDelta(orig_file, edit_file, temp_patch_file)
			# compare patches
			if not force_override and hash(patch_file) == hash(temp_patch_file):
				# equal -> keep old patch
				if VERBOSE >= 3: print(msg_prefix, 'keep')
				ctr['keep'] = ctr.get('keep', 0) + 1
				remove(temp_patch_file)
			else:
				# new -> update patch
				if VERBOSE >= 2: print(msg_prefix, 'update')
				ctr['update'] = ctr.get('update', 0) + 1
				remove(patch_file)
				rename(temp_patch_file, patch_file)
		else:
			# create new patch
			if VERBOSE >= 2: print(msg_prefix, 'create')
			ctr['create'] = ctr.get('create', 0) + 1
			createXDelta(orig_file, edit_file, patch_file)
	return ctr


################
## Distribute ##
################

def distribute(languages, version = None, version_only = False, original_language = 'JA', destination_dir = '_dist', force_override = False, verbose = None):
	""" Copies all patches for the given [languages] to the [destination_dir].
		version = None -> (LayeredFS v1.0, CIA v1.0) Copies all v1.0 files
		version = vX.Y, version_only = False -> (LayeredFS vX.Y) Copies all v1.0 files (excluding updated files) and copies all vX.Y files
		version = vX.Y, version_only = True -> (CIA vX.Y) Copies all xV.Y files
	"""
	if verbose is None: verbose = VERBOSE
	if not isinstance(languages, tuple): languages = (languages,)
	if version is None or version == 'v1.0': versions = [None]
	elif version is not None and not version_only: versions = [None, version]
	elif version is not None and version_only: versions = [version]
	ctr  = distributeBinJAndEFiles(languages, versions, original_language, destination_dir, force_override, verbose)
	ctr2 = distributeOtherFiles(languages, versions, original_language, destination_dir, force_override, verbose)
	for k, v in ctr2.items(): ctr[k] = ctr.get(k, 0) + v
	print()
	if VERBOSE >= 1 and ctr.get('add', 0) > 0 or VERBOSE >= 3: print('Added %d files.' % ctr.get('add', 0))
	if VERBOSE >= 1: print('Updated %d files.' % ctr.get('update', 0))
	if VERBOSE >= 3: print('Kept %d files.' % ctr.get('keep',   0))

def distributeBinJAndEFiles(languages, versions, original_language, destination_dir, force_override, VERBOSE):
	""" Creates .binJ files from different .savJ / .patJ / .binJ files (line by line)
		  and copies them to the destination.
		Creates .e    files from different .savE / .patE / .e    files (line by line)
		  and copies them to the destination.
	"""
	
	def getData(filename):
		ext = splitext(filename)[1]
		# savJ/savE -> get edit data
		if ext in ['.savJ', '.savE']:
			with ZipFile(filename, 'r') as zip: datj = zip.read('edit.datJ').decode('ANSI')
			return parseDatJ(datj)
		# patJ/patE -> read edit data
		elif ext in ['.patJ', '.patE']:
			with open(filename, 'r', encoding = 'ANSI') as file: patj = file.read()
			return parseDatJ(patj)
		# binJ/e -> read orig data
		elif ext in ['.binJ', '.e']:
			return getOrigData(filename)[0]
	
	def getOrigData(filename):
		ext = splitext(filename)[1]
		# savJ -> get orig data and extra
		if ext == '.savJ':
			with ZipFile(filename, 'r') as zip:
				datj = zip.read('orig.datJ').decode('ANSI')
				prefix = zip.read('prefix.bin')
			return parseDatJ(datj), {'prefix': prefix}
		# savE -> get orig data and extra
		elif ext == '.savE':
			with ZipFile(filename, 'r') as zip:
				datj = zip.read('orig.datJ').decode('ANSI')
				prefix = zip.read('prefix.bin')
				header = zip.read('header.datE').decode('ASCII')
				scripts = zip.read('scripts.spt').decode('ASCII')
				links = zip.read('links.tabE').decode('ASCII')
			header = parseDatE(header)
			scripts = parseSpt(scripts)
			links = parseTabE(links)
			extra = {'prefix': prefix, 'header': header, 'scripts': scripts, 'links': links}
			return parseDatJ(datj), extra
		# binJ -> read orig data and extra
		elif ext == '.binJ':
			try:
				with open(filename, 'rb') as file: bin = file.read()
				return parseBinJ(bin, Params.SEP())
			except:
				print(' !', 'Error: Parsing .binJ file failed.')
				return None, None
		# e -> read orig data and extra
		elif ext == '.e':
			try:
				with GzipFile(filename, 'r') as file: bin = file.read()
				return parseE(bin, Params.SEP())
			except:
				print(' !', 'Error: Parsing .e file failed.')
				return None, None
	
	def saveBinJ(filename, data, extra):
		bin = createBinJ(data, Params.SEP(), extra)
		with open(filename, 'wb') as file: file.write(bin)
	
	def saveE(filename, data, extra):
		bin = createE(data, Params.SEP(), extra)
		with open(filename, 'wb') as file:
			with GzipFile(fileobj=file, mode='w', filename='', mtime=0) as gzipFile: gzipFile.write(bin)
	
	def collectFiles(folder, ext_orig, ext_save, ext_patch, ver = None):
		# collect all files ordered by priority language and priority type
		files = dict() # dict of shortname (no first folder, no ext) -> list of files
		for lang in languages + (None,):
			for type in [ext_save, ext_patch, ext_orig]:
				for file in [join(dp, f) for dp, dn, fn in walk(joinFolder(folder, lang, ver)) for f in [n for n in fn if splitext(n)[1] == type]]:
					shortname = join(*extpath(splitext(file)[0]))
					files[shortname] = files.get(shortname, list()) + [(lang, type)]
		
		# add original files
		for file in [join(dp, f) for dp, dn, fn in walk(joinFolder(folder, original_language, ver)) for f in [n for n in fn if splitext(n)[1] == ext_orig]]:
			shortname = join(*extpath(splitext(file)[0]))
			files[shortname] = files.get(shortname, list()) + [(original_language, ext_orig)]
		
		# only keep needed files
		for shortname, file_list in files.items():
			# convert to list for every language, list of (lang, [types])
			f = list()
			for lang, type in file_list:
				if f and f[-1][0] == lang: f[-1][1].append(type)
				else: f.append((lang, [type]))
			
			# last file must contain original data (savJ or binJ)
			while ext_save not in f[-1][1] and ext_orig not in f[-1][1]:
				if not f: # no original file found, skip
					files[shortname] = None # filter None values later
					continue
				del f[-1]
			if ext_patch in f[-1][1]: f[-1][1].remove(ext_patch)
			if ext_save in f[-1][1] and ext_orig in f[-1][1]: f[-1][1].remove(ext_orig)
			
			# keep best option for other languages
			for _, types in f[:-1]: del types[1:]
			
			# remove languages if a previous language only contains a binJ
			for i, (_, types) in enumerate(f):
				if types == [ext_orig]: del f[i+1:]
			
			# remove files that only have the original data
			if not any(lang != original_language for lang, _ in f):
				files[shortname] = None # filter None values later
				continue
			
			# update file_list
			files[shortname] = [join(joinFolder(folder, lang, ver), shortname + type[0]) for lang, type in f]
		
		# filter None values
		files = {k: v for k, v in files.items() if v}
		return files
	
	# iterate over all patj folders
	ctr = dict()
	for folder, (mode, ext_orig, ext_save, ext_patch) in Params.patFolders().items():
		for ver in versions: # iterate over versions
			# collect files
			files = collectFiles(folder, ext_orig, ext_save, ext_patch, ver)
			if len(versions) > 1 and ver is None: # remove files that are in the original update
				update_files = [join(*extpath(splitext(join(dp, f))[0])) for dp, dn, fn in walk(joinFolder(folder, original_language, versions[1])) for f in [n for n in fn if splitext(n)[1] == ext_orig]]
				files = {shortname: file_list for shortname, file_list in files.items() if shortname not in update_files}
			if VERBOSE >= 3 or VERBOSE >= 1 and len(files) > 0: print(joinFolder(folder, ver), '[%d]' % len(files))
			
			# create output files
			dest_folder = join(destination_dir, Params.parentFolders()[folder])
			for shortname, file_list in files.items():
				msg_prefix = ' * %s%s:' % (shortname, ext_orig)
				dest_file = join(dest_folder, shortname + ext_orig)
				
				# collect data
				data = None
				for file in file_list:
					update_data = getData(file)
					if data: data = [e if e else update_data[i] for i, e in enumerate(data)]
					else: data = update_data
				orig_data, extra = getOrigData(file_list[-1])
				if orig_data is None: continue
				data = [e if e else orig_data[i] for i, e in enumerate(data)]
				
				# create temporary output file
				temp_dest_file = dest_file + '.temp'
				makedirs(dirname(dest_file), exist_ok=True)
				if mode == 'binJ': saveBinJ(temp_dest_file, data, extra)
				elif mode == 'e': saveE(temp_dest_file, data, extra)
				
				# check if file already exists
				if exists(dest_file):
					# compare files
					if not force_override and hash(dest_file) == hash(temp_dest_file):
						# equal -> keep old
						if VERBOSE >= 3: print(msg_prefix, 'keep')
						ctr['keep'] = ctr.get('keep', 0) + 1
						remove(temp_dest_file)
					else:
						# new -> update file
						if VERBOSE >= 2: print(msg_prefix, 'update')
						ctr['update'] = ctr.get('update', 0) + 1
						remove(dest_file)
						rename(temp_dest_file, dest_file)
				else:
					# add new file
					if VERBOSE >= 2: print(msg_prefix, 'add')
					ctr['add'] = ctr.get('add', 0) + 1
					makedirs(dirname(dest_file), exist_ok=True)
					rename(temp_dest_file, dest_file)
	return ctr

def distributeOtherFiles(languages, versions, original_language, destination_dir, force_override, VERBOSE):
	""" Copies all *.* files to the given destination. """
	
	def collectFiles(folder, types, ver = None):
		# collect all files ordered by priority language
		files = list() # list of (filename, simplename)
		for lang in languages + (None,): # fallback from folders without language
			for file in [join(dp, f) for dp, dn, fn in walk(joinFolder(folder, lang, ver)) for f in [n for n in fn if splitext(n)[1] in types]]:
				simplename = extpath(file)
				if any(s == simplename for _, s in files): continue
				files.append((file, simplename))
		
		# remove files that are the same as the original files
		orig_folder = joinFolder(folder, original_language)
		files = [(f, s) for f, s in files if not exists(join(orig_folder, *s)) or hash(join(orig_folder, *s)) != hash(f)]
		return files
	
	# iterate over all xdelta folders
	ctr = dict()
	for folder, types in Params.xdeltaFolders().items():
		for ver in versions: # iterate over versions
			# collect files
			files = collectFiles(folder, types, ver)
			if len(versions) > 1 and ver is None: # remove files that are in the original update
				update_files = [extpath(join(dp, f)) for dp, dn, fn in walk(joinFolder(folder, original_language, versions[1])) for f in [n for n in fn if splitext(n)[1] in types]]
				files = [(file, simplename) for file, simplename in files if simplename not in update_files]
			if VERBOSE >= 3 or VERBOSE >= 1 and len(files) > 0: print(joinFolder(folder, ver), '[%d]' % len(files))
			
			# copy collected files
			dest_folder = join(destination_dir, Params.parentFolders()[folder])
			for source_file, simplename in files:
				msg_prefix = ' * %s:' % source_file
				dest_file = join(dest_folder, *simplename)
				
				# check if file already exists
				if exists(dest_file):
					# compare files
					if not force_override and hash(dest_file) == hash(source_file):
						# equal -> keep old file
						if VERBOSE >= 3: print(msg_prefix, 'keep')
						ctr['keep'] = ctr.get('keep', 0) + 1
					else:
						# new -> update file
						if VERBOSE >= 2: print(msg_prefix, 'update')
						ctr['update'] = ctr.get('update', 0) + 1
						remove(dest_file)
						copyfile(source_file, dest_file)
				else:
					# add new file
					if VERBOSE >= 2: print(msg_prefix, 'add')
					ctr['add'] = ctr.get('add', 0) + 1
					makedirs(dirname(dest_file), exist_ok=True)
					copyfile(source_file, dest_file)
	return ctr
