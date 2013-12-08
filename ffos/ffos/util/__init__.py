'''
Utilities for j

Created on Nov 28, 2013

Classes and functions to help view management.

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

import sys, os, json, traceback
from datetime import datetime

def parseDir(directory,sillent=False):
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
                #if not sillent:
                #    print datetime.strftime(datetime.now(), '%d-%m-%Y %H:%M:%S'),\
                #    'parsing',name,
                try:
                    json_objects.append(json.load(open(f)))
                    i += 1
                except Exception as e:
                    sys.stderr.write(' '.join([datetime.strftime(datetime.now(),
                        '%d-%m-%Y %H:%M:%S'),name,str(e),'\n']))
                    traceback.print_exc()
                    if not sillent:
                        print datetime.strftime(datetime.now(),
                            '%d-%m-%Y %H:%M:%S'),'failed!'
                else:
                    if not sillent:
                        print datetime.strftime(datetime.now(),
                            '%d-%m-%Y %H:%M:%S done!'),i, 'files loaded'
    return json_objects