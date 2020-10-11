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
from os.path import join, exists, splitext, dirname, basename, normpath
from shutil import copyfile
from hashlib import md5
from zipfile import ZipFile
from BinJEditor.JTools import parseBinJ, createBinJ, parseDatJ, createDatJ
from tempfile import gettempdir as tempdir
from subprocess import run

# 0: nothing, 1: minimal, 2: all
VERBOSE = 1

# default DQM separator token
SEP = b'\xe3\x1b'

# folders to search for files and patches
XDELTA_FOLDERS = {
	'Banner':      ['.bcwav', '.cmbd', '.cgfx'],
	'Battle':      ['.bcres'],
	'Debug':       ['.bin'],
	'Effect':      ['.bcres'],
	'Event':       ['.gz', '.e'],
	'Field':       ['.gz', '.xbb', '.bcres'],
	'Font':        ['.bcfnt'],
	'KeyImage':    ['.bclim'],
	'Layout':      ['.arc'],
	'Menu3D':      ['.bcres', '.bcenv'],
	'Model':       ['.bcres'],
	'MonsterIcon': ['.bclim'],
	'NaviMap':     ['.arc'],
	'Param':       ['.gz', '.bin'],
	'PartsIcon':   ['.bclim'],
	'Title':       ['.bcres'],
}
PATJ_FOLDERS = {
	'Message': ['.savJ'],
}

# where to put the folders when distributing
PARENT_FOLDERS = {
	'Banner':      'ExtractedBanner',
	'Battle':      join('ExtractedRomFS', 'data', 'Battle'),
	'Debug':       join('ExtractedRomFS', 'data', 'Debug'),
	'Effect':      join('ExtractedRomFS', 'data', 'Effect'),
	'Event':       join('ExtractedRomFS', 'data', 'Event'),
	'Field':       join('ExtractedRomFS', 'data', 'Field'),
	'Font':        join('ExtractedRomFS', 'data', 'Font'),
	'KeyImage':    join('ExtractedRomFS', 'data', 'KeyImage'),
	'Layout':      join('ExtractedRomFS', 'data', 'Layout'),
	'Menu3D':      join('ExtractedRomFS', 'data', 'Menu3D'),
	'Message':     join('ExtractedRomFS', 'data', 'Message'),
	'Model':       join('ExtractedRomFS', 'data', 'Model'),
	'MonsterIcon': join('ExtractedRomFS', 'data', 'MonsterIcon'),
	'NaviMap':     join('ExtractedRomFS', 'data', 'NaviMap'),
	'Param':       join('ExtractedRomFS', 'data', 'Param'),
	'PartsIcon':   join('ExtractedRomFS', 'data', 'PartsIcon'),
	'Title':       join('ExtractedRomFS', 'data', 'Title'),
}


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

def loopFiles(folders, original_language = None):
	""" Loops over the files in the folders with the given names that
		match the given file types.
	"""
	# iterate over all defined folders
	for folder, types in folders.items():
		
		if original_language:
			orig_folder = '%s_%s' % (folder, original_language)
			if not exists(orig_folder): continue
			
			# iterate over all languages found
			for edit_folder in [dir for dir in listdir('.') if dir.split('_')[0] == folder and dir != orig_folder]:
				if VERBOSE >= 1: print(edit_folder, end=' ', flush=True)
				
				# iterate over all files with a valid file extension
				files = [join(dp, f) for dp, dn, fn in walk(edit_folder) for f in [n for n in fn if splitext(n)[1] in types]]
				if VERBOSE >= 1: print('[%s]' % len(files))
				for edit_file in files:
					yield (edit_file, orig_folder)
		
		else:
			# iterate over all languages found
			for edit_folder in [dir for dir in listdir('.') if dir.split('_')[0] == folder]:
				if VERBOSE >= 1: print(edit_folder, end=' ', flush=True)
				
				# iterate over all files with a valid file extension
				files = [join(dp, f) for dp, dn, fn in walk(edit_folder) for f in [n for n in fn if splitext(n)[1] in types]]
				if VERBOSE >= 1: print('[%s]' % len(files))
				for edit_file in files:
					yield edit_file


###########
## Apply ##
###########

