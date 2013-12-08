#!/usr/bin/env python
'''
Created on Nov 26, 2013
 
Functions to pull the data from the MOZILLA API

It can be used as a script. Usage::

    $ ./ffosdatafetcher.py <option> <arg>

OPTIONS::

    > app: fetch and load to db the app data
    > user: fetch and load to db the user data
    > start: Start a cron job to fetch all data (users and apps)
    periodically. I also has a arg for the number of hours interval in witch
    it should execute.
    > kill: kill all cron jobs.
 
 
.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>
'''
 
# Tab file for the cron scheduling
 
import os, sys, tarfile, urllib, shutil

sys.path.append(os.path.dirname(__file__)+'/../../')
from datetime import datetime
from ffos.data import load_apps
from ffos.util import parseDir
from ffos.models import FFOSApp
from crontab import CronTab
 
def json_files(members):
    '''
    Pull .json files only
    '''
    for tarinfo in members:
        name = os.path.splitext(tarinfo.name)
        if name[1] == ".json" and name[0][0] != '.':
            yield tarinfo
 
def download_files_app():
    '''
    Download the files to the database
    '''
    # The could download an html file in case of didn't have new data
    if not os.path.exists('tmp'):
        os.makedirs('tmp')
    urllib.urlretrieve(datetime.strftime(datetime.now(),APP_FILE),'tmp/app.tgz')
    tar = tarfile.open('tmp/app.tgz')
    tar.extractall(members=json_files(tar),path='tmp')
    tar.close()
    return os.path.dirname(__file__)+'/tmp/apps'

def clean():
    '''
    Deletes all files in tmp
    '''
    shutil.rmtree('tmp')

def main(options):
    '''
    Fetch the data file from the mozilla server and load it to database

    **Args**

    options *list*:
        A string with the option of app or user. If app
        it will try to fetch the apps from the mozilla API. If User the users.
        If its none of that it writes an error message.

    **Returns**

    *bool*:
        True if the data was fetched. False if some problem occurred
    '''
    try:
        if options[0] == 'app':
            FFOSApp.load(*parseDir(download_files_app()))
            clean()
            return True
        elif options[0] == 'user':
            # Not implemented
            # clean()
            return False
        elif options[0][-3:] == 'job':
            for job in JOBS:
                CRON.remove(job)
            if options[0][:-3] == 'start':
                job = CRON.new(CMD,comment='Fetch data from user and app')
                job.hour().each(int(options[1]))
                print job.render()
            elif options[0][:-3] == 'kill':
                print 'Cron jobs killed'

    except tarfile.ReadError:
        sys.stderr.write(datetime.strftime(datetime.now(),
            '%d-%m-%Y %H:%M:%S Error: There was no data available'))
        return False
    except Exception:
        raise

 
APP_FILE = 'https://marketplace.cdn.mozilla.net/dumped-apps/tarballs/%Y-%m-%d.tgz'
#APP_FILE = 'https://marketplace.cdn.mozilla.net/dumped-apps/tarballs/2013-11-26.tgz'
USER_FILE = ''
CMD =  './dataloader_cron.py app && ./dataloader_cron.py user'
CRON = CronTab()
JOBS = CRON.find_command(CMD)
 
if __name__ == '__main__':
    main(sys.argv[1:])
