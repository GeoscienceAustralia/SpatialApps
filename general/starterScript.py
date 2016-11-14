# -*- coding: utf-8 -*-
"""
Created on Wed Nov 2 13:27:35 2016
Description: Base script that offers:
                - capture of duration of the script,
                - logging,
                - archival (zip) of the script and contents of the workspace.
                - creation of unique, matching, log and zip files
            Future development
                - Useful, rather than somewhat arbitrary, testing
                - including a method to capture the GitHub hash of the script
                   used
                       e.g. http://stackoverflow.com/questions/14989858/
                       get-the-current-git-hash-in-a-python-script


@author: Duncan Moore - Geoscience Australia November 2016
"""

#==============================================================================
# Import libraries
#==============================================================================
#import arcpy
#from arcpy.sa import *
import logging as log
import os
import time
import sys
import zipfile
import doctest
import unittest

## Check out any necessary licenses
#arcpy.CheckOutExtension("spatial")
#
##Set overwrite option
#arcpy.env.overwriteOutput = True

#==============================================================================
# Classes
#==============================================================================
class TestTimer(unittest.TestCase):

    def test_timer(self):
        self.assertEqual(timer(time.time()-1440),
                         'Processing complete. Time taken: 0 hours,'
                         '24 minutes, 0 seconds')


#==============================================================================
# Functions
#==============================================================================
def timer(t0):    #
    '''Timer calculates how long the script took to run and prints the results
    to the console

    Usage:
    >>> timer(time.time()-1440)
    Processing complete. Time taken: 0 hours, 24 minutes, 0 seconds

    Arguments
    t0 -- time that the script started
    '''

    return ('Processing complete. Time taken: {0} hours, {1} minutes, {2}'
            ' seconds'.format(int((time.time()-t0)/3600),
            int(((time.time()-t0)%3600)/60), int((time.time()-t0)%60)))

def stub(pathFileName):
    '''use a while loop to create a non-existant, numbered date file name to
    capture multiple processing runs on the same day. Both the zip and the log
    file names are checked for existance so that versions match between the log
    and the zip.

    Usage: #needs to be fixed (add '>>' to include in doctest)
    > stub(os.path.join(r'c:\workspace',r'logfile.log'))
    Unique stub search started (to create unique and matching log and zip file
    date/version stubs)
    c:\workspace\logfile.log
    '2016-11-09_v0'



    Arguments
    pathFileName -- the path being checked for its existence

    '''
    print('Unique stub search started (to create unique and matching log and'
            ' zip file date/version stubs)')
    tuple_time = time.localtime()

    ext = 0
    print pathFileName
#    print os.path.join(pathFileName.split('.')[0] + "_" +
#    time.strftime("%Y-%m-%d", tuple_time))
#    print os.path.join(pathFileName.split('.')[0] + "_" +
#    time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext) + '.log')
    while os.path.exists(os.path.join('zipFile' + "_" +
            time.strftime("%Y-%m-%d", tuple_time) + "_v" +
            str(ext)) + '.zip') or os.path.exists(os.path.join(
            pathFileName.split('.')[0] + "_" + time.strftime(
            "%Y-%m-%d", tuple_time) + "_v" + str(ext)) + '.log'):
        print os.path.join('zipFile' + "_" +
            time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext))
        print "\tStub exists in either zip or log files: _" + time.strftime(
            "%Y-%m-%d", tuple_time) + "_v" + str(ext)
        ext = ext + 1
    print '\t\tNew stub to be written: _' + time.strftime(
        "%Y-%m-%d", tuple_time) + "_v" + str(ext)
    return time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext)



def zipArchive(workspace, script, logg):
    ''' Zip file storage of the inputs, outputs and script used to create the
    results. The folder structure is created in zip file which allows more
    rapid review of the process with this direct pointer.

    The zip file is created in the parent folder from where the rasters are
    located (during testing this was a ESRI file geodatabase).

    Arguments
    workspace -- the location that the input and outputs are stored
    script    -- the script used to generate the results
    logg   -- the logfile created when the script was run
    '''
    zipFILE = os.path.join(workspace, r'zipFile_' + versionStub + '.zip')
    log.info('Empty Zipfile being created: ' + zipFILE)
    print '\nEmpty Zipfile being created: ', zipFILE
    with zipfile.ZipFile(zipFILE, 'w') as zf:
#    zf = zipfile.ZipFile(zipFILE, 'w')
        print '\tzipping workspace'
       # Write the contents of the file geodatabase to the zip file. Note that
       # this requires the full path to the file, not just the file name (f)
        for f in os.listdir(workspace):
            print '\t\t',f
            if f == os.path.split(zipFILE)[1]:
                print '\t\t\tSkipped adding new Zip contents to Zip file'
            elif f == os.path.split(logg)[1]:
                print '\t\t\tSkipped adding logfile - still being written to'
            elif not f.endswith('.lock'):
                zf.write(os.path.join(workspace,f))
                print '\t\t\tWritten:', f
        print '\tzipping script'
        zf.write(os.path.split(script)[1])
        log.info(os.path.split(script)[1] +
            'Script successfully written to the Zipfile')
        print '\tzipping logfile'
        # Write to the log that the zipfile has been created prior to adding
        # the log to the zip
        log.info('Zipfile successfully created')
        zf.write(logg)
        print '  ~~~~ Zipfile successfully created ~~~'

#    zf.close()


    return

#==============================================================================
# Mainline
#==============================================================================


# In python version 3 input is dropped and raw_input is renamed input
#  therefore...
if sys.version_info.major == 3:
    raw_input = input

if __name__ == '__main__':
    # Run through the functions running the doctests
#    doctest.testmod()
    # Comment in/out the following line (unittest.main()) to run/not run
    # unit tests
#    unittest.main()
    t0 = time.time()
    # User input to change the workspace
    workspace = r"C:\Workspace\test"
    os.path.exists(workspace)
    if not os.path.exists(workspace):
        print('Required input Workspace (',workspace ,') does not exist!'
            ' Exit processing')
        sys.exit()

    #arcpy.env.workspace = workspace

    # Create a unique logfile based on date and integer
    versionStub = stub(os.path.join(workspace,r'logfile.log'))
    logfile = os.path.join(workspace, r'logfile_' + versionStub + '.log')
    print '\nlogfile name:' + logfile

    # Configure the logfile
    log.basicConfig(filename=logfile,
                    level=log.DEBUG,
                    filemode='w',# 'w' = overwrite log file, 'a' = append
                    format='%(asctime)s,   Line:%(lineno)d %(levelname)s: %(message)s',
                    datefmt='%a %d/%b/%Y %I:%M:%S %p')
#    doctest.testmod()
    assert os.path.exists(logfile)
    # Log the path and name of the script used to the logfile
    log.info('Script started: ' + sys.argv[0])
#    assert os.path.exists(logfile)
    # Log the workspace to the logfile
    log.info('Workspace: ' + workspace)

    #Zip everything in the workspace
    zipArchive(workspace, sys.argv[0], logfile)
    # Print the duration of the script to screen and capture in the log file
    print('\nFinished at: ' + time.strftime("%c", time.localtime(time.time())))
    finishMsg = timer(t0)
    print time.time()
    print finishMsg
    log.info(finishMsg)
