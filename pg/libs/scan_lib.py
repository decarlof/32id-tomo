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
        aps32id_lib.stop_scan(global_PVs, variableDict)
        return

    aps32id_lib.disable_fast_shutter(global_PVs, variableDict)

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
    aps32id_lib.reset_angles_0_360(global_PVs)
    log_lib.info('  *** Finalizing scan: Done!') 



def tomo_step_scan(variableDict, global_PVs, detector_filename):
    log_lib.info(' ')
    log_lib.info('  *** start_scan')

    def cleanup(signal, frame):
        aps32id_lib.stop_scan(global_PVs, variableDict)
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if variableDict.has_key('StopTheScan'):
        aps32id_lib.stop_scan(global_PVs, variableDict)
        return

    # Start scan sleep in min so min * 60 = sec
    time.sleep(float(variableDict['StartSleep_min']) * 60.0)

    aps32id_lib.setup_detector(global_PVs, variableDict)
    aps32id_lib.setup_writer(global_PVs, variableDict, detector_filename)

    aps32id_lib.acquire_pre_dark(variableDict, global_PVs)
    aps32id_lib.acquire_pre_flat(variableDict, global_PVs)

    log_lib.info(' ')
    log_lib.info('  *** Setting for step scan')
    aps32id_lib.move_sample_in(global_PVs, variableDict)
    aps32id_lib.open_shutters(global_PVs, variableDict)
    aps32id_lib.disable_smaract(global_PVs, variableDict)

    if variableDict['Use_Fast_Shutter']: # Fast shutter management:
        uniblitz_status = global_PVs['Fast_Shutter_Uniblitz'].get() # should be returned from the fun enable_fast_shutter in future
        aps32id_lib.enable_fast_shutter(global_PVs, variableDict)
    log_lib.info('  *** Setting for step scan: Done!')

    theta = []
    step_size = ((float(variableDict['SampleEnd_Rot']) - float(variableDict['SampleStart_Rot'])) / (float(variableDict['Projections']) - 1.0))
    if variableDict.has_key('Interlaced') and int(variableDict['Interlaced']) > 0:
#        theta = gen_interlaced_theta()
#        theta = aps32id_lib.gen_interlaced_bidirectional(variableDict) # Tekin algo
        theta = aps32id_lib.gen_interlaced_theta_W(variableDict) # Wolfgang algo
    else:
        theta = np.arange(float(variableDict['SampleStart_Rot']), float(variableDict['Projections'])*step_size, step_size)
    global_PVs['Cam1_FrameType'].put(aps32id_lib.FrameTypeData, wait=True)
    global_PVs['Cam1_NumImages'].put(1, wait=True)
    if variableDict['Recursive_Filter_Enabled'] == 1:
        global_PVs['Proc1_Filter_Enable'].put('Enable')

    for sample_rot in theta:
        log_lib.info(' ')
        log_lib.info('-->Sample Rot: %.3f' % sample_rot)
        global_PVs['Motor_SampleRot'].put(sample_rot, wait=True)
        log_lib.info('Stabilize Sleep (ms)'+str(variableDict['StabilizeSleep_ms']))
        time.sleep(float(variableDict['StabilizeSleep_ms']) / 1000.0)

        # start detector acquire
        if variableDict['Recursive_Filter_Enabled'] == 1:
            aps32id_lib.acquire_proj_recursive_filt(global_PVs, variableDict)
        elif variableDict['ProjectionsPerRot'] > 1:
            aps32id_lib.acq_mutliple_proj_per_rot(global_PVs, variableDict)
        else:
            aps32id_lib.acquire_proj(global_PVs, variableDict)

    if variableDict['Recursive_Filter_Enabled'] == 1:
        global_PVs['Proc1_Filter_Enable'].put('Disable', wait=True)
    if variableDict['ProjectionsPerRot'] > 1:
        theta = aps32id_lib.update_theta_for_more_proj(theta, variableDict)

    aps32id_lib.enable_smaract(global_PVs, variableDict)
    
    if variableDict['Use_Fast_Shutter']: # Fast shutter management
        global_PVs['Fast_Shutter_Uniblitz'].put(uniblitz_status)
        aps32id_lib.disable_fast_shutter(global_PVs, variableDict)

    aps32id_lib.acquire_post_flat(variableDict, global_PVs)
    aps32id_lib.acquire_post_dark(variableDict, global_PVs)

    log_lib.info(' ')
    log_lib.info('  *** Finalizing scan') 
    aps32id_lib.close_shutters(global_PVs, variableDict)

    time.sleep(0.25)
    aps32id_lib.wait_pv(global_PVs['HDF1_Capture_RBV'], 0, 600)
    
    aps32id_lib.add_theta(global_PVs, variableDict, theta)
    aps32id_lib.reset_CCD(global_PVs, variableDict)
    aps32id_lib.reset_angles_0_360(global_PVs)
    log_lib.info('  *** Finalizing scan: Done!')
    


