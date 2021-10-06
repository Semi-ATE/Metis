# -*- coding: utf-8 -*-
import argparse

try:
    from .__init__ import __version__
except:
    from __init__ import __version__
    
"""
Proof of concept tool for:
    - Importing STDF binary files into HDF5 files
    - Converting STDF single record or whole STDF file into one Pandas dataframe
    - Writing Pandas dataframe back into the HDF5 file
"""

tool_name = 'Tool for importing STDF binary files into HDF5 and convertion to Pandas dataframes.'

class SHP():
    def __init__(self, input_stdf_file, output_folder, debug=False):
        
        print(tool_name)
        print(f"Version {__version__}")
        
        if debug:
            print("Debug is enabled")

def main():
    
    parser = argparse.ArgumentParser(description=tool_name)

    parser.add_argument('-i', '--input',
                        required=True,
                        help='Input STDF file location')
    
    parser.add_argument('-o', '--output',
                        required=True,
                        help='Output folder where the HDF5 file will be saved')

    parser.add_argument('-d', '--debug',
                        action='store_false',
                        required=False,
                        help='Debug flag')

    args = parser.parse_args()
    
    if args.debug:
        debug = False
    else:
        debug = True
    
    stdf2hdf52pandas = SHP(args.input, args.output, debug)
    
    
if __name__ == "__main__":
    main()

