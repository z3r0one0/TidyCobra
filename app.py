from os.path import expanduser
from pathlib import Path
from .GUI import view_main

def run():
    print("Welcome to TidyCobra!")
    view_main.render_GUI()