def tiff_2Dscan(variableDict, global_PVs, detector_filename):
    log_lib.info(' ')
    log_lib.info('  *** start_scan')

    def cleanup(signal, frame):
        aps32id_lib.stop_scan(global_PVs, variableDict)
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if variableDict.has_key('StopTheScan'):
        aps32id_lib.stop_scan(global_PVs, variableDict)
        return

    # Start scan sleep in min so min * 60 = sec
    time.sleep(float(variableDict['StartSleep_min']) * 60.0)

    aps32id_lib.setup_detector(global_PVs, variableDict)
    aps32id_lib.setup_tiff_writer(global_PVs, variableDict, detector_filename)

    aps32id_lib.acquire_pre_dark(variableDict, global_PVs)
    aps32id_lib.acquire_pre_flat(variableDict, global_PVs)

    log_lib.info(' ')
    log_lib.info('  *** Setting for 2D tiff scan')
    aps32id_lib.move_sample_in(global_PVs, variableDict)
    aps32id_lib.open_shutters(global_PVs, variableDict)
    aps32id_lib.disable_smaract(global_PVs, variableDict)

    if variableDict['Use_Fast_Shutter']: # Fast shutter management:
        uniblitz_status = global_PVs['Fast_Shutter_Uniblitz'].get() # should be returned from the fun enable_fast_shutter in future
        aps32id_lib.enable_fast_shutter(global_PVs, variableDict)
    log_lib.info('  *** Setting for tiff scan: Done!')

    global_PVs['Cam1_NumImages'].put(1, wait=True)
    # start detector acquire
    if variableDict['Recursive_Filter_Enabled'] == 1:
        global_PVs['Proc1_Filter_Enable'].put('Enable')

    log_lib.info('--> Acquing %i Im with %0.3f sec between exposures' % (int(variableDict['Projections']), float(variableDict['Delay_next_exposure_s'])))
    for i in range(int(variableDict['Projections'])):
        # start detector acquire
        if variableDict['Recursive_Filter_Enabled'] == 1:
            aps32id_lib.acquire_proj_recursive_filt(global_PVs, variableDict)
        else:
            aps32id_lib.acquire_proj(global_PVs, variableDict)

        time.sleep(float(variableDict['Delay_next_exposure_s'])) # Pause between 2 acquisition with shutter closed

    if variableDict['Recursive_Filter_Enabled'] == 1:
        global_PVs['Proc1_Filter_Enable'].put('Disable', wait=True)
    
    aps32id_lib.enable_smaract(global_PVs, variableDict)
    
    if variableDict['Use_Fast_Shutter']: # Fast shutter management
        global_PVs['Fast_Shutter_Uniblitz'].put(uniblitz_status)
        aps32id_lib.disable_fast_shutter(global_PVs, variableDict)

    aps32id_lib.acquire_post_flat(variableDict, global_PVs)
    aps32id_lib.acquire_post_dark(variableDict, global_PVs)

    log_lib.info(' ')
    log_lib.info('  *** Finalizing scan') 
    aps32id_lib.close_shutters(global_PVs, variableDict)

    time.sleep(0.25)
    
    aps32id_lib.reset_CCD(global_PVs, variableDict)
    log_lib.info('  *** Finalizing scan: Done!')
    
    
    