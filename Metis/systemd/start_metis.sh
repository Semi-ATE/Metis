#!/bin/bash
source $HOME/maxiconda/etc/profile.d/conda.sh
conda activate gst 
export GST_PLUGIN_PATH=/usr/share/metis
# -u: unbuffered output
python -u /usr/share/metis/sinotify.py
