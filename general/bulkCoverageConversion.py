# -*- coding: utf-8 -*-
"""
Created on Tue Nov 9 12:57:15 2016

@author: Duncan Moore
This script iterates through a user specified folder structure (ws) and
converts the coverages found into datasets/feature classes in esri 
File Geodatabases. The folder structure of the input dataset is partly 
replicated in the output folder so as to link the File Geodatabases to 
the source data.

Coverage files considered are in the coverageFiles list and include:
    'label', 'polygon', 'point', 'tic', 'annotation.vpf', 'node', 'arc'

The log file is created each time the script is run with a unique date/version
stamp. Review the log file for a record of what was processed and any data
that failed processing (ERROR level reporting).

Dependencies:
    os
    arcpy
    sys
    logging
    time

"""
#==============================================================================
# Import modules
#==============================================================================


import os
import arcpy
import logging as log
import sys
import time


#==============================================================================
# Functions
#==============================================================================

def timer(t0):    #
    '''Timer calculates how long the script took to run and prints the results
    to the console

    Usage:
    >>> timer(time.time()-1440)
    Time taken: 0 hours, 24 minutes, 0 seconds

    Arguments
    t0 -- time that the script started
    '''

    print('Time taken: {0} hours, {1} minutes, {2} seconds'.format(int((time.time()-t0)/3600), int(((time.time()-t0)%3600)/60), int((time.time()-t0)%60)))
    log.info('Processing complete. Time taken: {0} hours, {1} minutes, {2} seconds'.format(int((time.time()-t0)/3600), int(((time.time()-t0)%3600)/60), int((time.time()-t0)%60)))

    return

def stub(pathFileName):
    '''use a while loop to create a non-existant, numbered date file name to
    capture multiple processing runs on the same day. Both the zip and the log
    file names are checked for existance so that versions match between the log
    and the zip.

    Usage:
    >>> stub(os.path.join(r'c:\workspace',r'logfile.log'))
    Unique stub search started (to create unique and matching log and zip file date/version stubs)
    c:\workspace\logfile.log
            New stub to be written: _2016-11-07_v0
    '2016-11-07_v0'



    Arguments
    pathFileName -- the path being checked for its existence

    '''
    print 'Unique stub search started (to create unique and matching log and zip file date/version stubs)'
    tuple_time = time.localtime()

    ext = 0
    print pathFileName
#    print os.path.join(pathFileName.split('.')[0] + "_" + time.strftime("%Y-%m-%d", tuple_time))
#    print os.path.join(pathFileName.split('.')[0] + "_" + time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext) + '.log')
    while os.path.exists(os.path.join('zipFile' + "_" + time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext)) + '.zip') or os.path.exists(os.path.join(pathFileName.split('.')[0] + "_" + time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext)) + '.log'):
        print os.path.join('zipFile' + "_" + time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext))
        print "\tStub exists in either zip or log files: _" + time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext)
        ext = ext + 1
    print '\t\tNew stub to be written: _' + time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext)
    return time.strftime("%Y-%m-%d", tuple_time) + "_v" + str(ext)

