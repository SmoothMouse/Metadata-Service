# coding: utf-8
import os, tempfile
from subprocess import check_output

import settings, metadata

# Really basic tests for metadata
def test_system_dependencies():
	check_output(['cabextract', '-v'])
	check_output(['identify', '-version'])
	check_output(['convert', '-version'])

def test_get_ms_device_metadata():
	md = metadata.get_ms_device_metadata(1133, 49182)
	
	assert 'Logitech' in md['vendor_name']
	assert '518' in md['product_name']
	assert os.path.isfile(md['icon_path'])
	os.remove(md['icon_path'])
	
def test_get_linux_device_metadata():
	md = metadata.get_linux_device_metadata(1133, 49182)
	
	assert 'Logitech' in md['vendor_name']
	assert '518' in md['product_name']
	
def test_get_sm_device_metadata():
	md = metadata.get_sm_device_metadata(1133, 49182)
	
	assert 'Logitech' in md['vendor_name']
	assert '518' in md['product_name']