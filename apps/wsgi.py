"""
WSGI config for boilerplate project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os
from dotenv import load_dotenv

from django.core.wsgi import get_wsgi_application

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.settings_prod')

application = get_wsgi_application()
