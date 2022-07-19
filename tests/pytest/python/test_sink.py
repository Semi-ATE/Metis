#!/usr/local/bin/python3
import sys
import gi
import os
import h5py
import time
import numpy as np
from yaml import safe_load, dump 
gi.require_version("Gst", "1.0")
gi.require_version('GstBase', '1.0')

from os import path
from gi.repository import Gst, GObject, GstBase
Gst.init(None)

def yaml_loader():
    """Loads yaml file"""
    filepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], "config.yaml")
    
    try:
        with open(filepath, "r") as f:
            data = safe_load(f)
            return data
    except Exception as e:
        error = f'Could not open config file, {e}.'
        sys.exit(error)
        os._exit
    
class test_sink(GstBase.BaseSink):
    __gstmetadata__ = ("Sink data",
                       "Transform",
                       "Simple plugin to sink binary data",
                       'Seimit')

    __gsttemplates__ = (Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.new_any()))
    
    __gproperties__ = {"file-name":(str,  # GObject.TYPE_*
                                     "file-name", # str
                                     "name of file in wich we will paste",  # str
                                     "out.std",  # any
                                     GObject.ParamFlags.READWRITE)}

    def __init__(self):
        GstBase.BaseSink.__init__(self)
        self.filename = "out_sink.std"
        self.byteorder = ""
        self.file_offset = 0
        self.record = 0
        self.lot = ""

    def do_start(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)
        self.file = open(self.filename, "ba")
        self.file_read = open(self.filename, "rb")
        print("Test sink started")
        return True

    def do_get_property(self, prop):
         if prop.name == 'file-name':
             return self.filename
         else:
             raise AttributeError('unknown property %s' % prop.name) 
                      
    def do_set_property(self, prop, value):
         if prop.name == 'file-name':
             self.filename = value
         else:
             raise AttributeError('unknown property %s' % prop.name)
             
    def get_lot_id(self):##from stdf helper
        byteorder = self.byteorder
        
        with open(self.filename, "rb") as f:   
            while(True):
                rec_len = f.read(2)
                # EOF reached
                if not rec_len:
                    print("EOF reached")
                    return ''
                rec_typ = f.read(1)
                rec_sub = f.read(1)

                # Converting raw bytes to int
                typ_rec = int.from_bytes(rec_typ, byteorder)
                sub_rec = int.from_bytes(rec_sub, byteorder)
                
                if typ_rec == 1 and sub_rec == 10:
                #    # Skip 15 bytes, to get the lot_id
                    f.read(15)
                #    # length of the lot string in one byte
                    len_lot_id = f.read(1)
                    lot_id_len = int.from_bytes(len_lot_id, byteorder)
                    if lot_id_len > 0:
                        lot_id = f.read(lot_id_len)
                        return lot_id.decode('ascii')
                    else:
                        return ''
                else:
                    skip_bytes = int.from_bytes(rec_len, byteorder)
                    f.read(skip_bytes)         
    
    def do_render(self, buffer):
        try:
            with buffer.map(Gst.MapFlags.READ) as info:
               
               if self.byteorder == "":
                   if info.data[4] == 2:
                       self.byteorder = "little"
                   elif info.data[4] == 1:
                       self.byteorder = "big"
                   else:
                       self.byteorder = sys.byteorder
               
               if self.byteorder == "little": 
                   flen = info.data[1] << 8 | info.data[0]
               elif self.byteorder == "big":
                   flen = info.data[0] << 8 | info.data[1]
                                                       
               b_type = info.data[2]
               b_sub = info.data[3]
               #print(f"b_type {b_type} b_sub {b_sub}")
#             
                #https://docs.python.org/3/library/stdtypes.html#memoryview.tobytes

               data = info.data[0:flen+4].tobytes()
               
               self.file.write(data)                
               self.file.flush()
               
               if b_type == 1 and b_sub == 10 and self.lot == "":
                   self.lot = self.get_lot_id()
                   
               # Check for MRR record - end of file
               if b_type == 1 and b_sub == 20:
                   data = yaml_loader()
                   path_yam = data['metis']['paths']['write-path'] 
                   hdf_path = path_yam + self.lot + '.h5'
                   
                   with h5py.File(hdf_path, "a") as hdf5:
                       if 'backup' in hdf5.keys():
                           #print("echo1")
                           g = hdf5['backup']
                       else:
                           #print("echo2")
                           g = hdf5.create_group('backup')
                       
                       
                       file_cont = self.file_read.read() 
                       
                       # set up an HDF5 type appropriately sized for our data
                       dtype = h5py.h5t.create(h5py.h5t.OPAQUE, len(file_cont))
                       dtype.set_tag(b'binary/stdf')
                       
                       # set up a simple scalar HDF5 data space
                       space = h5py.h5s.create(h5py.h5s.SCALAR)
                       
                       # get dataset
                       ds = h5py.h5d.open(g.id, bytes(self.filename, 'utf-8')) or h5py.h5d.create(g.id, bytes(self.filename, 'utf-8'), dtype, space)
                        
                       # copy file cont in to dataset
                       ds.write(space, space, np.frombuffer(file_cont, dtype=np.uint8), dtype)
                        
                   print("test_sink : EOF")
                   self.file.close()
                   self.file_read.close()
                   return Gst.FlowReturn.OK
        except Exception as e:
            Gst.error("Mapping error: %s" % e)
            return Gst.FlowReturn.ERROR
            
        return Gst.FlowReturn.OK


GObject.type_register(test_sink)
__gstelementfactory__ = ("test_sink", Gst.Rank.NONE, test_sink)