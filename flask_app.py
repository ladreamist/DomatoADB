# -*- coding: utf-8 -*-
"""DomatoADB Flask Server

This module contains the Flask app that shall provide a backend for
fuzzing mobile browsers. This project has largely been built
in order for me to further understand the development of
fuzzers and harnesses.

To run:
    $ FLASK_APP=flask_app.py flask run --host=0.0.0.0

"""
import sqlite3
import os
import string
import sys
import random
import time
from datetime import datetime

from flask import (Flask, request, jsonify, make_response,
                   send_from_directory, redirect)
from os.path import isfile, isdir
from subprocess import Popen, PIPE

from utils import (generatedatabase, getdevices, getbrowsers,
                   getdeviceid, forwardlocalhosts, updatebrowserfuzz,
                   launchbrowser, CONFIG)

sys.path.insert(0, 'domato/') #Depends on domato right now.
import generator

DBNAME = 'fuzz.db'
RUNSDIR = 'fuzzruns'
LOGS = []
HOST = CONFIG['host']
PORT = CONFIG['port']

app = Flask(__name__)

STATIC = 'static'


def gen_cookie():
    """ Generate a random alphanumeric cookie. """
    return ''.join(random.choice(string.ascii_lowercase + string.digits)\
            for _ in range(20))


@app.route("/devices")
def devices():
    """"
    Returns a list of device objects in JSON format.

    Uses `adb devices` to gather a list of devices, and makes
    a connection to the SQLite database to acquire the current fuzzing
    status.
    """
    return jsonify(getdevices())


@app.route("/generaterun")
def generaterun(iterations=50, engine="domato"):
    """Create a new fuzzrun directory."""
    if not isdir(RUNSDIR):
        os.mkdir(RUNSDIR)
    newrun = os.path.join(RUNSDIR, str(int(time.time())))
    os.mkdir(newrun)
    print("Generated dir:{}.".format(newrun))
    outfiles = []
    base = "fuzz-%d.html"
    for i in range(iterations):
        outfiles.append(os.path.join(newrun, base % i))
        print("Generating %s" % outfiles[i])
    generator.generate_samples("domato", outfiles)
    with sqlite3.connect(DBNAME) as conn:
        curs = conn.cursor()
        curs.execute('INSERT INTO fuzzruns VALUES (?, ?)', (newrun, iterations))
    res = {'output':newrun}
    return jsonify(res)


@app.route("/launchadb")
@app.route("/launchadb/<string:devicename>")
@app.route("/launchadb/<string:devicename>/<string:browser>")
def launchadb(devicename=None, browser=None):
    """Launches a device browser through ADB.
        Returns a JSON string either representing success,
        an error, or a request for more information.

        When no browser is given, a list of available browsers
        for that device should be provided."""
    #Get browsers for that device if none
    if devicename == None:
        return jsonify({'output':'You must select a device.'})
    if browser == None:
        return jsonify({'output':'Must choose a browser manually for now.'})
    return jsonify(launchbrowser(devicename, browser))


@app.route("/begin")
@app.route("/begin/<string:devicename>")
def beginfuzz(devicename=None):
    """
    Initiate fuzzing for a given browser visiting this endpoint.
    """
    
    if not devicename:
        return make_response("Need a devicename, sorry.")
    
    resp = make_response("""
    <html><body>
        <p>Prepare to begin!</p>
        <script>window.location = "/fuzz";</script>
    </body></html>
    """)
    #Get user agent
    useragent = request.headers.get('User-Agent')
    deviceid = getdeviceid(devicename)
    #Low probability of collision, unique to each browser
    browsercookie = gen_cookie() 
    
    #Check for cookie already stored for this device
    cookie = request.cookies.get("fuzzID")
    if not cookie:
        resp.set_cookie("fuzzID", value=browsercookie)
        resp.set_cookie("fuzzrun", value="1")
        resp.set_cookie("fuzzcount", value="0")
        resp.set_cookie("deviceid", value=deviceid)
    return resp


@app.route("/fuzz")
def fuzztest():
    """Get to fuzzing."""
    fuzzID = request.cookies.get("fuzzID")
    run = request.cookies.get("fuzzrun")
    count = request.cookies.get("fuzzcount")
    print("Request cookies:",request.cookies)
    path   = None
    if run == None or count == None:
        print("Redirecting to /begin, run:%s,count:%s" % (run,count))
        return redirect('/begin')
    
    with sqlite3.connect(DBNAME) as conn:
        curs = conn.cursor()
        #Get greatest fuzzrun rowid
        curs.execute("SELECT COUNT(rowid) FROM fuzzruns")
        row = curs.fetchone()
        if int(run) >= row[0]:
            print("Need to generate a new run...")
            generaterun()
        curs.execute("""SELECT run_label, iterations 
            FROM fuzzruns where rowid = ?""", (run,))
        row = curs.fetchone()
        path = row[0]
        if int(count) >= row[1]:
            run = int(run) + 1
            count = 0
            curs.execute("""SELECT run_label, iterations 
                FROM fuzzruns where rowid = ?""", (run,))
            path = curs.fetchone()[0]
        resp = send_from_directory(path, \
                "fuzz-%d.html" % int(count) )
        #Store test return
        updatebrowserfuzz(fuzzID, run)
        count = int(count) + 1
        path = row[0]
        resp.set_cookie("fuzzcount", value=str(count))
        resp.set_cookie("fuzzrun", value=str(run))
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Last-Modified"] = datetime.now()
        resp.headers["Cache-Control"] = \
                "no-cache, no-store, must-revalidate, " + \
                "post-check=0, pre-check=0, max-age=0"
        resp.headers['Expires'] = '-1'
        #Do a reload patch...
        resp.direct_passthrough = False
        data = resp.get_data().split()
        data.insert(-1, b"""
        <script>setTimeout(function(){window.location.reload();}, %d);</script>
        """ % (int(CONFIG['force-reload']) * 1000))
        resp.set_data(''.join([d.decode('utf-8') for d in data]))
        print("Response length:",len(resp.get_data()))
        return resp


@app.route("/panel")
def view():
    return make_response("On the TODO")


@app.route("/index")
@app.route("/")
def index():
    if not isfile(DBNAME):
        generatedatabase()
    return send_from_directory(STATIC, 'index.html')


@app.route('/<path:path>')
def servestatic(path):
    return send_from_directory(STATIC, path)


if __name__ == "__main__":
    #Popen(['adb', 'reverse', '--remove-all'])
    #Popen(['adb', 'reverse', 'tcp:80', 'tcp:' + str(PORT)])
    forwardlocalhosts(PORT)
    app.run(host=HOST, port=PORT)