def applyPatches(original_language = 'JA', force_override = False):
	ctr  = applyPatJPatches(original_language, force_override)
	ctr2 = applyXDeltaPatches(original_language, force_override)
	for k, v in ctr2.items(): ctr[k] = ctr.get(k, 0) + v
	print()
	if VERBOSE >= 1 and ctr.get('create', 0) > 0 or VERBOSE >= 2: print('Created %d files.' % ctr.get('create', 0))
	if VERBOSE >= 1: print('Updated %d files.' % ctr.get('update', 0))
	if VERBOSE >= 2: print('Kept %d files.' % ctr.get('keep',   0))

def applyPatJPatches(original_language, force_override):
	""" Creates .binJ files from .patJ patches and the original .binJ file.
		Creates .savJ files from .patJ patches and the old .savJ save file.
	"""
	
	def applyPatJToBinJ(orig_file, patch_file, output_file):
		# read original file
		try:
			with open(orig_file, 'rb') as file: binj = file.read()
			prefix, orig_data = parseBinJ(binj, SEP)
		except:
			print('Error: Parsing .binJ file failed.')
			return
		# read patch file
		with open(patch_file, 'r', encoding = 'ANSI') as file: patj = file.read()
		edit_data = parseDatJ(patj)
		# check if compatible
		if len(edit_data) != len(orig_data):
			print('Warning: Lengths of original file and patch differ.')
			if len(edit_data) > len(orig_data): edit_data = edit_data[:len(orig_data)]
			else: edit_data = edit_data + [b'']*(len(orig_data) - len(edit_data))
		# patch data
		output_data = [v if v else orig_data[i] for i, v in enumerate(edit_data)]
		# save output file
		binj = createBinJ(prefix, output_data, SEP)
		with open(output_file, 'wb') as file: file.write(binj)
	
	def applyPatJToSavJ(save_file, patch_file, output_file):
		# read save file
		with ZipFile(save_file, 'r') as zip:
			prefix = zip.read('prefix.bin')
			origj = zip.read('orig.datJ').decode('ANSI')
			sep_from_save = zip.read('SEP.bin')
			specialj = zip.read('special.tabJ')
			decodej = zip.read('decode.tabJ')
			encodej = zip.read('encode.tabJ')
		orig_data = parseDatJ(origj)
		# read patch file and override edit_data
		with open(patch_file, 'r', encoding = 'ANSI') as file: patj = file.read()
		edit_data = parseDatJ(patj)
		# check if compatible
		if len(edit_data) != len(orig_data):
			print('Warning: Lengths of original file and patch differ.')
			if len(edit_data) > len(orig_data): edit_data = edit_data[:len(orig_data)]
			else: edit_data = edit_data + [b'']*(len(orig_data) - len(edit_data))
		# save output file
		origj = createDatJ(orig_data)
		editj = createDatJ(edit_data)
		prefix_filename = join(tempdir(), 'prefix.bin')
		with open(prefix_filename, 'wb') as file: file.write(prefix)
		orig_filename = join(tempdir(), 'orig.datJ')
		with open(orig_filename, 'w', encoding = 'ANSI') as file: file.write(origj)
		edit_filename = join(tempdir(), 'edit.datJ')
		with open(edit_filename, 'w', encoding = 'ANSI') as file: file.write(editj)
		sep_filename = join(tempdir(), 'SEP.bin')
		with open(sep_filename, 'wb') as file: file.write(sep_from_save)
		special_filename = join(tempdir(), 'special.tabJ')
		with open(special_filename, 'wb') as file: file.write(specialj)
		decode_filename = join(tempdir(), 'decode.tabJ')
		with open(decode_filename, 'wb') as file: file.write(decodej)
		encode_filename = join(tempdir(), 'encode.tabJ')
		with open(encode_filename, 'wb') as file: file.write(encodej)
		with ZipFile(output_file, 'w') as file:
			file.write(prefix_filename, arcname=basename(prefix_filename))
			file.write(orig_filename, arcname=basename(orig_filename))
			file.write(edit_filename, arcname=basename(edit_filename))
			file.write(sep_filename, arcname=basename(sep_filename))
			file.write(special_filename, arcname=basename(special_filename))
			file.write(decode_filename, arcname=basename(decode_filename))
			file.write(encode_filename, arcname=basename(encode_filename))
		remove(prefix_filename)
		remove(orig_filename)
		remove(edit_filename)
		remove(sep_filename)
		remove(special_filename)
		remove(decode_filename)
		remove(encode_filename)
	
	ctr = dict()
	folders = dict(zip(PATJ_FOLDERS, ['.patJ']*len(PATJ_FOLDERS)))
	for patch_file, orig_folder in loopFiles(folders, original_language):
		simplename = extpath(patch_file)
		msg_prefix = ' * %s:' % join(*simplename[:-1], splitext(simplename[-1])[0] + '.binJ')
		
		# find corresponding original file
		orig_file = join(orig_folder, *simplename[:-1], splitext(simplename[-1])[0] + '.binJ')
		if not exists(orig_file):
			if VERBOSE >= 1: print(' !', 'Warning: Original File Not Found:', join(*extpath(orig_file)))
			continue
		
		# define output file
		output_file = patch_file[:-len('.patJ')]+'.binJ'
		
		# check if output file already exists
		if exists(output_file):
			# create temporary output file
			temp_output_file = output_file + '.temp'
			applyPatJToBinJ(orig_file, patch_file, temp_output_file)
			# compare output files
			if not force_override and hash(output_file) == hash(temp_output_file):
				# equal -> keep old output file
				if VERBOSE >= 2: print(msg_prefix, 'keep')
				ctr['keep'] = ctr.get('keep', 0) + 1
				remove(temp_output_file)
			else:
				# new -> update output file
				if VERBOSE >= 1: print(msg_prefix, 'update')
				ctr['update'] = ctr.get('update', 0) + 1
				remove(output_file)
				rename(temp_output_file, output_file)
		else:
			# create new output file
			if VERBOSE >= 1: print(msg_prefix, 'create')
			ctr['create'] = ctr.get('create', 0) + 1
			applyPatJToBinJ(orig_file, patch_file, output_file)
		
		# define output save file
		msg_prefix = ' * %s:' % join(*simplename[:-1], splitext(simplename[-1])[0] + '.savJ')
		output_save_file = patch_file[:-len('.patJ')]+'.savJ'
		
		# check if output save file exists
		if exists(output_save_file):
			# create temporary output save file
			temp_output_save_file = output_save_file + '.temp'
			applyPatJToSavJ(output_save_file, patch_file, temp_output_save_file)
			# compare save files
			if not force_override and hashZip(output_save_file) == hashZip(temp_output_save_file):
				# equal -> keep old save file
				if VERBOSE >= 2: print(msg_prefix, 'keep')
				ctr['keep'] = ctr.get('keep', 0) + 1
				remove(temp_output_save_file)
			else:
				# new -> update save file
				if VERBOSE >= 1: print(msg_prefix, 'update')
				ctr['update'] = ctr.get('update', 0) + 1
				remove(output_save_file)
				rename(temp_output_save_file, output_save_file)
	return ctr

