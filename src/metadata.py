# coding: utf-8
import os, sys, tempfile, shutil, re, sqlite3, urlparse, logging
from subprocess import check_output
from xml.etree.ElementTree import ElementTree, Element

import requests
from bottle import template

import settings

def get_ms_device_metadata_filename(vid, pid):
	"""
	Returns a filename of device metadata archive on the Microsoft server
	Example: da7428fa-7dd7-4d22-af80-afa4c260a773.devicemetadata-ms
	
	If Microsoft does not provide metadata, return None.
	"""
	
	# Send request
	service_url = 'http://dmd.metaservices.microsoft.com/dms/metadata.svc'
	payload = template(os.path.join('templates', 'ms_request_body.tpl'), vid=format(vid, 'x').zfill(4), pid=format(pid, 'x').zfill(4)).encode('UTF-16LE')
	headers = {
		'Content-Type': 'text/xml; charset="UTF-16LE"', 
		'Content-Length': len(payload), 
		'User-Agent': 'MICROSOFT_DEVICE_METADATA_RETRIEVAL_CLIENT', 
		'SOAPAction': 'http://schemas.microsoft.com/windowsmetadata/services/2007/09/18/dms/DeviceMetadataService/GetDeviceMetadata', 
		'Connection': 'Keep-Alive'
	}
	
	request = requests.post(service_url, headers=headers, data=payload)
	if request.status_code != 200 or not request.text:
		raise Exception('Device metadata filename request failed')
	
	# Extract filename using a regular expression
	try:
		filename = re.search('<fn>(.*\.devicemetadata-ms)</fn>', request.text).group(1)
	except Exception:
		filename = None
	
	return filename
	
def prepare_ms_icon(src, dst, min_width=48):
	"""Extract the desired icon from $src and save it as $dst in PNG format."""
	contents = check_output(['identify', '-format', '%p @ %w @ %h @ %z\n', src]).strip().split(os.linesep)
	
	def icon_filter(item):
		props = item.split(' @ ')

		if len(props) is not 4:
			return None
		
		props = [int(prop) for prop in props]
		
		if props[1] < min_width:
			return None # ignore too small images
		
		if props[3] < 8:
			return None # ignore images with color depth of less than 8 bits	
		
		return props

	# Move the best option to the beginning of the list
	contents = [icon_filter(i) for i in contents]
	contents = [i for i in contents if i]
	contents.sort(key=lambda x: x[3], reverse=True) # sort by color depth, starting from highest
	contents.sort(key=lambda x: x[1], reverse=True) # sort by dimension, starting from highest
		
	# Convert
	temp_dir_path = tempfile.mkdtemp()	
	check_output(['convert', src, os.path.join(temp_dir_path, 'icon.png')])
	selected_icon = os.path.join(temp_dir_path, 'icon-%i.png' % contents[0][0])
	if not os.path.isfile(selected_icon):
		raise Exception('Error converting icon')
		
	# Centering
	canvas_size = '%ix%i' % (contents[0][1], contents[0][2])
	check_output(['convert', selected_icon, 
		'-trim', 
		'-background', 'none', 
		'-gravity', 'center', 
		'-extent', canvas_size, 
	dst])
	
	# Clean up
	shutil.rmtree(temp_dir_path)
	return True

