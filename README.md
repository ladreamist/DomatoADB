# DomatoADB
Server for fuzzing Android browsers. Originally built with Domato as a core
component for generating HTML, CSS, and JS, with plans soon to move Domato related
code to a driver, interchangable with other generators.

# Issues
- Fuzzing isn't yet hands free. Need to work on launching pages after crashes, and diagnosing.
- Older devices experience OOM crashes very easily in Chrome. But it's preferable to keep hardware cheap.


# Current Roles:
1. Frontend Server (flask_app.py)
- Serves content of user interface.
- Initializes database.
2. Backend harness
- Loops through all connected devices
- Monitors logs to catch SIGSEGV signals
- TODO: Extracts tombstones from device that had crashed, appends testcase to filename if possible.
3. Utility Code
- Code shared in common between the frontend and the harness.
- Database functions for startups.
- Launching browsers on devices through ADB.
4. Drivers (TODO)
- Separates the server and harness code from Domato such that any generative fuzzing tech could be used in its place.

# Steps to use:
- Install tmux (optional), and ADB for your platform.
- Run `./start.sh`, or (sans tmux) run flask_app.py and harness.py with Python 3.
- Connect devices to ADB.
- Wait for device to appear, and click on ADB besides it to begin fuzzing.

# TODO:
- Separate ADB and harness backend from frontend server.
- Consider using named pipes for communication with backend.
- Use pydoc, document everything.
- Separate use of domato into a driver.
- Fix bugs that happen because SQLite database is being used for a separate device's fuzzing.
- Find out why crashes in Binder request "invalid crash size 0". Whenever this happens, no tombstone gets created. :/
