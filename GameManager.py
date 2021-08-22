""" Author: Dominik Beese
>>> Game Manager
<<<
"""

from os import makedirs, listdir, remove, rename
from os.path import join, isfile, isdir, splitext, abspath
from subprocess import run, PIPE, STDOUT


#############
## Extract ##
#############

def extractGame(game_file, game_dir, dstool, ctrtool):
	""" Extracts the given [game_file] to the given [game_dir]. Supports .cia and .3ds files. """
	try:
		mode = splitext(game_file)[1][1:].lower()
		
		# step 1: cia / 3ds -> DecryptedPartitionX.bin
		print('Extracting Step 1/7')
		makedirs(game_dir, exist_ok=True)
		if mode == 'cia':
			proc = run('"%s" -x --content="%s" "%s"' % (abspath(ctrtool), abspath(join(game_dir, 'Decrypted')), abspath(game_file)), shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
			partitions = list()
			for decrypted_file in [f for f in listdir(game_dir) if f.startswith('Decrypted')]:
				id = int(decrypted_file[10:14])
				rename(join(game_dir, decrypted_file), join(game_dir, 'DecryptedPartition%d.bin' % id))
				partitions.append(id)
		elif mode == '3ds':
			proc = run('"%s" -xtf 3ds "%s" --header HeaderNCCH.bin -0 DecryptedPartition0.bin -1 DecryptedPartition1.bin -2 DecryptedPartition2.bin -6 DecryptedPartition6.bin -7 DecryptedPartition7.bin' % (abspath(dstool), abspath(game_file)), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
			partitions = [int(f[18]) for f in listdir(game_dir) if f.startswith('DecryptedPartition')]
		
		# step 2: DecryptedPartitionX.bin -> HeaderNCCHX.bin, DecryptedXXX.bin, ...
		print('Extracting Step 2/7')
		if 0 in partitions:
			print(' ', 'Partition0')
			proc = run('"%s" -xtf cxi DecryptedPartition0.bin --header HeaderNCCH0.bin --exh DecryptedExHeader.bin --exefs DecryptedExeFS.bin --romfs DecryptedRomFS.bin --logo LogoLZ.bin --plain PlainRGN.bin' % abspath(dstool), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		if 1 in partitions:
			print(' ', 'Partition1')
			proc = run('"%s" -xtf cfa DecryptedPartition1.bin --header HeaderNCCH1.bin --romfs DecryptedManual.bin' % abspath(dstool), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		if 2 in partitions:
			print(' ', 'Partition2')
			proc = run('"%s" -xtf cfa DecryptedPartition2.bin --header HeaderNCCH2.bin --romfs DecryptedDownloadPlay.bin' % abspath(dstool), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		for id in partitions: remove(join(game_dir, 'DecryptedPartition%d.bin' % id))
		
		# step 3: DecryptedExeFS.bin -> ExtractedExeFS
		print('Extracting Step 3/7')
		if isfile(join(game_dir, 'DecryptedExeFS.bin')):
			proc = run('"%s" -xtf exefs DecryptedExeFS.bin --exefs-dir ExtractedExeFS --header HeaderExeFS.bin' % abspath(dstool), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
			exefs_dir = join(game_dir, 'ExtractedExeFS')
			if isfile(join(exefs_dir, 'banner.bnr')): rename(join(exefs_dir, 'banner.bnr'), join(exefs_dir, 'banner.bin'))
			if isfile(join(exefs_dir, 'icon.icn')):   rename(join(exefs_dir, 'icon.icn'),   join(exefs_dir, 'icon.bin'))
		
		# step 4: banner.bin -> ExtractedBanner
		print('Extracting Step 4/7')
		if isfile(join(game_dir, 'ExtractedExeFS', 'banner.bin')):
			proc = run('"%s" -xtf banner "%s" --banner-dir ExtractedBanner' % (abspath(dstool), abspath(join(game_dir, 'ExtractedExeFS', 'banner.bin'))), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
			banner_dir = join(game_dir, 'ExtractedBanner')
			if isfile(join(banner_dir, 'banner0.bcmdl')): rename(join(banner_dir, 'banner0.bcmdl'), join(banner_dir, 'banner.cgfx'))
		
		# step 5: DecryptedRomFS.bin -> ExtractedRomFS
		print('Extracting Step 5/7')
		if isfile(join(game_dir, 'DecryptedRomFS.bin')):
			proc = run('"%s" -xtf romfs DecryptedRomFS.bin --romfs-dir ExtractedRomFS' % abspath(dstool), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		
		# step 6: DecryptedManual.bin -> ExtractedManual
		print('Extracting Step 6/7')
		if isfile(join(game_dir, 'DecryptedManual.bin')):
			proc = run('"%s" -xtf romfs DecryptedManual.bin --romfs-dir ExtractedManual' % abspath(dstool), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: print('Warning: Extracting DecryptedManual.bin Failed')
		
		# step 7: DecryptedDownloadPlay.bin -> ExtractedDownloadPlay
		print('Extracting Step 7/7')
		if isfile(join(game_dir, 'DecryptedDownloadPlay.bin')):
			proc = run('"%s" -xtf romfs DecryptedDownloadPlay.bin --romfs-dir ExtractedDownloadPlay' % abspath(dstool), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: print('Warning: Extracting DecryptedDownloadPlay.bin Failed')
		
		# success
		print('Extracted to', game_dir)
		print()
		return True
		
	except Exception as e:
		print(str(e).strip())
		print('ERROR: Extracting Failed')
		print()
		return False


#############
## Rebuild ##
#############

def rebuildGame(game_dir, game_file, version, dstool, makerom):
	""" Rebuilds the given [game_dir] to the given [game_file]. Supports .cia and .3ds files.
		Sets the version of the cia file to [version].
	"""
	try:
		def getFile(possibilities): return next((f for f in possibilities if isfile(join(game_dir, f))), None)
		mode = splitext(game_file)[1][1:].lower()
		
		# step 1: ExtractedRomFS -> CustomRomFS.bin
		print('Rebuilding Step 1/6')
		if isdir(join(game_dir, 'ExtractedRomFS')):
			proc = run('"%s" -ctf romfs CustomRomFS.bin --romfs-dir ExtractedRomFS' % abspath(dstool), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		
		# step 2: ExtractedManual -> CustomManual.bin
		print('Rebuilding Step 2/6')
		if isdir(join(game_dir, 'ExtractedManual')):
			proc = run('"%s" -ctf romfs CustomManual.bin --romfs-dir ExtractedManual' % abspath(dstool), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		
		# step 3: ExtractedDownloadPlay -> CustomDownloadPlay.bin
		print('Rebuilding Step 3/6')
		if isdir(join(game_dir, 'ExtractedDownloadPlay')):
			proc = run('"%s" -ctf romfs CustomDownloadPlay.bin --romfs-dir ExtractedDownloadPlay' % abspath(dstool), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		
		# step 4: ExtractedExeFS -> CustomExeFS.bin
		print('Rebuilding Step 4/6')
		headerExe = getFile(['CustomHeaderExeFS.bin',  'HeaderExeFS.bin'])
		exefs_dir = join(game_dir, 'ExtractedExeFS')
		if isdir(exefs_dir) and headerExe:
			if isfile(join(exefs_dir, 'banner.bin')): rename(join(exefs_dir, 'banner.bin'), join(exefs_dir, 'banner.bnr'))
			if isfile(join(exefs_dir, 'icon.bin')):   rename(join(exefs_dir, 'icon.bin'),   join(exefs_dir, 'icon.icn'))
			proc = run('"%s" -ctf exefs CustomExeFS.bin --exefs-dir ExtractedExeFS --header %s' % (abspath(dstool), headerExe), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
			if isfile(join(exefs_dir, 'banner.bnr')): rename(join(exefs_dir, 'banner.bnr'), join(exefs_dir, 'banner.bin'))
			if isfile(join(exefs_dir, 'icon.icn')):   rename(join(exefs_dir, 'icon.icn'),   join(exefs_dir, 'icon.bin'))
		
		# step 5: CustomHeaderNCCHX.bin, CustomDecryptedXXX.bin, ... -> CustomPartitionX.bin
		print('Rebuilding Step 5/6')
		headerN0 = getFile(['CustomHeaderNCCH0.bin',  'HeaderNCCH0.bin'])
		headerN1 = getFile(['CustomHeaderNCCH1.bin',  'HeaderNCCH1.bin'])
		headerN2 = getFile(['CustomHeaderNCCH2.bin',  'HeaderNCCH2.bin'])
		exHeader = getFile(['CustomExHeader.bin',     'DecryptedExHeader.bin'])
		exeFS    = getFile(['CustomExeFS.bin',        'DecryptedExeFS.bin'])
		romFS    = getFile(['CustomRomFS.bin',        'DecryptedRomFS.bin'])
		manual   = getFile(['CustomManual.bin',       'DecryptedManual.bin'])
		dlplay   = getFile(['CustomDownloadPlay.bin', 'DecryptedDownloadPlay.bin'])
		logoLZ   = getFile(['CustomLogoLZ.bin',       'LogoLZ.bin'])
		plainRGN = getFile(['CustomPlainRGN.bin',     'PlainRGN.bin'])
		if all([headerN0, exHeader, exeFS, romFS]):
			print(' ', 'Partition0')
			arguments = ['--header %s' % headerN0, '--exh %s' % exHeader, '--exefs %s' % exeFS, '--romfs %s' % romFS]
			if logoLZ:   arguments.append('--logo %s' % logoLZ)
			if plainRGN: arguments.append('--plain %s' % plainRGN)
			proc = run('"%s" -ctf cxi CustomPartition0.bin %s' % (abspath(dstool), ' '.join(arguments)), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		if all([headerN1, manual]):
			print(' ', 'Partition1')
			proc = run('"%s" -ctf cfa CustomPartition1.bin --header %s --romfs %s' % (abspath(dstool), headerN1, manual), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		if all([headerN2, dlplay]):
			print(' ', 'Partition2')
			proc = run('"%s" -ctf cfa CustomPartition2.bin --header %s --romfs %s' % (abspath(dstool), headerN2, dlplay), cwd=game_dir, shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		
		# step 6: CustomPartitionX.bin -> cia / 3ds
		print('Rebuilding Step 6/6')
		if mode == 'cia':
			def int2version(v): return 'v%d.%d.%d' % (v // 2**10, v % 2**10 // 2**4, v % 2**10 % 2**4)
			print(' ', 'CIA', int2version(version))
			contents = ['-content "%s":%s:%s' % (abspath(join(game_dir, f)), f[15], f[15]) for f in listdir(game_dir) if f.startswith('CustomPartition')]
			proc = run('"%s" -f cia %s -ver %d -o "%s" -target p -ignoresign' % (abspath(makerom), ' '.join(contents), version, abspath(game_file)), shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		elif mode == '3ds':
			contents = ['--header "%s"' % abspath(join(game_dir, 'HeaderNCCH.bin'))]
			contents += ['-%s "%s"' % (f[15], abspath(join(game_dir, f))) for f in listdir(game_dir) if f.startswith('CustomPartition')]
			proc = run('"%s" -ctf 3ds "%s" --header HeaderNCCH.bin %s' % (abspath(dstool), abspath(game_file), ' '.join(contents)), shell=True, stdout=PIPE, stderr=STDOUT)
			if proc.returncode != 0: raise Exception(proc.stdout.decode(errors='replace'))
		for file in [f for f in listdir(game_dir) if f.startswith('CustomPartition')]: remove(join(game_dir, file))
		
		# success
		print('Rebuilt', game_file)
		print()
		return True
		
	except Exception as e:
		print(str(e).strip())
		print('ERROR: Rebuild Failed')
		print()
		return False
