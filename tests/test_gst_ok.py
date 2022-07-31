import os
test_loc = os.path.dirname(__file__)
root_loc = os.path.join(test_loc, "..")
os.environ['GST_PLUGIN_PATH'] = os.path.join(root_loc, "Metis")
print(f"GST_PLUGIN_PATH = {os.environ['GST_PLUGIN_PATH']}")
os.environ['TEST_METIS'] = "True"
import gi
import time
import threading
import filecmp
import sys
import stat

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject

# The file from which we will read and write into src_file to stimulate inotify
org_file = os.path.join(test_loc, "test.std")
src_file3 = os.path.join(test_loc,  "test.std.src3")
dst_file = os.path.join(test_loc, "test.std.dst")
yaml_file = os.path.join(root_loc, "Metis/test_metisd.yaml")
wrong_yaml_file = os.path.join(root_loc, "Metis/nometisd.yaml")

def gst_run(src):

    Gst.init(None)
    Gst.debug_set_active(True)
    Gst.debug_set_default_threshold(3)

    # create the elements
    source = Gst.ElementFactory.make("metis_source", "metis_source")
    if not source:
        print("ERROR: Can not find source plugin")
        sys.exit(1)
    source.set_property("file-name", src)

    mid = Gst.ElementFactory.make("metis_process", "metis_process")
    if not mid:
        print("ERROR: Can not find mid plugin")
        sys.exit(1)

    sink = Gst.ElementFactory.make("metis_sink", "metis_sink")
    if not sink:
        print("ERROR: Can not find sink plugin")
        sys.exit(1)
    sink.set_property("file-name", dst_file)

    # create the empty pipeline
    global pipeline
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
    
    
    # start playing
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("ERROR: Unable to set the pipeline to the playing state")
        return

    print("Play the pipeline")
    # wait for EOS or error
    bus = pipeline.get_bus()
    while True:
#        print("Play the pipeline -")
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

    print(f"End of transfering {src}")
    pipeline.set_state(Gst.State.NULL)

def test_gst_pass():

    if os.path.exists(src_file3):
        os.remove(src_file3)

    if os.path.exists(dst_file):
        os.remove(dst_file)
    
    print(f"src_file3 {src_file3}")
    thread = threading.Thread(target=gst_run, args=(src_file3,))
    
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
    
    if os.path.exists(src_file3):
        os.remove(src_file3)
