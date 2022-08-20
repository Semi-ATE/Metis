import os
test_loc = os.path.dirname(__file__)
root_loc = os.path.join(test_loc, "..")
os.environ['GST_PLUGIN_PATH'] = os.path.join(root_loc, "Metis")
print(f"GST_PLUGIN_PATH = {os.environ['GST_PLUGIN_PATH']}")

import gi
import time
import threading
import filecmp
import sys
import stat

from Metis.sinotify import start_stream

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject

# The file from which we will read and write into src_file to stimulate inotify
org_file = os.path.join(test_loc, "test.std")
src_file1 = os.path.join(test_loc,  "test.std.src1")
src_file2 = os.path.join(test_loc,  "test.std.src2")
src_file3 = os.path.join(test_loc,  "test.std.src4")
src_file4 = os.path.join(test_loc,  "test.std.src5")
dst_file = os.path.join(test_loc, "test.std.dst")
yaml_file = os.path.join(test_loc, "test_metisd.yaml")
wrong_yaml_file = os.path.join(test_loc, "nometisd.yaml")

def test_config_not_exist():
    
    Gst.init(None)
    Gst.debug_set_active(True)
    Gst.debug_set_default_threshold(3)

    if os.path.exists(src_file1):
        os.remove(src_file1)

    if os.path.exists(dst_file):
        os.remove(dst_file)
    
    thread = threading.Thread(target=start_stream, args=(src_file1, dst_file, yaml_file))
    
    byteorder = None
    
    with open(org_file, "rb") as in_file:
         while(True):
            out_file = open(src_file1, "ab")
            # Get record length
            rec_len = in_file.read(2)
            # EOF reached
            if not rec_len:
                break
            # Get record type
            rec_type = in_file.read(1)
            # Get record sub-type
            rec_subtype = in_file.read(1)

            if byteorder == None:
                bo = in_file.read(1)
                if bo == b'\x01':
                    byteorder = 'big'
                elif bo == b'\x02':
                    byteorder = 'little'
                else:
                    byteorder = sys.byteorder
                ver = in_file.read(1)

                len_rec = int.from_bytes(rec_len, byteorder)

                
                os.rename(yaml_file, wrong_yaml_file)
                try:
                    thread.start()
                except:
                    os.rename(wrong_yaml_file, yaml_file)

                out_file.write(rec_len)
                out_file.write(rec_type)
                out_file.write(rec_subtype)
                out_file.write(bo)
                out_file.write(ver)
                out_file.close()
                    
            else:
                len_rec = int.from_bytes(rec_len, byteorder)
                # Get rest of the record
                rec = in_file.read(len_rec)

                out_file.write(rec_len)
                out_file.write(rec_type)
                out_file.write(rec_subtype)
                out_file.write(rec)
                out_file.close()
    
    res = os.path.exists(dst_file)
    if os.path.exists(wrong_yaml_file):
        os.rename(wrong_yaml_file,yaml_file)

    assert res == False

    if os.path.exists(src_file1):
        os.remove(src_file1)

def test_negative_byteorder():

    Gst.init(None)
    Gst.debug_set_active(True)
    Gst.debug_set_default_threshold(3)
    
    if os.path.exists(src_file2):
        os.remove(src_file2)

    if os.path.exists(dst_file):
        os.remove(dst_file)
     
    thread = threading.Thread(target=start_stream, args=(src_file2, dst_file, yaml_file))
    
    byteorder = None

    with open(org_file, "rb") as in_file:
         while(True):
            out_file = open(src_file2, "ab")
            # Get record length
            rec_len = in_file.read(2)
            # EOF reached
            if not rec_len:
                break
            # Get record type
            rec_type = in_file.read(1)
            # Get record sub-type
            rec_subtype = in_file.read(1)

            if byteorder == None:
                bo = in_file.read(1)
                if bo == b'\x01':
                    byteorder = 'big'
                elif bo == b'\x02':
                    byteorder = 'little'
                else:
                    byteorder = sys.byteorder
                ver = in_file.read(1)

                len_rec = int.from_bytes(rec_len, byteorder)

                out_file.write(rec_len)
                out_file.write(rec_type)
                out_file.write(rec_subtype)
                
                out_file.write(b'\x03')
                
                out_file.write(ver)
                out_file.close()
                
                thread.start()
            else:
                len_rec = int.from_bytes(rec_len, byteorder)
                # Get rest of the record
                rec = in_file.read(len_rec)

                out_file.write(rec_len)
                out_file.write(rec_type)
                out_file.write(rec_subtype)
                out_file.write(rec)
                out_file.close()

    res = os.path.exists(dst_file)
    assert res == False

    if os.path.exists(src_file2):
        os.remove(src_file2)

    
