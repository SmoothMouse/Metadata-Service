#!/usr/bin/env python
# coding: utf-8
'''
	Usage: 
		fab production deploy
		fab production setup_icons
'''
	
import os, sys, functools
from contextlib import contextmanager

from fabric.api import *
from fabric.contrib.files import exists
from fabric.colors import blue

# Configuration
# -----------------------------------------------------------------------
env.git = 'git@bitbucket.org:smoothmouse/metadata-service.git'
env.git_for_icons = 'https://github.com/SmoothMouse/Device-Icons.git'
env.forward_agent = True
env.settings = os.path.join('conf', 'settings.py') # local
env.settings_env = 'export METADATA_SETTINGS=' + os.path.join(env.path, 'conf', 'settings.py') 

@task
def staging():
	env.hosts = ['localhost']
	env.user = 'Dae'
	env.path = '/Users/Dae/Desktop/test/'

@task
def production():
	env.hosts = ['server1.cyberic.eu']
	env.user = 'cyberic'
	env.name = 'metadata'
	env.path = '/var/www/metadata.smoothmouse.com/'
	env.uwsgi_conf = os.path.join(env.path, 'conf', 'uwsgi.ini')

# Helpers
# -----------------------------------------------------------------------
# Initialize git repository
def git_init():
	if not exists('.git'):
		run('git init')

# Update git remote "origin"
def update_git_origin(url=env.git):
	with hide():
		remotes = run('git remote -v')

		if 'origin' in remotes:
			run('git remote set-url origin %s' % url)
		else:	
			run('git remote add origin %s' % url)

# Wrapper for md5 hashing, which returns empty string if an error occurs
def get_hash(path):
	if exists(path):
		result = run('openssl md5 ' + path)
		
		if result:
			return result		
	return ''

# Common tasks
# -----------------------------------------------------------------------
@task
def uwsgi_stop():
	if env.get('uwsgi_conf'):
		print blue('Stopping uWSGI...')
		uwsgi_conf_tmp = env.uwsgi_conf + '.tmp'
		
		run('mv %s %s' % (env.uwsgi_conf, uwsgi_conf_tmp))
		
@task
def uwsgi_start():
	if env.get('uwsgi_conf'):
		print blue('Starting uWSGI...')
		uwsgi_conf_tmp = env.uwsgi_conf + '.tmp'
	
		run('mv %s %s' % (uwsgi_conf_tmp, env.uwsgi_conf))
		
@task
def checkout_commit(commit_id):
	print blue('Resetting to the specified commit and cleaning up...')
	repo_path = os.path.join(env.path, 'git')
	run('mkdir -p ' + repo_path)
	
	with cd(repo_path):
		git_init()
		update_git_origin()
	
		# Fetch does not change working tree
		run('git fetch --prune origin')

		# Update the working tree and clean up
		run('git reset --hard %s' % commit_id)
		run('git clean -xdf')

@task
def install_requirements():
	print blue('Installing dependencies from requirements.txt to the virtualenv...')
	with cd(env.path):
		if not exists('venv/bin/pip'):
			run('virtualenv venv')
			
		run('venv/bin/pip install -r git/requirements.txt')

@task
def upload_settings():
	print blue('Uploading settings...')
	conf_path = os.path.join(env.path, 'conf')
	
	if not exists(conf_path):
		run('mkdir ' + conf_path)
	
	put(env.settings, conf_path)

@task
def run_tests():
	print blue('Running py.test tests...')
	with prefix(env.settings_env):
		with cd(env.path), prefix('source venv/bin/activate'):
			run('py.test git/src')

# Project-specific tasks
# -----------------------------------------------------------------------
@task # Run this
def deploy(commit_id='origin/master'):
	print os.linesep
	
	path_to_requirements = os.path.join(env.path, 'git', 'requirements.txt')
	requirements_hash_old = get_hash(path_to_requirements)
	
	uwsgi_stop()
	
	checkout_commit(commit_id)
	
	if not exists(os.path.join(env.path, 'venv')):
		install_requirements()
	else:
		requirements_hash_new = get_hash(path_to_requirements)
		if requirements_hash_new != requirements_hash_old:
			install_requirements()
	
	upload_settings()
	
	run_tests()
	
	uwsgi_start()

@task
def update_usb_ids():
	with cd(env.path):
		run('mkdir -p static/cache/')
		
		with prefix(env.settings_env):
			run('venv/bin/python git/src/manage.py --update-usb-ids')

@task
def setup_icons():
	icons_path = os.path.join(env.path, 'static', 'icons')
	run('mkdir -p ' + icons_path)
	
	with cd(icons_path):
		git_init()
		update_git_origin(env.git_for_icons)