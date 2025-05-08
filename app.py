from os.path import expanduser
from pathlib import Path
from GUI import view_main
import glob

def run():
    print("Welcome to TidyCobra!")
    print("Downloads path is:",__name__)
    print(glob.glob("./*.txt"))
    view_main.render_GUI()