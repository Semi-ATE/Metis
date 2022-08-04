#!/bin/sh
ls
cd /home/runner/work/Metis/Metis/tests/
export GST_PLUGIN_PATH=$PWD/../Metis
echo $GST_PLUGIN_PATH
pytest -s --cov=Metis
