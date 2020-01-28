'''
	Tiff 2d for Sector 32 ID C

'''
import sys
import json
import time
from epics import PV
import h5py
import shutil
import os
import imp
import traceback

import libs.aps32id_lib as aps32id_lib
import libs.scan_lib as scan_lib
import libs.log_lib as log_lib
import libs.dm_lib as dm_lib
from datetime import datetime

global variableDict

variableDict = {'PreDarkImages': 0,
				'PreWhiteImages': 0,
                'PostDarkImages': 0,
				'PostWhiteImages': 0,
				'Projections': 100000000,
				'SampleXOut': 0.4,
				'SampleYOut': 0.0,
				'SampleZOut': 0.0,
				'SampleXIn': 0.0,
				'SampleYIn': 0.0,
				'SampleZIn': 0.0,
				'StartSleep_min': 0,
				'ExposureTime': 1,
				'Use_Fast_Shutter': 1,
				'Delay_next_exposure_s': 2,
				'IOC_Prefix': '32idcPG3:',
				'TIFFNDArrayPort': 'PROC1',
				'FileWriteMode': 'Stream',
				'Recursive_Filter_Enabled': 0,
				'Recursive_Filter_N_Images': 2,
				'Recursive_Filter_Type': 'RecursiveAve',
                'RemoteAnalysisDir': 'usr32idc@txmtwo:/local/dataraid/'
				}

global_PVs = {}

def getVariableDict():
    global variableDict
    return variableDict

def main():
    # create logger
    # # python 3.5+ 
    # home = str(pathlib.Path.home())
    home = os.path.expanduser("~")
    logs_home = home + '/logs/'

    # make sure logs directory exists
    if not os.path.exists(logs_home):
        os.makedirs(logs_home)

    lfname = logs_home + datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S") + '.log'
    log_lib.setup_logger(lfname)

    aps32id_lib.update_variable_dict(variableDict)
    aps32id_lib.init_general_PVs(global_PVs, variableDict)
    FileName = global_PVs['TIFF1_FileName'].get(as_string=True)

    log_lib.info(' ')
    log_lib.info('  *** Starting tiff stack acq.')
    scan_lib.tiff_2Dscan(variableDict, global_PVs, FileName)
    dm_lib.scp(global_PVs, variableDict)

if __name__ == '__main__':
	main()
