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
        print(message)

        ### Save config ###
        if message == "save_config":
            print("received=", arg2)
            with open(self.config_path, 'w+') as f:
                json.dump(arg2, f)
            print(f"Configuration successfully saved to {self.config_path}")
        ### Load config ###
        elif message == "import_config":
            if arg2 and os.path.isfile(arg2):
                try:
                    config = self.validate_config_file(arg2)
                    if config:
                        pub.sendMessage("configImportResult", message="success", config=config)
                    else:
                        pub.sendMessage("configImportResult", message="invalid_format")
                except json.JSONDecodeError:
                    pub.sendMessage("configImportResult", message="invalid_json")
            else:
                pub.sendMessage("configImportResult", message="file_not_found")

    def validate_config_file(self, config_path):
        """Validates a config file format and checks paths"""
        with open(config_path) as f:
            config = json.load(f)
            
        # Check required fields
        if not isinstance(config, dict) or "path_downloads" not in config or "rules" not in config:
            return None
            
        # Check rules format
        if not isinstance(config["rules"], list):
            return None
            
        for rule in config["rules"]:
            if not isinstance(rule, list) or len(rule) != 2:
                return None
        
        # All validation passed
        return config

    def validate_paths(self, config):
        """Checks if paths in the config exist"""
        results = {
            "valid": True,
            "downloads_exists": os.path.isdir(config["path_downloads"]),
            "destination_paths": []
        }
        
        for rule in config["rules"]:
            dest_path = rule[0]
            results["destination_paths"].append({
                "path": dest_path,
                "exists": os.path.isdir(dest_path)
            })
            
        return results

    def load_config(self):
        if not os.path.isfile(self.config_path):
            raise FileNotFoundError(f"No config.json at {self.config_path}")
        with open(self.config_path) as f:
            config = json.load(f)
            return config


