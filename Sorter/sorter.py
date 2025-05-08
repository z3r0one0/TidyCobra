'''Handles sorting logic for TidyCobra'''
from . import configurator
import glob, os, shutil
from datetime import datetime

class Sorter:

    def fix_duplicate(self,path):
        # hacky way to handle path duplication
        new_name = path.split(".")
        new_name[0] += "_duplicate" + str(int(datetime.timestamp(datetime.now()))%1000000)
        return ".".join(new_name)

    def sort(self,path_destination,extensions):
        for extension in extensions:
            print(extension)
            for file in glob.glob("*"+extension):
                print(file)
                current_file_path = os.path.join(self.path_downloads, file)
                new_file_path = os.path.join(path_destination, file)
                if os.path.isfile(new_file_path):
                    new_file_path = self.fix_duplicate(new_file_path)

                shutil.move(current_file_path,new_file_path)
        print(f"Done sorting {', '.join(extensions)} files to {path_destination}")


    def __init__(self):
        cfg = configurator.Configurator()
        self.config = cfg.load_config()
        self.path_downloads = self.config["path_downloads"]
        old_path = os.getcwd()
        os.chdir(self.path_downloads)
        print("path_dw:",self.path_downloads,"current dir",os.getcwd())
        for rule in self.config["rules"]:
            path_destination = rule[0]
            extensions = rule[1].split(' ')
            print(path_destination, extensions)
            self.sort(path_destination, extensions)
        os.chdir(old_path)