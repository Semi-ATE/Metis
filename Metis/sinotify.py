#!/usr/bin/python

import inotify.adapters
import os
import sys
import gi
from yaml import safe_load 
from datetime import datetime
import threading
import logging

gi.require_version('Gst', '1.0')
from gi.repository import Gst

def _main():
    here = os.path.realpath(__file__)
    
    here = os.path.dirname(here)
    
    os.environ['GST_PLUGIN_PATH'] = here 

    conf_data = yaml_loader("/etc/metisd.yaml")
    
    if conf_data['metis']['log']['logging'] == True:
        loglevel = conf_data['metis']['log']['log-level']
        numeric_level = getattr(logging, loglevel.upper(), None)
        logging.basicConfig(filename = conf_data['metis']['log']['log-path'], filemode='a', level=numeric_level)
    
    
    logging.info(f'Stdf-inotify has started, time:{datetime.now()}.')
    
    Gst.init(None)
    Gst.debug_set_active(True)
    Gst.debug_set_default_threshold(3)    
    
    watch_list = []
    sink_list = []
    threads = []

    path = conf_data['metis']['paths']['main-daemon-path']
    write_path = conf_data['metis']['paths']['write-path']
    files = os.listdir(path)
    i = inotify.adapters.InotifyTree(path) 
    #add already existing files to watch list

    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        out_sink = os.path.join(write_path, str(filename) + ".sink")
        sink_list.append(out_sink)
        
        if filename == "exit.exit":
            logging.info(f"Stdf-inotity exit, exit file created, time:{datetime.now()}.")
            os.remove(str(path+'/'+filename))
            sys.exit(0)
        
        if_write_event = False
        
        if (str(type_names) == "['IN_CREATE']" or str(type_names) == "['IN_MODIFY']"):
            if_write_event = True
        
        is_file_not_in_watch_list = False
        if (filename not in watch_list):
            is_file_not_in_watch_list = True
        
        if if_write_event and is_file_not_in_watch_list:
            file_path = str(path + '/' + str(filename))
            print(str(filename))
            
            if not os.path.isdir(file_path):
                watch_list.append(filename)
                
                th = threading.Thread(target=start_stream, args=(file_path, out_sink, None))
                th.daemon = True # Thread dies when main thread (only non-daemon thread) exits.

                th.start()
                
                logging.info(f'Started thread,  file:{file_path}, time:{datetime.now()}.')
        
#starts gstreamer  
def start_stream(src_file, out_sink, conf_file):

#    Gst.init(None)
#    Gst.debug_set_active(True)
#    Gst.debug_set_default_threshold(5)        

    print(f"start stream conf {conf_file}")
    conf_data = yaml_loader(conf_file)
    
    if conf_data['metis']['log']['logging'] == True:
        loglevel = conf_data['metis']['log']['log-level']
        numeric_level = getattr(logging, loglevel.upper(), None)
        logging.basicConfig(filename = conf_data['metis']['log']['log-path'], filemode='a', level=numeric_level)
        
    # initialize GStreamer
    # create the elements
    source = Gst.ElementFactory.make("metis_source", "metis_source")
    if not source:
        print(f'Can not find source plugin,  file:{src_file}, time:{datetime.now()}.')
        logging.error(f'Can not find source plugin,  file:{src_file}, time:{datetime.now()}.')
        sys.exit(1)
        
    mid = Gst.ElementFactory.make("metis_process", "metis_process")
    if not mid:
        print(f'Can not find mid plugin,  file:{src_file}, time:{datetime.now()}.')
        logging.error(f'Can not find mid plugin,  file:{src_file}, time:{datetime.now()}.')
        #print("ERROR: Can not find mid plugin")
        sys.exit(1)

    sink = Gst.ElementFactory.make("metis_sink", "metis_sink")
    if not sink:
        print(f'Can not find sink plugin,  file:{src_file}, time:{datetime.now()}.')
        logging.error(f'Can not find sink plugin,  file:{src_file}, time:{datetime.now()}.')
        #print("ERROR: Can not find sink plugin")
        sys.exit(1)

    # create the empty pipeline
    pipeline = Gst.Pipeline.new("test-pipeline")
    

    if not pipeline:
        logging.error(f'Can not create pipeline,  file:{src_file}, time:{datetime.now()}.')
        #print("ERROR: Can not create pipeline")
        sys.exit(1)

    source.set_pipeline(pipeline)

    # build the pipeline
    pipeline.add(source, mid, sink)
    if not source.link(mid):
        logging.error(f'Can not link source to mid,  file:{src_file}, time:{datetime.now()}.')
        #print("ERROR: Could not link source to mid")
        sys.exit(1)

    if not mid.link(sink):
        logging.error(f'Can not link mid to sink,  file:{src_file}, time:{datetime.now()}.')
        #print("ERROR: Could not link mid to sink")
        sys.exit(1)

    #modify the source's properties
    source.set_property("file-name", src_file)

    sink.set_property("file-name", out_sink)

    # start playing
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        logging.error(f'Unable to set the pipeline to playing state,  file:{src_file}, time:{datetime.now()}.')
        #print("ERROR: Unable to set the pipeline to the playing state")

    # wait for EOS or error
    bus = pipeline.get_bus()
    while True:
        msg = bus.timed_pop_filtered(
            Gst.CLOCK_TIME_NONE,
            Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR | Gst.MessageType.EOS
            )
    
        if msg:
            t = msg.type
            if t == Gst.MessageType.ERROR:
                err, dbg = msg.parse_error()
                #print("ERROR:", msg.src.get_name(), ":", err.message)
                logging.error(f'{msg.src.get_name()}:{err.message},  file:{src_file}, time:{datetime.now()}.')
            elif t == Gst.MessageType.EOS:
                #print("End-Of-Stream reached")
                logging.info(f'End of Stream reached,  file:{src_file}, time:{datetime.now()}.')
            elif t == Gst.MessageType.STATE_CHANGED:
                old_state, new_state, pending_state = msg.parse_state_changed()
                if old_state == Gst.State.PLAYING and new_state == Gst.State.PAUSED:
                    break;
            else:
                # this should not happen. we only asked for ERROR and EOS
                #print(f"ERROR: Unexpected message received : {msg}")
                logging.error(f'Unexpected message received, msg:{msg}  file:{src_file}, time:{datetime.now()}.')

    #print(f"End of transfering {src_file}")
    logging.info(f'End of transfering,  file:{src_file}, time:{datetime.now()}.')
    pipeline.set_state(Gst.State.NULL)


def yaml_loader(conf_file):
    """Loads yaml file"""
    if conf_file == None:
        conf_file = "/etc/metisd.yaml"
    with open(conf_file, "r") as f:
        data = safe_load(f)
        return data

if __name__ == '__main__':
    _main()

