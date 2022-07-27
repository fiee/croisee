#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fabfile for Django:
derived from http://morethanseven.net/2009/07/27/fabric-django-git-apache-mod_wsgi-virtualenv-and-p/
"""
from __future__ import unicode_literals, print_function
import os
import time
from fabric.api import env, sudo, local, require, settings, run, prompt, cd, put

# Fabric setup
env.colorize_errors = True

# globals
env.prj_name = 'croisee'  # no spaces!
env.prj_dir = 'croisee'  # subdir under git root that contains the deployable part
env.sudoers_group = 'admin'
env.use_feincms = False
env.use_medialibrary = False  # feincms.medialibrary or similar
env.use_daemontools = False
env.use_supervisor = True
env.use_celery = False
env.use_memcached = False
env.webserver = 'nginx'  # nginx (directory name below /etc!), nothing else ATM
env.dbserver = 'mysql'  # mysql or postgresql


# environments


def localhost():
    "Use the local virtual server"
    env.hosts = ['localhost']
    env.requirements = 'local'
    env.user = env.prj_name  # used by ssh
    env.adminuser = 'hraban'
    env.homepath = '/Users/%(adminuser)s' % env  # User home on OSX, TODO: check local OS
    env.prj_path = '%(homepath)s/workspace/%(prj_name)s' % env
    env.virtualhost_path = env.prj_path
    env.pysp = '%(virtualhost_path)s/lib/python2.7/site-packages' % env
    env.tmppath = '/var/tmp/django_cache/%(prj_name)s' % env


def webserver():
    "Use the actual webserver"
    env.hosts = ['semla.fiee.net'] # Change to your server name!
    env.requirements = 'webserver'
    env.user = env.prj_name
    env.adminuser = 'root'
    env.homepath = '/home/%(user)s' % env  # User home on Linux
    env.prj_path = '/var/www/%(prj_name)s' % env
    env.virtualhost_path = env.prj_path
    env.pysp = '%(virtualhost_path)s/lib/python2.7/site-packages' % env
    env.tmppath = '/var/tmp/django_cache/%(prj_name)s' % env
    env.cryptdomain = 'croisee.fiee.net'
    if not _is_host_up(env.hosts[0], 22):
        import sys
        sys.exit(1)


# helpers


def _is_host_up(host, port):
    import socket
    import paramiko
    original_timeout = socket.getdefaulttimeout()
    new_timeout = 3
    socket.setdefaulttimeout(new_timeout)
    host_status = False
    try:
        paramiko.Transport((host, port))
        host_status = True
    except:
        print('***Warning*** Host {host} on port {port} is down.'.format(
            host=host, port=port)
        )
    socket.setdefaulttimeout(original_timeout)
    return host_status


# tasks


def test():
    "Run the test suite and bail out if it fails"
    local("cd %(prj_path)s/releases/current/%(prj_name)s; python manage.py test" % env)  # , fail="abort")


def setup():
    """
    Setup a fresh virtualenv as well as a few useful directories, then run
    a full deployment
    """
    require('hosts', provided_by=[webserver])
    require('prj_path')

    if env.requirements == 'local':
        return local_setup()

    with settings(user=env.adminuser):
        # install Python environment and version control
        sudo('apt-get install -y build-essential python3-dev python3-setuptools python3-virtualenv libyaml-dev python3-yaml git-core')
        # If you need Django modules in development, install more version control systems
        # sudo('apt-get install -y subversion git-core mercurial', pty=False)

        # install more Python stuff
        # Don't install setuptools or virtualenv on Ubuntu with easy_install or pip! Only Ubuntu packages work!
        # sudo('easy_install pip')  # maybe broken

        if env.use_daemontools:
            sudo('apt-get install -y daemontools daemontools-run')
            sudo('mkdir -p /etc/service/%(prj_name)s' % env, pty=True)
        if env.use_supervisor:
            sudo('pip install supervisor')
            # sudo('echo; if [ ! -f /etc/supervisord.conf ]; then echo_supervisord_conf > /etc/supervisord.conf; fi', pty=True) # configure that!
            sudo('echo; if [ ! -d /etc/supervisor ]; then mkdir /etc/supervisor; fi', pty=True)
        if env.use_celery:
            sudo('apt-get install -y rabbitmq-server')  # needs additional deb-repository, see tools/README.rst!
            if env.use_daemontools:
                sudo('mkdir -p /etc/service/%(prj_name)s-celery' % env, pty=True)
            elif env.use_supervisor:
                local('echo "CHECK: You want to use celery under supervisor. Please check your celery configuration in supervisor-celery.conf!"', pty=True)
        if env.use_memcached:
            sudo('apt-get install -y memcached python-memcache')

        # install webserver and database server
        if env.webserver == 'nginx':
            sudo('apt-get remove -y apache2 apache2-mpm-prefork apache2-utils')  # is mostly pre-installed
            sudo('apt-get install -y nginx-full')
        else:
            local('echo "WARNING: Your webserver «%s» is not supported!"' % env.webserver, pty=True)  # other webservers?
        if env.dbserver == 'mysql':
            sudo('apt-get install -y mysql-server python-mysqldb libmysqlclient-dev')
        elif env.dbserver == 'postgresql':
            sudo('apt-get install -y postgresql python-psycopg2')

        with settings(warn_only=True, pty=True):
            # disable default site
            sudo('cd /etc/%(webserver)s/sites-enabled/; rm default;' % env)
            # install certbot scripts
            sudo('git clone https://github.com/certbot/certbot /opt/letsencrypt; cd /opt/letsencrypt; ./certbot-auto')
            sudo('cp tools/renew-letsencrypt.sh /etc/cron-monthly/')

    # new project setup
    setup_user()
    deploy('first')


def setup_user():
    """
    Create a new Linux user, set it up for certificate login.
    Call `setup_passwords`.
    """
    require('hosts', provided_by=[webserver])
    require('adminuser')
    env.new_user = env.user
    with settings(user=env.adminuser, pty=True):
        # create user and add it to admin group
        sudo('adduser "%(new_user)s" --disabled-password --gecos "" && adduser "%(new_user)s" %(sudoers_group)s' % env)
        # copy authorized_keys from root for certificate login
        sudo('mkdir %(homepath)s/.ssh && cp /root/.ssh/authorized_keys %(homepath)s/.ssh/' % env)
        # Now we should be able to login with that new user

        with settings(warn_only=True):
            # create web and temp dirs
            sudo('mkdir -p %(prj_path)s; chown %(new_user)s:%(new_user)s %(prj_path)s;' % env)
            sudo('mkdir -p %(tmppath)s; chown %(new_user)s:%(new_user)s %(tmppath)s;' % env)
            # symlink web dir in home
            run('cd ~; ln -s %(prj_path)s www;' % env)
    env.user = env.new_user

    # cd to web dir and activate virtualenv on login
    run('echo "\ncd %(prj_path)s && source bin/activate\n" >> %(homepath)s/.profile\n' % env, pty=True)

    setup_passwords()


def setup_passwords():
    """
    create .env and MySQL user; to be called from `setup` or `local_setup`
    """
    print('I will now ask for the passwords to use for database and email account access. If one is empty, I’ll use the non-empty for both. If you leave both empty, I won’t create an database user.')
    prompt('Please enter DATABASE_PASSWORD for user %(prj_name)s:' % env, key='database_password')
    prompt('Please enter EMAIL_PASSWORD for user %(user)s:' % env, key='email_password')

    if env.database_password and not env.email_password:
        env.email_password = env.database_password
    if env.email_password and not env.database_password:
        env.database_password = env.email_password
    # TODO: check input for need of quoting!

    with settings(user=env.adminuser, pty=True):
        # create .env and set database and email passwords
        run('echo; if [ ! -f %(prj_path)s/.env ]; then echo "DJANGO_SETTINGS_MODULE=settings\nDATABASE_PASSWORD=%(database_password)s\nEMAIL_PASSWORD=%(email_password)s\n" > %(prj_path)s/.env; fi' % env)

        # create MySQL user
        if env.dbserver == 'mysql' and env.database_password:
            env.dbuserscript = '%(homepath)s/userscript.sql' % env
            run('''echo "\ncreate user '%(prj_name)s'@'localhost' identified by '%(database_password)s';
    create database %(prj_name)s character set 'utf8';\n
    grant all privileges on %(prj_name)s.* to '%(prj_name)s'@'localhost';\n
    flush privileges;\n" > %(dbuserscript)s''' % env)
            print('Setting up %(prj_name)s in MySQL. Please enter password for MySQL root:')
            run('mysql -u root -p -D mysql < %(dbuserscript)s' % env)
            run('rm %(dbuserscript)s' % env)
        # TODO: add setup for PostgreSQL
    setup_paths()


def setup_paths():

    with cd(env.prj_path):
        run('virtualenv .')  # activate with 'source ~/www/bin/activate', perhaps add that to your .bashrc or .profile
        with settings(warn_only=True):
            # create necessary directories
            for folder in 'logs run releases shared packages backup letsencrypt ssl'.split():
                run('mkdir %s' % folder, pty=True)
            run('chmod a+w logs', pty=True)
            with settings(user=env.adminuser):
                run('chown www-data:www-data letsencrypt && chown www-data:www-data ssl')
            if env.use_medialibrary:
                run('mkdir medialibrary', pty=True)
            run('cd releases; ln -s . current; ln -s . previous;', pty=True)


def check_dotenv(local=True):
    """
    Check if there is a .env file, otherwise create it.
    Works ATM only locally.
    """
    require('prj_name')
    require('prj_path')
    require('user')

    dotenv_filename = '%(prj_path)s/%(prj_name)s/.env' % env
    if not os.path.isfile(dotenv_filename):
        print('I will now ask for the passwords to use for ' +
              ('local ' if local else '') + 'database and ' +
              'email account access. If one is empty, I’ll use the non-empty ' +
              'for both. If you leave both empty, I won’t create a database ' +
              'user.')
        prompt('Please enter DATABASE_PASSWORD for user %(prj_name)s:' % env, key='database_password')
        prompt('Please enter EMAIL_PASSWORD for user %(user)s:' % env, key='email_password')

        if env.database_password and not env.email_password:
            env.email_password = env.database_password
        if env.email_password and not env.database_password:
            env.database_password = env.email_password
        # TODO: check input for need of quoting!

        # create .env and set database and email passwords
        from django.utils.crypto import get_random_string
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#^&*(-_=+)'  # without % and $
        dotenv = 'SECRET_KEY="%s"\n' % get_random_string(50, chars)
        dotenv += 'DJANGO_SETTINGS_MODULE=settings%s\n' % ('.local' if local else '')
        dotenv += 'DATABASE_PASSWORD="%(database_password)s"\n' % env
        dotenv += 'EMAIL_PASSWORD="%(email_password)s"\n' % env

        try:
            dotenv_file = open(dotenv_filename, 'x', encoding='utf-8')
            dotenv_file.write(dotenv)
        except TypeError:  # Python 2.x
            dotenv_file = open(dotenv_filename, 'w')
            dotenv_file.write(dotenv.encode('utf-8'))
        dotenv_file.close()
    else:
        print('Reading existing .env file...')
        import dotenv
        dotenv.read_dotenv(dotenv_filename)
        env.database_password = os.environ['DATABASE_PASSWORD']


def local_setup():
    """
    user setup on localhost
    """
    require('hosts', provided_by=[localhost])
    require('prj_path')
    with cd(env.prj_path):
        if not (os.path.isdir(os.path.join(env.prj_path, 'bin')) and
                os.path.isdir(os.path.join(env.prj_path, 'lib')) and
                os.path.isdir(os.path.join(env.prj_path, 'include'))):
            with settings(warn_only=True):
                local('/Library/Frameworks/Python.framework/Versions/3.6/bin/virtualenv . && source bin/activate')
        local('source bin/activate && pip install -U -r ./requirements/%(requirements)s.txt' % env)

    check_dotenv(local=True)

    # create MySQL user
    if env.dbserver == 'mysql' and env.database_password:
        # check MySQL:
        print('Checking database connection...')
        try:
            import _mysql, _mysql_exceptions
        except ImportError as ex:
            print(ex)
            print('MySQL module not installed!')

        try:
            db = _mysql.connect(host=env.hosts[0], user=env.user, passwd=env.database_password, db=env.prj_name)
            print('Database connection successful.')
            del db
        except Exception as ex:
            print(ex)

            env.dbuserscript = '%(prj_path)s/userscript.sql' % env
            dbs = open(env.dbuserscript, 'w')
            dbs.write('''create user '%(prj_name)s'@'localhost' identified by '%(database_password)s';
create database %(prj_name)s character set 'utf8mb4';
grant all privileges on %(prj_name)s.* to '%(prj_name)s'@'localhost';
flush privileges;\n''' % env)
            dbs.close()
            print('Setting up %(prj_name)s in MySQL. Please enter password for MySQL root:' % env)
            local('mysql -u root -p -D mysql -e "source %(dbuserscript)s"' % env)
            os.unlink(env.dbuserscript)


def deploy(param=''):
    """
    Deploy the latest version of the site to the servers, install any
    required third party modules, install the virtual host and
    then restart the webserver
    """
    require('hosts', provided_by=[localhost, webserver])
    require('prj_path')
    env.release = time.strftime('%Y%m%d%H%M%S')
    upload_tar_from_git()
    if param == 'first': install_requirements()
    install_site()
    symlink_current_release()
    migrate(param)
    restart_webserver()


def deploy_version(version):
    "Specify a specific version to be made live"
    require('hosts', provided_by=[localhost, webserver])
    require('prj_path')
    env.version = version
    with cd(env.prj_path):
        run('rm -rf releases/previous; mv releases/current releases/previous;', pty=True)
        run('ln -s %(version)s releases/current' % env, pty=True)
    restart_webserver()


def rollback():
    """
    Limited rollback capability. Simply loads the previously current
    version of the code. Rolling back again will swap between the two.
    """
    require('hosts', provided_by=[localhost, webserver])
    require('prj_path')
    with cd(env.prj_path):
        run('mv releases/current releases/_previous;', pty=True)
        run('mv releases/previous releases/current;', pty=True)
        run('mv releases/_previous releases/previous;', pty=True)
    # TODO: check Django migrations for rollback
    restart_webserver()


# Helpers. These are called by other functions rather than directly


def upload_tar_from_git():
    "Create an archive from the current Git master branch and upload it"
    require('release', provided_by=[deploy, setup])
    local('git archive --format=tar master | gzip > %(release)s.tar.gz' % env)
    run('mkdir -p %(prj_path)s/releases/%(release)s' % env)  # , pty=True)
    put('%(release)s.tar.gz' % env, '%(prj_path)s/packages/' % env)
    run('cd %(prj_path)s/releases/%(release)s && tar zxf ../../packages/%(release)s.tar.gz' % env, pty=True)
    local('rm %(release)s.tar.gz' % env)


def install_site():
    "Add the virtualhost config file to the webserver's config, activate logrotate"
    require('release', provided_by=[deploy, setup])
    with cd('%(prj_path)s/releases/%(release)s' % env):
        with settings(user=env.adminuser, pty=True):
            run('cp server-setup/%(webserver)s.conf /etc/%(webserver)s/sites-available/%(prj_name)s' % env)
            if env.use_daemontools:  # activate new service runner
                run('cp server-setup/service-run.sh /etc/service/%(prj_name)s/run; chmod a+x /etc/service/%(prj_name)s/run;' % env)
            else:  # delete old service dir
                run('echo; if [ -d /etc/service/%(prj_name)s ]; then rm -rf /etc/service/%(prj_name)s; fi' % env)
            if env.use_supervisor:  # activate new supervisor.conf
                run('cp server-setup/supervisor.conf /etc/supervisor/conf.d/%(prj_name)s.conf' % env)
                if env.use_celery:
                    run('cp server-setup/supervisor-celery.conf /etc/supervisor/conf.d/%(prj_name)s-celery.conf' % env)
            else:  # delete old config file
                # if you set a process name in supervisor.ini, then you must add it like %(prj_name):appserver
                run('echo; if [ -f /etc/supervisor/%(prj_name)s.ini ]; then supervisorctl %(prj_name)s stop rm /etc/supervisor/%(prj_name)s.ini; fi' % env)
                run('echo; if [ -f /etc/supervisor/conf.d/%(prj_name)s.conf ]; then supervisorctl %(prj_name)s stop rm /etc/supervisor/conf.d/%(prj_name)s.conf; fi' % env)
                if env.use_celery:
                    run('echo; if [ -f /etc/supervisor/%(prj_name)s-celery.ini ]; then supervisorctl celery celerybeat stop rm /etc/supervisor/%(prj_name)s-celery.ini; fi' % env)
                    run('echo; if [ -f /etc/supervisor/conf.d/%(prj_name)s-celery.conf ]; then supervisorctl celery celerybeat stop rm /etc/supervisor/conf.d/%(prj_name)s-celery.conf; fi' % env)
            if env.use_celery and env.use_daemontools:
                run('cp server-setup/service-run-celeryd.sh /etc/service/%(prj_name)s-celery/run; chmod a+x /etc/service/%(prj_name)s-celery/run;' % env)
            # try logrotate
            with settings(warn_only=True):
                run('cp server-setup/logrotate.conf /etc/logrotate.d/website-%(prj_name)s' % env)
                if env.use_celery:
                    run('cp server-setup/logrotate-celery.conf /etc/logrotate.d/celery' % env)
                run('cp server-setup/letsencrypt.conf /etc/letsencrypt/configs/%(cryptdomain)s.conf' % env)
    with settings(user=env.adminuser, warn_only=True, pty=True):
        run('ln -s /etc/%(webserver)s/sites-available/%(prj_name)s /etc/%(webserver)s/sites-enabled/%(prj_name)s' % env)


def install_requirements():
    "Install the required packages from the requirements file using pip"
    require('release', provided_by=[deploy, setup])
    require('requirements', provided_by=[localhost, webserver])
    run('cd %(prj_path)s; pip install -U -r ./releases/%(release)s/requirements/%(requirements)s.txt' % env, pty=True)


def symlink_current_release():
    "Symlink our current release"
    require('release', provided_by=[deploy, setup])
    with cd(env.prj_path):
        run('rm releases/previous; mv releases/current releases/previous;', pty=True)
        run('ln -s %(release)s releases/current' % env, pty=True)
        # copy South migrations from previous release, if there are any
        run('cd releases/previous/%(prj_name)s; if [ -d migrations ]; then cp -r migrations ../../current/%(prj_name)s/; fi' % env, pty=True)
        # collect static files
        with cd('releases/current/%(prj_name)s' % env):
            run('rm settings/local.*')  # delete local settings, could also copy webserver to local
            run('mkdir ../logs', warn_only=True)  # needed at start, while it stays empty
            run('%(prj_path)s/bin/python manage.py collectstatic -v0 --noinput' % env, pty=True)


def migrate(param=''):
    "Update the database"
    require('prj_name')
    require('prj_path')
    env.southparam = '--auto'
    if param == 'first':
        if env.use_feincms:
            # FeinCMS 1.9 doesn’t yet have migrations
            run('cd %(prj_path)s/releases/current/%(prj_name)s; %(prj_path)s/bin/python manage.py makemigrations page medialibrary' % env, pty=True)
        run('cd %(prj_path)s/releases/current/%(prj_name)s; %(prj_path)s/bin/python manage.py makemigrations %(prj_name)s' % env, pty=True)
        run('cd %(prj_path)s/releases/current/%(prj_name)s; %(prj_path)s/bin/python manage.py migrate --noinput' % env, pty=True)
    # with cd('%(prj_path)s/releases/current/%(prj_name)s' % env):
    #    run('%(prj_path)s/bin/python manage.py schemamigration %(prj_name)s %(southparam)s && %(prj_path)s/bin/python manage.py migrate %(prj_name)s' % env)
    #    # TODO: should also migrate other apps! get migrations from previous releases


def restart_webserver():
    "Restart the web server"
    require('webserver')
    with settings(user=env.adminuser, warn_only=True, pty=True):
        if env.webserver == 'nginx':
            require('prj_path')
            if env.use_daemontools:
                run('kill `cat %(prj_path)s/logs/django.pid`' % env)  # kill process, daemontools will start it again, see service-run.sh
            if env.use_supervisor:
                # if you set a process name in supervisor.ini, then you must add it like %(prj_name):appserver
                if env.use_celery:
                    run('supervisorctl restart %(prj_name)s celery celerybeat' % env)
                else:
                    run('supervisorctl restart %(prj_name)s' % env)
            # require('prj_name')
            # run('cd %(prj_path)s; bin/python releases/current/manage.py runfcgi method=threaded maxchildren=6 maxspare=4 minspare=2 host=127.0.0.1 port=%(webport)s pidfile=./logs/django.pid' % env)
        run('service %(webserver)s reload' % env)
