# -*- coding: utf-8 -*-

import io
import os 
import hashlib
import h5py
import numpy as np

class HDF5Helper():

    def __init__(self):
        pass
    
    def get_check_sum(file_path):
        
        h = hashlib.sha256()
    
        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                h.update(chunk)
    
        return h.hexdigest()

    def import_binary_file(hdf5_file, group, bin_file):

        if os.path.isfile(hdf5_file):
            hdf5 = h5py.File(hdf5_file, "a")
            groups = hdf5.keys()
            if group in groups:
                hdf5_group = hdf5[group]
            else:
                hdf5_group = hdf5.create_group(group)
        else:
            try:
                hdf5 = h5py.File(hdf5_file, "w")
            except:
                print(f"ERROR : Can not create a file : {hdf5_file}")
                return False
            try:
                hdf5_group = hdf5.create_group(group)
            except:
                print(f"ERROR : Can not create a HDF5 group in the file : {hdf5_file}")
                return False

        datasets = hdf5_group.keys()
        
        bin_file_name = os.path.basename(bin_file)
        
        # File already exists
        if bin_file_name in datasets:
            
            hash_sum_file = HDF5Helper.get_check_sum(bin_file)
            print(f"The file {bin_file_name} is already imported, nothing to do")
            h = hashlib.sha256()
            b = bytearray(hdf5_group[bin_file_name])
            h.update(b)
            hash_sum_dataset = h.hexdigest()
            
            if hash_sum_file != hash_sum_dataset:
                print(f"File exists in the hdf5 file, but check sum differ from the input file")
                print(f"SHA256 check sum {bin_file_name} :\n{hash_sum_file}")
                print(f"SHA256 check sum for the dataset :\n{hash_sum_dataset}")
                hdf5.close()
                return False
            
        else:
            # File does not exists, try to import
            bin_data = np.fromfile(bin_file, dtype=np.uint8)
            hdf5_group.create_dataset(bin_file_name, 
                                         np.shape(bin_data),  
                                         h5py.h5t.STD_U8BE, 
                                         bin_data)
            print(f"The file {bin_file_name} was imported into {hdf5_file}")
            hdf5.close()
            return True

