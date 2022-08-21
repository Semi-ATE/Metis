#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml
import gi
import sys
import inotify.adapters
import os
import logging
from datetime import datetime

try:
    from .MetisConfig import MetisConfig
except:
    cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, cwd)
    from MetisConfig import MetisConfig
    
file_loc = os.path.dirname(__file__)

gi.require_version("Gst", "1.0")
gi.require_version('GstBase', '1.0')

from gi.repository import Gst, GObject, GstBase
Gst.init(None)                        

class metis_source(GstBase.BaseSrc, MetisConfig):
    __gstmetadata__ = ("Source data",
                       "Transform",
                       "Metis gstreamer plugin to source binary data",
                       'vboy')

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.new_any()))
    
    __gproperties__ = {"file-name":(str,  # GObject.TYPE_*
                                     "file-name", # str
                                     "name of file from wich we will copy data",  # str
                                     "test.std",  # any
                                     GObject.ParamFlags.READWRITE)}

    def __init__(self):
        GstBase.BaseSrc.__init__(self)
        self.set_live(True)
        self.tested = False
        self.max_needed_buffer_size = 65536
        super().set_blocksize(self.max_needed_buffer_size)
        self.byteorder = None
        self.i = 0
        self.my_offset = 0
        self.file_offset = 0
        self.in_file = "test.std"
        self.lot = ""
        
        MetisConfig.__init__(self)
        
    def do_get_property(self, prop):
        if prop.name == 'file-name':
            return self.in_file
        else:
            raise AttributeError('unknown property %s' % prop.name) 

    def do_set_property(self, prop, value):
        if prop.name == 'file-name':
            self.in_file = value
        else:
            raise AttributeError('unknown property %s' % prop.name)        

    def do_start (self):
        print("Metis source plugin started")
        
        self.l = inotify.adapters.Inotify()
        
        try:
            self.l.add_watch(self.in_file)
            self.file = open(self.in_file, "rb")
        except Exception as e:
            error = f"file could not be opened, file:{self.in_file}, error: {e}."
            print(error)
            sys.exit(error)
            os._exit
        
        self.my_offset = os.path.getsize(self.in_file)
        self.file_offset = 0
        self.rec_id = 0
        self.eof = False
        self.lot = None
        #print(f"Test source started {self.file}")
        logging.info(f'Source started, file:{self.in_file} ,time:{datetime.now()}.')
        
        return True
        
    def set_pipeline(self, pipeline):
        self.pipeline = pipeline

    def process_record(self, buf):
        b_len = self.file.read(2)
        b_type = self.file.read(1)
        b_sub = self.file.read(1)

        type = int.from_bytes(b_type, sys.byteorder)
        sub = int.from_bytes(b_sub, sys.byteorder)
                
        if self.byteorder == None:
            bo = self.file.read(1)
            if bo == b'\x01':
                self.byteorder = 'big'
            elif bo == b'\x02':
                self.byteorder = 'little'
            
            try:
                assert self.byteorder == 'little' or self.byteorder == 'big'
            except Exception as e:
                error = f'Wrong byteorder, file:{self.in_file}, {e}.'
                sys.exit(error)
                os._exit
            
            ver = self.file.read(1)
            # check for version. if not 4 -> exit
            rec_len = int.from_bytes(b_len, self.byteorder)
            self.file_offset += 4
                
            try:
                assert  ver == b'\x04'
            except Exception as e:
                error = f'Wrong file version, file:{self.in_file}, {e}.'
                sys.exit(error)
                os._exit
                
            with buf.map(Gst.MapFlags.WRITE | Gst.MapFlags.READ) as info:
                info.data[0] = b_len[0]
                info.data[1] = b_len[1]
                info.data[2] = type
                info.data[3] = sub
                info.data[4] = int.from_bytes(bo, self.byteorder)
                info.data[5] = int.from_bytes(ver, self.byteorder)
                
        else:
            rec_len = int.from_bytes(b_len, self.byteorder)
            #print(f"record length {rec_len}")
            rec = self.file.read(rec_len)
            if rec_len != len(rec):
                print(f"ERROR: Record not read fully : readed {len(rec)} bytes, but requested {rec_len} bytes!")
            self.file_offset += 4 + len(rec)
            
            # check for MIR record for the lot name
            if type == 1 and sub == 10 and self.lot == None:
                len_lot_id = rec[15]
                lot_id = rec[16:16+len_lot_id]
                self.lot = lot_id.decode('ascii')
                self.file_offset = 0
                self.file.seek(0)

            if len(rec) > 0:
                with buf.map(Gst.MapFlags.WRITE | Gst.MapFlags.READ) as info:
                    info.data[0] = b_len[0]
                    info.data[1] = b_len[1]
                    info.data[2] = type
                    info.data[3] = sub
                    
                    for b in range(len(rec)):
                        info.data[4+b] = rec[b]
                                
        if self.lot != None:
            self.rec_id += 1
        return type, sub
        
    def do_fill(self, offset, length, buf):
        
        self.queue = buf
        buf.memset(0, 0, self.max_needed_buffer_size)
        
        if self.lot != None:

            if self.eof:
                logging.info(f'Source do_file EOS, file:{self.in_file} ,time:{datetime.now()}.')
                self.pipeline.set_state(Gst.State.PAUSED)
                return Gst.FlowReturn.FLUSHING

            if os.path.getsize(self.in_file) > self.file_offset:
        
                type, sub = self.process_record(buf)
            
#                print(f"record number {self.rec_id} length {len} type {type} subtype {sub}")
#                print(f"1 type = {type} sub = {sub}")
            
                # Check for MRR record - end of file
                if type == 1 and sub == 20:
                    self.eof = True
                    logging.info(f'Source EOF, file:{self.in_file} ,time:{datetime.now()}.')
                    #print("test_source : EOF")
                return (Gst.FlowReturn.OK, buf)
            
        
        for event in self.l.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            
            if str(type_names) == "['IN_CLOSE_WRITE']" or str(type_names) == "['IN_OPEN']":
                logging.debug(f'Source file modified, file:{self.in_file} ,time:{datetime.now()}.')
                # in the case when more than one record was written at once
                while os.path.getsize(self.in_file) > self.file_offset:
                    
                    is_lot_found = False
                    if self.lot != None:
                        is_lot_found = True
                        
                    type, sub = self.process_record(buf)
#                    print(f"record number {self.rec_id} length {len} type {type} subtype {sub}")
#                    print(f"2 type = {type} sub = {sub}")

                    # Check for MRR record - end of file
                    if (type == 1 and sub == 20) or (type == 0 and sub == 0):
                        self.eof = True
                        logging.info(f'Source EOF, file:{self.in_file} ,time:{datetime.now()}.')
                        #print("test_source : EOF")
                    
                    if is_lot_found:
                        return (Gst.FlowReturn.OK, buf)
            
        return (Gst.FlowReturn.OK, buf)
            
GObject.type_register(metis_source)
__gstelementfactory__ = ("metis_source", Gst.Rank.NONE, metis_source)
