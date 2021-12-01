import json


class ConfigReader:
    def __init__(self, config_path):
        self.config_path = config_path
        self.load_config(self.config_path)

    def load_config(self, path):
        with open (path, 'r') as f:
            self.from_dict(json.load(f))

    def from_dict(self, dict):
        self.__dict__.update(dict)