# -*- coding: utf-8 -*-

import sys

class STDFHelper():

    def __init__(self):
        pass
    
    def is_plain_stdf(stdf_file):
        """
        Check if the file is non compressed STDF ver. 4

        Parameters
        ----------
        stdf_file : str
            STDF file location and name.

        Returns
        -------
        True if the file is not compressed.

        """
        with open(stdf_file, "rb") as f:            
            length = f.read(2)
            rec_typ = f.read(1)
            rec_sub = f.read(1)
            bo = f.read(1)
            ver = f.read(1)

            if ver != b'\x04':
                return False

            if rec_typ != b'\x00':
                return False

            if rec_sub != b'\x0A':
                return False

            if bo == 1:
                byteorder = 'big'
            elif bo == 2:
                byteorder = 'little'
            else:
                byteorder = sys.byteorder
            # Converting raw bytes to int
            len_bytes = int.from_bytes(length, byteorder)
            if len_bytes != 2:
                return False
            
            return True


    def get_byteorder(stdf_file):
        """
        Checks the first STDF record FAR and takes the 5th byte.
        If value is 1, returns 'big' endianness 
        If value is 2, returns 'little' endianness 
        Otherwise returns the system endianness via sys.byteorder

        Parameters
        ----------
        stdf_file : string
            STDF file location and name.

        Returns
        -------
        byteorder : str
            'big' or 'little' endianness

        """
        with open(stdf_file, "rb") as f:            
            # Skip the first 4 bytes
            f.read(4)
            bo = f.read(1)
            if bo == 1:
                byteorder = 'big'
            elif bo == 2:
                byteorder = 'little'
            else:
                byteorder = sys.byteorder
        return byteorder
    
    def get_lot_id(stdf_file):

        """
        Extract Lot ID from non compressed STDF file

        Parameters
        ----------
        stdf_file : string
            STDF file location and name.

        Returns
        -------
        lot_id : str
            Lot ID
        """        
        
        # First get the byte order
        byteorder = STDFHelper.get_byteorder(stdf_file)
        
        with open(stdf_file, "rb") as f:            
            
            while(True):

                rec_len = f.read(2)
                # EOF reached
                if not rec_len:
                    return ''
                rec_typ = f.read(1)
                rec_sub = f.read(1)

                # Converting raw bytes to int
                typ_rec = int.from_bytes(rec_typ, byteorder)
                sub_rec = int.from_bytes(rec_sub, byteorder)
                
                if typ_rec == 1 and sub_rec == 10:
                    # Skip 15 bytes, to get the lot_id
                    f.read(15)
                    # length of the lot string in one byte
                    len_lot_id = f.read(1)
                    lot_id_len = int.from_bytes(len_lot_id, byteorder)
                    if lot_id_len > 0:
                        lot_id = f.read(lot_id_len)
                        return lot_id.decode('ascii')
                    else:
                        return ''
                else:
                    skip_bytes = int.from_bytes(rec_len, byteorder)
                    f.read(skip_bytes)