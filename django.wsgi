import os
import sys
# put the Django project on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ["DJANGO_SETTINGS_MODULE"] = "croisee.settings"
from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
