__author__ = "joaonrb"
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frappe_settings.settings")
import django
django.setup()
from recommendation.models import User

if __name__ == "__main__":
    User.load_owned_items()