'''
    TomoScan for Sector 32 ID C

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
import numpy
from libs.aps32id_lib import *
#import matplotlib.pyplot as plt
global variableDict

variableDict = {'PreDarkImages': 5,
        'PreWhiteImages': 10,
        'Projections': 721,
        'ProjectionsPerRot': 1, # saving several images / angle
        'PostDarkImages': 0,
        'PostWhiteImages': 0,
        'SampleXOut': 0,
#        'SampleYOut': 0.1,
#        'SampleZOut': 0,
#        'SampleRotOut': 90.0,
        'SampleXIn': 0.0,
#        'SampleYIn': 0.1,
#        'SampleZIn': 0.0,
        'SampleStart_Rot': 0.0,
        'SampleEnd_Rot': 180.0,
        'StartSleep_min': 0,
        'StabilizeSleep_ms': 0,
        'ExposureTime': 0.5,
        'ExposureTime_Flat': 0.5,
        'IOC_Prefix': '32idcPG3:',
        'FileWriteMode': 'Stream',
        'Interlaced': 0,
        'Interlaced_Sub_Cycles': 4,
        'rot_speed_deg_per_s': 2,
        'Recursive_Filter_Enabled': 0,
        'Recursive_Filter_N_Images': 5,
        'Recursive_Filter_Type': 'RecursiveAve',
        'Use_Fast_Shutter': 1,
        'Display_live': 1
        }

global_PVs = {}

def getVariableDict():
    global variableDict
    return variableDict

def update_theta_for_more_proj(orig_theta):
    new_theta = []
    for val in orig_theta:
        for j in range( int(variableDict['ProjectionsPerRot']) ):
            new_theta += [val]
    return new_theta

def tomo_scan():
    print('tomo_scan()')
    theta = []
    step_size = ((float(variableDict['SampleEnd_Rot']) - float(variableDict['SampleStart_Rot'])) / (float(variableDict['Projections']) - 1.0))
    if variableDict.has_key('Interlaced') and int(variableDict['Interlaced']) > 0:
#        theta = gen_interlaced_theta()
        theta = gen_interlaced_bidirectional(variableDict)
    else:
        theta = numpy.arange(float(variableDict['SampleStart_Rot']), float(variableDict['Projections'])*step_size, step_size)
    global_PVs['Cam1_FrameType'].put(FrameTypeData, wait=True)
    global_PVs['Cam1_NumImages'].put(1, wait=True)
    if variableDict['Recursive_Filter_Enabled'] == 1:
        global_PVs['Proc1_Filter_Enable'].put('Enable')

    for sample_rot in theta:
        print('Sample Rot:', sample_rot)
        global_PVs['Motor_SampleRot'].put(sample_rot, wait=True)
        print('Stabilize Sleep (ms)', variableDict['StabilizeSleep_ms'])
        time.sleep(float(variableDict['StabilizeSleep_ms']) / 1000.0)

        # start detector acquire
        if variableDict['Recursive_Filter_Enabled'] == 1:
            global_PVs['Proc1_Callbacks'].put('Enable', wait=True)
            for k in range(int(variableDict['Recursive_Filter_N_Images'])):
                global_PVs['Cam1_Acquire'].put(DetectorAcquire)
                wait_pv(global_PVs['Cam1_Acquire'], DetectorAcquire, 2)
                if variableDict['Use_Fast_Shutter']:
                    global_PVs['Fast_Shutter_Trigger'].put(1)
#                    wait_pv(global_PVs['Fast_Shutter_Trigger'], DetectorIdle, 60)
                    wait_pv(global_PVs['Cam1_Acquire'], DetectorIdle, 60)
                else:
                    global_PVs['Cam1_SoftwareTrigger'].put(1)
                    wait_pv(global_PVs['Cam1_Acquire'], DetectorIdle, 60)
        elif variableDict['ProjectionsPerRot'] > 1:
            for j in range( int(variableDict['ProjectionsPerRot']) ):
                global_PVs['Cam1_Acquire'].put(DetectorAcquire)
                wait_pv(global_PVs['Cam1_Acquire'], DetectorAcquire, 2)
                if variableDict['Use_Fast_Shutter']:
                    global_PVs['Fast_Shutter_Trigger'].put(1)
#                    wait_pv(global_PVs['Fast_Shutter_Trigger'], DetectorIdle, 60)
                    wait_pv(global_PVs['Cam1_Acquire'], DetectorIdle, 60)
                else:
                    global_PVs['Cam1_SoftwareTrigger'].put(1)
                    wait_pv(global_PVs['Cam1_Acquire'], DetectorIdle, 60)
        else:
            global_PVs['Cam1_Acquire'].put(DetectorAcquire)
            wait_pv(global_PVs['Cam1_Acquire'], DetectorAcquire, 2)
            if variableDict['Use_Fast_Shutter']:
                global_PVs['Fast_Shutter_Trigger'].put(1)
#                wait_pv(global_PVs['Fast_Shutter_Trigger'], DetectorIdle, 60)
                wait_pv(global_PVs['Cam1_Acquire'], DetectorIdle, 60)
            else:
                global_PVs['Cam1_SoftwareTrigger'].put(1)
                wait_pv(global_PVs['Cam1_Acquire'], DetectorIdle, 60)

    if variableDict['Recursive_Filter_Enabled'] == 1:
        global_PVs['Proc1_Filter_Enable'].put('Disable', wait=True)
    if variableDict['ProjectionsPerRot'] > 1:
        theta = update_theta_for_more_proj(theta)

    return theta


def full_tomo_scan(variableDict, detector_filename):
    print('start_scan()')
    init_general_PVs(global_PVs, variableDict)
    if variableDict.has_key('StopTheScan'):
        stop_scan(global_PVs, variableDict)
        return

    # Start scan sleep in min so min * 60 = sec
    time.sleep(float(variableDict['StartSleep_min']) * 60.0)
    setup_detector(global_PVs, variableDict)
    setup_writer(global_PVs, variableDict, detector_filename)
    if int(variableDict['PreDarkImages']) > 0:
        close_shutters(global_PVs, variableDict)
        print('Capturing Pre Dark Field')
        capture_multiple_projections(global_PVs, variableDict, int(variableDict['PreDarkImages']), FrameTypeDark)
    if int(variableDict['PreWhiteImages']) > 0:
        print('Capturing Pre White Field')
        global_PVs['Cam1_AcquireTime'].put(float(variableDict['ExposureTime_Flat']) )
        open_shutters(global_PVs, variableDict)
        move_sample_out(global_PVs, variableDict)
        capture_multiple_projections(global_PVs, variableDict, int(variableDict['PreWhiteImages']), FrameTypeWhite)
        global_PVs['Cam1_AcquireTime'].put(float(variableDict['ExposureTime']) )
    move_sample_in(global_PVs, variableDict)
    open_shutters(global_PVs, variableDict)
    # Fast shutter management:
    uniblitz_status = global_PVs['Fast_Shutter_Uniblitz'].get()
    if variableDict['Use_Fast_Shutter']:
        enable_fast_shutter(global_PVs, variableDict)
        global_PVs['Fast_Shutter_Exposure'].put(float(variableDict['ExposureTime']) )

    print('Disabling the Smaract')
    disable_smaract(global_PVs, variableDict)
        
    # Main scan:
    theta = tomo_scan()

    print('Re-enabling the Smaract')
    enable_smaract(global_PVs, variableDict)
    
    # Fast shutter management:
    global_PVs['Fast_Shutter_Uniblitz'].put(uniblitz_status)
    if variableDict['Use_Fast_Shutter']:
        disable_fast_shutter(global_PVs, variableDict)

    if int(variableDict['PostWhiteImages']) > 0:
        print('Capturing Post White Field')
        global_PVs['Cam1_AcquireTime'].put(float(variableDict['ExposureTime_Flat']) )
        move_sample_out(global_PVs, variableDict)
        capture_multiple_projections(global_PVs, variableDict, int(variableDict['PostWhiteImages']), FrameTypeWhite)
        global_PVs['Cam1_AcquireTime'].put(float(variableDict['ExposureTime']) )
    if int(variableDict['PostDarkImages']) > 0:
        print('Capturing Post Dark Field')
        close_shutters(global_PVs, variableDict)
        capture_multiple_projections(global_PVs, variableDict, int(variableDict['PostDarkImages']), FrameTypeDark)
    close_shutters(global_PVs, variableDict)
    wait_pv(global_PVs["HDF1_Capture_RBV"], 0, 600)
    add_theta(global_PVs, variableDict, theta)
    reset_CCD(global_PVs, variableDict)
#    plt.plot(theta, 'b-', theta, 'r.'), plt.grid(), plt.xlabel('indices'), plt.ylabel('angles (deg)'), title('Interlaced scan')

def main():
    update_variable_dict(variableDict)
    init_general_PVs(global_PVs, variableDict)
    FileName = global_PVs['HDF1_FileName'].get(as_string=True)
    full_tomo_scan(variableDict, FileName)

if __name__ == '__main__':
    main()

