#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fabfile for Django:
# http://morethanseven.net/2009/07/27/fabric-django-git-apache-mod_wsgi-virtualenv-and-p/
# modified for fabric 0.9/1.0
from __future__ import with_statement # needed for python 2.5
from fabric.api import *

# globals
env.project_name = 'croisee' # no spaces!
env.use_photologue = False # django-photologue gallery module
env.use_feincms = False
env.use_medialibrary = False # feincms.medialibrary or similar
env.use_daemontools = False  # not available for hardy heron!
env.webserver = 'nginx' # nginx or apache2 (directory name below /etc!)
env.dbserver = 'mysql' # mysql or postgresql
# TODO: database and SSH setup

env.port = 8099 # local FCGI server


# environments

def localhost():
    "Use the local virtual server"
    env.hosts = ['localhost']
    env.user = 'hraban' # You must create and sudo-enable the user first!
    env.path = '/Users/%(user)s/workspace/%(project_name)s' % env # User home on OSX, TODO: check local OS
    env.virtualhost_path = env.path
    env.pysp = '%(virtualhost_path)s/lib/python2.6/site-packages' % env

def webserver():
    "Use the actual webserver"
    env.hosts = ['astarte.fiee.net'] # Change to your server name!
    env.user = env.project_name
    env.path = '/var/www/%(project_name)s' % env
    env.virtualhost_path = env.path
    env.pysp = '%(virtualhost_path)s/lib/python2.5/site-packages' % env
    
# tasks

def test():
    "Run the test suite and bail out if it fails"
    local("cd %(path)s; python manage.py test" % env) #, fail="abort")
    
    
def setup():
    """
    Setup a fresh virtualenv as well as a few useful directories, then run
    a full deployment
    """
    require('hosts', provided_by=[localhost,webserver])
    require('path')
    # install Python environment
    sudo('apt-get install -y build-essential python-dev python-setuptools python-imaging')
    # install some version control systems, since we need Django modules in development
    sudo('apt-get install -y subversion git-core mercurial')

    if env.use_daemontools:
        sudo('apt-get install -y daemontools')
        sudo('mkdir -p /etc/service/%(project_name)s' % env, pty=True)
        
    # install more Python stuff
    sudo('easy_install -U setuptools')
    sudo('easy_install pip')
    sudo('pip install -U virtualenv')
    
    # install webserver and database server
    sudo('apt-get remove -y apache2 apache2-mpm-prefork') # is mostly pre-installed
    if env.webserver=='nginx':
        sudo('apt-get install -y nginx')
    else:
        sudo('apt-get install -y apache2-threaded')
        sudo('apt-get install -y libapache2-mod-wsgi') # outdated on hardy!
    if env.dbserver=='mysql':
        sudo('apt-get install -y mysql-server python-mysqldb')
    elif env.dbserver=='postgresql':
        sudo('apt-get install -y postgresql python-psycopg2')
        
    # disable default site
    env.warn_only=True
    sudo('cd /etc/%(webserver)s/sites-enabled/; rm default;' % env, pty=True)
    env.warn_only=False
    
    # new project setup
    sudo('mkdir -p %(path)s; chown %(user)s:%(user)s %(path)s;' % env, pty=True)
    run('ln -s %(path)s www;' % env, pty=True) # symlink web dir in home
    with cd(env.path):
        run('virtualenv .')
        env.warn_only=True
        run('mkdir -m a+w logs; mkdir releases; mkdir shared; mkdir packages; mkdir backup;' % env, pty=True)
        env.warn_only=False
        if env.use_feincms:
            with cd(env.pysp):
                run('git clone git://github.com/matthiask/django-mptt.git; echo django-mptt > mptt.pth;', pty=True)
                run('git clone git://github.com/matthiask/feincms.git; echo feincms > feincms.pth;', pty=True)
        if env.use_photologue:
            run('mkdir photologue', pty=True)
            #run('pip install -E . -U django-photologue' % env, pty=True)
        if env.use_medialibrary:
            run('mkdir medialibrary', pty=True)
        run('cd releases; ln -s . current; ln -s . previous;', pty=True)
    deploy()
    