def test_negative_exist():

    Gst.init(None)
    Gst.debug_set_active(True)
    Gst.debug_set_default_threshold(3)
    
    if os.path.exists(src_file3):
        os.remove(src_file3)

    if os.path.exists(dst_file):
        os.remove(dst_file)
     
    thread = threading.Thread(target=start_stream, args=(src_file3, dst_file, yaml_file))
    
    byteorder = None

    with open(org_file, "rb") as in_file:
         while(True):
            out_file = open(src_file3, "ab")
            # Get record length
            rec_len = in_file.read(2)
            # EOF reached
            if not rec_len:
                break
            # Get record type
            rec_type = in_file.read(1)
            # Get record sub-type
            rec_subtype = in_file.read(1)

            if byteorder == None:
                bo = in_file.read(1)
                if bo == b'\x01':
                    byteorder = 'big'
                elif bo == b'\x02':
                    byteorder = 'little'
                else:
                    byteorder = sys.byteorder
                ver = in_file.read(1)

                len_rec = int.from_bytes(rec_len, byteorder)

                out_file.write(rec_len)
                out_file.write(rec_type)
                out_file.write(rec_subtype)
                out_file.write(bo)
                out_file.write(ver)
                out_file.close()
                
                os.remove(src_file3)
                
                thread.start()
    
                break;
                
    res = os.path.exists(dst_file)
    assert res == False

    if os.path.exists(src_file3):
        os.remove(src_file3)

def test_negative_version():

    Gst.init(None)
    Gst.debug_set_active(True)
    Gst.debug_set_default_threshold(3)
    
    if os.path.exists(src_file4):
        os.remove(src_file4)

    if os.path.exists(dst_file):
        os.remove(dst_file)
     
    thread = threading.Thread(target=start_stream, args=(src_file4, dst_file, yaml_file))
    
    byteorder = None

    with open(org_file, "rb") as in_file:
         while(True):
            out_file = open(src_file4, "ab")
            # Get record length
            rec_len = in_file.read(2)
            # EOF reached
            if not rec_len:
                break
            # Get record type
            rec_type = in_file.read(1)
            # Get record sub-type
            rec_subtype = in_file.read(1)

            if byteorder == None:
                bo = in_file.read(1)
                if bo == b'\x01':
                    byteorder = 'big'
                elif bo == b'\x02':
                    byteorder = 'little'
                else:
                    byteorder = sys.byteorder
                ver = in_file.read(1)
                ver = b'\x03'

                len_rec = int.from_bytes(rec_len, byteorder)

                out_file.write(rec_len)
                out_file.write(rec_type)
                out_file.write(rec_subtype)
                out_file.write(bo)
                out_file.write(ver)
                out_file.close()
                
                thread.start()
            else:
                len_rec = int.from_bytes(rec_len, byteorder)
                # Get rest of the record
                rec = in_file.read(len_rec)

                out_file.write(rec_len)
                out_file.write(rec_type)
                out_file.write(rec_subtype)
                out_file.write(rec)
                out_file.close()

    res = os.path.exists(dst_file)
    assert res == False
    if os.path.exists(src_file4):
        os.remove(src_file4)
