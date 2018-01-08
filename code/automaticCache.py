import sys
import logging
import time
from threading import Thread

import js2py
from apscheduler.schedulers.blocking import BlockingScheduler
import requests#
import urllib2
from urllib2 import urlopen
import webbrowser

sched = BlockingScheduler()

js ="""pyimport urllib;
           var result = urllib.urlopen('http://127.0.0.1:8000/explore').read();
           console.log(result.length)
        """

# Executes every night at 3:00am UTC time |
#@sched.scheduled_job('interval', seconds=60)
@sched.scheduled_job('cron', day_of_week='mon-sun', hour=3)#, minute = 28)
def timed_job():
    #print('This job is run every 5 seconds.')
    #try:
    print "----------------BEGIN JOB2---------------------"
    from explore_tree.ajax import cache_all_docs

    url = 'http://127.0.0.1:8000/explore'
    webbrowser.open(url,0, autoraise = False)
    #response = urllib.request.urlopen(req)

    print "----------------END JOB2---------------------"
    #except:
    #    pass

class CacheThread(Thread):

    def __init__(self,args=None):
        Thread.__init__(self)
        self.args = args
    def run(self):
        if self.args !=None:
            print "11111111111111111"
            from django.core.management import execute_from_command_line

            execute_from_command_line(self.args)
        elif self.args == None:
            print "22222222222222222"
        #    req = urllib2.Request('http://127.0.0.1:8000/explore')
        #    response = urllib2.urlopen(req)

        #    response = urllib2.urlopen(req)
            sched.start()
