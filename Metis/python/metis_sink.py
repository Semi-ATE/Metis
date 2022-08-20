
import sys
import gi
import os
import h5py
import time
import logging
import numpy as np
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

        

class metis_sink(GstBase.BaseSink, MetisConfig):
    __gstmetadata__ = ("Sink data",
                       "Transform",
                       "Writes stdf files into hdf5 file",
                       'vboy')

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
        self.off = 0
        self.first_lot = True
        self.file_off = 0
        self.lot = ""
        self.hdf_path = ""
        self.time1 = time.time()
        self.time2 = time.time()
        self.queue = bytearray()
        self.file = None
        
        MetisConfig.__init__(self)
        
    def do_start(self):
        logging.info(f'Sink started, file:{self.filename} ,time:{datetime.now()}.')
        return True

    def do_get_property(self, prop):
         if prop.name == 'file-name':
             return self.filename
         else:
             logging.error(f'Unknown property, property name:{prop.name}, file:{self.filename}, time:{datetime.now()}.')
             raise AttributeError('unknown property %s' % prop.name) 
                      
    def do_set_property(self, prop, value):
         if prop.name == 'file-name':
             self.filename = value
         else:
             logging.error(f'Unknown property, property name:{prop.name}, file:{self.filename}, time:{datetime.now()}.')
             raise AttributeError('unknown property %s' % prop.name)
             
    
    def do_render(self, buffer):
        
        if self.file == None:
            self.file = open(self.filename, "ba")
    
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

                my_data = info.data[0:flen+4].tobytes()

                self.file.write(my_data)                
                self.file.flush()
                
                if self.lot == "":    
                    self.queue += my_data
                
                if b_type == 1 and b_sub == 10 and self.lot == "":
                    len_lot_id = my_data[19]
                    
                    for i in range(len_lot_id):
                        self.lot += chr(my_data[20+i])
                    
                    self.time1 = time.time()
                    logging.debug(f'Sink LOT_ID found, file:{self.filename}, lot-id:{self.lot}, time:{datetime.now()}.')
                
                
                if self.lot != "":
                    path_yam = self.config['metis']['paths']['write-path'] 
                    hdf_path = path_yam + self.lot + '.h5'
                    
                    count = flen+4

                    with h5py.File(hdf_path, 'a') as output_file:
                        if os.path.basename(self.filename) not in output_file.keys():
                            ds = output_file.create_dataset(os.path.basename(self.filename), (0,1), maxshape=(None,1), dtype='u1', chunks=True)
                            data = np.frombuffer(self.queue, dtype='u1', count = -1)
                        else:
                            name = os.path.basename(self.filename)
                            ds = output_file[name]
                        
                            data = np.frombuffer(my_data, dtype='u1', count = count)   
                            
                        readed = len(data)
                        
                        ds.resize(self.off+readed,0)
                        
                        ds[self.off:self.off+readed,0] = data
                        self.off = self.off + readed

                # Check for MRR record - end of file
                if b_type == 1 and b_sub == 20:
                            
                   #print("test_sink : EOF")
                    logging.info(f'Sink EOF, file:{self.filename}, time:{datetime.now()}.')
                    
                    print("final time since lot id:")
                    print(time.time() - self.time1)
                    return Gst.FlowReturn.OK
                
        except Exception as e:
            logging.error(f'Mapping error {e}, file:{self.filename}, time:{datetime.now()}.')
            Gst.error("Mapping error: %s" % e)
            return Gst.FlowReturn.ERROR
            
        return Gst.FlowReturn.OK


GObject.type_register(metis_sink)
__gstelementfactory__ = ("metis_sink", Gst.Rank.NONE, metis_sink)
