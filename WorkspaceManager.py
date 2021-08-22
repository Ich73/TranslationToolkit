""" Author: Dominik Beese
>>> Workspace Manager
<<<
"""

from os import makedirs, listdir, walk, remove, rename, stat, chmod
from os.path import join, normpath, sep, exists, isdir, dirname, basename, splitext, commonprefix, relpath, abspath
from stat import S_IXUSR, S_IXGRP, S_IXOTH
from subprocess import run, PIPE, STDOUT, DEVNULL
from zipfile import ZipFile
from tarfile import open as TarFile
from io import BytesIO
from urllib.request import urlopen
from tempfile import mkdtemp
from shutil import move, rmtree, copyfile, copytree
import re
import ssl

from TranslationPatcher import hash, splitFolder, joinFolder, Params

# 0: nothing, 1: normal, 2: all
VERBOSE = 1


###########
## Tools ##
###########

def checkTool(tool, target_version, args = ''):
	""" Checks the version of the given [tool] by calling it using
		the given [args] and returns true if the version matches
		the [target_version], false otherwise.
	"""
	proc = run(' '.join((abspath(tool), args)), shell=True, stdout=PIPE, stderr=STDOUT)
	output = proc.stdout.decode('UTF-8', errors='replace')
	match = re.search(r'\d+(\.\d+)+\w*', output)
	version = match.group() if match else None
	return version == target_version

def downloadTool(download_url, filename):
	""" Downloads an executable from the given [download_url],
		puts it in the current directory and renames it to [filename].
		If the download is a zip or tar file it uses the first executable found in the archive.
	"""
	# remove file if existent
	if exists(filename):
		print('Updating', filename)
		remove(filename)
	
	# get type and download data
	print('Downloading', basename(download_url))
	print(' ', 'from', download_url)
	type = splitext(download_url)[1]
	with urlopen(download_url, context=ssl._create_unverified_context()) as url: data = url.read()
	
	# zip archive
	if type == '.zip':
		with ZipFile(BytesIO(data)) as zip:
			file = next((file for file in zip.infolist() if splitext(file.filename)[1] == splitext(filename)[1]), None)
			if not file: raise Exception('The downloaded zip archive does not contain a suitable executable.')
			print('Extracting', basename(file.filename))
			zip.extract(file)
			rename(basename(file.filename), filename)
	
	# tar archive
	elif type in ['.tar', '.gz']:
		with TarFile(fileobj=BytesIO(data)) as tar:
			file = next((file for file in tar.getmembers() if splitext(file.name)[1] == splitext(filename)[1]), None)
			if not file: raise Exception('The downloaded tar archive does not contain a suitable executable.')
			print('Extracting', basename(file.name))
			tar.extract(file)
			rename(basename(file.name), filename)
	
	# executable
	elif type in ['.exe', '']:
		with open(filename, 'wb') as file:
			file.write(data)
	
	# not supported
	else: raise Exception('The download link does not point towards a zip archive, tar archive or executable.')
	
	# make executable
	chmod(filename, stat(filename).st_mode | S_IXUSR | S_IXGRP | S_IXOTH)
	
	# success
	print('Downloaded', filename)
	print()


###########
## Setup ##
###########

def downloadAndExtractPatches(download_url):
	try:
		with urlopen(download_url, context=ssl._create_unverified_context()) as url: data = url.read()
		return extractPatches(BytesIO(data))
	except Exception as e:
		print('Error:', str(e))
		return False

def extractPatches(zip_file):
	try:
		# create temporary folder
		tempdir = mkdtemp()
		
		# extract patches to temporary folder and move them
		ctr = dict()
		folders = list()
		with ZipFile(zip_file) as zip:
			for file in zip.infolist():
				if file.is_dir(): continue
				filename = file.filename
				simplename = normpath(filename).split(sep)[1:]
				if not simplename: continue
				folder = simplename[0] if len(simplename) > 1 else None
				simplename = join(*simplename)
				if VERBOSE >= 2: print(simplename)
				if VERBOSE == 1 and folder and folder not in folders:
					print(folder)
					folders.append(folder)
				extracted_file = zip.extract(filename, path=tempdir)
				if exists(simplename) and hash(extracted_file) == hash(simplename):
					remove(extracted_file)
				else:
					directory = dirname(simplename)
					if directory: makedirs(directory, exist_ok=True)
					move(extracted_file, simplename)
					ctr['update'] = ctr.get('update', 0) + 1
				ctr['extract'] = ctr.get('extract', 0) + 1
		if VERBOSE >= 1:
			print()
			print('Extracted %d patches.' % ctr.get('extract', 0))
			print('Updated %d patches.'    % ctr.get('update', 0))
		
		# delete temporary folder
		rmtree(tempdir)
		return True
	
	except Exception as e:
		print('Error:', str(e))
		return False

