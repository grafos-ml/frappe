'''
Utilities for j

Created on Nov 28, 2013

Classes and functions to help view management.

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

import sys, os, json, traceback, logging
from datetime import datetime

def parseDir(directory):
    '''

    Parse all the .json files in the directory and subdirectories.

    **Return**

    *list*:
        A list of every json in the file
    '''
    json_objects = []
    i = 0
    for path, _, files in os.walk(directory):
        for name in files:
            if name[-5:].lower() == '.json':
                f = '/'.join([path,name])
                try:
                    json_objects.append(json.load(open(f)))
                    i += 1
                except Exception as e:
                    logging.error(' '.join([name,str(e)]))
                    traceback.print_exc()
    logging.info('All done! %s files loaded' % i)
    return json_objects