""" Author: Dominik Beese
>>> File Replacer
<<<
"""

from os import listdir, walk
from os.path import isdir, basename, join
from shutil import copyfile

def replaceFiles(source_files, destination_dir):
	for file in [join(dp, f) for dp, dn, fn in walk(destination_dir) for f in fn]:
		for source_file in source_files:
			if basename(file) == basename(source_file):
				print(basename(source_file), '->', file)
				copyfile(source_file, file)

if __name__ == '__main__':
	import sys
	if len(sys.argv) != 3:
		print('Usage:')
		print('  * py -3 FileReplacer.py <FileToCopy> <DirectoryToCopyTo>')
		print('  * py -3 FileReplacer.py <FolderToCopyFrom> <DirectoryToCopyTo>')
	else:
		if isdir(sys.argv[1]):
			source_files = [join(sys.argv[1], f) for f in listdir(sys.argv[1])]
		else: source_files = [sys.argv[1]]
		destination_dir = sys.argv[2]
		replaceFiles(source_files, destination_dir)
