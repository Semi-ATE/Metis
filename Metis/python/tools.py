# -*- coding: utf-8 -*-
#!/usr/bin/env python

import argparse
import time
import os
import os.path
import pandas as pd
import io 
import hashlib
import h5py

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
import Semi_ATE.STDF.WRR as WRR
import Semi_ATE.STDF.WCR as WCR
import Semi_ATE.STDF.PRR as PRR
import Semi_ATE.STDF.TSR as TSR
import Semi_ATE.STDF.PTR as PTR
import Semi_ATE.STDF.MPR as MPR
import Semi_ATE.STDF.FTR as FTR
import Semi_ATE.STDF.BPS as BPS
import Semi_ATE.STDF.GDR as GDR
import Semi_ATE.STDF.DTR as DTR

import warnings
from tables import NaturalNameWarning
warnings.filterwarnings('ignore', category=NaturalNameWarning)
   
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


class STDFHelper():
    
    PART_INDEX = 'PART_INDEX'

    def __init__(self):
        pass
    
    def is_plain_stdf(stdf_file):
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

            if bo == b'\x01':
                byteorder = 'big'
            elif bo == b'\x02':
                byteorder = 'little'
            else:
                byteorder = sys.byteorder
            # Converting raw bytes to int
            len_bytes = int.from_bytes(length, byteorder)
            if len_bytes != 2:
                return False
            
            return True


    def get_byteorder(stdf_file):
        with open(stdf_file, "rb") as f:            
            # Skip the first 4 bytes
            f.read(4)
            bo = f.read(1)
            if bo == b'\x01':
                byteorder = 'big'
            elif bo == b'\x02':
                byteorder = 'little'
            else:
                byteorder = sys.byteorder
        return byteorder
    
    def get_version(stdf_file, byteorder):
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
        fields_names = []
        
        record_name = type(stdr_record).__name__
        
        ignore_fields = ['REC_LEN', 'REC_TYP', 'REC_SUB']

        fields = stdr_record.fields.keys()
        for field in fields:
            if field not in ignore_fields:
                fields_names.append(record_name+"."+field)    
    
        return fields_names
            
    def get_str_field(str_fields, stdf_record, rec_name):
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
                f.read(len_rec)
                record_number = record_number + 1
                
        return record_number

tool_name = '\nTool for importing STDF binary files into HDF5 and conversion to Pandas dataframes.'

