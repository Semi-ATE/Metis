import os
import sys
import time
import logging
from yaml import safe_load, dump 
from datetime import datetime

file_loc = os.path.dirname(__file__)
test_loc = os.path.join(file_loc, "../test_metisd.yaml")

class MetisConfig():

    def __init__(self):
        
        self.config = self.load_config()

        if self.config['metis']['log']['logging'] == True:
            loglevel = self.config['metis']['log']['log-level']
            numeric_level = getattr(logging, loglevel.upper(), None)
            log_path = self.config['metis']['log']['log-path']
            logging.basicConfig(filename=log_path, filemode='a', level=numeric_level)

    def load_config(self):
        """Loads yaml file"""
        try:
            # In the case of normal deamon mode:
            with open("/etc/metisd.yaml", "r") as f:
                config_data = safe_load(f)
                return config_data
        except Exception as e:
            # In the case of test mode:
            try:
                with open(test_loc, "r") as f:
                    config_data = safe_load(f)
                    return config_data
            except Exception as e:
                error = f'Could not open config file, {e}.'
                sys.exit(error)
            os._exit