def doUpdateActions():
	# force reloading params in case they changed
	Params.loadParams(force_reload = True)
	
	# iterate over all actions in params
	for action, options in Params.updateActions():
		
		# rename-folder -> rename matching folders and copy over all files without overriding existing files
		if action.lower() == 'rename-folder':
			old_folder, new_folder = options
			directories = [splitFolder(dir) for dir in listdir('.') if isdir(dir) and splitFolder(dir)['folder'] == old_folder]
			for dir in directories:
				old_dir = joinFolder(old_folder, dir.get('lang'), dir.get('version'))
				new_dir = joinFolder(new_folder, dir.get('lang'), dir.get('version'))
				if VERBOSE >= 1: print('Copy %s to %s' % (old_dir, new_dir))
				copytree(old_dir, new_dir, ignore=lambda _, l: [f for f in l if exists(join(new_dir, f))], dirs_exist_ok=True)
		
		# delete-folder -> delete all matching folders
		if action.lower() == 'delete-folder':
			folder = options
			directories = [dir for dir in listdir('.') if isdir(dir) and splitFolder(dir)['folder'] == old_folder]
			for dir in directories:
				if VERBOSE >= 1: print('Delete %s' % dir)
				rmtree(dir)
	
	if VERBOSE >= 1: print('Finished all actions.')

def copyOriginalFiles(cia_dir, version = None, original_language = 'JA'):
	try:
		# collect patched folders
		folders = Params.xdeltaFolders().copy() # merge xdelta and pat folders
		for k, v in Params.patFolders().items(): folders[k] = folders.get(k, list()) + [v[1]]
		folders = {folder: types for folder, types in folders.items() # only keep existing folders
					if exists(folder) or any(x.split('_')[0] == folder for x in listdir('.'))}
		
		# copy files
		ctr = dict()
		for folder, types in sorted(folders.items()):
			cia_folder = join(cia_dir, Params.parentFolders()[folder])
			workspace_folder = joinFolder(folder, original_language, version)
			if VERBOSE >= 1: print(workspace_folder)
			for original_file in [join(dp, f) for dp, dn, fn in walk(cia_folder) for f in fn if splitext(f)[1] in types]:
				common_prefix = commonprefix((original_file, cia_folder))
				simplename = relpath(original_file, common_prefix)
				workspace_file = join(workspace_folder, simplename)
				if VERBOSE >= 2: print(' *', simplename)
				ctr['find'] = ctr.get('find', 0) + 1
				if exists(workspace_file) and hash(original_file) == hash(workspace_file): continue
				directory = dirname(workspace_file)
				if directory: makedirs(directory, exist_ok=True)
				copyfile(original_file, workspace_file)
				ctr['copy'] = ctr.get('copy', 0) + 1
		
		if VERBOSE >= 1:
			print()
			print('Found %d files.' % ctr.get('find', 0))
			print('Copied %d files.' % ctr.get('copy', 0))
		
		return True
		
	except Exception as e:
		print('Error:', str(e))
		return False


#############
## Release ##
#############

def copyPatchedFiles(output_folder, cia_dir):
	try:
		if VERBOSE >= 1: print('Copying files...')
		ctr = 0
		for src_file in [join(dp, f) for dp, dn, fn in walk(output_folder) for f in fn]:
			common_prefix = commonprefix((src_file, output_folder))
			simplename = relpath(src_file, common_prefix)
			if VERBOSE >= 2: print(' *', simplename)
			dest_file = join(cia_dir, simplename)
			directory = dirname(dest_file)
			if directory: makedirs(directory, exist_ok=True)
			copyfile(src_file, dest_file)
			ctr += 1
		
		if VERBOSE >= 1:
			print()
			print('Copied %d files.' % ctr)
		
		return True
		
	except Exception as e:
		print('Error:', str(e))
		return False

