# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import numpy as np

import Semi_ATE.STDF.STDR as STDR
import Semi_ATE.STDF.FAR as FAR
import Semi_ATE.STDF.ATR as ATR
import Semi_ATE.STDF.MIR as MIR
import Semi_ATE.STDF.MRR as MRR
import Semi_ATE.STDF.PCR as PCR
import Semi_ATE.STDF.HBR as HBR
import Semi_ATE.STDF.SBR as SBR
import Semi_ATE.STDF.PMR as PMR
import Semi_ATE.STDF.PGR as PGR
import Semi_ATE.STDF.PLR as PLR
import Semi_ATE.STDF.RDR as RDR
import Semi_ATE.STDF.SDR as SDR
import Semi_ATE.STDF.WIR as WIR
import Semi_ATE.STDF.WRR as WRR
import Semi_ATE.STDF.WCR as WCR
import Semi_ATE.STDF.PIR as PIR
import Semi_ATE.STDF.PRR as PRR
import Semi_ATE.STDF.TSR as TSR
import Semi_ATE.STDF.PTR as PTR
import Semi_ATE.STDF.MPR as MPR
import Semi_ATE.STDF.FTR as FTR
import Semi_ATE.STDF.BPS as BPS
import Semi_ATE.STDF.EPS as EPS
import Semi_ATE.STDF.GDR as GDR
import Semi_ATE.STDF.DTR as DTR
import Semi_ATE.STDF.utils as u


