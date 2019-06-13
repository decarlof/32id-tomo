'''
    Data Management Lib for Sector 32-ID internal data transfer
    
'''
from __future__ import print_function

import os
import pathlib
from paramiko import SSHClient
from scp import SCPClient

from tomo_scan_lib import *


def scp(global_PVs, variableDict):
    info('      *** start scp')
    fname_origin = global_PVs['HDF1_FullFileName_RBV'].get(as_string=True)
    p = pathlib.Path(fname_origin)
    
    fname_destination = variableDict['RemoteAnalysisDir'] + p.parts[-3] + '/' + p.parts[-2] + '/'
    info('           *** origin: %s' % fname_origin)
    info('           *** destination: %s' % fname_destination)

    err = os.system('scp -q ' + fname_origin + ' ' + fname_destination + '&')
    if (err == 0):
        info('      *** start scp: Done!')
    else:
        error('      *** scp error: check that destination directory exists at %s' % (fname_destination))