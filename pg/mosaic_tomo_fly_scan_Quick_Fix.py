'''
	FlyScan for Sector 32 ID C

# mosaic_tomo_fly_VDA.py was crashing in June 2018 during an experiment and had trouble to quickly debug it.
    Therefore, I created this quick_fix, basically, extracting tomo_fly_VDA.py and copying into mosaic_tomo_fly_VDA.py 
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

from tomo_scan_lib import *

global variableDict

variableDict = {'PreDarkImages': 10,
			    'PreWhiteImages': 50,
                'Projections': 2500,
                'PostDarkImages': 0,
                'PostWhiteImages': 00,
                'SampleXOut': 5,
#                'SampleYOut': 0.0,
                'SampleXIn': 0.0,
#                'SampleYIn': -10.0,
                'SampleStartPos': 0.0,
                'SampleEndPos': 180.0,
                'StartSleep_min': 0,
                #'StabilizeSleep_ms': 1000,
                'ExposureTime': 0.090,
                'ExposureTime_Flat': 0.090,
                'CCD_Readout': 0.01,
                'IOC_Prefix': '32idcPG3:',
                'FileWriteMode': 'Stream',
                'X_Start': 0.0,
                'X_NumTiles': 1,
                'X_Stop': 0.0,
                'Y_Start': 0.0,
                'Y_NumTiles': 2,
                'Y_Stop': 0.4,
#                'SampleMoveSleep': 0.0,
                'MosaicMoveSleep': 3.0,
                'Auto_focus': 0,
                'Display_live': 1
#                'UseInterferometer': 0
                }

global_PVs = {}

def getVariableDict():
	global variableDict
	return variableDict

def get_calculated_num_projections(variableDict):
	print('get_calculated_num_projections')
	delta = ((float(variableDict['SampleEndPos']) - float(variableDict['SampleStartPos'])) / (float(variableDict['Projections'])))
	slew_speed = (float(variableDict['SampleEndPos']) - float(variableDict['SampleStartPos'])) / (float(variableDict['Projections']) * (float(variableDict['ExposureTime']) + float(variableDict['CCD_Readout'])))
	print 'start pos ',float(variableDict['SampleStartPos']),'end pos', float(variableDict['SampleEndPos'])
	global_PVs['Fly_StartPos'].put(float(variableDict['SampleStartPos']), wait=True)
	global_PVs['Fly_EndPos'].put(float(variableDict['SampleEndPos']), wait=True)
	global_PVs['Fly_SlewSpeed'].put(slew_speed, wait=True)
	global_PVs['Fly_ScanDelta'].put(delta, wait=True)
	time.sleep(3.0)
	calc_num_proj = global_PVs['Fly_Calc_Projections'].get()
	print('Calculated # of prj: %f' % calc_num_proj)
	if calc_num_proj == None:
		print 'Error getting fly calculated number of projections!'
		calc_num_proj = global_PVs['Fly_Calc_Projections'].get()
	if calc_num_proj != int(variableDict['Projections']):
		print 'Updating number of projections from:', variableDict['Projections'], ' to: ', calc_num_proj
		variableDict['Projections'] = int(calc_num_proj)
	print 'Num projections = ',int(variableDict['Projections']), ' fly calc triggers = ', calc_num_proj

def fly_scan(variableDict):
	print 'fly_scan()'
	theta = []
   	# Estimate the time needed for the flyscan
   	FlyScanTimeout = (float(variableDict['Projections']) * (float(variableDict['ExposureTime']) + float(variableDict['CCD_Readout'])) ) + 30
	print 'FlyScanTimeout = ', FlyScanTimeout
	global_PVs['Reset_Theta'].put(1)
#	global_PVs['Fly_Set_Encoder_Pos'].put(1) # ensure encoder value match motor position -- only for the PIMicos
	global_PVs['Cam1_AcquireTime'].put(float(variableDict['ExposureTime']) )

	#num_images1 = ((float(variableDict['SampleEndPos']) - float(variableDict['SampleStartPos'])) / (delta + 1.0))
	num_images = int(variableDict['Projections'])
	global_PVs['Cam1_FrameType'].put(FrameTypeData, wait=True)
	global_PVs['Cam1_NumImages'].put(num_images, wait=True)
	global_PVs['Cam1_TriggerMode'].put('Overlapped', wait=True)
	# start acquiring
	global_PVs['Cam1_Acquire'].put(DetectorAcquire)
	wait_pv(global_PVs['Cam1_Acquire'], 1)
#	print 'Taxi'
#	global_PVs['Fly_Taxi'].put(1, wait=True)
#	wait_pv(global_PVs['Fly_Taxi'], 0)
	print 'Fly'
	global_PVs['Fly_Run'].put(1, wait=True)
	wait_pv(global_PVs['Fly_Run'], 0)
	# wait for acquire to finish
	# if the fly scan wait times out we should call done on the detector
 	if False == wait_pv(global_PVs['Cam1_Acquire'], DetectorIdle, FlyScanTimeout):
		global_PVs['Cam1_Acquire'].put(DetectorIdle)
	# set trigger move to internal for post dark and white
	#global_PVs['Cam1_TriggerMode'].put('Internal')
	global_PVs['Proc_Theta'].put(1)
	#theta_cnt = global_PVs['Theta_Cnt'].get()
	theta = global_PVs['Theta_Array'].get(count=int(variableDict['Projections']))
	return theta


def start_scan(variableDict, detector_filename):
	print 'start_scan()'
#	init_general_PVs(global_PVs, variableDict)
	def cleanup(signal, frame):
		stop_scan(global_PVs, variableDict)
		sys.exit(0)
	signal.signal(signal.SIGINT, cleanup)
	if variableDict.has_key('StopTheScan'):
		stop_scan(global_PVs, variableDict)
		return
	get_calculated_num_projections(variableDict)
	global_PVs['Fly_ScanControl'].put('Custom')
	# Start scan sleep in min so min * 60 = sec
	time.sleep(float(variableDict['StartSleep_min']) * 60.0)
   	print 'Launch Taxi before starting capture'
	global_PVs['Fly_Taxi'].put(1, wait=True)
	wait_pv(global_PVs['Fly_Taxi'], 0)
	setup_detector(global_PVs, variableDict)
	setup_writer(global_PVs, variableDict, detector_filename)
	if int(variableDict['PreDarkImages']) > 0:
		close_shutters(global_PVs, variableDict)
		print 'Capturing Pre Dark Field'
		capture_multiple_projections(global_PVs, variableDict, int(variableDict['PreDarkImages']), FrameTypeDark)
	if int(variableDict['PreWhiteImages']) > 0:
		print 'Capturing Pre White Field'
		global_PVs['Cam1_AcquireTime'].put(float(variableDict['ExposureTime']) )
		open_shutters(global_PVs, variableDict)
		time.sleep(2)
		move_sample_out(global_PVs, variableDict)
		capture_multiple_projections(global_PVs, variableDict, int(variableDict['PreWhiteImages']), FrameTypeWhite)
		global_PVs['Cam1_AcquireTime'].put(float(variableDict['ExposureTime']) )
	move_sample_in(global_PVs, variableDict)
	#time.sleep(float(variableDict['StabilizeSleep_ms']) / 1000.0)
	open_shutters(global_PVs, variableDict)
	# run fly scan
	theta = fly_scan(variableDict)
	###wait_pv(global_PVs['HDF1_NumCaptured'], expected_num_cap, 60)
	if int(variableDict['PostWhiteImages']) > 0:
		print 'Capturing Post White Field'
  		global_PVs['Cam1_AcquireTime'].put(float(variableDict['ExposureTime']) )
		move_sample_out(global_PVs, variableDict)
		capture_multiple_projections(global_PVs, variableDict, int(variableDict['PostWhiteImages']), FrameTypeWhite)
		global_PVs['Cam1_AcquireTime'].put(float(variableDict['ExposureTime']) )
	if int(variableDict['PostDarkImages']) > 0:
		print 'Capturing Post Dark Field'
		close_shutters(global_PVs, variableDict)
		time.sleep(2)
		capture_multiple_projections(global_PVs, variableDict, int(variableDict['PostDarkImages']), FrameTypeDark)
	close_shutters(global_PVs, variableDict)
	time.sleep(0.25)
	wait_pv(global_PVs["HDF1_Capture_RBV"], 0, 600)
	add_theta(global_PVs, variableDict, theta)
	global_PVs['Fly_ScanControl'].put('Standard')
	if False == wait_pv(global_PVs['HDF1_Capture'], 0, 10):
		global_PVs['HDF1_Capture'].put(0)
	reset_CCD(global_PVs, variableDict)


def main():
	tic =  time.time()
	update_variable_dict(variableDict)
	init_general_PVs(global_PVs, variableDict)
	if variableDict.has_key('StopTheScan'):
		stop_scan(global_PVs, variableDict)
		return
	global_PVs['Fly_ScanControl'].put('Custom')
	FileName = global_PVs['HDF1_FileName'].get(as_string=True)
	FileTemplate = global_PVs['HDF1_FileTemplate'].get(as_string=True)
	global_PVs['HDF1_FileTemplate'].put('%s%s.h5')
	if int(variableDict['Y_NumTiles']) <= 1:
		y_itr = 0.0
	else:
		y_itr = ((float(variableDict['Y_Stop']) - float(variableDict['Y_Start'])) / (float(variableDict['Y_NumTiles']) - 1))
	if int(variableDict['X_NumTiles']) <= 1:
		x_itr = 0.0
	else:
		x_itr = ((float(variableDict['X_Stop']) - float(variableDict['X_Start'])) / (float(variableDict['X_NumTiles']) - 1))
	y_val = float(variableDict['Y_Start'])
#	for y in range( int(variableDict['Y_NumTiles']) ):
	for y in range( int(variableDict['Y_NumTiles']) ):
		x_val = float(variableDict['X_Start'])
		global_PVs['Motor_Y_Tile'].put(y_val, wait=True, timeout=600.0)
		#print 'sleep', float(variableDict['MosaicMoveSleep'])
		#time.sleep(float(variableDict['MosaicMoveSleep']))
		#wait_pv(global_PVs["Motor_Y_Tile"], y_val, 600)
		y_val += y_itr
		print('##########')
		print('Move to Y = %0.3f' % y_val)
		print('Y step = %0.3f' % y_itr)
		for x in range( int(variableDict['X_NumTiles']) ):
			print('Move to X = %0.3f' % x_val)
			print('X step = %0.3f' % x_itr)
			start_tile_time = time.time()
			global_PVs["Motor_X_Tile"].put(x_val, wait=True, timeout=600.0)
			print 'sleep', float(variableDict['MosaicMoveSleep'])
			time.sleep(float(variableDict['MosaicMoveSleep']))
			#wait_pv(global_PVs["Motor_X_Tile"], x_val, 600)
			x_val += x_itr
			start_scan(variableDict, FileName+'_y' + str(y) + '_x' + str(x) )
			print('   ---> tile done in %0.3f min' % ((time.time() - start_tile_time)/60))
		if int(variableDict['Auto_focus'])==1:
			auto_focus_microCT(global_PVs, variableDict, 0.04, 20, 'Focus_10X')

	global_PVs['Fly_ScanControl'].put('Standard')
	global_PVs['HDF1_FileName'].put(FileName)
	global_PVs['HDF1_FileTemplate'].put('%s%s_%3.3d.h5')
	print (time.time() - tic)/60


if __name__ == '__main__':
	main()
