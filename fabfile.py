#!/usr/bin/env python
# coding: utf-8
import os, sys, functools
from contextlib import contextmanager

from fabric.api import *
from fabric.contrib.files import exists
from fabric.colors import blue, green

# Configuration
# -----------------------------------------------------------------------
env.git = 'git@bitbucket.org:smoothmouse/metadata-service.git'
env.forward_agent = True

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
def update_git_origin():
	with hide():
		remotes = run('git remote -v')

		if 'origin' in remotes:
			run('git remote set-url origin %(git)s' % env)
		else:	
			run('git remote add origin %(git)s' % env)

# Wrapper for md5 hashing, which returns empty string if an error occurs
def get_hash(path):
	if exists(path):
		result = run('openssl md5 ' + path)
		
		if result:
			return result		
	return ''

# Tasks
# -----------------------------------------------------------------------
@task
def uwsgi_stop():
	if env.get('uwsgi_conf'):
		print blue('Stopping uWSGI...')
		uwsgi_conf_tmp = env.uwsgi_conf + '.tmp'
		
		run('mv %s %s' % (env.uwsgi_conf, uwsgi_conf_tmp))
		print green('Done.')
		
@task
def uwsgi_start():
	if env.get('uwsgi_conf'):
		print blue('Starting uWSGI...')
		uwsgi_conf_tmp = env.uwsgi_conf + '.tmp'
	
		run('mv %s %s' % (uwsgi_conf_tmp, env.uwsgi_conf))
		print green('Done.')
		
@task
def checkout_commit(commit_id):
	print blue('Resetting to the specified commit and cleaning up...')
	repo_path = os.path.join(env.path, 'git')
	
	if not exists(repo_path):
		run('mkdir ' + repo_path)	
	
	with cd(repo_path):
		git_init()
		update_git_origin()
	
		# Fetch does not change working tree
		run('git fetch --prune origin')

		# Update the working tree and clean up
		run('git reset --hard %s' % commit_id)
		run('git clean -xdf')
	print green('Done.')

@task
def install_requirements():
	print blue('Installing dependencies from requirements.txt to the virtualenv...')
	with cd(env.path):
		if not exists('venv'):
			run('virtualenv venv')
			
		run('venv/bin/pip install -r git/requirements.txt')
	print green('Done.')

@task
def upload_settings():
	print blue('Uploading settings from local conf/ to remote conf/...')
	conf_path = os.path.join(env.path, 'conf')
	
	if not exists(conf_path):
		run('mkdir ' + conf_path)
		
	put('conf/*', conf_path)
	print green('Done.')

@task
def run_tests():
	print blue('Running py.test tests...')
	with cd(env.path), prefix('source venv/bin/activate'):
		run('py.test git/src')
	print green('Done.')

@task # Complete deployment scenario for this project
def deploy(commit_id='origin/master'):
	print os.linesep
	
	with settings():
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
		
		with prefix('export METADATA_SETTINGS=' + os.path.join(env.path, 'conf', 'settings.py')):
			run_tests()
			
		uwsgi_start()