def get_ms_device_metadata(vid, pid):
	"""
	Return device metadata from metaservices.microsoft.com
	If not found, return an empty dictionary. In case of an error, throw an exception.
	"""
	result = {}
	
	# Get the name of cab file with metadata to download from metaservices.microsoft.com
	filename = get_ms_device_metadata_filename(vid, pid)
	
	if not filename:
		return result
	
	# Form the URL	
	url = 'http://download.dmd.metaservices.microsoft.com/dp/winqual/%(filename)s' % {'filename': filename}
	# DEBUG:url = 'http://localhost/~Dae/da7428fa-7dd7-4d22-af80-afa4c260a773.devicemetadata-ms'
	
	# Create a temporary directory
	temp_dir_path = tempfile.mkdtemp()
	
	# Download
	request = requests.get(url)
	if request.status_code != 200 or not request.content:
		raise Exception('Device metadata download failed')
	
	archive_path = os.path.join(temp_dir_path, 'Archive.cab')
	with open(archive_path, 'wb') as archive_file:
		archive_file.write(request.content)
	
	# Unpack
	check_output(['cabextract', '-q', '--directory', temp_dir_path, archive_path])
	device_info_xml = os.path.join(temp_dir_path, 'DeviceInformation', 'DeviceInfo.xml')
	if not os.path.isfile(device_info_xml):
		raise Exception('Microsoft-provided metadata is invalid')
	
	# Parse DeviceInfo.xml
	namespaces = {'DeviceInfo': 'http://schemas.microsoft.com/windows/DeviceMetadata/DeviceInfo/2007/11/'}
	# DEBUG:device_info_xml = os.path.join(settings.BASE_DIR, 'docs', 'samples', 'DeviceInfo.xml')
	tree = ElementTree()
	root = tree.parse(device_info_xml)
	
	def find_in_root(root, query, namespaces):
		try:
			return root.find(query, namespaces=namespaces).text.strip()
		except AttributeError:
			sys.exc_clear()
	
	# - icon_path
	icon_filename = find_in_root(root, 'DeviceInfo:DeviceIconFile', namespaces=namespaces)
	icon_path = os.path.join(temp_dir_path, 'DeviceInformation', icon_filename)
	if icon_filename and os.path.isfile(icon_path):
		icon_path_temp = tempfile.mkstemp(prefix='icon', suffix='.ico')[1]
		shutil.copy(icon_path, icon_path_temp)
		result['icon_path'] = icon_path_temp
	
	# - vendor_name
	vendor_name = find_in_root(root, 'DeviceInfo:Manufacturer', namespaces=namespaces)
	if vendor_name:
		result['vendor_name'] = vendor_name
	
	# - product_name
	product_name = find_in_root(root, 'DeviceInfo:ModelName', namespaces=namespaces)
	if product_name:
		result['product_name'] = product_name
		
	# Clean up
	shutil.rmtree(temp_dir_path)
	
	return result

def get_linux_device_metadata(vid, pid):
	"""
	Return device metadata from the local SQLite3 database with data from linux-usb.org
	If not found, return an empty dictionary. In case of an error, throw an exception.
	"""
	try:
		handle = sqlite3.connect(settings.USB_IDS_DB_PATH)
		handle.row_factory = sqlite3.Row
		cursor = handle.cursor()
		
		cursor.execute('SELECT vendor_name, product_name FROM usb_ids WHERE vendor_id=? AND product_id=?', (vid, pid))	
		row = cursor.fetchone()
		
		if row:
			return dict(zip(row.keys(), row))
		else:
			return {}
			
	except sqlite3.Error, e:
		logging.error('Database error %s:' % e.args[0])
	
	finally:
		if 'handle' in locals() and handle:
			handle.close()

def get_sm_device_metadata(vid, pid):
	"""
	Query Linux metadata and local icon cache, if not found query Microsoft. 
	This callable should catch all exceptions from lower levels and log them.
	If not found, return an empty dictionary.
	"""
	
	device_metadata = {}
	
	# First try to get vendor_name, product_name from Linux
	try:
		device_metadata.update(get_linux_device_metadata(vid, pid))
	except Exception, e:
		logging.error('Failed to fetch Linux metadata for %i:%i: %s' % (vid, pid, str(e)))
		sys.exc_clear()
		
	if not device_metadata:
		logging.info('No Linux metadata available for %i:%i' % (vid, pid))
		
	# Also try to get icon from our local cache
	icon_filename = '%i_%i.png' % (vid, pid)
	icon_path = os.path.join(settings.ICONS_DIR, icon_filename)
	if os.path.isfile(icon_path): # cached?
		device_metadata['icon'] = urlparse.urljoin(settings.ICONS_URL, icon_filename)
	
	# We need to bother Microsoft if...
	if not device_metadata.get('vendor_name') \
		or not device_metadata.get('product_name') \
		or not device_metadata.get('icon'):
		
		# Calling Microsoft
		try:
			ms_metadata = get_ms_device_metadata(vid, pid)
			
			if not ms_metadata:
				logging.info('No Microsoft metadata available for %i:%i' % (vid, pid))
			
			if not device_metadata.get('vendor_name') and ms_metadata.get('vendor_name'):
				device_metadata['vendor_name'] = ms_metadata['vendor_name']
			
			if not device_metadata.get('product_name') and ms_metadata.get('product_name'):
				device_metadata['product_name'] = ms_metadata['product_name']
			
			if ms_metadata.get('icon_path'):
				if not device_metadata.get('icon'):
		 			try:
		 				prepare_ms_icon(ms_metadata['icon_path'], icon_path)
						device_metadata['icon'] = urlparse.urljoin(settings.ICONS_URL, icon_filename)
		 			except Exception, e:
		 				logging.error('Error processing the icon: %s' % str(e))
			
				# Don't forget to clean-up
				os.remove(ms_metadata['icon_path'])
		except Exception, e:
			logging.error('Failed to fetch Microsoft metadata for %i:%i: %s' % (vid, pid, str(e)))
			sys.exc_clear()
	
	return device_metadata