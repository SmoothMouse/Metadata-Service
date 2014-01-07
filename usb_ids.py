# coding: utf-8
import os, codecs, tempfile, shutil, sqlite3, urllib, logging
from subprocess import check_output

import settings

def is_hex(str):
	"""Check if str is a valid hexadecimal number"""
	for digit in str:
		if not digit.isdigit() and not digit in 'abcdef':
			return False
	return True

def download_usb_ids_list(url, to_path):
	"""Download a gzip archive with usb.ids, unpack and return the path to it"""
	temp_dir_path = tempfile.mkdtemp()
	archive_path = os.path.join(temp_dir_path, 'usb.ids.gz')
	list_path_temp = os.path.join(temp_dir_path, 'usb.ids')
	list_path_final = os.path.join(to_path, 'usb.ids')
	
	# Download
	urllib.urlretrieve(url, archive_path)
	
	# Unpack
	check_output(['gunzip', archive_path])
	
	if not os.path.isfile(list_path_temp):
		raise Exception('Error unpacking the archive')
		
	shutil.copy(list_path_temp, list_path_final)
	
	# Clean-up
	shutil.rmtree(temp_dir_path)
	
	return list_path_final
	
def parse_usb_ids_list(usb_ids_list_path):
	"""Read usb.ids line by line, return iterator"""
	current_vendor_id = 0
	current_vendor_name = ''
	
	with codecs.open(usb_ids_list_path, encoding='utf-8', errors='ignore') as file_handle:
		for line in file_handle:	
			# Skip comments
			if line[0] == '#':
				continue
		
			# Skip empty lines
			line = line.rstrip(os.linesep)
			if len(line) == 0:
				continue
			
			# Parse vendor
			if is_hex(line[0:4]):
				current_vendor_id = int(line[0:4], 16)
				current_vendor_name = line[6:].strip()
			
			# Parse device
			elif line[0] == '\t' and is_hex(line[1:5]):
				current_product_id = int(line[1:5], 16)
				current_product_name = line[7:].strip()
			
				yield current_vendor_id, current_vendor_name, current_product_id, current_product_name

def update_database(database, data):
	"""Drop existing data from the database, insert new"""
	try:
		handle = sqlite3.connect(database)
		cursor = handle.cursor()
		
		cursor.execute('DROP TABLE IF EXISTS usb_ids')
		cursor.execute('CREATE TABLE usb_ids (vendor_id integer, vendor_name text, product_id integer, product_name text)')
		cursor.executemany('INSERT INTO usb_ids VALUES (?,?,?,?)', data)	
		handle.commit()
	
	except sqlite3.Error, e:
		logging.error('Database error: %s' % str(e))
	   
	finally:
		if 'handle' in locals() and handle:
			handle.close()

def update_usb_ids(url, database):
	"""Download a gzip archive with usb.ids from `url`, process it and update the `database`"""
	temp_dir_path = tempfile.mkdtemp()
	
	try:
		usb_ids_list = download_usb_ids_list('http://www.linux-usb.org/usb.ids.gz', temp_dir_path)
	except IOError, e:
		logging.error('Failed to download usb.ids: %s' % str(e))
		return
		
	usb_ids_iter = parse_usb_ids_list(usb_ids_list)
	update_database(database, usb_ids_iter)
	shutil.rmtree(temp_dir_path)