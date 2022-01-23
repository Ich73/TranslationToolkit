""" Author: Dominik Beese
>>> Tool Manager
<<<
"""

from os import remove, rename, chmod, stat
from os.path import join, exists, basename, dirname, splitext, abspath
from stat import S_IXUSR, S_IXGRP, S_IXOTH
from subprocess import run, PIPE, STDOUT
from zipfile import ZipFile
from tarfile import open as TarFile
from io import BytesIO
from urllib.request import urlopen
import re
import ssl

def checkTool(tool, target_version, args = ''):
	""" Checks the version of the given [tool] by calling it using
		the given [args] and returns true if the version matches
		the [target_version], false otherwise.
	"""
	proc = run(' '.join(('"%s"' % abspath(tool), args)), shell=True, stdout=PIPE, stderr=STDOUT, stdin=PIPE)
	output = proc.stdout.decode('UTF-8', errors='replace')
	match = re.search(r'\d+(\.\d+)+\w*', output)
	version = match.group() if match else None
	return version == target_version

def downloadTool(download_url, filename):
	""" Downloads an executable from the given [download_url],
		puts it in the current directory and renames it to [filename].
		If the download is a zip or tar file it uses the first executable found in the archive.
	"""
	# get type and download data
	print('Downloading', basename(download_url))
	print(' ', 'from', download_url)
	type = splitext(download_url)[1]
	
	try:
		with urlopen(download_url, context=ssl._create_unverified_context()) as url: data = url.read()
	except Exception as e:
		if exists(filename): # if tool exists with wrong version, keep it
			print('Error:', str(e))
			print('Keep old', basename(filename))
			return
		raise e # otherwise raise exception
	
	# zip archive
	if type == '.zip':
		with ZipFile(BytesIO(data)) as zip:
			file = next((file for file in zip.infolist() if splitext(file.filename)[1] == splitext(filename)[1]), None)
			if not file: raise Exception('The downloaded zip archive does not contain a suitable executable.')
			print('Extracting', basename(file.filename))
			if exists(filename): remove(filename)
			zip.extract(file, path=dirname(filename))
			rename(join(dirname(filename), basename(file.filename)), filename)
	
	# tar archive
	elif type in ['.tar', '.gz']:
		with TarFile(fileobj=BytesIO(data)) as tar:
			file = next((file for file in tar.getmembers() if splitext(file.name)[1] == splitext(filename)[1]), None)
			if not file: raise Exception('The downloaded tar archive does not contain a suitable executable.')
			print('Extracting', basename(file.name))
			if exists(filename): remove(filename)
			tar.extract(file, path=dirname(filename))
			rename(join(dirname(filename), basename(file.name)), filename)
	
	# executable
	elif type in ['.exe', '']:
		if exists(filename): remove(filename)
		with open(filename, 'wb') as file:
			file.write(data)
	
	# not supported
	else: raise Exception('The download link does not point towards a zip archive, tar archive or executable.')
	
	# make executable
	chmod(filename, stat(filename).st_mode | S_IXUSR | S_IXGRP | S_IXOTH)
	
	# success
	print('Downloaded', filename)
	print()