def applyXDeltaPatches(original_language, force_override):
	""" Creates .* files from .*.xdelta patches and the original .* files. """
	
	def applyXDelta(orig_file, patch_file, output_file):
		run(['xdelta', '-f', '-d', '-s', orig_file, patch_file, output_file])
	
	ctr = dict()
	folders = dict(zip(XDELTA_FOLDERS.keys(), ['.xdelta']*len(XDELTA_FOLDERS)))
	for patch_file, orig_folder in loopFiles(folders, original_language):
		simplename = extpath(patch_file)
		simplename[-1] = simplename[-1][:-len('.xdelta')]
		msg_prefix = ' * %s:' % join(*simplename)
		
		# find corresponding original file
		orig_file = join(orig_folder, *simplename)
		if not exists(orig_file):
			print(' !', 'Warning: Original File Not Found:', join(*simplename))
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
				if VERBOSE >= 2: print(msg_prefix, 'keep')
				ctr['keep'] = ctr.get('keep', 0) + 1
				remove(temp_output_file)
			else:
				# new -> update output file
				if VERBOSE >= 1: print(msg_prefix, 'update')
				ctr['update'] = ctr.get('update', 0) + 1
				remove(output_file)
				rename(temp_output_file, output_file)
		else:
			# create new output file
			if VERBOSE >= 1: print(msg_prefix, 'create')
			ctr['create'] = ctr.get('create', 0) + 1
			applyXDelta(orig_file, patch_file, output_file)
	return ctr


############
## Create ##
############