def prepareReleasePatches(cia_dir, original_language = 'JA'):
	ctr = 0
	# save original banner if not existent
	if exists(join(cia_dir, 'ExtractedBanner')) and not exists(join(cia_dir, 'banner-%s.bin' % original_language)):
		if VERBOSE >= 1: print('Save original banner to banner-%s.bin' % original_language)
		copyfile(join(cia_dir, 'ExtractedExeFS', 'banner.bin'), join(cia_dir, 'banner-%s.bin' % original_language))
		ctr += 1
	
	# save original code and icon if not existent
	for item in ['code', 'icon']:
		if exists(join(cia_dir, 'ExtractedExeFS', '%s.bin' % item)) and not exists(join(cia_dir, '%s-%s.bin' % (item, original_language))):
			if VERBOSE >= 1: print('Save original %s to %s-%s.bin' % (item, item, original_language))
			copyfile(join(cia_dir, 'ExtractedExeFS', '%s.bin' % item), join(cia_dir, '%s-%s.bin' % (item, original_language)))
			ctr += 1
	
	if VERBOSE >= 1: print('Saved %d files.' % ctr)

def createReleasePatches(cia_dir, patches_filename, xdelta, dstool, original_language = 'JA'):
	try:
		# create banner patch
		if exists(join(cia_dir, 'ExtractedBanner')):
			# rebuild banner
			if VERBOSE >= 1: print('Rebuilding banner...')
			rename(join(cia_dir, 'ExtractedBanner', 'banner.cgfx'), join(cia_dir, 'ExtractedBanner', 'banner0.bcmdl'))
			run([abspath(dstool), '-ctf', 'banner', 'banner.bin', '--banner-dir', 'ExtractedBanner'], cwd=cia_dir, stdout=DEVNULL, stderr=DEVNULL)
			rename(join(cia_dir, 'ExtractedBanner', 'banner0.bcmdl'), join(cia_dir, 'ExtractedBanner', 'banner.cgfx'))
			# copy to exeFS (if you want to create a CIA file)
			if exists(join(cia_dir, 'ExtractedExeFS')):
				if VERBOSE >= 1: print('Copy banner to ExtractedExeFS')
				copyfile(join(cia_dir, 'banner.bin'), join(cia_dir, 'ExtractedExeFS', 'banner.bin'))
			# create patch
			if hash(join(cia_dir, 'banner.bin')) != hash(join(cia_dir, 'banner-%s.bin' % original_language)):
				if VERBOSE >= 1: print('Creating banner patch...')
				run([abspath(xdelta), '-f', '-s', 'banner-%s.bin' % original_language, 'banner.bin', 'banner.xdelta'], cwd=cia_dir)
				if VERBOSE >= 1: print()
			else:
				if VERBOSE >= 2:
					print('Skip banner patch')
					print()
		
		# create code and icon patch
		for item in ['code', 'icon']:
			if exists(join(cia_dir, 'ExtractedExeFS', '%s.bin' % item)):
				# create patch
				if hash(join(cia_dir, 'ExtractedExeFS', '%s.bin' % item)) != hash(join(cia_dir, '%s-%s.bin' % (item, original_language))):
					if VERBOSE >= 1: print('Creating %s patch...' % item)
					run([abspath(xdelta), '-f', '-s', '%s-%s.bin' % (item, original_language), join('ExtractedExeFS', '%s.bin' % item), '%s.xdelta' % item], cwd=cia_dir)
					if VERBOSE >= 1: print()
				else:
					if VERBOSE >= 2:
						print('Skip %s patch' % item)
						print()
		
		# create romFS patch
		if exists(join(cia_dir, 'ExtractedRomFS')):
			# rebuild romFS
			if VERBOSE >= 1: print('Rebuilding RomFS...')
			run([abspath(dstool), '-ctf', 'romfs', 'CustomRomFS.bin', '--romfs-dir', 'ExtractedRomFS'], cwd=cia_dir, stdout=DEVNULL, stderr=DEVNULL)
			# create patch
			if VERBOSE >= 1: print('Creating RomFS patch...')
			run([abspath(xdelta), '-f', '-s', 'DecryptedRomFS.bin', 'CustomRomFS.bin', 'RomFS.xdelta'], cwd=cia_dir)
			if VERBOSE >= 1: print()
		
		# archive patches
		directory = dirname(patches_filename)
		if directory: makedirs(directory, exist_ok=True)
		with ZipFile(patches_filename, 'w') as zip:
			for patch in ['banner.xdelta', 'code.xdelta', 'icon.xdelta', 'RomFS.xdelta']:
				file = join(cia_dir, patch)
				if exists(file):
					if VERBOSE >= 1: print('Add %s to patches' % patch)
					zip.write(file, arcname=patch)
		if VERBOSE >= 1:
			print()
			print('Saved all patches to %s' % patches_filename)
		
		return True
		
	except Exception as e:
		print('Error:', str(e))
		return False
