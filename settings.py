# coding: utf-8
import os, logging

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

CACHE_DIR = os.path.join(BASE_DIR, 'cache')

ICONS_DIR = os.path.join(BASE_DIR, 'icons')
ICONS_URL = 'http://192.168.0.110:8000/icons/'

USB_IDS_DB_PATH = os.path.join(CACHE_DIR, 'usb-ids.sql')

logging.basicConfig(
	level=logging.INFO, 
	format='%(asctime)s %(levelname)s %(message)s',
	datefmt='%H:%M:%S',
)

# Debug
#import tempfile
#tempfile.tempdir = os.path.join(BASE_DIR, 'temp')