def createPatches(original_language = 'JA', force_override = False):
	ctr  = createPatJPatches(force_override)
	ctr2 = createXDeltaPatches(original_language, force_override)
	for k, v in ctr2.items(): ctr[k] = ctr.get(k, 0) + v
	print()
	if VERBOSE >= 1 and ctr.get('create', 0) > 0 or VERBOSE >= 2: print('Created %d patches.' % ctr.get('create', 0))
	if VERBOSE >= 1: print('Updated %d patches.' % ctr.get('update', 0))
	if VERBOSE >= 1 and ctr.get('delete', 0) > 0 or VERBOSE >= 2: print('Deleted %d patches.' % ctr.get('delete', 0))
	if VERBOSE >= 2: print('Kept %d patches.' % ctr.get('keep',   0))
	if VERBOSE >= 2: print('Skipped %d files.' % ctr.get('skip',   0))

def createPatJPatches(force_override):
	""" Creates .patJ patches from .savJ files. """
	
	def createPatJ(savj_file, patj_file):
		# read edit data from save
		with ZipFile(savj_file, 'r') as zip:
			data = zip.read('edit.datJ').decode('ANSI')
		# correct newlines
		data = createDatJ(parseDatJ(data))
		# save patch file
		with open(patj_file, 'w', encoding = 'ANSI') as file:
			file.write(data)
	
	ctr = dict()
	for edit_file in loopFiles(PATJ_FOLDERS):
		simplename = extpath(edit_file)
		msg_prefix = ' * %s:' % join(*simplename[:-1], splitext(simplename[-1])[0]+'.patJ')
		
		# define patch file
		patch_file = splitext(edit_file)[0] + '.patJ'
		
		# check if patch already exists
		if exists(patch_file):
			# create temporary patch
			temp_patch_file = patch_file + '.temp'
			createPatJ(edit_file, temp_patch_file)
			# compare patches
			if not force_override and hash(patch_file) == hash(temp_patch_file):
				# equal -> keep old patch
				if VERBOSE >= 2: print(msg_prefix, 'keep')
				ctr['keep'] = ctr.get('keep', 0) + 1
				remove(temp_patch_file)
			else:
				# new -> update patch
				if VERBOSE >= 1: print(msg_prefix, 'update')
				ctr['update'] = ctr.get('update', 0) + 1
				remove(patch_file)
				rename(temp_patch_file, patch_file)
		else:
			# create new patch
			if VERBOSE >= 1: print(msg_prefix, 'create')
			ctr['create'] = ctr.get('create', 0) + 1
			createPatJ(edit_file, patch_file)
	return ctr

def createXDeltaPatches(original_language, force_override):
	""" Creates .*.xdelta patches from pairs of .* files. """
	
	def createXDelta(orig_file, edit_file, patch_file):
		run(['xdelta', '-f', '-s', orig_file, edit_file, patch_file])
	
	ctr = dict()
	for edit_file, orig_folder in loopFiles(XDELTA_FOLDERS, original_language):
		simplename = extpath(edit_file)
		msg_prefix = ' * %s:' % join(*simplename[:-1], simplename[-1]+'.xdelta')
		
		# find corresponding original file
		orig_file = join(orig_folder, *simplename)
		if not exists(orig_file):
			if VERBOSE >= 1: print(' !', 'Warning: Original File Not Found:', join(*simplename))
			continue
		
		# define patch file
		patch_file = edit_file + '.xdelta'
		
		# compare files
		if hash(orig_file) == hash(edit_file):
			# check if patch exists
			if exists(patch_file):
				if VERBOSE >= 1: print(msg_prefix, 'delete patch')
				ctr['delete'] = ctr.get('delete', 0) + 1
				remove(patch_file)
			else:
				if VERBOSE >= 2: print(msg_prefix, 'skip')
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
				if VERBOSE >= 2: print(msg_prefix, 'keep')
				ctr['keep'] = ctr.get('keep', 0) + 1
				remove(temp_patch_file)
			else:
				# new -> update patch
				if VERBOSE >= 1: print(msg_prefix, 'update')
				ctr['update'] = ctr.get('update', 0) + 1
				remove(patch_file)
				rename(temp_patch_file, patch_file)
		else:
			# create new patch
			if VERBOSE >= 1: print(msg_prefix, 'create')
			ctr['create'] = ctr.get('create', 0) + 1
			createXDelta(orig_file, edit_file, patch_file)
	return ctr


