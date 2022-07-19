#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 08:46:55 2022

@author: nz
"""

import daemon
import os
import logging
import numpy as np
from yaml import safe_load, dump 
from datetime import datetime
import sys
from datetime import datetime
import signal
import sinotify
import lockfile

    
def shutdown(signum, frame):  # signum and frame are mandatory
    #open exit
    sys.exit(0)

def yaml_loader():
    """Loads yaml file"""
    filepath = "../../../etc/config.yaml"
    with open(filepath, "r") as f:
        data = safe_load(f)
        return data
       
data = yaml_loader()
log_path = data['metis']['log']['log-path']
log_type = data['metis']['log']['log-level']
is_log = data['metis']['log']['logging']
pid_path = data['metis']['paths']['pid-path']
logged = False

f = open(log_path, "a")

if (log_type == "INFO" or log_type == "DEBUG") and is_log == True:
    to_log = True

with daemon.DaemonContext(
        files_preserve=[f],
        stdout=sys.stdout,
        chroot_directory=None,
        working_directory='/mnt/stdf',
        signal_map={
            signal.SIGTERM: shutdown,
            signal.SIGTSTP: shutdown
        },
        pidfile=lockfile.FileLock(pid_path)
        ):
    
    if to_log and not logged:
        log = str("INFO:root: working-directory:" + os.getcwd() + f", daemon started, time:{datetime.now()} \n")
        print(log)
        logged = True
        f.write(log)

    try:
        os.system('python sinotify.py')
        print("inotify started")
    except:
        print("inotify failed")
        if to_log:
            log = str("CRITICAL:root: working-directory:" + os.getcwd() + f", daemon inotify crashed, time:{datetime.now()} \n")
            f.write(log)
            
            f.close()    
            sys.exit(0)
        
    f.close()        
            
                
    
    
    
    
    
    
    
    
    
    