#!/usr/bin/env python
# coding: utf-8
import argparse, logging

import settings, usb_ids

parser = argparse.ArgumentParser()
parser.add_argument('--update-usb-ids', action='store_true', help='Update usb.ids database')
args = parser.parse_args()

if args.update_usb_ids:
	usb_ids.update_usb_ids('http://www.linux-usb.org/usb.ids.gz', settings.USB_IDS_DB_PATH)
	logging.info('Done')