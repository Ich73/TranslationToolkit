""" Author: Dominik Beese
>>> Send to Citra
<<<
"""

from os import makedirs, walk, sep
from os.path import join, normpath, basename, exists, dirname
from shutil import copyfile
from TranslationPatcher import hash

# 0: nothing, 1: minimal, 2: all
VERBOSE = 1

def sendFiles(source_dir, title_id, citra_dir, force_override = False):
	# set citra mod path
	mod_path = join(citra_dir, 'load', 'mods', title_id.upper())
	
	# for exefs and romfs
	ctr = dict()
	for src_fs, name_fs, dest_fs in [('ExtractedExeFS', 'ExeFS', 'exefs'), ('ExtractedRomFS', 'RomFS', 'romfs')]:
		PATH = dest_fs
		
		# for all source files
		for src_filename in [join(dp, f) for dp, _, fn in walk(join(source_dir, src_fs)) for f in fn]:
			# calculate path and filename
			simplename = basename(src_filename)
			path = normpath(src_filename).split(sep)[2:-1]
			dest_filename = join(mod_path, dest_fs, *path, simplename)
			msg_prefix = ' * %s:' % simplename
			
			# print path if different
			if VERBOSE >= 1 and PATH != path:
				if VERBOSE >= 1: print('/'.join(path) if path else name_fs)
				PATH = path
			
			# check if file already exists
			if exists(dest_filename):
				# compare patches
				if not force_override and hash(src_filename) == hash(dest_filename):
					# equal -> keep old file
					if VERBOSE >= 2: print(msg_prefix, 'keep')
					ctr['keep'] = ctr.get('keep', 0) + 1
					continue
				else:
					# new -> update file
					if VERBOSE >= 1: print(msg_prefix, 'update')
					ctr['update'] = ctr.get('update', 0) + 1
			else:
				# add new file
				if VERBOSE >= 1: print(msg_prefix, 'add')
				ctr['add'] = ctr.get('add', 0) + 1
			
			# copy file
			makedirs(dirname(dest_filename), exist_ok=True)
			copyfile(src_filename, dest_filename)
	
	# summary
	print()
	if VERBOSE >= 1 and ctr.get('add', 0) > 0 or VERBOSE >= 2: print('Added %d files.' % ctr.get('add', 0))
	if VERBOSE >= 1: print('Updated %d files.' % ctr.get('update', 0))
	if VERBOSE >= 2: print('Kept %d files.' % ctr.get('keep', 0))