################
## Distribute ##
################

def distribute(languages, original_language = 'JA', destination_dir = '_dist', force_override = False):
	if not isinstance(languages, tuple): languages = (languages,)
	ctr  = distributeBinJFiles(languages, original_language, destination_dir, force_override)
	ctr2 = distributeOtherFiles(languages, original_language, destination_dir, force_override)
	for k, v in ctr2.items(): ctr[k] = ctr.get(k, 0) + v
	print()
	if VERBOSE >= 1 and ctr.get('add', 0) > 0 or VERBOSE >= 2: print('Added %d files.' % ctr.get('add', 0))
	if VERBOSE >= 1: print('Updated %d files.' % ctr.get('update', 0))
	if VERBOSE >= 2: print('Kept %d files.' % ctr.get('keep',   0))

def distributeBinJFiles(languages, original_language, destination_dir, force_override):
	""" Creates .binJ files from different .savJ / .patJ / .binJ files (line by line)
		and copys them to the given destination.
	"""
	# Info: Does not support folders without a language extension
	
	def getData(filename):
		ext = splitext(filename)[1]
		# savJ -> get edit data
		if ext == '.savJ':
			with ZipFile(filename, 'r') as zip: datj = zip.read('edit.datJ').decode('ANSI')
			return parseDatJ(datj)
		# patJ -> read edit data
		elif ext == '.patJ':
			with open(filename, 'r', encoding = 'ANSI') as file: patj = file.read()
			return parseDatJ(patj)
		# binJ -> read orig data
		elif ext == '.binJ':
			return getOrigData(filename)[1]
	
	def getOrigData(filename):
		ext = splitext(filename)[1]
		# savJ -> get orig data and prefix
		if ext == '.savJ':
			with ZipFile(filename, 'r') as zip:
				prefix = zip.read('prefix.bin')
				datj = zip.read('orig.datJ').decode('ANSI')
			return prefix, parseDatJ(datj)
		# binJ -> read orig data and prefix
		elif ext == '.binJ':
			try:
				with open(filename, 'rb') as file: binj = file.read()
				return parseBinJ(binj, SEP)
			except:
				print('Error: Parsing .binJ file failed.')
				return None, None
	
	def saveBinJ(filename, prefix, data):
		binj = createBinJ(prefix, data, SEP)
		with open(filename, 'wb') as file: file.write(binj)
	
	# iterate over all patj folders
	ctr = dict()
	for folder in PATJ_FOLDERS:
		# collect all files ordered by priority language and priority type
		files = dict() # dict of shortname (no first folder, no ext) -> list of files
		for lang in languages:
			for type in ['.savJ', '.patJ', '.binJ']:
				for file in [join(dp, f) for dp, dn, fn in walk('%s_%s' % (folder, lang)) for f in [n for n in fn if splitext(n)[1] == type]]:
					shortname = join(*extpath(splitext(file)[0]))
					files[shortname] = files.get(shortname, list()) + [(lang, type)]
		
		# add original files
		for file in [join(dp, f) for dp, dn, fn in walk('%s_%s' % (folder, original_language)) for f in [n for n in fn if splitext(n)[1] == '.binJ']]:
			shortname = join(*extpath(splitext(file)[0]))
			files[shortname] = files.get(shortname, list()) + [(original_language, '.binJ')]
		
		# only keep needed files
		for shortname, file_list in files.items():
			# convert to list for every language, list of (lang, [types])
			f = list()
			for lang, type in file_list:
				if f and f[-1][0] == lang: f[-1][1].append(type)
				else: f.append((lang, [type]))
			
			# last file must contain original data (savJ or binJ)
			while '.savJ' not in f[-1][1] and '.binJ' not in f[-1][1]: del f[-1]
			if '.patJ' in f[-1][1]: f[-1][1].remove('.patJ')
			if '.savJ' in f[-1][1] and '.binJ' in f[-1][1]: f[-1][1].remove('.binJ')
			
			# keep best option for other languages
			for _, types in f[:-1]: del types[1:]
			
			# remove languages if a previous language only contains a binJ
			for i, (_, types) in enumerate(f):
				if types == ['.binJ']: del f[i+1:]
			
			# remove files that only have the original data
			if not any(lang != original_language for lang, _ in f):
				files[shortname] = None # filter None values later
				continue
			
			# update file_list
			files[shortname] = [join('%s_%s' % (folder, lang), shortname + type[0]) for lang, type in f]
		
		# filter None values
		files = {k: v for k, v in files.items() if v}
		if VERBOSE >= 2 or VERBOSE >= 1 and len(files) > 0: print(folder, '[%d]' % len(files))
		
		# create output files
		dest_folder = join(destination_dir, PARENT_FOLDERS[folder])
		for shortname, file_list in files.items():
			msg_prefix = ' * %s.binJ:' % shortname
			dest_file = join(dest_folder, shortname + '.binJ')
			
			# collect data
			data = None
			for file in file_list:
				update_data = getData(file)
				if data: data = [e if e else update_data[i] for i, e in enumerate(data)]
				else: data = update_data
			prefix, orig_data = getOrigData(file_list[-1])
			if orig_data is None: continue
			data = [e if e else orig_data[i] for i, e in enumerate(data)]
			
			# create temporary output file
			temp_dest_file = dest_file + '.temp'
			makedirs(dirname(dest_file), exist_ok=True)
			saveBinJ(temp_dest_file, prefix, data)
			
			# check if file already exists
			if exists(dest_file):
				# compare files
				if not force_override and hash(dest_file) == hash(temp_dest_file):
					# equal -> keep old
					if VERBOSE >= 2: print(msg_prefix, 'keep')
					ctr['keep'] = ctr.get('keep', 0) + 1
					remove(temp_dest_file)
				else:
					# new -> update file
					if VERBOSE >= 1: print(msg_prefix, 'update')
					ctr['update'] = ctr.get('update', 0) + 1
					remove(dest_file)
					rename(temp_dest_file, dest_file)
			else:
				# add new file
				if VERBOSE >= 1: print(msg_prefix, 'add')
				ctr['add'] = ctr.get('add', 0) + 1
				makedirs(dirname(dest_file), exist_ok=True)
				rename(temp_dest_file, dest_file)
	return ctr

