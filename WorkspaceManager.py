""" Author: Dominik Beese
>>> Workspace Manager
<<<
"""

from os import makedirs
from os.path import join, normpath, sep, exists, isdir, dirname
from zipfile import ZipFile
from io import BytesIO
from urllib.request import urlopen
from tempfile import mkdtemp
from shutil import move, rmtree

# 0: nothing, 1: normal, 2: all
VERBOSE = 1

def downloadAndExtractPatches(download_url):
	try:
		# create temporary folder
		tempdir = mkdtemp()
		
		# download patches
		with urlopen(download_url) as url: data = url.read()
		
		# extract patches to temporary folder and move them
		ctr = 0
		folders = list()
		with ZipFile(BytesIO(data)) as zip:
			for file in zip.infolist():
				if file.is_dir(): continue
				filename = file.filename
				simplename = normpath(filename).split(sep)[1:]
				if not simplename: continue
				folder = simplename[0] if len(simplename) > 1 else None
				simplename = join(*simplename)
				directory = dirname(simplename)
				if VERBOSE >= 2: print(simplename)
				if VERBOSE == 1 and folder and folder not in folders:
					print(folder)
					folders.append(folder)
				zip.extract(filename, path=tempdir)
				if directory and not exists(directory): makedirs(directory)
				move(join(tempdir, filename), simplename)
				ctr += 1
		if VERBOSE >= 1:
			print()
			print('Downloaded %d files.' % ctr)
		
		# delete temporary folder
		rmtree(tempdir)
		return True
	
	except Exception as e:
		print('Error:', str(e))
		return False

if __name__ == '__main__':
	downloadAndExtractPatches()