class SHP():
    STDF_RECORDS_DIR = '/raw_stdf_data/'
    STDF_FILES_DIR = 'backup'
    COL_STDF_FILE_NAME = 'STDF_FILE_NAME'
    COL_STDF_FOLDER_NAME = 'STDF_FOLDER_NAME'
    
    def __init__(self, debug=False, update_progress=None):
        
        print(tool_name)
        
        self.debug = debug
        self.records_count = 0
        self.cur_record = 0
        self.update_progress = update_progress

        if self.debug:
            print("Debug is enabled")

    def import_stdf_into_hdf5(self, input_stdf_file, output_folder, group = STDF_FILES_DIR, disable_progress = False, disable_trace = False):
        lot_id = None
        
        stdf_file = str(input_stdf_file)
        out_folder = str(output_folder)
        
        if os.path.isfile(stdf_file):
            if os.access(stdf_file, os.R_OK):
                is_plain_stdf = STDFHelper.is_plain_stdf(stdf_file)
                if is_plain_stdf == False:
                    print(f"ERROR : Can not decode FAR record. Make sure the file is not compressed : {stdf_file}")
                    return
                else:
                    self.records_count = STDFHelper.get_stdf_record_number(stdf_file)
                    if self.debug:
                        print(f"Found {self.records_count} STDF records.")
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
        hdf5_file = os.path.join(out_folder, lot_id + ".h5")
        res = HDF5Helper.import_binary_file(hdf5_file, group, stdf_file)
        if res:
            self.stdf2pandas(stdf_file, hdf5_file, disable_progress, disable_trace)

    def create_empty_pandas_data_frames(self):
        dataframes = {}
        
        far_columns = [] 
        far_columns.extend(STDFHelper.get_stdf_rec_fields(FAR()))
        far = pd.DataFrame(columns = far_columns)
        far.name = 'FAR'
        dataframes[far.name] = far

        mir_columns = [] 
        mir_columns.extend(STDFHelper.get_stdf_rec_fields(MIR()))
        mir = pd.DataFrame(columns = mir_columns)
        mir.name = 'MIR'
        dataframes[mir.name] = mir

        mrr_columns = [] 
        mrr_columns.extend(STDFHelper.get_stdf_rec_fields(MRR()))
        mrr = pd.DataFrame(columns = mrr_columns)
        mrr.name = 'MRR'
        dataframes[mrr.name] = mrr

        rdr_columns = [] 
        rdr_columns.extend(STDFHelper.get_stdf_rec_fields(RDR()))
        rdr = pd.DataFrame(columns = rdr_columns)
        rdr.name = 'RDR'
        dataframes[rdr.name] = rdr

        wcr_columns = [] 
        wcr_columns.extend(STDFHelper.get_stdf_rec_fields(WCR()))
        wcr = pd.DataFrame(columns = wcr_columns)
        wcr.name = 'WCR'
        dataframes[wcr.name] = wcr

        sdr_columns = [] 
        sdr_columns.extend(STDFHelper.get_stdf_rec_fields(SDR()))
        sdr = pd.DataFrame(columns = sdr_columns)
        sdr.name = 'SDR'
        dataframes[sdr.name] = sdr

        atr_columns = []        
        atr_columns.extend(STDFHelper.get_stdf_rec_fields(ATR()))
        atr = pd.DataFrame(columns = atr_columns)
        atr.name = 'ATR'
        dataframes[atr.name] = atr

        pgr_columns = []        
        pgr_columns.extend(STDFHelper.get_stdf_rec_fields(PGR()))
        pgr = pd.DataFrame(columns = pgr_columns)
        pgr.name = 'PGR'        
        dataframes[pgr.name] = pgr

        plr_columns = []        
        plr_columns.extend(STDFHelper.get_stdf_rec_fields(PLR()))
        plr = pd.DataFrame(columns = plr_columns)
        plr.name = 'PLR'        
        dataframes[plr.name] = plr

        pcr_columns = []        
        pcr_columns.extend(STDFHelper.get_stdf_rec_fields(PCR()))
        pcr = pd.DataFrame(columns = pcr_columns)
        pcr.name = 'PCR'        
        dataframes[pcr.name] = pcr

        hbr_columns = []        
        hbr_columns.extend(STDFHelper.get_stdf_rec_fields(HBR()))
        hbr = pd.DataFrame(columns = hbr_columns)
        hbr.name = 'HBR'        
        dataframes[hbr.name] = hbr

        sbr_columns = []        
        sbr_columns.extend(STDFHelper.get_stdf_rec_fields(SBR()))
        sbr = pd.DataFrame(columns = sbr_columns)
        sbr.name = 'SBR'        
        dataframes[sbr.name] = sbr

        pmr_columns = []        
        pmr_columns.extend(STDFHelper.get_stdf_rec_fields(PMR()))
        pmr = pd.DataFrame(columns = pmr_columns)
        pmr.name = 'PMR'        
        dataframes[pmr.name] = pmr

        wrr_columns = []        
        wrr_columns.extend(STDFHelper.get_stdf_rec_fields(WRR()))
        wrr = pd.DataFrame(columns = wrr_columns)
        wrr.name = 'WRR'        
        dataframes[wrr.name] = wrr

        prr_columns = [STDFHelper.PART_INDEX]
        prr_columns.extend(STDFHelper.get_stdf_rec_fields(PRR()))
        prr = pd.DataFrame(columns = prr_columns)
        prr.name = 'PRR'        
        dataframes[prr.name] = prr

        tsr_columns = []        
        tsr_columns.extend(STDFHelper.get_stdf_rec_fields(TSR()))
        tsr = pd.DataFrame(columns = tsr_columns)
        tsr.name = 'TSR'
        dataframes[tsr.name] = tsr

        ptr_columns = [STDFHelper.PART_INDEX]        
        ptr_columns.extend(STDFHelper.get_stdf_rec_fields(PTR()))
        ptr_columns.extend(STDFHelper.get_stdf_rec_fields(BPS()))
        ptr = pd.DataFrame(columns = ptr_columns)
        ptr.name = 'PTR'        
        dataframes[ptr.name] = ptr

        mpr_columns = [STDFHelper.PART_INDEX]
        mpr_columns.extend(STDFHelper.get_stdf_rec_fields(MPR()))
        mpr_columns.extend(STDFHelper.get_stdf_rec_fields(BPS()))
        mpr = pd.DataFrame(columns = mpr_columns)
        mpr.name = 'MPR'        
        dataframes[mpr.name] = mpr

        ftr_columns = [STDFHelper.PART_INDEX]        
        ftr_columns.extend(STDFHelper.get_stdf_rec_fields(FTR()))
        ftr_columns.extend(STDFHelper.get_stdf_rec_fields(BPS()))
        # Issue #8 Make extra column in the FTR dataframe for part retest/pass/fail
        ftr_columns.extend('RESULT')
        ftr = pd.DataFrame(columns = ftr_columns)
        ftr.name = 'FTR'        
        dataframes[ftr.name] = ftr

        gdr_columns = []        
        gdr_columns.extend(STDFHelper.get_stdf_rec_fields(GDR()))
        gdr = pd.DataFrame(columns = gdr_columns)
        gdr.name = 'GDR'
        dataframes[gdr.name] = gdr

        dtr_columns = []        
        dtr_columns.extend(STDFHelper.get_stdf_rec_fields(DTR()))
        dtr = pd.DataFrame(columns = dtr_columns)
        dtr.name = 'DTR'
        dataframes[dtr.name] = dtr
        
        return dataframes

    def retrieve_pandas_data_frames(self, output_file):
        
        frames = {}

        recs = ['LOT', 'FAR', 'MIR', 'MRR', 'RDR', 'WCR',
                'SDR', 'ATR', 'PGR', 'PLR', 'PCR', 'HBR', 'SBR', 'PMR', 
                'WRR', 'PRR', 'TSR', 'PTR', 'MPR', 'FTR', 'GDR', 'DTR']
        
        for record_name in recs:
            rec = pd.read_hdf(output_file, key = SHP.STDF_RECORDS_DIR + record_name)
            frames[record_name] = rec

        return frames
    
    def stdf2pandas(self, stdf_file, output_file, disable_progress = False, disable_trace = False):
        
        frames = self.create_empty_pandas_data_frames()
                
        part_index = 0
        bps_seq_name = None
        
        # First get the byte order
        byteorder = STDFHelper.get_byteorder(stdf_file)
        # Get the version
        ver = STDFHelper.get_version(stdf_file, byteorder)
        
        if ver == None:
            print("ERROR : The version of the STDF file is not 4!")
            return

        rec_count = {}        
        str_fields = []
        processed_records = []
        wir_start_t = {}
        last_wir_start_t = 0
        last_wir_wafer_id = 0
        
        if disable_trace == False:
            print(f"Parsing stdf file {stdf_file} is in progress:")

        if disable_progress == False:
            from tqdm import tqdm
            progress = tqdm(total = self.records_count, unit = " records", position=0 , leave=True)
        
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
                
                self.cur_record += 1
                if self.update_progress is not None:
                    self.update_progress(self.cur_record, self.records_count)

                if disable_progress == False:
                    progress.update(1)
                
                stdf_record = STDFHelper.get_stdf_record(ver, byteorder, rec_len, rec_typ, rec_sub, rec)

                rec_name = type(stdf_record).__name__
                
                if rec_name not in processed_records:
                    STDFHelper.get_str_field(str_fields, stdf_record, rec_name)
                    processed_records.append(rec_name)
                
                if rec_name in rec_count:
                    rec_count[rec_name] = rec_count[rec_name] + 1
                else:
                    rec_count[rec_name] = 1

                if rec_name == 'PIR':
                    continue

                if rec_name == 'EPS':
                    bps_seq_name = None
                    continue

                if rec_name == 'BPS':
                    bps_seq_name = stdf_record.get_value('SEQ_NAME')
                    continue

                if rec_name == 'WIR':
                    wafer_id = stdf_record.get_value('WAFER_ID')
                    start_t = stdf_record.get_value('START_T')
                    wir_start_t[wafer_id] = start_t
                    last_wir_start_t = start_t
                    last_wir_wafer_id = wafer_id
                    continue
                
                if rec_name == 'PTR' or rec_name == 'MPR' or \
                    rec_name == 'FTR' or rec_name == 'PRR':
                    pi = part_index
                else:
                    pi = None

                # DataFrame.append is too slow, so first we will create 
                # a temporary csv and later we will import it as DataFrame
                self.stdf2csv(stdf_record, pi, bps_seq_name, wir_start_t, last_wir_start_t, last_wir_wafer_id)
                
                if rec_name == "PRR":
                    part_index = part_index + 1
                    if self.debug:
                        if pi != None:
                            print(f"Data for part # {pi} was saved.")
        if disable_progress == False:
            progress.close()
        if disable_trace == False:
            print(f"\nImporting stdf data as pandas dataframe into hdf5 file {output_file} ...")
        
        start = time.time()
        
        file_name = os.path.basename(stdf_file)
        dataset_path = SHP.STDF_RECORDS_DIR+'/'+file_name+'/'

        for record_name in frames.keys():
           
            fn = record_name + ".csv"
            if os.path.isfile(fn):
                data = pd.read_csv(fn) 
                data_loc = dataset_path+record_name
                # Sets string type for STDF fields with C*n/B*n/kxTYPE type 
                # after CSV import
                fields = data.keys()
                for field in fields:
                    if field in str_fields:
                        data[field] = data[field].astype('|S')
                data.to_hdf(output_file, data_loc, complevel = 9);
                os.remove(fn)

        stop = time.time()
        import_time = stop-start
        if disable_trace == False:
            print("Import process took {:.2f} sec.".format(import_time))
            print("Number of imported records :")
            for r_name in rec_count:
                print(f"{r_name} : {rec_count[r_name]}")

    def stdf2csv(self, stdr_record, part_index, bps_seq_name, wir_start_t, last_wir_start_t, last_wir_wafer_id):

        record_name = type(stdr_record).__name__
        ignore_fields = ['REC_LEN', 'REC_TYP', 'REC_SUB']
               
        fn = record_name + ".csv"
        
        # Writing headers if file does not exists:
        if os.path.isfile(fn) == False: 
            with open(fn, 'w') as f:
                s = ''
                if part_index != None:
                    s += STDFHelper.PART_INDEX + ','
                    if bps_seq_name != None:
                        s += 'BPS.SEQ_NAME,'
                        
                if record_name == 'WRR':
                    s += 'WIR.START_T,'
                # Issue #8
                # Make extra column in the FTR dataframe for part retest/pass/fail
                if record_name == 'FTR':
                    s += 'RESULT,'
                
                fields = stdr_record.fields.keys()
                for field_name in fields:
                    if field_name not in ignore_fields:
                        column_name = record_name+"."+field_name
                        s += column_name + ','
                        
                s = s[:-1] + '\n'
                f.write(s)
        
        # Writing data:
        with open(fn, 'a') as f:
            s = ''
            if part_index != None:
                s += str(part_index) + ','
                if bps_seq_name != None:
                    s += bps_seq_name + ','
    
            if record_name == 'WRR':
                wafer_id = stdr_record.get_value('WAFER_ID')
                if len(wafer_id) > 0 and wafer_id in wir_start_t:
                        start_t = wir_start_t[wafer_id]
                        s += str(start_t) + ','
                else:
                        s += str(last_wir_start_t) + ','

            if record_name == 'FTR':
                test_flg = stdr_record.fields['TEST_FLG']['Value']
                if len(test_flg) > 0:
                    if test_flg[6] == '1':
                        s += '0,'
                    elif test_flg[7] == '1':
                        s += '1,'
                    elif test_flg[7] == '0':
                        s += '2,'
                    else:
                        err = f"Not valid 7th bit value in the FTR record for part index {part_index}.\n"
                        err += f"Expected 0, but got {test_flg[7]}"
                        raise Exception(err)
                else:
                    s += '-1,'

            fields = stdr_record.fields.keys()
            for field_name in fields:
                
                if field_name not in ignore_fields:
                    
                    column_name = record_name+"."+field_name
                    value = stdr_record.fields[field_name]['Value']
                    # Converting the list as string
                    if type(value) == list:
                        v = str(value)
                        s += '"' + v + '",'
                        continue
                    else:
                        value = str(value)

                    ftype = stdr_record.fields[field_name]['Type']
                        
                    if len(value) == 0:
                        if field_name == "WAFER_ID":
                            v = str(last_wir_wafer_id)
                            s += '"' + v + '",'
                            continue
                        if ftype.startswith('U'):
                            s += '0,'
                        elif ftype.startswith('I'):
                            s += '0,'
                        elif ftype.startswith('R'):
                            s += '0.0,'
                        elif ftype.startswith('C'):
                            s += '" ",'
                        else:
                            s += '" ",'
                    elif ftype.startswith('C'):
                        # Explicitly set double quotes for char arrays
                        s += '"' + value + '",'
                    else:
                        s += value + ','
            s = s[:-1] + '\n'
            f.write(s)
            
def main():
    
    parser = argparse.ArgumentParser(description=tool_name)

    parser.add_argument('-i', '--input',
                        required=True,
                        type=str,
                        nargs='+',
                        help='Input STDF file location')
    
    parser.add_argument('-o', '--output',
                        required=True,
                        help='Output folder where the HDF5 file will be saved')

    parser.add_argument('-d', '--debug',
                        action='store_false',
                        required=False,
                        help='Debug flag')

    parser.add_argument('-g', '--group',
                        required=False,
                        help='Group in HDF5 file')

    args = parser.parse_args()
    
    if args.debug:
        debug = False
    else:
        debug = True
        
    
    stdf2hdf52pandas = SHP(debug)
    for input_file in args.input:
        stdf2hdf52pandas.import_stdf_into_hdf5(input_file, args.output, args.group)
    
    
if __name__ == "__main__":
    main()

