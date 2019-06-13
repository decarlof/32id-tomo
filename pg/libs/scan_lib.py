import sys
import time
import signal
import numpy as np

import aps32id_lib
import log_lib

def dummy_tomo_fly_scan(global_PVs, variableDict, fname):
    log_lib.Logger(variableDict['LogFileName']).info(' ')
    log_lib.Logger(variableDict['LogFileName']).info('  *** start_scan')

    def cleanup(signal, frame):
        aps32id_lib.stop_scan(global_PVs, variableDict)
        sys.exit(0)
    signal.signal(signal.SIGINT, cleanup)

    # moved to outer loop in main()
    # pgInit(global_PVs, variableDict)

    # pgSet(global_PVs, variableDict, fname) 


def tomo_fly_scan(variableDict, global_PVs, detector_filename):
    log_lib.info(' ')
    log_lib.info('  *** start_scan')

    def cleanup(signal, frame):
        aps32id_lib.stop_scan(global_PVs, variableDict)
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if variableDict.has_key('StopTheScan'):
        stop_scan(global_PVs, variableDict)
        return

    # Start scan sleep in min so min * 60 = sec
    time.sleep(float(variableDict['StartSleep_min']) * 60.0)

    aps32id_lib.setPSO(global_PVs, variableDict)

    aps32id_lib.setup_detector(global_PVs, variableDict)
    aps32id_lib.setup_writer(global_PVs, variableDict, detector_filename)

    aps32id_lib.acquire_pre_dark(variableDict, global_PVs)
    aps32id_lib.acquire_pre_flat(variableDict, global_PVs)
    
    log_lib.info(' ')
    log_lib.info('  *** Setting for fly scan')
    aps32id_lib.move_sample_in(global_PVs, variableDict)
    aps32id_lib.open_shutters(global_PVs, variableDict)
    aps32id_lib.disable_smaract(global_PVs, variableDict)
    log_lib.info('  *** Setting for fly scan: Done!')

    # run fly scan
    theta = aps32id_lib.acquire_fly(global_PVs, variableDict)
    ###aps32id_lib.wait_pv(global_PVs['HDF1_NumCaptured'], expected_num_cap, 60)
    aps32id_lib.enable_smaract(global_PVs, variableDict)

    aps32id_lib.acquire_post_flat(variableDict, global_PVs)
    aps32id_lib.acquire_post_dark(variableDict, global_PVs)
    

    log_lib.info(' ')
    log_lib.info('  *** Finalizing scan') 
    aps32id_lib.close_shutters(global_PVs, variableDict)
    time.sleep(0.25)
    aps32id_lib.wait_pv(global_PVs['HDF1_Capture_RBV'], 0, 600)
    
    aps32id_lib.add_theta(global_PVs, variableDict, theta)
    aps32id_lib.add_interferometer(global_PVs, variableDict, theta)

    global_PVs['Fly_ScanControl'].put('Standard')
    if False == aps32id_lib.wait_pv(global_PVs['HDF1_Capture'], 0, 10):
        global_PVs['HDF1_Capture'].put(0)
    aps32id_lib.reset_CCD(global_PVs, variableDict)
    log_lib.info('  *** Finalizing scan: Done!') 
