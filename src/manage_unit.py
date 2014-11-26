#!/usr/bin/env python
import os
import sys
import warnings

warnings.simplefilter('ignore', Warning)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recommendation.settings.unit.recommendation.settings")
from django.core.management import execute_from_command_line
execute_from_command_line(sys.argv)