import os
import sys

INTERP = os.path.expanduser("~/venv/bin/python3.8")

if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