def coverageReport(folder, coverages, outFolder):
    ''' Create a list of coverages in the input folder and for each coverage
    iterate through the coverage file list (a coverage is a collection of files)
    and covert each file to a feature dataset in a File Geodatabase.

    The folder structure in the outFolder is replicated partly from the folder
    input to this function. see the 'e' variabale for the point that the folder
    structure is replicated.

    Arguments
    folder    -- input folder to be assessed for coverages within
    coverages -- number of coverages processed
    outFolder -- output folder to where the input folder strucutre is then
                  partly replicated and to house the converted data.

    '''
    # List of coverage file types that are converted if they exist
    coverageFiles = ['label', 'polygon', 'point', 'tic', 'annotation.vpf', 'node', 'arc'] #''annotation.igds' exist but I'm not sure what they are - they cause erros

    #Set the workspace, needed as this is where arcpy.ListDatasets() function identifies datasets
    arcpy.env.workspace = folder
    print '  Workspace: ' + folder

    #Work through the list of the coverages in the tile (folder)
    # note this uses the 'ListDatasets' function, not 'ListFeatureClasses'
    coverageList = arcpy.ListDatasets('','Coverage')
    print '\t',len(coverageList), 'Coverages found'
    if len(coverageList) == 0:
        print '\t0 Coverages'
        log.info(folder)
        log.info('\t0 Coverages found')
    else:
        # Split the folder path to use the path past this point to create the
        # output folder structure to identify the link to source data
        e = folder.split('GAB_hydrogeology')[1]
        conCatFolder = outFolder + os.sep + e
        print '\toutfolder: ' + conCatFolder
        # If the folder and file geodatabase don't exist in the output folder then create them
        if not os.path.exists(conCatFolder):
            os.makedirs(conCatFolder)
        if not arcpy.Exists(os.path.join(conCatFolder, "coverageConversion.gdb")):
            arcpy.CreateFileGDB_management(conCatFolder, "coverageConversion.gdb")

        for f in coverageList:
            print '#### ', f, ' ###'
            coverages += 1
            print coverages, 'of total processed.', len(coverageList), 'coverages in', folder, 'being processed'
            # Validating table name is not picking up the first character being a number
            if f[0].isdigit():
                fValid = '_' + arcpy.ValidateTableName(f)
            else:
                fValid = arcpy.ValidateTableName(f)
            print '\tValidated name to suit geodatabase:', fValid
            #Create a feature dataset for the coverage as per the coverage name, apply the Coodinate Reference System from the coverage to the feature dataset
            # Used try statement as where the coverage is corrupt the coordinate reference system can not be applied to the new feature dataset and causes the script to exit.
            try:
                # Usage: CreateFeatureDataset_management (out_dataset_path, out_name, {spatial_reference})
                arcpy.CreateFeatureDataset_management(os.path.join(conCatFolder, "coverageConversion.gdb"),fValid,os.path.join(folder, f))
            except:
                print '### Could not create', os.path.join(conCatFolder, "coverageConversion.gdb",fValid)
                log.exception('### Could not create' + os.path.join(conCatFolder, "coverageConversion.gdb",fValid))
            print '\tInput: ' + os.path.join(folder, f)
            #For coverage file type within a coverage convert this file to a feature class within the feature dataset
            if arcpy.Exists(os.path.join(conCatFolder, "coverageConversion.gdb",fValid)):
                for c in coverageFiles:
                    try:
                        if arcpy.Exists(os.path.join(folder,f, c)):
                            print '\t\t\t' + os.path.join(f, c), 'coverage exists'
                            log.info(os.path.join(folder,f, c) + ' coverage exists')
                            #Treat the 'annotation.vpf' differently as the name needs to change, remove the '.' to be applied in the geodatabase
                            if c in ['annotation.vpf']:
                                arcpy.arcpy.ImportCoverageAnnotation_conversion(f + os.sep + c, os.path.join(conCatFolder, "coverageConversion.gdb",fValid), arcpy.ValidateTableName(fValid + "_" + c.replace(".","_")),50000)
                                print '\t\t\t\t' + c + ' converted to vpf table in ' + os.path.join(conCatFolder, "coverageConversion.gdb",fValid, fValid + "_" + c.replace(".","_"))
                                log.info('\t\t'+ c + ' converted to vpf table in ' + os.path.join(conCatFolder, "coverageConversion.gdb",fValid, fValid + "_" + c.replace(".","_")))
                                arcpy.env.workspace = os.path.join(conCatFolder, "coverageConversion.gdb",fValid)
                                print '\t\t\t\t\t' + str(arcpy.GetCount_management(fValid + "_" + c.replace(".","_"))) + ' output rows counted'
                                log.info('\t\t'+ str(arcpy.GetCount_management(fValid + "_" + c.replace(".","_"))) + ' output rows counted')
                            #For the remaining coverage file types convert them to a feature class in the feature dataset
                            else:
                                arcpy.FeatureClassToFeatureClass_conversion(f + os.sep + c, os.path.join(conCatFolder, "coverageConversion.gdb",fValid), fValid + "_" + c)
                                print '\t\t\t\t' + c + ' converted to feature class in ' + os.path.join(conCatFolder, "coverageConversion.gdb")
                                log.info('\t\t'+ c + ' converted to feature class in ' + os.path.join(conCatFolder, "coverageConversion.gdb"))
                                arcpy.env.workspace = os.path.join(conCatFolder, "coverageConversion.gdb",fValid)
                                print '\t\t\t\t\t\t' + str(arcpy.GetCount_management(fValid + "_" + c)) + ' output rows counted'
                                log.info('\t\t\t'+ str(arcpy.GetCount_management(fValid + "_" + c)) + ' output rows counted')
                            # Reset the workspace to the location of the coverages!!!
                            arcpy.env.workspace = folder
                        else:
                            print '\t\t\t' + os.path.join(f, c), 'coverage does not exist'
                            log.info('\t\t'+ os.path.join(f, c) + 'coverage does not exist')
                    except:
                        print os.path.join(folder,f,c), 'failed processing'
                        log.exception(os.path.join(folder,f,c) + ' failed processing')
        #Import the tables into the geodatbase from the tile (folder)
        print "\tTables being imported"
        for t in arcpy.ListTables():
            try:
                if '.' in t:
                    print "\t\t" + t
                    log.info('\t\t'+ t + ' exists')
                    arcpy.TableToTable_conversion(t, os.path.join(conCatFolder, "coverageConversion.gdb"),arcpy.ValidateTableName(t.split('.')[0] + "__" + t.split('.')[1]))
                    print "\t\t\t" + t + ' imported'
                    log.info('\t\t\t'+ t + ' imported')
                else:
                    print "\t\t" + t
                    log.info(t + ' exists')
                    arcpy.TableToTable_conversion(t, os.path.join(conCatFolder, "coverageConversion.gdb"),arcpy.ValidateTableName(t))
                    print "\t\t\t" + t + ' imported'
                    log.info('\t\t'+ t + ' imported')
            except:
                print os.path.join(folder,t), 'failed processing'
                log.exception(os.path.join(folder,t) + ' failed processing')



