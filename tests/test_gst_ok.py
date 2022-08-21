import os
test_loc = os.path.dirname(__file__)
from pathlib import Path
root_loc = Path(test_loc).parent
os.environ['GST_PLUGIN_PATH'] = os.path.join(root_loc, "Metis")
#print(f"test_gst.ok GST_PLUGIN_PATH = {os.environ['GST_PLUGIN_PATH']}")

import gi
import threading
import filecmp
import sys

from Metis.sinotify import start_stream

gi.require_version('Gst', '1.0')
from gi.repository import Gst

# The file from which we will read and write into src_file to stimulate inotify
org_file = os.path.join(test_loc, "test.std")
src_file = os.path.join(test_loc,  "test.std.src")
dst_file = os.path.join(test_loc, "test.std.dst")
yaml_file = os.path.join(test_loc, "test_metisd.yaml")

def test_gst_pass():

    Gst.init(None)
    Gst.debug_set_active(True)
    Gst.debug_set_default_threshold(3)

    if os.path.exists(src_file):
        os.remove(src_file)

    if os.path.exists(dst_file):
        os.remove(dst_file)
    
    print(f"yaml_file {yaml_file}")
    thread = threading.Thread(target=start_stream, args=(src_file, dst_file, yaml_file))    
    
    byteorder = None

    with open(org_file, "rb") as in_file:
         while(True):
            out_file = open(src_file, "ab")
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

    res = filecmp.cmp(org_file, dst_file, shallow=False)
    assert res == True
    
    if os.path.exists(src_file):
        os.remove(src_file)
