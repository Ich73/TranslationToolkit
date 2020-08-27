""" Author: Dominik Beese
>>> Send via FTP
<<<
"""

from ftplib import FTP
from os import walk, sep
from os.path import normpath, basename, join, getmtime
from time import strptime, localtime

# 0: nothing, 1: minimal, 2: all
VERBOSE = 1

def sendRomFiles(source_dir, title_id, ip, port, user, passwd, force_override = False):
	
	def createAndEnterPath(ftp, path):
		for directory in path:
			if directory not in [dir for dir, _ in ftp.mlsd()]:
				if VERBOSE >= 2: print('Create directory \'%s\'' % directory)
				ftp.mkd(directory)
			ftp.cwd(directory)
	
	try:
		with FTP(timeout = 5) as ftp:
			# connect and login
			if VERBOSE >= 1: print('Connect to \'%s:%d\'' % (ip, port))
			if VERBOSE >= 1: print('>>', ftp.connect(host = ip, port = port))
			if VERBOSE >= 1: print('Login as \'%s\'' % user)
			if VERBOSE >= 1: print('>>', ftp.login(user = user, passwd = passwd))
			print()
			
			# enter basepath
			basepath = ('luma', 'titles', title_id, 'romfs')
			createAndEnterPath(ftp, basepath)
			
			# store mlsd info and current path
			MLSD = dict()
			PATH = basepath
			
			# for all source files
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
							continue
				
				# send file
				with open(src_filename, 'rb') as file:
					if VERBOSE >= 1: print(msg_prefix, 'send')
					ftp.storbinary('STOR %s' % dest_filename, file)
			
			# quit connection
			print()
			print('Disconnect')
			print('>>', ftp.quit())
	
	except Exception as e:
		print('Error:', str(e))
