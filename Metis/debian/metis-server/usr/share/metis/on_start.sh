#!/bin/bash
source $HOME/maxiconda/etc/profile.d/conda.sh
conda activate gst # change to your conda environment's name
# -u: unbuffered output
python -u /usr/share/metis/metis-daemon.py