class STDFHelper():
    
    PART_INDEX = 'PART_INDEX'

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
    
    def get_version(stdf_file, byteorder):
        """
        Checks the first STDF record FAR and takes the 6th byte.

        Parameters
        ----------
        stdf_file : string
            STDF file location and name.
        byteorder : string
            byte order of the STDF file : 'little' or 'big'
        Returns
        -------
        version : str
            'V4' or None 
            We support only STDF ver. 4

        """
        with open(stdf_file, "rb") as f:            
            # Skip the first 4 bytes
            f.read(5)
            v = f.read(1)
            ver = int.from_bytes(v, byteorder)

            if ver == 4:
                return "V4"
            else:
                return None
    
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
                    
    def get_stdf_rec_fields(stdr_record):
        
        """
        Return fields names of the given STDF record as list

        Parameters
        ----------
        stdr_record : STDR object
            STDF record object .

        Returns
        -------
        fields_names : list
            list of STDF record's fields without header's fields
        """        

        fields_names = []
        
        record_name = type(stdr_record).__name__
        
        ignore_fields = ['REC_LEN', 'REC_TYP', 'REC_SUB']

        fields = stdr_record.fields.keys()
        for field in fields:
            if field not in ignore_fields:
                fields_names.append(record_name+"."+field)    
    
        return fields_names
            
    def get_str_field(str_fields, stdf_record, rec_name):

        """
        Collects STDF's record fields which have string data (C*n)

        Parameters
        ----------
        str_fields : list
            list with all string fields in the STDF file .
        stdr_record : STDR object
            STDF record object .
        rec_name : str
            Name of the record .

        """        
        
        fields = stdf_record.fields.keys()
        
        for field_name in fields:
        
            field_type = stdf_record.fields[field_name]['Type']
            if field_type.startswith('C') or \
                field_type.startswith('B*') or \
                field_type.startswith('x'):

                    full_field_name = rec_name+'.'+field_name
                    if full_field_name not in str_fields:
                        str_fields.append(full_field_name)

    def get_stdf_record(ver, byteorder, rec_len, rec_typ, rec_sub, rec):

        """
        Creates STDR record object based in binary data in the STDF file
        
        Parameters
        ----------

        ver : str
            STDF file version. Expecting value 4

        byteorder : str
            Byte order : little or big.

        rec_len : binary string taken from the STDF file
            Length of the STDF record without the header.
            Value of the REC_LEN STDF record's field.

        rec_typ : binary string taken from the STDF file
            Type of the STDF record .
            Value of the REC_TYP STDF record's field.

        rec_sub : binary string taken from the STDF file
            Sub-type of the STDF record .
            Value of the REC_SUB STDF record's field.

        rec : binary data
            STDF record data after the header.

        Returns
        -------
        number of stdf records
        
        """        

        # Converting raw bytes to int
        typ_rec = int.from_bytes(rec_typ, byteorder)
        sub_rec = int.from_bytes(rec_sub, byteorder)
        
        if byteorder == 'little':
            endian = '<'
        elif byteorder == 'big':
            endian = '>'
        else:
            return None
        
        binary_record = rec_len + rec_typ + rec_sub + rec

        if typ_rec == 0 and sub_rec == 10: 
            return FAR(ver, endian, binary_record)
        elif typ_rec == 0 and sub_rec == 20: 
            return ATR(ver, endian, binary_record)
        elif typ_rec == 1 and sub_rec == 10: 
            return MIR(ver, endian, binary_record)
        elif typ_rec == 1 and sub_rec == 20: 
            return MRR(ver, endian, binary_record)
        elif typ_rec == 1 and sub_rec == 30: 
            return PCR(ver, endian, binary_record)
        elif typ_rec == 1 and sub_rec == 40: 
            return HBR(ver, endian, binary_record)
        elif typ_rec == 1 and sub_rec == 50: 
            return SBR(ver, endian, binary_record)
        elif typ_rec == 1 and sub_rec == 60: 
            return PMR(ver, endian, binary_record)
        elif typ_rec == 1 and sub_rec == 62: 
            return PGR(ver, endian, binary_record)
        elif typ_rec == 1 and sub_rec == 63: 
            return PLR(ver, endian, binary_record)
        elif typ_rec == 1 and sub_rec == 70: 
            return RDR(ver, endian, binary_record)
        elif typ_rec == 1 and sub_rec == 80: 
            return SDR(ver, endian, binary_record)
        elif typ_rec == 2 and sub_rec == 10: 
            return WIR(ver, endian, binary_record)
        elif typ_rec == 2 and sub_rec == 20: 
            return WRR(ver, endian, binary_record)
        elif typ_rec == 2 and sub_rec == 30: 
            return WCR(ver, endian, binary_record)
        elif typ_rec == 5 and sub_rec == 10: 
            return PIR(ver, endian, binary_record)
        elif typ_rec == 5 and sub_rec == 20: 
            return PRR(ver, endian, binary_record)
        elif typ_rec == 10 and sub_rec == 30: 
            return TSR(ver, endian, binary_record)
        elif typ_rec == 15 and sub_rec == 10: 
            return PTR(ver, endian, binary_record)
        elif typ_rec == 15 and sub_rec == 15: 
            return MPR(ver, endian, binary_record)
        elif typ_rec == 15 and sub_rec == 20: 
            return FTR(ver, endian, binary_record)
        elif typ_rec == 20 and sub_rec == 10: 
            return BPS(ver, endian, binary_record)
        elif typ_rec == 20 and sub_rec == 20: 
            return EPS(ver, endian, binary_record)
        elif typ_rec == 50 and sub_rec == 10: 
            return GDR(ver, endian, binary_record)
        elif typ_rec == 50 and sub_rec == 30: 
            return DTR(ver, endian, binary_record)
        else:
            return None
        
    def get_stdf_record_number(stdf_file):
        """
        Count the number of STDF records. Useful for progress bar info
        
        Parameters
        ----------
        stdf_file : str
            STDF file location and name.

        Returns
        -------
        number of stdf records
        
        """        

        byteorder = STDFHelper.get_byteorder(stdf_file)

        record_number = 0;
        
        with open(stdf_file, "rb") as f:            
            
            while(True):
                # Get record length
                rec_len = f.read(2)
                # EOF reached
                if not rec_len:
                    break
                # Get record type
                f.read(1)
                # Get record sub-type
                f.read(1)
                len_rec = int.from_bytes(rec_len, byteorder)
                # Get rest of the record
                rec = f.read(len_rec)
                record_number = record_number + 1
                
        return record_number