def distributeOtherFiles(languages, original_language, destination_dir, force_override):
	""" Copys all *.* files to the given destination. """
	
	# iterate over all xdelta folders
	ctr = dict()
	for folder, types in XDELTA_FOLDERS.items():
		# collect all files ordered by priority language
		files = list() # list of (filename, simplename)
		for lang in languages:
			for file in [join(dp, f) for dp, dn, fn in walk('%s_%s' % (folder, lang)) for f in [n for n in fn if splitext(n)[1] in types]]:
				simplename = extpath(file)
				if any(s == simplename for _, s in files): continue
				files.append((file, simplename))
		
		# add files from folder without language extension
		for file in [join(dp, f) for dp, dn, fn in walk(folder) for f in [n for n in fn if splitext(n)[1] in types]]:
			simplename = extpath(file)
			if any(s == simplename for _, s in files): continue
			files.append((file, simplename))
		
		# remove files that are the same as the original files
		orig_folder = '%s_%s' % (folder, original_language)
		files = [(f, s) for f, s in files if not exists(join(orig_folder, *s)) or hash(join(orig_folder, *s)) != hash(f)]
		if VERBOSE >= 2 or VERBOSE >= 1 and len(files) > 0: print(folder, '[%d]' % len(files))
		
		# copy collected files
		dest_folder = join(destination_dir, PARENT_FOLDERS[folder])
		for source_file, simplename in files:
			msg_prefix = ' * %s:' % source_file
			dest_file = join(dest_folder, *simplename)
			
			# check if file already exists
			if exists(dest_file):
				# compare files
				if not force_override and hash(dest_file) == hash(source_file):
					# equal -> keep old file
					if VERBOSE >= 2: print(msg_prefix, 'keep')
					ctr['keep'] = ctr.get('keep', 0) + 1
				else:
					# new -> update file
					if VERBOSE >= 1: print(msg_prefix, 'update')
					ctr['update'] = ctr.get('update', 0) + 1
					remove(dest_file)
					copyfile(source_file, dest_file)
			else:
				# add new file
				if VERBOSE >= 1: print(msg_prefix, 'add')
				ctr['add'] = ctr.get('add', 0) + 1
				makedirs(dirname(dest_file), exist_ok=True)
				copyfile(source_file, dest_file)
	return ctr
