#######################
##### To be tested!
##### for each energy step, a projection and then a flat field is being acquired
##### The script is calling the move move_energy function from tomo_scan_lib

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
import math

from tomo_scan_lib import *

global variableDict
variableDict = {'PreDarkImages': 0,
				'PreWhiteImages': 0,
				'PostDarkImages': 0,
				'PostWhiteImages': 0,
        		'Projections': 100,
				'SampleXOut': 0.0,
				'SampleYOut': 0.0,
				'SampleXIn': 0.0,
				'SampleYIn': 0.0,
				'StartSleep_min': 0,
				'StabilizeSleep_ms': 1000,
				'ExposureTime': 2,
				'IOC_Prefix': '32idcPG3:',
				'FileWriteMode': 'Stream',
				'Energy_Start': 8.951,
				'Energy_End': 9.081,
				'Energy_Step': 0.001,
				'ZP_diameter': 180,
				'drn': 60,
				'constant_mag': 1, # 1 means CCD will move to maintain constant magnification
				'Offset': 0.17,
#				'BSC_diameter': 1320,
#				'BSC_drn': 60
				}

global_PVs = {}

def getVariableDict():
	global variableDict
	return variableDict

def energy_scan(variableDict):
	
    # Extract variables from variableDict:
    Energy_Start = float(variableDict['Energy_Start'])
    Energy_End = float(variableDict['Energy_End'])
    Energy_Step = float(variableDict['Energy_Step'])
    ZP_diameter = float(variableDict['ZP_diameter'])
    Offset = float(variableDict['Offset'])
    drn = float(variableDict['drn'])

    StabilizeSleep_ms = float(variableDict['StabilizeSleep_ms'])
    
    global_PVs['Cam1_NumImages'].put(1, wait=True)
    global_PVs['DCMmvt'].put(1, wait=True)
    global_PVs['GAPputEnergy'].put(Energy_Start, wait=True)
    wait_pv(global_PVs['EnergyWait'], 0.05)
    energy = Energy_Start
    num_iters = int( (Energy_End - Energy_Start) / Energy_Step ) +1
    energies = [
        np.arange(8951, 8971, 20), # 1 radio
        np.arange(8971, 9011, 1), # 35 radio
        np.arange(9011, 9116, 35), # 2 radio
    ]
    energies = np.concatenate(energies, axis=0) / 1000.

    totalProj = n_pre_dark + 2 * len(energies)
    global_PVs['HDF1_NumCapture'].put(totalProj)

    print 'Capturing ', num_iters, 'energies'
#    for i in range(num_iters):
    for i in energies:
		print 'Energy ', energy
		print 'Stabilize Sleep (ms)', StabilizeSleep_ms
		time.sleep(StabilizeSleep_ms / 1000.0)

		variableDict.update({'new_Energy': energy})
		# Call move energy function: adjust ZP (& CCD position if constant mag is checked)
		move_energy(global_PVs, variableDict)
  
		print 'Stabilize Sleep (ms)', variableDict['StabilizeSleep_ms']
		time.sleep(StabilizeSleep_ms / 1000.0)

		# save theta to array
		energy_arr += [energy]

		# Sample projection acquisition:
		#-------------------------------
		global_PVs['Cam1_FrameType'].put(FrameTypeData, wait=True) # Prepare datatype for the hdf5 file: next proj will be a sample proj
		# start detector acquire
		global_PVs['Cam1_Acquire'].put(DetectorAcquire)
		wait_pv(global_PVs['Cam1_Acquire'], DetectorAcquire, 2)
		global_PVs['Cam1_SoftwareTrigger'].put(1)
		wait_pv(global_PVs['Cam1_Acquire'], DetectorIdle, 60)

		# Flat-field projection acquisition:
		#-------------------------------
		move_sample_out()
		global_PVs['Cam1_FrameType'].put(FrameTypeWhite, wait=True) # Prepare datatype for the hdf5 file: next proj will be a flat-field
		# start detector acquire
		global_PVs['Cam1_Acquire'].put(DetectorAcquire, wait=True)
		# wait for acquire to finish
		wait_pv(global_PVs['Cam1_Acquire'], DetectorIdle)
		move_sample_in()

		# update Energy to the next one
		energy += Energy_Step

    global_PVs['DCMmvt'].put(0)
    return energy_arr



def add_energy_arr(energy_arr):
	print 'add_energy_arr()'
	fullname = global_PVs['HDF1_FullFileName_RBV'].get(as_string=True)
	try:
		hdf_f = h5py.File(fullname)
		energy_ds = hdf_f.create_dataset('/exchange/energy', (len(energy_arr),))
		energy_ds[:] = energy_arr[:]
		hdf_f.close()
	except:
		traceback.print_exc(file=sys.stdout)


def start_scan(variableDict, detector_filename):
    while 1:
	    print 'start_scan()'
	    init_general_PVs(global_PVs, variableDict)
	    if variableDict.has_key('StopTheScan'): # stopping the scan in a clean way
		    stop_scan(global_PVs, variableDict)
		    return
	    # Start scan sleep in min so min * 60 = sec
	    time.sleep(float(variableDict['StartSleep_min']) * 60.0)
	    setup_writer(global_PVs, variableDict, detector_filename)
	    if int(variableDict['PreDarkImages']) > 0:
		    close_shutters()
		    print 'Capturing Pre Dark Field'
		    capture_multiple_projections(int(variableDict['PreDarkImages']), FrameTypeDark)
	    move_sample_in(global_PVs, variableDict)
	    open_shutters(global_PVs, variableDict)
	    energy_arr = []
    #	global_PVs['Cam1_FrameType'].put(FrameTypeWhite, wait=True)
	    energy_arr += energy_scan(variableDict)
    #	move_sample_out()
    #	global_PVs['Cam1_FrameType'].put(FrameTypeData, wait=True)
    #	energy_scan()
	    close_shutters(global_PVs, variableDict)
	    add_energy_arr(energy_arr)
	    #move_dataset_to_run_dir()


def main():
	update_variable_dict(variableDict)
	init_general_PVs(global_PVs, variableDict)
	FileName = global_PVs['HDF1_FileName'].get(as_string=True)
	start_scan(variableDict, FileName)


if __name__ == '__main__':
	main()

