#!/bin/sh
echo "Pulling submodule(s)."
git submodule init
git submodule update
echo "Starting fuzzing server..."
tmux new-session -d "DomatoADB Server" \; \
	split-window "python3 harness.py; read" \; \
	split-window "python3 flask_app.py; read" \; \
	select-layout even-vertical
