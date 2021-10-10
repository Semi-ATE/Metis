# -*- coding: utf-8 -*-

from Metis.poc import SHP

import time

import Semi_ATE.STDF.FAR as FAR
import Semi_ATE.STDF.ATR as ATR
import Semi_ATE.STDF.WIR as WIR
import Semi_ATE.STDF.MIR as MIR
import Semi_ATE.STDF.PCR as PCR
import Semi_ATE.STDF.MRR as MRR

def test_1():
        
    stdf2hdf52pandas = SHP()
    d1= str('d:\test')
    stdf2hdf52pandas.import_stdf_into_hdf5(d1, "d:\test")

def test_make_stdf():
    
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
        mir.set_value('LOT_ID', 'NAS9999')
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
