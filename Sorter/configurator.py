''' Manipulates configuration files for TidyCobra '''
from pubsub import pub
import json
import os

class Configurator():

    def __init__(self):
        # always read/write config.json in the same folder as this script
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        pub.subscribe(self.listener_configurator, "configuratorListener")

    def listener_configurator(self, message, arg2=None):
        ### Save config ###
        if message == "save_config":
            with open(self.config_path, 'w+') as f:
                json.dump(arg2, f)
        ### Load config ###
        elif message == "import_config":
            #TODO:implement
            return -1

    def load_config(self):
        if not os.path.isfile(self.config_path):
            raise FileNotFoundError(f"No config.json at {self.config_path}")
        with open(self.config_path) as f:
            config = json.load(f)
            return config


