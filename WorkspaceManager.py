""" Author: Dominik Beese
>>> Workspace Manager
<<<
"""

from os import makedirs, listdir, walk, remove, getenv, rename
from os.path import join, normpath, sep, exists, isdir, dirname, splitext, commonprefix, relpath
from subprocess import run
from zipfile import ZipFile
from io import BytesIO
from urllib.request import urlopen
from tempfile import mkdtemp
from shutil import move, rmtree, copyfile

from TranslationPatcher import hash, joinFolder, XDELTA_FOLDERS, PAT_FOLDERS, PARENT_FOLDERS

# 0: nothing, 1: normal, 2: all
VERBOSE = 1

# Hacking Toolkit
TOOL_PATH = None
for base in [getenv('PROGRAMFILES'), getenv('PROGRAMFILES(x86)')]:
	path = join(base, 'HackingToolkit3DS', '3dstool.exe')
	if exists(path):
		TOOL_PATH = path
		break

def downloadAndExtractPatches(download_url):
	try:
		# create temporary folder
		tempdir = mkdtemp()
		
		# download patches
		with urlopen(download_url) as url: data = url.read()
		
		# extract patches to temporary folder and move them
		ctr = dict()
		folders = list()
		with ZipFile(BytesIO(data)) as zip:
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
					if directory and not exists(directory): makedirs(directory)
					move(extracted_file, simplename)
					ctr['update'] = ctr.get('update', 0) + 1
				ctr['download'] = ctr.get('download', 0) + 1
		if VERBOSE >= 1:
			print()
			print('Downloaded %d patches.' % ctr.get('download', 0))
			print('Updated %d patches.'    % ctr.get('update', 0))
		
		# delete temporary folder
		rmtree(tempdir)
		return True
	
	except Exception as e:
		print('Error:', str(e))
		return False

def copyOriginalFiles(cia_dir, version = None, original_language = 'JA'):
	try:
		# collect patched folders
		folders = XDELTA_FOLDERS.copy() # merge xdelta and pat folders
		for k, v in PAT_FOLDERS.items(): folders[k] = folders.get(k, list()) + [v[1]]
		folders = {folder: types for folder, types in folders.items() # only keep existing folders
					if exists(folder) or any(x.split('_')[0] == folder for x in listdir('.'))}
		
		# copy files
		ctr = dict()
		for folder, types in sorted(folders.items()):
			cia_folder = join(cia_dir, PARENT_FOLDERS[folder])
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
				if directory and not exists(directory): makedirs(directory)
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
			if directory and not exists(directory): makedirs(directory)
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
	
	# save original code if not existent
	if exists(join(cia_dir, 'ExtractedExeFS', 'code.bin')) and not exists(join(cia_dir, 'code-%s.bin' % original_language)):
		if VERBOSE >= 1: print('Save original code to code-%s.bin' % original_language)
		copyfile(join(cia_dir, 'ExtractedExeFS', 'code.bin'), join(cia_dir, 'code-%s.bin' % original_language))
		ctr += 1
	
	if VERBOSE >= 1: print('Saved %d files.' % ctr)

def createReleasePatches(cia_dir, patches_filename, original_language = 'JA'):
	try:
		# create banner patch
		if exists(join(cia_dir, 'ExtractedBanner')):
			# rebuild banner
			if VERBOSE >= 1: print('Rebuilding banner...')
			rename(join(cia_dir, 'ExtractedBanner', 'banner.cgfx'), join(cia_dir, 'ExtractedBanner', 'banner0.bcmdl'))
			run('"%s" -c -t banner -f banner.bin --banner-dir ExtractedBanner' % TOOL_PATH, cwd=cia_dir)
			rename(join(cia_dir, 'ExtractedBanner', 'banner0.bcmdl'), join(cia_dir, 'ExtractedBanner', 'banner.cgfx'))
			# copy to exeFS (if you want to create a CIA file)
			if exists(join(cia_dir, 'ExtractedExeFS')):
				if VERBOSE >= 1: print('Copy banner to ExtractedExeFS')
				copyfile(join(cia_dir, 'banner.bin'), join(cia_dir, 'ExtractedExeFS', 'banner.bin'))
			# create patch
			if VERBOSE >= 1: print('Creating banner patch...')
			run('xdelta -f -s banner-%s.bin banner.bin banner.xdelta' % original_language, cwd=cia_dir)
			if VERBOSE >= 1: print()
		
		# create code patch
		if exists(join(cia_dir, 'ExtractedExeFS', 'code.bin')):
			# save original code if not existent
			if not exists(join(cia_dir, 'code-%s.bin' % original_language)):
				if VERBOSE >= 1: print('Save original code to code-%s.bin' % original_language)
				copyfile(join(cia_dir, 'ExtractedExeFS', 'code.bin'), join(cia_dir, 'code-%s.bin' % original_language))
			# create patch
			if VERBOSE >= 1: print('Creating code patch...')
			run('xdelta -f -s code-%s.bin ExtractedExeFS\\code.bin code.xdelta' % original_language, cwd=cia_dir)
			if VERBOSE >= 1: print()
		
		# create romFS patch
		if exists(join(cia_dir, 'ExtractedRomFS')):
			# rebuild romFS
			if VERBOSE >= 1: print('Rebuilding RomFS...')
			run('"%s" -c -t romfs -f CustomRomFS.bin --romfs-dir ExtractedRomFS' % TOOL_PATH, cwd=cia_dir)
			# create patch
			if VERBOSE >= 1: print('Creating RomFS patch...')
			run('xdelta -f -s DecryptedRomFS.bin CustomRomFS.bin RomFS.xdelta', cwd=cia_dir)
			if VERBOSE >= 1: print()
		
		# archive patches
		directory = dirname(patches_filename)
		if directory and not exists(directory): makedirs(directory)
		with ZipFile(patches_filename, 'w') as zip:
			for patch in ['banner.xdelta', 'code.xdelta', 'RomFS.xdelta']:
				if VERBOSE >= 1: print('Add %s to patches' % patch)
				file = join(cia_dir, patch)
				if exists(file):
					zip.write(file, arcname=patch)
		if VERBOSE >= 1:
			print()
			print('Saved all patches to %s' % patches_filename)
		
		return True
		
	except Exception as e:
		print('Error:', str(e))
		return False
