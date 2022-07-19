#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 17:22:18 2022

@author: nz
"""


import gi
import time
import sys

gi.require_version("Gst", "1.0")
gi.require_version('GstBase', '1.0')

from gi.repository import Gst, GObject, GstBase
Gst.init(None)


class metis_process(GstBase.BaseTransform):
    __gstmetadata__ = ("Process plugin",
                       "Transform",
                       "Process stdf content if required",
                       "vboy")

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.new_any()),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.new_any()))


    def __init__(self):
        GstBase.BaseTransform.__init__(self)
#        self.max_needed_buffer_size = 65536
        #super().set_blocksize(self.max_needed_buffer_size)

    def do_set_property(self, prop, value):
        if prop.name == 'in_file':
            self.in_file = value
        
    def do_start(self):
        print("Metis process plugin started")
        return True    

    #Passthrough mode
    #Element has no interest in modifying the buffer. 
    #It may want to inspect it, in which case the element should have a transform_ip function. 
    #If there is no transform_ip function in passthrough mode, the buffer is pushed intact.
    def do_transform_ip(self, buf):
        pass
    #def do_transform(self, inbuf, outbuf):
#        print("Sending.")
        #try:
            #buf.memset(0, 0, self.max_needed_buffer_size)
            #with buf.map(Gst.MapFlags.READ) as info:
             #   buffer = info.data.copy()
              #  print("dasd")
        
        #except Exception as e:
         #   Gst.error("Mapping error: %s" % e)
          #  return Gst.FlowReturn.ERROR

        return (Gst.FlowReturn.OK, buf)
    

# Register plugin to use it from command line
GObject.type_register(metis_process)
__gstelementfactory__ = ("metis_process", Gst.Rank.NONE, metis_process)
