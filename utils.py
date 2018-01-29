# -*- coding:utf-8 -*-

import sqlite3
import sys
import os

from datetime import datetime
from subprocess import Popen, PIPE

DBNAME = 'fuzz.db'
RUNSDIR = 'fuzzruns'
BROWSERFILE = "browsers.txt"
BROWSERS = {}
CONFIG = {'port':5000, 
        'host':'0.0.0.0',
        'remoteport':'5000',
        'logsdir':'./logs/',
        'force-reload': 15, #Seconds until the harness forces reloads
        'js-reload':12,
        'static':'./static'
        }

def testadb():
    try:
        with Popen(['adb'], stdout=PIPE, stdin=PIPE, stderr=PIPE) as p:
            return True
    except:
        return False

def initbrowsers():
    try:
        os.stat(BROWSERFILE)
    except NameError as e:
        print("Does browsers.txt exist?")
        print(e)
        with open(BROWSERFILE, "w") as f:
            #Just keep things from breaking immediately.
            pass
    if len(BROWSERS) == 0:
        print("Initializing browsers")
        entries = open(BROWSERFILE).readlines()
        for entry in entries:
            if "#" in entry:
                continue
            browser, package = entry.split(":")
            BROWSERS[browser] = package[:-1] #Rid trailing newline

def launchbrowser(devname, browserid):
    """Use ADB to launch a given browser on a device."""
    initbrowsers()
    devfound = False
    for dev in getdevices():
        if devname == dev['name']:
            devfound = True
            break
    if not devfound:
        #Device not found.
        return {'output':'Sorry, could not find device {}.'.format(devname)}
    if browserid not in BROWSERS:
        return {'output':"Sorry, don't have that browser's package."}
    package = BROWSERS[browserid]
    url = "{}:{}/begin/{}".format(CONFIG['host'], CONFIG['port'], devname)
    args = ['adb', '-s', devname, 'shell', 'am', 'start', '-n', package, '-d', url]
    print("Args:", args)
    p = Popen(args, stdout=PIPE)
    return {'output':p.stdout.read().decode('utf-8')}
    
def getdeviceid(devname):
    with sqlite3.connect(DBNAME) as conn:
        curs = conn.cursor()
        curs.execute("""SELECT rowid FROM devices WHERE device_name = ?""", \
                (devname,))
        try:
            res= curs.fetchone()
            return res['rowid']
        except:
            return str(0)

def generatedatabase():
    """
    Break things down by device and browser. Our fuzzruns should be identified
    by rowid (given by SQLite).
    """
    curs = sqlite3.connect(DBNAME).cursor()
    curs.execute("""CREATE TABLE IF NOT EXISTS devices(device_name TEXT UNIQUE,
            device_type TEXT, logfile TEXT)""")
    curs.execute("""CREATE TABLE IF NOT EXISTS browsers(device_id INTEGER,
            fuzzid TEXT, package TEXT, user_agent TEXT, cookie TEXT, 
            lastrunid INTEGER, lasttest TEXT, laststart TEXT)""")
    curs.execute("""CREATE TABLE IF NOT EXISTS crashes(browser_id INTEGER,
            logpos INTEGER, logpath TEXT,
            path TEXT, localpath TEXT, testpath TEXT)""")
    curs.execute("""CREATE TABLE IF NOT EXISTS browserruns(browser_id INTEGER,
            starttime TEXT, endtime TEXT)""")
    curs.execute("""CREATE TABLE IF NOT EXISTS fuzzruns(run_label TEXT,
            iterations INTEGER)""")

def updatebrowserfuzz(fuzzID, run, count=0):
    with sqlite3.connect(DBNAME) as conn:
        curs = conn.cursor()
        curs.execute("""UPDATE browsers
                SET lasttest = ?, lastrunid = ?
                WHERE fuzzid = ?""", (datetime.now(), run, fuzzID))
    

def forwardlocalhost(devname, port):
    Popen(['adb', '-s', devname, 'reverse', 'tcp:' + str(CONFIG['remoteport']), \
            'tcp:' + str(port)])

def forwardlocalhosts(port):
    for device in getdevices():
        name = device['name']
        forwardlocalhost(name, port)

def savenewrun(runname, iterations):
    """
    """
    with sqlite3.connect(DBNAME).cursor() as curs:
        curs.execute("INSERT INTO fuzzruns VALUES (?, ?)", (runname, iterations))

def getbrowsers(devicename):
    """ Returns a list of all browsers found for the given device. """
    initbrowsers()
    #Should check first we're connected to the device
    browsersfound = []
    adb = Popen(['adb', '-s', devicename, 'shell', 'pm', \
            'list', 'packages'], stdout=PIPE)
    packages = adb.stdout.read().decode("utf-8").split()
    for package in packages:
        name = package.split(":")[1] 
        if name in BROWSERS.values():
            #print("Browser found:",name)
            for b in BROWSERS:
                if BROWSERS[b] == name:
                    browsersfound.append(b)
                    break
    return browsersfound


def getdevices():
    """"
    Returns a list of device objects in a dict.

    Uses `adb devices` to gather a list of devices.
    TODO: make a connection to the SQLite database to acquire 
    the current fuzzing status.
    """
    if not testadb():
        return {'Error':'Is adb on your PATH?'}
    initbrowsers()
    devproc = Popen(['adb', 'devices'], stdout=PIPE, stderr=PIPE)
    lines = devproc.stdout.readlines()
    conn = sqlite3.connect(DBNAME)
    devices = []
    for line in lines[1:-1]: #Skip header line, and empty line.
        #print("ADB devices:%s" % line)
        if b'daemon started' in line or b'List of devices' in line:
            continue
        outvals = line.strip().decode("utf-8").split()
        name = outvals[0]
        devicetype = outvals[1] if len(outvals) > 1 else 'unknown'
        logfile = getlog(name) #+ "-device.log"
        device = {'name':name, 'type':devicetype, 'fuzzing':False}
        #print('name',name)
        device['browsers'] = getbrowsers(name)
        curs = conn.cursor()
        """
        TODOs:
        - Get current fuzzing status.
        """
        try:
            curs.execute("INSERT INTO devices VALUES (?,?,?)",
                         (name, devicetype, logfile))
        except sqlite3.IntegrityError:
            pass #Constraint isn't unique
        devices.append(device)
    conn.commit()
    return devices

def getlog(devname):
    return os.path.join(CONFIG['logsdir'], devname + "-log.txt")

