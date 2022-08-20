#!/bin/sh
ls
#cd $PWD/tests/
export GST_PLUGIN_PATH=$PWD/Metis
echo $GST_PLUGIN_PATH
pytest -s #--cov=Metis
