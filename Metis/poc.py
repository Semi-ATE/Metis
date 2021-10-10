# -*- coding: utf-8 -*-
import argparse
import os
import os.path

try:
    from .__init__ import __version__
    from .STDFHelper import STDFHelper
    from .HDF5Helper import HDF5Helper
except:
    from __init__ import __version__
    from STDFHelper import STDFHelper
    from HDF5Helper import HDF5Helper
    
"""
Proof of concept tool for:
    - Importing STDF binary files into HDF5 files
    - Converting STDF single record or whole STDF file into one Pandas dataframe
    - Writing Pandas dataframe back into the HDF5 file
"""

tool_name = '\nTool for importing STDF binary files into HDF5 and conversion to Pandas dataframes.'

class SHP():
    '''
    S(TDF) -> H(DF5) -> P(andas) = SHP
    Main class for converting STDF files into Panda dataframes using HDF5 files as storage
    '''
    def __init__(self, debug=False):
        
        print(tool_name)
        print(f"Version {__version__}")
        
        self.debug = debug
        
        if self.debug:
            print("Debug is enabled")
            
    def import_stdf_into_hdf5(self, input_stdf_file, output_folder, hdf5_backup_folder = "backup"):
        '''
        Imports binary STDF file into HDF5 file in the following sequence:
        1. Takes the LOT_ID field value from the STDF MIR record
        2. Creates LOT_ID.hdf5 file if not exists
        3. Creates HDF5 group (folder) with name "hdf5_backup_folder" if does not exists
        4. Imports the stdf file in the "hdf5_backup_folder". A check will be performed if the file is already imported

        Parameters
        ----------
        input_stdf_file : string
            Location and name of the STDF file which will be imported into the HDF5 file.
        output_folder : string
            Output folder where the HDF5 file will be created if not exists.
        hdf5_backup_folder : string
            Name of the folder where the STDF file will be imported into HDF5 file.
            Optional argument. Default value is "backup"

        Returns
        -------
        None.

        '''
        
        lot_id = None
        
        stdf_file = str(input_stdf_file)
        out_folder = str(output_folder)
        
        if os.path.isfile(stdf_file):
            if os.access(stdf_file, os.R_OK):
                is_plain_stdf = STDFHelper.is_plain_stdf(stdf_file)
                if is_plain_stdf == False:
                    print(f"ERROR : Can not decode FAR record. Make sure the file is not compressed : {stdf_file}")
                    return
                lot_id = STDFHelper.get_lot_id(stdf_file)
                if len(lot_id) > 0:
                    if self.debug:
                        print(f"Found LOT_ID : {lot_id}")
                else:
                    print(f"ERROR : Input STDF file does not LOT_ID information : {stdf_file}")
                    return
            else:
                print(f"ERROR : Input STDF file does not have read permisssion : {stdf_file}")
                return
            
        else:
            print(f"ERROR : Input STDF file does not exists : {stdf_file}")
            return
            
        if os.path.isdir(out_folder):
            if not os.access(out_folder, os.W_OK):
                print(f"ERROR : Output folder does not have write permisssion : {out_folder}")
                return
        else:
            try:
                os.mkdir(out_folder)
            except:
                print(f"ERROR : Can not create the output folder : {out_folder}")
                return
            
        # Make HDF5 file if not exists
        hdf5_file = os.path.join(out_folder, lot_id + ".hdf5")
        res = HDF5Helper.import_binary_file(hdf5_file, hdf5_backup_folder, stdf_file)
        if res:
            # Convert STDF records into Pandas datasets
            pass

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
    
    stdf2hdf52pandas = SHP(debug)
    stdf2hdf52pandas.import_stdf_into_hdf5(args.input, args.output)
    
    
if __name__ == "__main__":
    main()