##        These lines were used to build an initial coverage list. The scipt would require
##        reworking for this to be used, i.e. not simply uncommented.
#        for c in coverageList:
#            print '\t', c
#            coverages += 1
#            fh = open(CSV,"a")
#            fh.write(os.path.join(root,f) + ',' + c + '\n')
#            fh.close()


    return coverages
#==============================================================================
# Mainline
#==============================================================================

if __name__ == '__main__':
    t0 = time.time()
#    doctest.testmod()
    print 'Script started'
    coverageFiles = ['arc', 'label', 'polygon', 'tic', 'point', 'annotation.vpf', 'node']
    # Existing outputs will be overwritten
    arcpy.env.overwriteOutput = True
    # Parent folder to recursively search for coverage files
    # Requires user input
    ws = r'C:\workspace\input'
    outFolder = r'C:\Workspace'
    CSV = os.path.join(outFolder, 'coverageCount.csv')

    # Create a unique logfile based on date and integer
    versionStub = stub(os.path.join(outFolder,r'logfile.log'))
    logfile = os.path.join(outFolder, r'logfile_' + versionStub + '.log')
    print '\nlogfile name:' + logfile

    # Configure the logfile
    log.basicConfig(filename=logfile,
                    level=log.DEBUG,
                    filemode='w',# 'w' = overwrite log file, 'a' = append
                    format='%(asctime)s,   Line:%(lineno)d %(levelname)s: %(message)s',
                    datefmt='%a %d/%b/%Y %I:%M:%S %p')

     # Log the path and name of the script used to the logfile
    log.info('Script started: ' + sys.argv[0])
    # Log the workspace to the logfile
    log.info('Workspace: ' + ws)

    coverages = 0

    # Check for coverages in root of WS
    coverages = coverageReport(ws,coverages, outFolder)

    # Check for coverages in subfolders of WS
    for root, folders, files in os.walk(ws):
        counter = 0
        for f in folders:
            coverages = coverageReport(os.path.join(root,f), coverages, outFolder)

            print str(coverages), 'processed.'



    print('\nFinished at: ' + time.strftime("%c", time.localtime(time.time())))
    timer(t0)
    print '\nScript finished: ', str(coverages), ' processed (all may not have been successful - see the log file.'
    log.info('Processing complete. ' + str(coverages) + ' processed (some may have failed - search log file for ''ERROR'')')




