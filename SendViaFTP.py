""" Author: Dominik Beese
>>> Send via FTP
<<<
"""

from ftplib import FTP
from os import walk, listdir, sep
from os.path import normpath, basename, join, getmtime
from time import strptime, localtime

# 0: nothing, 1: minimal, 2: all
VERBOSE = 1

def createAndEnterPath(ftp, path):
	for directory in path:
		if directory not in [dir for dir, _ in ftp.mlsd()]:
			if VERBOSE >= 2: print('Create directory \'%s\'' % directory)
			ftp.mkd(directory)
		ftp.cwd(directory)

def sendFiles(source_dir, title_id, ip, port, user, passwd, force_override = False):
	try:
		with FTP(timeout = 5) as ftp:
			# connect and login
			if VERBOSE >= 1: print('Connect to \'%s:%d\'' % (ip, port))
			tmp = ftp.connect(host = ip, port = port)
			if VERBOSE >= 1: print('>>', tmp)
			if user:
				if VERBOSE >= 1: print('Login as \'%s\'' % user)
				tmp = ftp.login(user = user, passwd = passwd)
				if VERBOSE >= 1: print('>>', tmp)
			print()
			
			# send files
			ctr = sendExeFiles(ftp, source_dir, title_id, force_override)
			ctr2 = sendRomFiles(ftp, source_dir, title_id, force_override)
			
			# quit connection
			print()
			print('Disconnect')
			print('>>', ftp.quit())
			
			# summary
			for k, v in ctr2.items(): ctr[k] = ctr.get(k, 0) + v
			print()
			if VERBOSE >= 1: print('Sent %d files.' % ctr['send'])
			if VERBOSE >= 2: print('Kept %d files.' % ctr['keep'])
			
	except Exception as e:
		print('Error:', str(e))

def sendExeFiles(ftp, source_dir, title_id, force_override = False):
	# enter basepath
	ftp.cwd('/')
	basepath = ('luma', 'titles', title_id)
	createAndEnterPath(ftp, basepath)
	
	# for all source files
	ctr = dict()
	if VERBOSE >= 1: print('ExeFS')
	for filename in listdir(join(source_dir, 'ExtractedExeFS')):
		src_filename = join(source_dir, 'ExtractedExeFS', filename)
		dest_filename = filename
		msg_prefix = ' * %s:' % dest_filename
		
		# compare file timestamps
		if not force_override:
			mlsd = ftp.mlsd('.')
			dest_timestamp = next((strptime(info['modify'], '%Y%m%d%H%M%S') for file, info in mlsd if file == dest_filename), None)
			if dest_timestamp is not None:
				src_timestamp = localtime(getmtime(src_filename))
				if dest_timestamp >= src_timestamp:
					if VERBOSE >= 2: print(msg_prefix, 'keep')
					ctr['keep'] = ctr.get('keep', 0) + 1
					continue
		
		# send file
		with open(src_filename, 'rb') as file:
			if VERBOSE >= 1: print(msg_prefix, 'send')
			ctr['send'] = ctr.get('send', 0) + 1
			ftp.storbinary('STOR %s' % dest_filename, file)
	
	return ctr

def sendRomFiles(ftp, source_dir, title_id, force_override = False):
	# enter basepath
	ftp.cwd('/')
	basepath = ('luma', 'titles', title_id, 'romfs')
	createAndEnterPath(ftp, basepath)
	
	# store mlsd info and current path
	MLSD = dict()
	PATH = basepath
	
	# for all source files
	ctr = dict()
	for src_filename in [join(dp, f) for dp, _, fn in walk(join(source_dir, 'ExtractedRomFS')) for f in fn]:
		# calculate path and filename
		dest_path, dest_filename = (tuple(normpath(src_filename).split(sep)[2:-1]), basename(src_filename))
		msg_prefix = ' * %s:' % dest_filename
		
		# enter path if different
		if PATH != basepath + dest_path:
			if VERBOSE >= 1: print('/'.join(dest_path))
			ftp.cwd('/' + '/'.join(basepath))
			createAndEnterPath(ftp, dest_path)
			PATH = basepath + dest_path
		
		# compare file timestamps
		if not force_override:
			if dest_path not in MLSD: MLSD[dest_path] = ftp.mlsd('.')
			dest_timestamp = next((strptime(info['modify'], '%Y%m%d%H%M%S') for file, info in MLSD[dest_path] if file == dest_filename), None)
			if dest_timestamp is not None:
				src_timestamp = localtime(getmtime(src_filename))
				if dest_timestamp >= src_timestamp:
					if VERBOSE >= 2: print(msg_prefix, 'keep')
					ctr['keep'] = ctr.get('keep', 0) + 1
					continue
		
		# send file
		with open(src_filename, 'rb') as file:
			if VERBOSE >= 1: print(msg_prefix, 'send')
			ctr['send'] = ctr.get('send', 0) + 1
			ftp.storbinary('STOR %s' % dest_filename, file)
	
	return ctr
