# -*- coding: utf-8 -*-
"""
Created on Wed Mar 1 11:50 2017
Description:
    This script processes a number of input spatial feature classes to combine
    them with a source dataset via the ArcPy update_analysis method. This
    method effectively clips from the dataset to be updated the geometry extent
    of the input dataset and then combines the cliped dataset and the update
    dataset.

    Via this method there will be no data overlaid on top of other data in the
    result, i.e. a spatial query will return a single feature not multiple
    features overlaid.

    Checks are completed after the addition of the data via a spatial join to
    match geometry. The expectation is that the number of rows should match
    between the result of the selected rows of spatial join to the resultant
    dataset and the input dataset. These results are written to the log file.

    Finally the same check is completed for the final result agaisnt the list
    of input datasets in a reverse order. The last dataset in should have
    a 1:1 match whereas the last datset in the list is liklely to have other
    data added on top therefore the number of features selected won't match the
    input dataset row count. These results are written to the log file and
    can be reviewed in light of the intial spatial join results via a manual
    check of the result.

Dependencies:
Python 3.x and Python libraries as outlined in the 'Import libraries' section.

@author: Duncan Moore - Geoscience Australia March 2017
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
import doctest
import unittest
import shutil
import arcinfo # Attempt to import arcinfo licence as this is required for update_Analysis
import arcpy


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
    print(pathFileName)
    while os.path.exists(os.path.join(pathFileName,'zipFile' + "_" +
            time.strftime("%Y-%m-%d", tuple_time) + "_v" +
            str(ext)) + '.zip') or os.path.exists(os.path.join(
            pathFileName + "_" + time.strftime(
            "%Y-%m-%d", tuple_time) + "_v" + str(ext)) + '.log'):
        print(os.path.join(pathFileName,'zipFile' + "_" +
            time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext)))
        print("\tStub exists in either zip or log files: _" + time.strftime(
            "%Y-%m-%d", tuple_time) + "_v" + str(ext))
        ext = ext + 1
    print('\t\tNew stub to be written: _' + time.strftime(
        "%Y-%m-%d", tuple_time) + "_v" + str(ext))
    return time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext)

def buildNational(inputs, national1MReclass, gdb):
    '''
    From an input list and a a file use the Update_analysis method to build
    a national dataset. The national dataset is incrementally updated based
    on previously added data.

    Arguments:
    inputs            -- Ordered list of datasets to be updated on top of
                         dataset in the second argument and progressively
                         the previously updated dataset
    national1MReclass -- Base dataset upon which the inputs list datasets
                         are progressively updated on top of
    gdb               -- ESRI Geodatabase to store the incrementally updated
                         datasets

    '''
    def updateSource(outputDataset, field, source):
        '''
        This function updates the table of features that have a NULL or empty
        value in the 'field' parameter field. The table is updated with the
        'source' input paramemter where the 'field' attribute is empty or NULL.

        Arguments:
        outputDataset -- The dataset where the table is to be edited
        field         -- The field to be checked/edited if NULL or empty
        source        -- The name of the source feature dataset that has most
                          recently been added to the national dataset

        '''
        rowCount = 0
        print('\t\tUpdating \'Source\' attribute...')
        log.info('\t\tUpdating \'Source\' attribute...')
        # Create update cursor for feature class
        with arcpy.da.UpdateCursor(outputDataset, field) as cursor:
            # For each row, evaluate the 'field' value (index position
            # of 0), and update 'field' if blank to the 'source'
            for row in cursor:
                if row[0] == None or row[0] == '':
                    rowCount += 1
                    row[0] = source

                # Update the cursor
                cursor.updateRow(row)

        print('\t\tUpdated \'Source\' attribute: {} rows updated'.format(rowCount))
        log.info('\t\tUpdated \'Source\' attribute: {} rows updated'.format(rowCount))
        return

    print('\nStarting spatial join of input datasets to derived dataset...')
    log.info('Starting spatial join of input datasets to derived dataset...')

    # Set the overwrite to True so as to overwrite the layer files
    arcpy.env.overwriteOutput = True

    print(len(inputs), ' feature classes to be updated:')
    cumulativeName = ''
    # Add a new field to the base dataset that all other data will be 'updated'
    # on top of.
    newField = 'Source'
    arcpy.MakeFeatureLayer_management(national1MReclass, 'nationalLayer')
    arcpy.AddField_management("nationalLayer", newField, "TEXT", field_length = 30)
    # Calculate the Source field to match the name of the base dataset
    updateSource('nationalLayer', newField, arcpy.ValidateTableName(
                os.path.split(national1MReclass)[1]))
    toBeUpdated = 'nationalLayer'
    for i in inputs:
        count = 0
        print('\n\t', i)
        log.info(i + ' update_Analysis onto ' + toBeUpdated)
        print('\t\tStarting Update...')
        name = cumulativeName + '_' + arcpy.ValidateTableName(
        os.path.split(i)[1])
        #print os.path.join(gdb, os.path.split(national1MReclass)[1] + os.path.split(i)[1])
        outputDataset = os.path.join(gdb, arcpy.ValidateTableName(
            os.path.split(national1MReclass)[1] + name))
        arcpy.Update_analysis(toBeUpdated,i,outputDataset,"BORDERS","#")
        print('\t\tComplete Update of: ' + os.path.split(i)[1])
        log.info('\tComplete Update of: ' + os.path.split(i)[1])
        log.info('\t\tOutput dataset: ' + outputDataset)
        print('\t\t\tOutput file: ' + outputDataset)
        # Run and report on a spatial join to see that all the features were transferred
        spatialJoin(i, outputDataset)
        # Update the input file to be updated from that which has been created in the last Update_analysis process
        toBeUpdated = os.path.join(gdb, arcpy.ValidateTableName(os.path.split(
        national1MReclass)[1] + name))

        if count == 0:
            count += 1
            updateSource(outputDataset, newField, arcpy.ValidateTableName(
                os.path.split(i)[1]))
        else:
            updateSource(outputDataset, newField, arcpy.ValidateTableName(
                os.path.split(i)[1]))
        cumulativeName = name

    print('\t\tCompleted update of input datasets to build national dataset.')

    return outputDataset

def spatialJoin(i, combinedResult):
    '''
    SpatialJoin function compares the geometry of two files and reports on the
    match to the log file

    Arguments:
    i              -- Source feature class to be compared to second provided
                      feature class
    CombinedResult -- Result feature class to match to the geometry of the
                      first provided feature class

    '''

    print('\tStarting spatial join of input datasets to derived dataset to'
            ' confirm updated dataset matches source dataset')
    log.info('\tStarting spatial join of input datasets to derived dataset to'
            ' confirm updated dataset matches source dataset')

    # Make a feature layer of input data as this is a required input to the
    #  spatial selection tool
    arcpy.MakeFeatureLayer_management(combinedResult, 'combo')
    # Set the overwrite to True so as to overwrite the layer files
    arcpy.env.overwriteOutput = True

    print('\t\t', i)
    log.info(i + ' geometry being assessed against ' + combinedResult)
    # Make a feature layer of input data as this is a required input to the
    #  spatial selection tool
    arcpy.MakeFeatureLayer_management(i, 'source_layer')

    # Run the spatial selection
    arcpy.SelectLayerByLocation_management('combo', 'ARE_IDENTICAL_TO',
                                           'source_layer' , '', 'NEW_SELECTION')
    natCount = arcpy.GetCount_management('combo')#[0]
    sourceCount = arcpy.GetCount_management(i)
    # print/log the number of rows selected
    print('\t\t', os.path.split(i)[1], ' selects ', str(natCount) ,
          ' rows from ' , os.path.split(combinedResult)[1])
    log.info(os.path.split(i)[1] +' selects ' + str(natCount) +
    ' rows from ' + os.path.split(combinedResult)[1])
    # print/log the number of rows in the selecting feature class - should be
    #  the same
    print('\t\t', str(sourceCount), ' rows in ', os.path.split(i)[1])
    log.info('\t\t' + str(sourceCount) + ' rows in: ' + os.path.split(i)[1])
    if int(natCount[0]) == int(sourceCount[0]):
        print('\t\t\tSelected rows match')
        log.info('\t\t\tSelected rows match')
    else:
        print('\t\t\tSelected rows don\'t match')
        log.info('\t\t\tSelected rows don\'t match')

    print('Completed spatial join of input datasets to derived dataset.')

    return

def inputsExist(inputs,combinedResult):
    '''
    The inputsExists function tests whether the input datasets exist. If they
    don't then the script stops. This function uses the ArcPy exists method
    and therefore is capable of testing the existence of ESRI Geodatabases.

    Arguments
    inputs         -- List of dataset inputs
    combinedResult -- Combined dataset made up of the datasets in the inputs
                        variable.
    '''
    if not arcpy.Exists(combinedResult):
        print(combinedResult,'does not exist')
        log.info('Input file: ' + combinedResult + ' does not exist')
        sys.exit()

    for i in inputs:
        print(i)
        if not arcpy.Exists(i):
            print(i, ' does not exist')
            log.info('Input file: ' + i + ' does not exist')
            sys.exit()
        else:

            print('\tInput exists')

#==============================================================================
# Mainline
#==============================================================================


# In python version 3 input is dropped and raw_input is renamed input
#  therefore...
if sys.version_info.major == 3:
    raw_input = input

# This script is designed to run in Python 3.x
if sys.version_info.major == 2:
    print('This script requires being run in Python 3.x')
    sys.exit()

if __name__ == '__main__':
    # Run through the functions running the doctests
#    doctest.testmod()
    # Comment in/out the following line (unittest.main()) to run/not run
    # unit tests
#    unittest.main()
    t0 = time.time()
    # User input to change the workspace
    pathStub = input('Provide the common folder path stub that ends in "\PRODUCTION":' )

    workspace = (os.path.join(os.path.split(pathStub)[0], r'working\buildNationalDataset'))

    os.path.exists(workspace)
    if not os.path.exists(workspace):
        print('Required input Workspace (',workspace ,') does not exist!'
            ' Exit processing')
        sys.exit()

    print(sys.argv[0])
    # Split from the right and only at the first case of the seperator
    print(os.path.split(sys.argv[0].rsplit('.',1)[0])[1])
    # Create a unique logfile based on date and integer
    versionStub = stub(os.path.join(workspace,os.path.split(sys.argv[0].rsplit(
        '.',1)[0])[1]))
    logfile = os.path.join(workspace, os.path.split(sys.argv[0].rsplit(
        '.',1)[0])[1] + '_' + versionStub + '.log')
    print('\nlogfile name:' + logfile)

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
    #Copy script to workspace
    shutil.copy2(sys.argv[0], os.path.join(workspace, os.path.split(
        sys.argv[0])[1].split('.')[0] + '_' + versionStub + '.py'))
    log.info('Script copied to workspace: ' + os.path.join(
        workspace, os.path.split(sys.argv[0])[1].split('.')[0] + versionStub +
        '.py'))
#    assert os.path.exists(logfile)
    # Log the workspace to the logfile
    log.info('Workspace: ' + workspace)


    inputs = [os.path.join(pathStub, r'VIC\output\VIC_250K.gdb\VIC_250K_geol'),
              #os.path.join(pathStub, r'NT\output\NT_250K_output.gdb\NT_250K'), # Left out due to 600 m displacement of features to equivalent in 1:100k data
              os.path.join(pathStub, r'NT\output\NT_100K_output.gdb\NT_100K'),
              os.path.join(pathStub, r'QLD\output\QLD_100K_output.gdb\QLD_100K'),
              os.path.join(pathStub, r'SA\SA_test.gdb\SA_test_NoNULLS'),
              os.path.join(pathStub, r'NSW\output\NSW_z56_output.gdb\NSW_z56_output_GDA94'),
              os.path.join(pathStub, r'VIC\output\VIC_50K.gdb\VIC_50K_geol'),
              os.path.join(pathStub, r'WA\output\WA_50K.gdb\WA_50K'),
              os.path.join(pathStub, r'TAS\output\TAS_25K_output.gdb\tas_25k')]

    national1MReclass = os.path.join(pathStub, r'AUS_1M\output\AUS_1M_output.gdb\AUS_1M')
    gdb = os.path.join(os.path.split(pathStub)[0], r'working\buildNationalDataset\buildNationalDataset.gdb')
    log.info('Data to be stored in: ' + gdb)
    # Check that the inputs exist
    inputsExist(inputs, national1MReclass)

    # Run the spatialJoin function to see whether the geometry matches the source and derived data
    outputDataset = buildNational(inputs, national1MReclass, gdb)

    #Run a second spatial join of source data to result to check the number
    #  of rows matched
    print('\nChecking spatial join of inputs in reverse order of being updated',
        'into the combined dataset')
    log.info('Checking spatial join of inputs in reverse order of being updated'
        'into the combined dataset')
    # Reverse the order in the list
    inputs.reverse()
    # Run the spatial join in reverse list order to compare against earlier spatial join as captured
    #  in the log file.
    for i in inputs:
        spatialJoin(i, outputDataset)
    print('Completed final spatial join checks')
    log.info('Completed final spatial join checks')


    # Print the duration of the script to screen and capture in the log file
    print('\nFinished at: ' + time.strftime("%c", time.localtime(time.time())))
    finishMsg = timer(t0)
    print(finishMsg)
    log.info(finishMsg)
