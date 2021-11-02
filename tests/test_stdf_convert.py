# -*- coding: utf-8 -*-
import time
import h5py
import os
import os.path

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import Semi_ATE.STDF.FAR as FAR
import Semi_ATE.STDF.ATR as ATR
import Semi_ATE.STDF.WIR as WIR
import Semi_ATE.STDF.MIR as MIR
import Semi_ATE.STDF.PCR as PCR
import Semi_ATE.STDF.MRR as MRR

from Metis.tools.stdf2ph5 import SHP
from Metis.tools.stdf2csv import SCC


# Tests are not finished yet. Only basic tests were written, not real ones.

def test_SHP():
    
    make_stdf()
       
    shp = SHP()
    stdf_file = str('test.stdf')
    out_folder = str('test_result')
    shp.import_stdf_into_hdf5(stdf_file, out_folder)

    hdf5_file = os.path.join(out_folder, '12345.hdf5')

    f = h5py.File(hdf5_file,'r')
    assert f['backup'] != None
    assert f['raw_stdf_data'] != None
    
    backup_group = f['backup']
    file = backup_group.get(stdf_file)
    assert file != None

    raw_group = f['raw_stdf_data']
    raw_file = raw_group.get(stdf_file)
    assert raw_file != None
    atr = raw_file.get('ATR')
    assert atr != None
    far = raw_file.get('FAR')
    assert far != None
    mir = raw_file.get('MIR')
    assert mir != None
    mrr = raw_file.get('MRR')
    assert mrr != None
    pcr = raw_file.get('PCR')
    assert pcr != None
    
    f.close()
    
def test_SCC():

    make_stdf()

    scc = SCC()
    stdf_file = str('test.stdf')
    out_folder = str('test_result')
    scc.convert(stdf_file, out_folder)
    
    csv_files = ['ATR.csv', 'FAR.csv', 'MIR.csv', 'MRR.csv', 'PCR.csv']
    
    for csv_file in csv_files:
        file = os.path.join(out_folder, csv_file)
        assert os.path.getsize(file) > 0


def make_stdf():
    
    with open('test.stdf', 'wb') as f:

        far = FAR()
        
        f.write(far.__repr__())
        
        atr = ATR()    
        atr.set_value('MOD_TIM', 1609462861)
        cmd_line = "modification_script.sh -src /data/stdf/2020-01-01"
        atr.set_value('CMD_LINE', cmd_line)
        f.write(atr.__repr__())
        
        wir = WIR()
        wir.set_value('HEAD_NUM', 1)
        wir.set_value('SITE_GRP', 1)
        wir.set_value('START_T', int(time.time()))
        wir.set_value('WAFER_ID', "WFR_ID_123456789")
        f.write(wir.__repr__())
        
        
        mir = MIR()
        mir.set_value('SETUP_T', 1609462861)
        mir.set_value('START_T', 1609462961)
        mir.set_value('STAT_NUM', 131)
        mir.set_value('MODE_COD', 'P')
        mir.set_value('RTST_COD', ' ')
        mir.set_value('PROT_COD', ' ')
        mir.set_value('BURN_TIM', 65535)
        mir.set_value('CMOD_COD', ' ')
        mir.set_value('LOT_ID', '12345')
        mir.set_value('PART_TYP', 'HAL3715')
        mir.set_value('NODE_NAM', 'Node123')
        mir.set_value('TSTR_TYP', 'SCT')
        mir.set_value('JOB_NAM', 'TPHAL3715_HCT')
        mir.set_value('JOB_REV', '4HEX2GIT')
        mir.set_value('SBLOT_ID', 'NAS9999-1')
        mir.set_value('OPER_NAM','op123')
        mir.set_value('EXEC_TYP', 'SCTSW')    
        mir.set_value('EXEC_VER', 'GIT4HEXREV')    
        mir.set_value('TEST_COD', 'PROBING')
        mir.set_value('TST_TEMP', '25C')    
        mir.set_value('USER_TXT', '')    
        mir.set_value('AUX_FILE', '')    
        mir.set_value('PKG_TYP', 'SOIC8')    
        mir.set_value('FAMLY_ID', 'HAL')    
        mir.set_value('DATE_COD', '1220')    
        mir.set_value('FACIL_ID', 'FR1')    
        mir.set_value('FLOOR_ID', 'PR1')
        mir.set_value('PROC_ID', 'FIN135nm')
        mir.set_value('OPER_FRQ', '1')
        mir.set_value('SPEC_NAM', 'PR35')
        mir.set_value('SPEC_VER', '1.1')
        mir.set_value('FLOW_ID', 'STD')
        mir.set_value('SETUP_ID', 'LB1111')
        mir.set_value('DSGN_REV', 'AB12CH')
        mir.set_value('ENG_ID', '')    
        mir.set_value('ROM_COD', 'RC12345')
        mir.set_value('SERL_NUM', '1221001')
        mir.set_value('SUPR_NAM', '')
        f.write(mir.__repr__())
    
        pcr = PCR()
        pcr.set_value('HEAD_NUM', 1)
        pcr.set_value('SITE_NUM', 1)
        pcr.set_value('PART_CNT', 4294967295)
        pcr.set_value('RTST_CNT', 123)
        pcr.set_value('ABRT_CNT', 0)
        pcr.set_value('GOOD_CNT', 4294967172)
        pcr.set_value('FUNC_CNT', 0)
        f.write(pcr.__repr__())
    
        mrr = MRR()
        mrr.set_value('FINISH_T', 1609462861)
        mrr.set_value('DISP_COD', 'Z')    
        mrr.set_value('USR_DESC', 'NAS12345')
        mrr.set_value('EXC_DESC', '12345')
        f.write(mrr.__repr__())
