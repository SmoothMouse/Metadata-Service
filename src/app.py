import os, urllib, cgi
import xml.etree.ElementTree as ET

from bottle import debug, route, static_file, request, response

import settings, metadata

@route('/devices/<vid:int>/<pid:int>/', method='GET')
def devices(vid, pid):
	# Preparation for outputting XML
	response.headers['Content-Type'] = 'application/xml'
	declaration = '<?xml version="1.0" encoding="UTF-8"?>'
	root = ET.Element('DeviceMetadata')
	tree = ET.ElementTree(root)
	
	# If XML output is cached, retrieve it
	cache_name = '%i_%i.xml' % (vid, pid)
	cache_path = os.path.join(settings.CACHE_DIR, cache_name)
	if os.path.isfile(cache_path):
		return static_file(cache_name, root=settings.CACHE_DIR)
	else: # no dice
		md = metadata.get_sm_device_metadata(vid, pid)
	
		if md:
			if md.get('icon'):
				child = ET.SubElement(root, 'Icon')
				child.text = md['icon']
	
			if md.get('vendor_name'):
				child = ET.SubElement(root, 'VendorName')
				child.text = md['vendor_name']

			if md.get('product_name'):
				child = ET.SubElement(root, 'ProductName')
				child.text = md['product_name']
			
			# Make sure to cache this
			tree.write(cache_path, encoding='utf-8', xml_declaration=True)
		else:
			response.status = 404 # Not Found
	
	return declaration + ET.tostring(root)
	
@route('/icons/<filename>')
def serve_icons(filename):
    return static_file(filename, root=settings.ICONS_DIR)

#from bottle import run
#run(host='192.168.0.110', port=8000, reloader=True)