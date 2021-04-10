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
			
			# for exefs and romfs
			ctr = dict()
			for src_fs, name_fs, dest_fs in [('ExtractedExeFS', 'ExeFS', None), ('ExtractedRomFS', 'RomFS', 'romfs')]:
				
				# enter basepath
				ftp.cwd('/')
				basepath = ('luma', 'titles', title_id.lower())
				if dest_fs: basepath += (dest_fs,)
				createAndEnterPath(ftp, basepath)
				
				# store mlsd info and current path
				MLSD = dict()
				PATH = dest_fs
				
				# for all source files
				for src_filename in [join(dp, f) for dp, _, fn in walk(join(source_dir, src_fs)) for f in fn]:
					# calculate path and filename
					dest_path, dest_filename = (tuple(normpath(src_filename).split(sep)[2:-1]), basename(src_filename))
					msg_prefix = ' * %s:' % dest_filename
					
					# enter path if different
					if PATH != basepath + dest_path:
						if VERBOSE >= 1: print('/'.join(dest_path) if dest_path else name_fs)
						ftp.cwd('/' + '/'.join(basepath))
						createAndEnterPath(ftp, dest_path)
						PATH = basepath + dest_path
					
					# compare file timestamps
					if not force_override:
						if dest_path not in MLSD: MLSD[dest_path] = list(ftp.mlsd('.'))
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
			
			# quit connection
			print()
			print('Disconnect')
			print('>>', ftp.quit())
			
			# summary
			print()
			if VERBOSE >= 1: print('Sent %d files.' % ctr.get('send', 0))
			if VERBOSE >= 2: print('Kept %d files.' % ctr.get('keep', 0))
			
	except Exception as e:
		print()
		print('Error:', str(e))
