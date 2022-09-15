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
import h5py
import collections

from yaml import safe_load, dump
from Metis.sinotify import start_stream
from Metis.tools.STDFHelper import STDFHelper

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
    
    with open(yaml_file) as f:
        list_doc = safe_load(f)
    list_doc['metis']['paths']['write-path'] = str(test_loc)
    with open(yaml_file, "w") as f:
        dump(list_doc, f)
    
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

    thread.join()
    res = filecmp.cmp(org_file, dst_file, shallow=False)
    assert res == True
    
    if os.path.exists(src_file):
        os.remove(src_file)

def test_h5py_types():

    with open(yaml_file, "r") as f:
        config_data = safe_load(f)

    org_file = os.path.join(test_loc, "test.std")
    hdf_path = config_data['metis']['paths']['write-path']
    hdf_name = str(STDFHelper.get_lot_id(org_file) + ".h5") 

    byteorder = STDFHelper.get_byteorder(org_file)
    types = []
    errors = []
    block_value = True
    types_with_count = {}
    with open(org_file, "rb") as f:
        while(True):
            rec_len = f.read(2)
            # EOF reached
            if not rec_len:
                break
            rec_typ = f.read(1)
            rec_sub = f.read(1)
            # Converting raw bytes to int
            typ_rec = int.from_bytes(rec_typ, byteorder)
            sub_rec = int.from_bytes(rec_sub, byteorder)
            len_rec = int.from_bytes(rec_len, byteorder)
            # Get rest of the record
            rec = f.read(len_rec)
            org_file = STDFHelper.get_stdf_record('V4', byteorder, rec_len, rec_typ, rec_sub, rec)
            rec_name = type(org_file).__name__
            #print(rec_name)
            
            if (rec_name not in types):
                if str(rec_name) != ( "PIR" or "EPS" ):
                    types_with_count[rec_name] = 1
            else:
                if str(rec_name) != ( "PIR" or "EPS" ):
                    types_with_count[rec_name] += 1

            types = list(dict.fromkeys(types_with_count))
        
    print(types)

    with h5py.File(os.path.join(hdf_path, hdf_name), 'a') as output_file:
        grp = output_file["/raw_stdf_data/test.std.dst"]
        hdf5_types = list(grp.keys())

        types_with_count = {key:val for key, val in types_with_count.items() if val != 1}
        
        for record in types_with_count:
            p = os.path.join("/raw_stdf_data/test.std.dst", record, "block0_values")
            dataframe_value = output_file[p]

            if dataframe_value.shape[0] != types_with_count[record]:
                print(types_with_count[record])
                print(record)
                block_value = False

    print(hdf5_types)

    # replace assertions by conditions
    if set(hdf5_types) != set(types):
        errors.append("Missing types in hdf5 file.")
    if not block_value:
        errors.append("Block values in dataframe are wrong.")

    # assert no error message has been registered, else print messages
    assert not errors, "errors occured:\n{}".format("\n".join(errors))
    
