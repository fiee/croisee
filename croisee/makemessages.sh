#!/bin/bash
./manage.py makemessages -a -e html,py,tex,txt
./manage.py makemessages -a -d djangojs
open locale/de/LC_MESSAGES/*.po
