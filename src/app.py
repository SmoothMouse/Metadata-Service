# coding: utf-8
import os
import xml.etree.ElementTree as ET
from subprocess import check_output

import settings, metadata

from flask import Flask, abort, send_from_directory

# Flask
app = Flask(__name__)


# Routes
# -----------------------------------------------------------------------
@app.route('/', methods=['GET'])
def home():
    return abort(400)  # Bad Request


@app.route('/devices/<int:vid>/<int:pid>/', methods=['GET'])
def devices(vid, pid):
    # If XML output is cached, retrieve it
    cache_name = '%i_%i.xml' % (vid, pid)
    cache_path = os.path.join(settings.CACHE_DIR, cache_name)
    
    if os.path.isfile(cache_path):
        return send_from_directory(settings.CACHE_DIR, cache_name)
    else:
        # Status code
        status = 404
        headers = {'Content-Type': 'application/xml'}
        
        # Prepare to output XML
        declaration = '<?xml version="1.0" encoding="UTF-8"?>'
        root = ET.Element('DeviceMetadata')
        tree = ET.ElementTree(root)
        
        md = metadata.get_sm_device_metadata(vid, pid)
        
        if md:
            status = 200
            
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
        
        return declaration + ET.tostring(root), status, headers


@app.route('/hooks/icons/<secret>/', methods=['POST'])
def icons_hook(secret):
    if secret == settings.SECRET:
        update_icons()
    return 'Success.'


def update_icons():
    wd = os.getcwd()
    os.chdir(settings.ICONS_DIR)
    check_output('git fetch origin', shell=True)
    check_output('git reset --hard origin/master', shell=True)
    os.chdir(wd)


# Development server
# -----------------------------------------------------------------------
if __name__ == '__main__':
    app.debug = True
    app.run()
