# -*- coding: utf-8 -*-
"""
Created on Wed Nov 17 2016
Description:
    This script processes a CSV in to an esri shapefile. The CSV is as
    supplied by the University of Queensland in support of the
    Bushfire and Natural Hazards CRC project 'Storm surge:
    resilience to clustered disaster events on the coast'

    Quality assurance to include:
        - via ArcGIS, check that the data plots in the right location relative
          to other date for the location (coordinate reference system check)
        - check on the number of vertices for each polygon match the number of
          coordinate pairs in the source CSV
        - check the number of features in the shapefile matches the CSV
        - manual check in ArcGIS to edit a polygon and confirm the number of
          vertices and the X/Y values are correct



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
import csv
import collections
import gdal
import ogr
import osr
import inspect
import shutil

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

def logAndprint(msg):
    '''
    Print the message to the console and also to the log file at the 'info'
    level.

    Arguments
    message -- Value to be written to the console and to the log file
    '''
    print(msg)
    log.info(' Line: ' + str(inspect.currentframe().f_back.f_lineno) +
        ' :: ' + msg)

    return

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
    print('Unique stub search started (to create unique and matching log'
            ' and zip file date/version stubs)')
    tuple_time = time.localtime()

    ext = 0
    print(pathFileName)
#    print os.path.join(pathFileName.split('.')[0] + "_" +
#    time.strftime("%Y-%m-%d", tuple_time))
#    print os.path.join(pathFileName.split('.')[0] + "_" +
#    time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext) + '.log')
    while os.path.exists(os.path.join('zipFile' + "_" +
            time.strftime("%Y-%m-%d", tuple_time) + "_v" +
            str(ext)) + '.zip') or os.path.exists(os.path.join(
            pathFileName.split('.')[0] + "_" + time.strftime(
            "%Y-%m-%d", tuple_time) + "_v" + str(ext)) + '.log'):
        print(os.path.join('zipFile' + "_" +
            time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext)))
        print( "\tStub exists in either zip or log files: _" +
            time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext))
        ext = ext + 1
    print('\t\tNew stub to be written: _' + time.strftime(
        "%Y-%m-%d", tuple_time) + "_v" + str(ext))

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
#    log.info('Empty Zipfile being created: ' + zipFILE)
    logAndprint('\nEmpty Zipfile being created: ', zipFILE)
    with zipfile.ZipFile(zipFILE, 'w') as zf:
#    zf = zipfile.ZipFile(zipFILE, 'w')
        logAndprint('\tzipping workspace')
       # Write the contents of the file geodatabase to the zip file. Note that
       # this requires the full path to the file, not just the file name (f)
        for f in os.listdir(workspace):
            logAndprint('\t\t',f)
            if f == os.path.split(zipFILE)[1]:
                logAndprint('\t\t\tSkipped adding new Zip contents to Zip file')
            elif f == os.path.split(logg)[1]:
                logAndprint('\t\t\tSkipped adding logfile - still being written to')
            elif not f.endswith('.lock'):
                zf.write(os.path.join(workspace,f))
                logAndprint('\t\t\tWritten:', f)
        logAndprint('\tzipping script')
        zf.write(os.path.split(script)[1])
        log.info(os.path.split(script)[1] +
            'Script successfully written to the Zipfile')
        logAndprint('\tzipping logfile')
        # Write to the log that the zipfile has been created prior to adding
        # the log to the zip
        zf.write(logg)
        logAndprint('  ~~~~ Zipfile successfully created ~~~')

#    zf.close()


    return

def Write_Dict_To_Shapefile_osgeo(totalList, shapefileName, EPSG):
    '''
    Adapted from
    https://github.com/GeoscienceAustralia/LidarProcessingScripts/RasterIndexTool_GDAL.py
    This function takes a list of dictionaries where each row in the list
    is a feature consisting of the X/Y geometries in the dictionary for each
    item in the list.

    Arguments:
    totalList     -- List of dictionaries
    shapefileName -- Name of the shapefile to be created/overwritten


    '''
    gdal.UseExceptions()

    shapePath = os.path.join(workspace,shapefileName)

    # Get driver
    driver = ogr.GetDriverByName('ESRI Shapefile')

    # Create shapeData, overwrite the data if it exists
    os.chdir(workspace)
    if os.path.exists(shapefileName):
        print('Shapefile exists and will be deleted')
        driver.DeleteDataSource(shapePath)
        assert not os.path.exists(shapePath)

    shapeData = driver.CreateDataSource(shapefileName)

    # Create spatialReference for output
    outputspatialRef = osr.SpatialReference()

    # Set coordinate reference system 
    outputspatialRef.ImportFromEPSG(EPSG)

    # Create layer
    layer = shapeData.CreateLayer(shapePath, srs=outputspatialRef, geom_type=ogr.wkbLineString)

    # add fields
    fieldNames = ["Date", "Time"]
    for n in range(0, len(fieldNames)):

        # add short text fields - convoluted method but was more extensive
        # in Jonah's script to capture more fields and various field types.
        if fieldNames[n] in ["Date", "Time"]:
            fieldstring = str(fieldNames[n])
            field_name = ogr.FieldDefn(fieldstring, ogr.OFTString)
            field_name.SetWidth(24)
            layer.CreateField(field_name)

    # Create polyline object
    line = ogr.Geometry(ogr.wkbLineString)
    count = 0
    for entry in totalList:
        logAndprint( 'Row {0} being processed'.format(count))
        dictCounter = 0
#        while dictCounter < 10:
        logAndprint('Dictionary count {0}'.format(len(totalList[count])))
        for key, value in totalList[count].iteritems():
            logAndprint('\n{0} row, {1} vertex being created'.format(count, dictCounter))
            logAndprint('\tKey: {0}, value: {1}'.format(key, value))
    #        print(count)
            if dictCounter < 2:
                logAndprint('\tRow passed')
                pass
                dictCounter += 1

            else:
                line.AddPoint(float(key), float(value))
                logAndprint('\t\t{0} and {1} vertex added to line'.format(key,value))
                dictCounter += 1

#        poly = ogr.Geometry(ogr.wkbLineString)
#        logAndprint('Adding geometry')
#        poly.AddGeometry(line)

        # Create feature
        layerDefinition = layer.GetLayerDefn()
        feature = ogr.Feature(layerDefinition)
        feature.SetGeometry(line)
        # Set the FID field to the count
        feature.SetFID(count)

        # Calculate fields
        logAndprint('Calculating "Date" & "Time" fields')

        # Date is supplied in YYYY/MM/DD
        date = str(totalList[count].keys()[1].split()[0])
        # For animation in ArcGIS the date needs to be in the form
        # DD/MM/YYYY
        reformattedDate = (date.split('/')[2] + '/' + date.split('/')[1] + '/' + date.split('/')[0])
        logAndprint('reformatted date:' + reformattedDate)
        feature.SetField('Date',str(reformattedDate))
        feature.SetField('Time',str(totalList[count].keys()[1].split()[1]))

        # Save feature
        layer.CreateFeature(feature)

        logAndprint('{0} rows processed'.format(count))
        count += 1

        # Empty the ring otherwise the vertices are accumulatied
        line.Empty()


    # Cleanup
    #poly.Destroy()
    feature.Destroy()

    # Cleanup
    shapeData.Destroy()
    # Return
    return shapePath

def csvProcessing():
    '''
    Process the CSV file into a list of dictionaries. Each item in the list
    contains the dictionary that is made up of key/values that are drawn from
    two rows in the CSV file.

    '''
    count = 0
    with open(shoreline, 'rb') as csvfile:
#        print shoreline.name
        rowReader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in rowReader:
            logAndprint('Row {0} being processed'.format(count))
            # For every second row, but not including row 0, create a dict
            # of the X/Y pairs from odd/even rows respectively
            if count % 2 == 0 and count != 0:
                values = list(row)
                dictionary = collections.OrderedDict(zip(keys,values))
                totalList.append(dictionary)
                del values
                del keys
    #                if count == 2:
    #                    Write_Dict_To_Shapefile_osgeo(dictionary, shapefileName)

            else:
                # if odd row number then create the list of X keys
                keys = list(row)
            if count == 2:
#                logAndprint(dictionary)
                logAndprint('Dictionary length: ' + str(len(dictionary)))

            count += 1

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
    # Start the timer
    t0 = time.time()

    # Required user input to specify the workspace where the CSV to be processed exists
    workspace = raw_input('Enter the folder containing the CSV to be processed: ')

    # EPSG code representing the coordinate reference system of the XY pairs in the CSV
    EPSG = int(raw_input('Enter the EPSG projection code (28356 = MGA56, 28354 = MGA54): '))
    assert type(EPSG) == int

    # CSV to be processed in the workspace
    csvFile = raw_input('Enter the CSV file name of the file to be processed: ')

    # Shapefile to be created
    shapefileName = csvFile.split('.')[0] + r'.shp'

    # Test to ensure the workspace provided exists
    os.path.exists(workspace)
    if not os.path.exists(workspace):
        print('Required input Workspace (',workspace ,') does not exist!'
            ' Exit processing')
        sys.exit()

    # Create a unique logfile based on date and integer
    versionStub = stub(os.path.join(workspace,r'logfile.log'))
    try: 
        log.shutdown()
    except:
        print('Logfile does not exist')
    logfile = os.path.join(workspace, r'logfile_' + versionStub + '.log')
    print('\nlogfile name:' + logfile)

    #Copy the python file being run to the destination folder to keep a copy of the script with the outputs
    # Use the versionStub so as to link the log file with the Python script
    shutil.copy2(sys.argv[0], os.path.join(workspace, os.path.split(sys.argv[0])[1].split('.')[0] + '_' + versionStub + '.py'))

    # Configure the logfile
    log.basicConfig(filename=logfile,
                    level=log.DEBUG,
                    filemode='w',# 'w' = overwrite log file, 'a' = append
                    format='%(asctime)s,   Line:%(lineno)d %(levelname)s: %(message)s',
                    datefmt='%a %d/%b/%Y %I:%M:%S %p')
#    doctest.testmod()
    # Log the path and name of the script used to the logfile
    log.info('Script started: ' + sys.argv[0])
    log.info('EPSG code: ' + str(EPSG))
    # Ensure the logfile exists
    assert os.path.exists(logfile)
    # Log the workspace to the logfile
    log.info('Workspace: ' + workspace)
    log.info('CSV: ' + os.path.join(workspace, csvFile))
    log.info('Output shapefile: ' + os.path.join(workspace, shapefileName))
    log.info(sys.argv[0] + ' saved to ' + os.path.split(sys.argv[0])[1].split('.')[0] + '_' + versionStub + '.py')

    shoreline = os.path.join(workspace, csvFile)

    dictionary = {}



    # List to contain dictionaries
    totalList = []

    csvProcessing()


    logAndprint('\ntotalList length: {0}'.format(len(totalList)))

    Write_Dict_To_Shapefile_osgeo(totalList, shapefileName, EPSG)
#    for entry in totalList:
#        print entry
#    print len(totalList)

    #Zip everything in the workspace
#    zipArchive(workspace, sys.argv[0], logfile)
    # Print the duration of the script to screen and capture in the log file
    print('\nFinished at: ' + time.strftime("%c", time.localtime(time.time())))
    finishMsg = timer(t0)
    print(finishMsg)
    log.info(finishMsg)
    # Close the logfile
    log.shutdown()
    # Remove variables from memory
    del t0
    del workspace
    del EPSG
    del csvFile
    del shapefileName
    del versionStub
    del logfile
    del dictionary
    del totalList
    del finishMsg
    del shoreline
    
    
