# coding: utf-8
import os, logging

SECRET = 'f7e2588439abf3f93d1601f140742c8f'

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), 'static')

CACHE_DIR = os.path.join(STATIC_DIR, 'cache')

ICONS_DIR = os.path.join(STATIC_DIR, 'icons')
ICONS_URL = 'http://localhost:8000/icons/'

USB_IDS_DB_PATH = os.path.join(CACHE_DIR, 'usb-ids.sql')

# -----------------------------------------------------------------------

logging.basicConfig(
	level=logging.INFO, 
	format='%(asctime)s %(levelname)s %(message)s',
	datefmt='%H:%M:%S',
)

# -----------------------------------------------------------------------

EXTRA_SETTINGS = os.getenv('METADATA_SETTINGS')

if EXTRA_SETTINGS:
	import imp
	imp.load_source('extra_settings', EXTRA_SETTINGS)
	from extra_settings import *