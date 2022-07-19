import os
import gi
import time
import threading
import filecmp
import sys
import stat

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject
os.environ['GST_PLUGIN_PATH'] = getcwd()

org_file = getcwd() + "/test.std"
org_file1 = getcwd() + "/test1.std"
org_file2 = getcwd() + "/test2.std"
src_file = getcwd() + "/test.std.src"
dst_file = "/tmp/test.std.dst"
    
def gst_run():

    Gst.init(None)

    # create the elements
    source = Gst.ElementFactory.make("test_source", "test_source")
    if not source:
        print("ERROR: Can not find source plugin")
        sys.exit(1)

    mid = Gst.ElementFactory.make("test_mid", "test_mid")
    if not mid:
        print("ERROR: Can not find mid plugin")
        sys.exit(1)

    sink = Gst.ElementFactory.make("test_sink", "test_sink")
    if not sink:
        print("ERROR: Can not find sink plugin")
        sys.exit(1)

    # create the empty pipeline
    pipeline = Gst.Pipeline.new("test-pipeline")


    if not pipeline:
        print("ERROR: Can not create pipeline")
        sys.exit(1)

    source.set_pipeline(pipeline)

    # build the pipeline
    pipeline.add(source, mid, sink)
    if not source.link(mid):
        print("ERROR: Could not link source to mid")
        sys.exit(1)

    if not mid.link(sink):
        print("ERROR: Could not link mid to sink")
        sys.exit(1)

    print("PASS: Pipeline is up and running")
    
    source.set_property("file-name", src_file)
    sink.set_property("file-name", dst_file)
    
    # start playing
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("ERROR: Unable to set the pipeline to the playing state")

    print("Play the pipeline")
    # wait for EOS or error
    bus = pipeline.get_bus()
#    bus.connect("message", bus_message_handler)
    while True:
        msg = bus.timed_pop_filtered(
            Gst.CLOCK_TIME_NONE,
            Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR | Gst.MessageType.EOS
            )

        if msg:
            t = msg.type
            if t == Gst.MessageType.ERROR:
                err, dbg = msg.parse_error()
                print("ERROR:", msg.src.get_name(), ":", err.message)
            elif t == Gst.MessageType.EOS:
                print("End-Of-Stream reached")
                break
            elif t == Gst.MessageType.STATE_CHANGED:
                old_state, new_state, pending_state = msg.parse_state_changed()
                if old_state == Gst.State.PLAYING and new_state == Gst.State.PAUSED:
                    break
            else:
                # this should not happen. we only asked for ERROR and EOS
                print(f"ERROR: Unexpected message received : {msg}")

    print(f"End of transfering {src_file}")
    pipeline.set_state(Gst.State.NULL)
#    res = filecmp.cmp(org_file, dst_file, shallow=False)
#    assert res == False

def test_config_chmod():
    
    if os.path.exists(src_file):
        os.remove(src_file)

    if os.path.exists(dst_file):
        os.remove(dst_file)
    
    thread = threading.Thread(target=gst_run)
    
    byteorder = None
    record_counter = 0

    with open(org_file1, "rb") as in_file:
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
                
                os.chmod("config.yaml", 000)
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
    
            
    #thread.join()            
    #res = os.path.exists(dst_file)
    res = filecmp.cmp(org_file1, dst_file, shallow=False)
    os.chmod("config.yaml", stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    assert res == False

def test_config_exist():
    
    if os.path.exists(src_file):
        os.remove(src_file)

    if os.path.exists(dst_file):
        os.remove(dst_file)
    
    thread = threading.Thread(target=gst_run)
    
    byteorder = None
    record_counter = 0

    with open(org_file1, "rb") as in_file:
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
                
                os.rename('config.yaml','con.yaml')
                
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
    
            
    #thread.join()            
    #res = os.path.exists(dst_file)
    res = filecmp.cmp(org_file1, dst_file, shallow=False)
    os.rename('con.yaml','config.yaml')
    assert res == False
               
def test_negative_version():
    
    if os.path.exists(src_file):
        os.remove(src_file)

    if os.path.exists(dst_file):
        os.remove(dst_file)
     
    thread = threading.Thread(target=gst_run)
    
    byteorder = None
    record_counter = 0
    
    with open(org_file1, "rb") as in_file:
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

    #thread.join()
    
    #res = os.path.exists(dst_file)
    res = filecmp.cmp(org_file1, dst_file, shallow=False)
    assert res == False


def test_negative_byteorder():
    
    if os.path.exists(src_file):
        os.remove(src_file)

    if os.path.exists(dst_file):
        os.remove(dst_file)
     
    thread = threading.Thread(target=gst_run)
    
    byteorder = None
    record_counter = 0
    
    with open(org_file1, "rb") as in_file:
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

    #thread.join()
    
    #res = os.path.exists(dst_file)
    res = filecmp.cmp(org_file1, dst_file, shallow=False)
    assert res == False


def test_negative_exist():
    
    if os.path.exists(src_file):
        os.remove(src_file)

    if os.path.exists(dst_file):
        os.remove(dst_file)
     
    thread = threading.Thread(target=gst_run)
    
    byteorder = None
    record_counter = 0
    
    with open(org_file1, "rb") as in_file:
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
                
                os.remove(src_file)
                
                thread.start()
    
                break;
                
    #thread.join()
    res = os.path.exists(dst_file)
    #res = filecmp.cmp(org_file, dst_file, shallow=False)
    assert res == False

def test_negative_chmod():
    
    if os.path.exists(src_file):
        os.remove(src_file)

    if os.path.exists(dst_file):
        os.remove(dst_file)
     
    thread = threading.Thread(target=gst_run)
    
    byteorder = None
    record_counter = 0
    
    with open(org_file1, "rb") as in_file:
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
                
                os.chmod(src_file, 000)
                
                thread.start()
                break;
                
    #thread.join()
    res = os.path.exists(dst_file)
    #res = filecmp.cmp(org_file, dst_file, shallow=False)
    assert res == False

    
def test_gst():

    if os.path.exists(src_file):
        os.remove(src_file)

    if os.path.exists(dst_file):
        os.remove(dst_file)
    
    thread = threading.Thread(target=gst_run)
    
    byteorder = None
    record_counter = 0

    with open(org_file1, "rb") as in_file:
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
                #print(bo)
                #print("==============================================================")
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

            #out_file.flush()
            #os.fsync(out_file)
            record_counter += 1
#            print(f"record number {record_counter} length {len_rec} type {rec_type} subtype  {rec_subtype} {byteorder}")
            
    thread.join()
    res = filecmp.cmp(org_file1, dst_file, shallow=False)
    assert res == True
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
