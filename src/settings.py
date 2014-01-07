# coding: utf-8
import os, logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

CACHE_DIR = os.path.join(STATIC_DIR, 'cache')

ICONS_DIR = os.path.join(STATIC_DIR, 'icons')
ICONS_URL = 'http://metadata.smoothmouse.com/icons/'

USB_IDS_DB_PATH = os.path.join(CACHE_DIR, 'usb-ids.sql')

logging.basicConfig(
	level=logging.INFO, 
	format='%(asctime)s %(levelname)s %(message)s',
	datefmt='%H:%M:%S',
)