import inotify.adapters
import os
import sys
import gi
import time
from yaml import safe_load, dump 
import threading

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject


def _main():

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
    
    print("Pipeline was created")
    
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


        #time.sleep(2)

        if msg:
            t = msg.type
            if t == Gst.MessageType.ERROR:
                err, dbg = msg.parse_error()
                print("ERROR:", msg.src.get_name(), ":", err.message)
            elif t == Gst.MessageType.EOS:
                print("End-Of-Stream reached")
            elif t == Gst.MessageType.STATE_CHANGED:
                old_state, new_state, pending_state = msg.parse_state_changed()
                if old_state == Gst.State.PLAYING and new_state == Gst.State.PAUSED:
                    break;
            else:
                # this should not happen. we only asked for ERROR and EOS
                print(f"ERROR: Unexpected message received : {msg}")

    #print(f"End of transfering {src_file}")
    pipeline.set_state(Gst.State.NULL)
    
if __name__ == '__main__':
    _main()

