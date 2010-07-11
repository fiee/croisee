#!/usr/bin/env bash
SITE=croisee
SITEUSER=$SITE
# PORT is 8 + last 3 numbers of user ID (starting at 1000 on Debian)
PORT=`id -u $SITE`
PORT=8${PORT#1}

SITEDIR=/var/www/${SITE}
DJANGODIR=${SITEDIR}/releases/current/${SITE}
PYTHON=${SITEDIR}/bin/python
PIDFILE=${SITEDIR}/logs/django.pid

# activate virtualenv
source ${SITEDIR}/bin/activate
cd ${SITEDIR}
# run django FCGI server
exec envuidgid $SITEUSER $PYTHON $DJANGODIR/manage.py runfcgi method=threaded maxchildren=6 maxspare=4 minspare=2 host=127.0.0.1 port=$PORT pidfile=$PIDFILE daemonize=false