def deploy():
    """
    Deploy the latest version of the site to the servers, install any
    required third party modules, install the virtual host and 
    then restart the webserver
    """
    require('hosts', provided_by=[localhost,webserver])
    require('path')
    import time
    env.release = time.strftime('%Y%m%d%H%M%S')
    upload_tar_from_git()
    install_requirements()
    install_site()
    symlink_current_release()
    migrate()
    restart_webserver()
    
def deploy_version(version):
    "Specify a specific version to be made live"
    require('hosts', provided_by=[localhost,webserver])
    require('path')
    env.version = version
    with cd(env.path):
        run('rm -rf releases/previous; mv releases/current releases/previous;', pty=True)
        run('ln -s %(version)s releases/current' % env, pty=True)
    restart_webserver()
    
def rollback():
    """
    Limited rollback capability. Simply loads the previously current
    version of the code. Rolling back again will swap between the two.
    """
    require('hosts', provided_by=[localhost,webserver])
    require('path')
    with cd(env.path):
        run('mv releases/current releases/_previous;', pty=True)
        run('mv releases/previous releases/current;', pty=True)
        run('mv releases/_previous releases/previous;', pty=True)
    restart_webserver()    
    
# Helpers. These are called by other functions rather than directly

def upload_tar_from_git():
    "Create an archive from the current Git master branch and upload it"
    require('release', provided_by=[deploy, setup])
    local('git archive --format=tar master | gzip > %(release)s.tar.gz' % env)
    run('mkdir -p %(path)s/releases/%(release)s' % env, pty=True)
    put('%(release)s.tar.gz' % env, '%(path)s/packages/' % env)
    run('cd %(path)s/releases/%(release)s && tar zxf ../../packages/%(release)s.tar.gz' % env, pty=True)
    local('rm %(release)s.tar.gz' % env)
    # copy secret settings (not in public distro)
    put('%(project_name)s/settings_webserver.py' % env, '%(path)s/releases/%(release)s/%(project_name)s/settings_local.py' % env)
    
def install_site():
    "Add the virtualhost file to the webserver's config"
    require('release', provided_by=[deploy, setup])
    with cd('%(path)s/releases/%(release)s' % env):
        sudo('cp %(webserver)s.conf /etc/%(webserver)s/sites-available/%(project_name)s' % env, pty=True)
        if env.use_daemontools:
            sudo('cp service-run.sh /etc/service/%(project_name)s/run' % env, pty=True)
    env.warn_only=True        
    sudo('cd /etc/%(webserver)s/sites-enabled/; ln -s ../sites-available/%(project_name)s %(project_name)s' % env, pty=True)
    env.warn_only=False
    
def install_requirements():
    "Install the required packages from the requirements file using pip"
    require('release', provided_by=[deploy, setup])
    run('cd %(path)s; pip install -E . -r ./releases/%(release)s/requirements.txt' % env, pty=True)
    
def symlink_current_release():
    "Symlink our current release"
    require('release', provided_by=[deploy, setup])
    with cd(env.path):
        run('rm releases/previous; mv releases/current releases/previous;', pty=True)
        run('ln -s %(release)s releases/current' % env, pty=True)
        if env.use_photologue:
            run('cd releases/current/%(project_name)s/static; rm -rf photologue; ln -s %(path)s/photologue;' % env, pty=True)
    
def migrate():
    "Update the database (doesn't really make sense - no migration)"
    require('project_name')
    run('cd %(path)s/releases/current/%(project_name)s; ../../../bin/python manage.py syncdb --noinput' % env, pty=True)
    
def restart_webserver():
    "Restart the web server"
    if env.webserver=='nginx':
        run('cd $(path)s; bin/python releases/current/%(project_name)s/manage.py runfcgi method=threaded maxchildren=6 maxspare=4 minspare=2 host=127.0.0.1 port=$(port)d pidfile=./logs/django.pid' % env)
    sudo('/etc/init.d/%(webserver)s reload' % env, pty=True)
