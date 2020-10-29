""" Author: Dominik Beese
>>> Workspace Manager
<<<
"""

from os import makedirs, listdir, walk, remove
from os.path import join, normpath, sep, exists, isdir, dirname, splitext, commonprefix, relpath
from zipfile import ZipFile
from io import BytesIO
from urllib.request import urlopen
from tempfile import mkdtemp
from shutil import move, rmtree, copyfile

from TranslationPatcher import hash, joinFolder, XDELTA_FOLDERS, PAT_FOLDERS, PARENT_FOLDERS

# 0: nothing, 1: normal, 2: all
VERBOSE = 1

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
