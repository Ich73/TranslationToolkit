""" Author: Dominik Beese
>>> Save Changer
<<<
"""

from os import walk, remove
from os.path import join, splitext, basename
from zipfile import ZipFile
from BinJEditor.JTools import parseDecodingTable, createTabJ, invertDict
from tempfile import gettempdir as tempdir

# 0: nothing, 1: all
VERBOSE = 1

# save file types
SAVE_FILE_TYPES = ['.savJ', '.savE']

def updateTableInSave(save_dir, table_file):
	try:
		# parse decoding table
		table = parseDecodingTable(table_file)
		specialj = createTabJ(table['special'], hexValue = False)
		decode = table['decode']
		encode = table['encode']
		decode = {k: decode[k] for k in set(decode) - set(invertDict(encode))} # remove every char that is in encode as well
		decodej = createTabJ(decode, hexValue = True)
		encodej = createTabJ(encode, hexValue = True)
	except Exception as e:
		print('Error:', str(e))
		return
	
	# iterate over all save files
	ctr = 0
	for save_file in [join(dp, f) for dp, _, fn in walk(save_dir) for f in fn if splitext(f)[1] in SAVE_FILE_TYPES]:
		if VERBOSE >= 1: print(save_file)
		
		# read save file
		with ZipFile(save_file, 'r') as zip:
			save_files = sorted({info.filename for info in zip.infolist()} - {'special.tabJ', 'decode.tabJ', 'encode.tabJ'})
			save_data = [zip.read(file) for file in save_files]
		
		# save output file
		special_filename = join(tempdir(), 'special.tabJ')
		with open(special_filename, 'w', encoding = 'UTF-8') as file: file.write(specialj)
		decode_filename = join(tempdir(), 'decode.tabJ')
		with open(decode_filename, 'w', encoding = 'ASCII') as file: file.write(decodej)
		encode_filename = join(tempdir(), 'encode.tabJ')
		with open(encode_filename, 'w', encoding = 'ASCII') as file: file.write(encodej)
		save_filenames = [join(tempdir(), file) for file in save_files]
		for i, save_filename in enumerate(save_filenames):
			with open(save_filename, 'wb') as file: file.write(save_data[i])
		with ZipFile(save_file, 'w') as file:
			file.write(special_filename, arcname=basename(special_filename))
			file.write(decode_filename, arcname=basename(decode_filename))
			file.write(encode_filename, arcname=basename(encode_filename))
			for save_filename in save_filenames:
				file.write(save_filename, arcname=basename(save_filename))
		ctr += 1
		
		# clear temporary files
		remove(special_filename)
		remove(decode_filename)
		remove(encode_filename)
		for save_filename in save_filenames:
			remove(save_filename)
	
	print()
	if VERBOSE >= 1: print('Updated %d files.' % ctr)
