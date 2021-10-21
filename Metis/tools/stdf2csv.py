# -*- coding: utf-8 -*-
import argparse
import os
import os.path
from tqdm import tqdm

import Semi_ATE.STDF.PTR as PTR
import Semi_ATE.STDF.MPR as MPR
import Semi_ATE.STDF.FTR as FTR
import Semi_ATE.STDF.PRR as PRR

try:
    from .STDFHelper import STDFHelper
    from .HDF5Helper import HDF5Helper
except:
    from STDFHelper import STDFHelper
    from HDF5Helper import HDF5Helper
    
"""
This is a tool which converts stdf file in multiple CSV files.
"""

tool_name = '\nTool for converting STDF binary files into CSV files.'

class SCC():
    '''
    S(TDF) -> (C)onvertor -> (C)SV = SCC
    Main class for converting STDF files into CSV files
    '''
    def __init__(self, debug=False):
        
        print(tool_name)
        
        self.debug = debug
        
        if self.debug:
            print("Debug is enabled")

    def stdf2csv(self, stdr_record, output_folder, part_num):

        fields_names = []
        
        record_name = type(stdr_record).__name__

        csv_file = os.path.join(output_folder, record_name + '.csv' )
        
        ignore_fields = ['REC_LEN', 'REC_TYP', 'REC_SUB']
               
        # Writing headers if file does not exists:
        if os.path.isfile(csv_file) == False: 
            print(f"File {csv_file} was created.")
            with open(csv_file, 'w') as f:
                s = ''

                if part_num != None:
                    s += 'PART_NUMBER,'

                fields = stdr_record.fields.keys()
                for field_name in fields:
                    if field_name not in ignore_fields:
                        s += field_name + ','
                s = s[:-1] + '\n'
                f.write(s)
        
        # Writing data:
        with open(csv_file, 'a') as f:
            s = ''

            if part_num != None:
                s += str(part_num) + ','
    
            fields = stdr_record.fields.keys()
            for field_name in fields:
                
                if field_name not in ignore_fields:
                    
                    value = stdr_record.fields[field_name]['Value']
                    #Converting the list as string
                    if type(value) == list:
                        v = str(value)
                        v = v.replace(',','')
                        v = v.replace('[','')
                        v = v.replace(']','')
                        value = v.replace('\'','')
                        value = '"' + value + '"'
                        s += value.replace(' ', '')
                        s += ','
                        continue
                    else:
                        value = str(value)

                    ftype = stdr_record.fields[field_name]['Type']
                        
                    if ftype.startswith('C'):
                        # Explicitly set double quotes for char arrays
                        s += '"' + value + '",'
                    else:
                        s += value + ','
            s = s[:-1] + '\n'
            f.write(s)         
            
            
    def convert(self, input_stdf_file, output_folder):
        '''
        Put here the description:
            ...
        Parameters
        ----------
        input_stdf_file : string
            Location and name of the STDF file which will be imported into the HDF5 file.
        output_folder : string
            Output folder where the CSV file will be created if not exists.

        Returns
        -------
        None.

        '''
        
        stdf_file = str(input_stdf_file)
        out_folder = str(output_folder)
        
        if os.path.isfile(stdf_file):
            if os.access(stdf_file, os.R_OK):
                is_plain_stdf = STDFHelper.is_plain_stdf(stdf_file)
                if is_plain_stdf == False:
                    print(f"ERROR : Can not decode FAR record. Make sure the file is not compressed : {stdf_file}")
                    return
                else:
                    records_count = STDFHelper.get_stdf_record_number(stdf_file)
                    if self.debug:
                        print(f"Found {records_count} STDF records.")
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

        # First get the byte order
        byteorder = STDFHelper.get_byteorder(stdf_file)
        # Get the version
        ver = STDFHelper.get_version(stdf_file, byteorder)
        
        if ver == None:
            print("ERROR : The version of the STDF file is not 4!")
            return
        
        rec_count = {}
        
        pi = 1
        
        progress = tqdm(total = records_count, unit = " records")
                
        with open(stdf_file, "rb") as f:            
            
            while(True):
                # Get record length
                rec_len = f.read(2)
                # EOF reached
                if not rec_len:
                    break
                # Get record type
                rec_typ = f.read(1)
                # Get record sub-type
                rec_sub = f.read(1)
                len_rec = int.from_bytes(rec_len, byteorder)
                # Get rest of the record
                rec = f.read(len_rec)
                
                progress.update(1)
                
                stdf_record = STDFHelper.get_stdf_record(ver, byteorder, rec_len, rec_typ, rec_sub, rec)

                rec_name = type(stdf_record).__name__
                                
                if rec_name in rec_count:
                    rec_count[rec_name] = rec_count[rec_name] + 1
                else:
                    rec_count[rec_name] = 1

                if rec_name == 'PTR' or rec_name == 'MPR' or \
                    rec_name == 'FTR' or rec_name == 'PRR':
                    part_num = pi
                else:
                    part_num = None
                
                self.stdf2csv(stdf_record, output_folder, part_num)

                if rec_name == "PRR":
                    pi = pi + 1
                    if self.debug:
                        if part_num != None:
                            print(f"Data for part # {part_num} was saved.")

        progress.close()
    
        print(f"Number of imported records :")
        for r_name in rec_count:
            print(f"{r_name} : {rec_count[r_name]}")
            
                            

def main():
    
    parser = argparse.ArgumentParser(description=tool_name)

    parser.add_argument('-i', '--input',
                        required=True,
                        help='Input STDF file location')
    
    parser.add_argument('-o', '--output',
                        required=True,
                        help='Output folder where the CSV files will be saved')

    parser.add_argument('-d', '--debug',
                        action='store_false',
                        required=False,
                        help='Debug flag')

    args = parser.parse_args()
    
    if args.debug:
        debug = False
    else:
        debug = True
    
    stdf2hdf52pandas = SCC(debug)
    stdf2hdf52pandas.convert(args.input, args.output)
    
    
if __name__ == "__main__":
    main()

