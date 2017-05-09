# -*- coding: utf-8 -*-
"""
Created on Thu Sep 8 10:34:35 2016
Description: Within the folder that this script is saved at,
    - iterate through .msg files and create a list,
        - folder should contain only  FindMeSPOT .msg files, other .msg files
        will create incorrect outputs.
    - iterate through the .msg list and extract the field crew name, location,
        and date/time stamp to create a data list
    - iterate through the data list to create an ESRI feature class in a
        file geodatabase

    The script's progress is printed to screen and stored in a logfile
    (logfile.log) wihtin the folder that the script exists.

    No inputs are required to be changed, simply copy the script to the
    location of the FindMeSpot emailed messages and run the script (within
    an IDE or double-clicking the .py file)



@author: Duncan Moore - Geoscience Australia September 2016
"""

#==============================================================================
# Import libraries
#==============================================================================
import arcpy

import logging as log
import os
import time
import sys
import win32com.client

#Set overwrite option
#arcpy.env.overwriteOutput = True

#==============================================================================
# Functions
#==============================================================================
def timer(t0):    #
    '''Timer calculates how long the script took to run and prints the results
    to the console

    Arguments
    t0 -- time that the script started
    '''
    print('\nFinished at: ' + time.strftime("%c", time.localtime(time.time())))
    print('Time taken: {0} hours, {1} minutes, {2} seconds'.format(int((time.time()-t0)/3600), int(((time.time()-t0)%3600)/60), int((time.time()-t0)%60)))
    log.info('Processing complete. Time taken: {0} hours, {1} minutes, {2} seconds'.format(int((time.time()-t0)/3600), int(((time.time()-t0)%3600)/60), int((time.time()-t0)%60)))

    return

def buildMSGList(folder):
    ''' buildMSBList function searches through the files that exist in the same
    folder as this script and builds a list of .msg files.

    Arguments
    folder -- The folder to list all the .msg files
    '''
    print 'Finding .msg files in: ', folder
    log.info('Started build of .msg files in: ' + os.path.split(sys.argv[0])[0])
    try:
        msgList = []
        for f in os.listdir(os.path.split(sys.argv[0])[0]):
            if f.endswith('msg'):
                msgList.append(f)
                log.info('Added to .msg list: ' + os.path.join(os.path.split(sys.argv[0])[0],f))
                print '\tAdded to .msg list: ', f

        print('List length',len(msgList))

        return msgList

    except Exception as e:
        log.exception('Failure processing')
        print(e.message, e.args)
        sys.exit('Error refer:' + logfile)

def buildDataList(msgList):
    ''' buildDataList function utilises the list of .msg files and extracts the
    lat, long, field crew name and date/time stamp from each .msg file and
    appends this to the returned list.

    Arguments
    msgList -- The list of .msg files in the folder that this script exists in
    '''
    log.info('Started converting .msg to a datalist (buildDataList function)')
    try:
        dataList = []
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        for msg in msgList:
            print '\n', '*'*50,'\n'
            print os.path.join(os.path.split(sys.argv[0])[0],msg)

            msg = outlook.OpenSharedItem(os.path.join(os.path.split(sys.argv[0])[0],msg))
    #        f = open(msg)
            print msg.Body
    #        print type(msg.Body)
            print 'Number of lines: ',len(msg.Body.splitlines())
            lines = msg.Body.splitlines()
            count = 0
            for line in lines:
                count += 1
                if count == 1:
                    team = line
                elif count == 2:
                    lat = line.split(':')[1]
                    print 'lat: ',lat
                elif count == 3:
                    longi = line.split(':')[1]
                    print 'long: ', longi
                elif count == 4:
                    # Split the dateTime line on the first occurrence of ':'
                    dateTime = line.split(':',1)[1]
                    print 'dateTime: ', dateTime
                    date = dateTime.split(' ')[0]
                    print 'date: ', date
                    time = dateTime.split(' ')[1]
                    print 'time: ', time
                elif count == 6:
                    # Split the message line on the first occurrence of ':'
                    message = line.split(':',1)[1]
                    print 'message: ', message
                elif count == 12:
                    googleMaps = line
            dataList.append([team, lat, longi, date, time, dateTime, message, googleMaps])
        del msg
        log.info('Completed converting .msg to a datalist (buildDataList function)')
        return dataList

    except Exception as e:
        log.exception('Failure processing')
        print(e.message, e.args)
        sys.exit('Error refer:' + logfile)

def sortList(dataList):
    ''' sortList function sorts the data list (lat,long, date, time, date/time)
    by the date/time entry and returns a sorted list.

    Arguments
    dataList -- List of data entries from each email .msg file to create
                 the spatial data (X/Y) and the associated attributes
    '''
    def getKey(item):
        '''

        Arguments
        item   -- The list to be sorted
        '''
        return item[5]

    log.info('Sorting list started')
    # Sort the list based on the last entry in the list (dateTime)
    try:
        dataList = sorted(dataList, key=getKey)
        print '~'* 150, '\nSorted dataList: '
        print 'list length: ', len(dataList)
        log.info('List sorted: ' + str(len(dataList)) + ' entries')
        for data in dataList:
            print '\t', data
        log.info('Sorting list complete')
        print 'Sorting list complete'
        return dataList
    except Exception as e:
        log.exception('Failure processing')
        print(e.message, e.args)
        sys.exit('Error refer:' + logfile)

def buildFeatureClass(sortedList):
    ''' buildFeatureClass function creates an ESRI feature class within an
    ESRI file geodatabase. If the file geodatabase doesn't exist it is created,
    along with the feature class, in the folder that the script exists. If the
    file geodatabase exists and the feature class then the feature class is
    deleted and recreated.

    Arguments
    sortedList -- List sorted in order of date/time stamp
    '''
    print '~'* 150
    print 'Started to build the feature class (buildFeatureClass function)'
    log.info('Started to build the feature class (buildFeatureClass function)')
    try:
        workspace = os.path.join(os.path.split(sys.argv[0])[0],'fGDB.gdb')
        arcpy.env.workspace = workspace
        if not arcpy.Exists(workspace):
            print('\tFile geodatabase doesn\'t exist and is being created')
            log.info('File geodatabase doesn\'t exist and is being created')
            arcpy.CreateFileGDB_management(os.path.split(sys.argv[0])[0],'fGDB.gdb')
            # Need to reallocate the workspace as it didn't exist previously
            # and appears to be not allocated if it doesn't exist!
            arcpy.env.workspace = workspace

        else:
            if arcpy.Exists('FieldCrewTracer'):
                print('\tFeature class exists and is being overwritten (deleted and recreated)')
                log.info('Feature class exists and is being overwritten (deleted and recreated)')
                arcpy.Delete_management('FieldCrewTracer')

        arcpy.CreateFeatureclass_management(workspace, 'FieldCrewTracer', "POINT", "#", "#", "#", arcpy.SpatialReference(4326))
        print('\t\tFeature class created')
        log.info('Feature class created')
#        print arcpy.Exists('FieldCrewTracer')

        # fields needs to match the input data sequence
        fields = ['SHAPE@XY', 'Field_crew_name', 'Date', 'Time', 'DateTime', 'Message', 'GoogleMaps_URL']
        arcpy.AddField_management('FieldCrewTracer', 'Field_crew_name', 'TEXT')
        arcpy.AddField_management('FieldCrewTracer', 'Date', 'DATE')
        arcpy.AddField_management('FieldCrewTracer', 'Time', 'TEXT')
        arcpy.AddField_management('FieldCrewTracer', 'DateTime', 'TEXT')
        arcpy.AddField_management('FieldCrewTracer', 'Message', 'TEXT')
        arcpy.AddField_management('FieldCrewTracer', 'GoogleMaps_URL', 'TEXT')

        cursor = arcpy.da.InsertCursor('FieldCrewTracer',fields)
        for line in sortedList:
            # XY needs to be fed via the insert cursor (insertRow) to the feature
            # class as a tuple. The following line creates the tuple.
#            print line
            xy = float(line[2]), float(line[1])
#            print xy
#            print type(xy)
#            print float(line[2]), float(line[1]), str(line[3]), str(line[4]), str(line[5])
            # Format the line to be fed to the feature class in the appropriate field order
            # to match the fields list. The order matches the fields list above
            formattedLine = [xy,str(line[0]), str(line[3]), str(line[4]), str(line[5]), str(line[6]), str(line[7])]
            print formattedLine
#            line = float(line[2]), float(line[1]), str(line[3]), str(line[4]), str(line[5])
            cursor.insertRow(formattedLine)
        print 'Completed building the feature class (buildFeatureClass function)'
        log.info('Completed building the feature class (buildFeatureClass function)')
        return

    except Exception as e:
        log.exception('Failure processing')
        print(e.message, e.args)
        sys.exit('Error refer:' + logfile)

# In python version 3 input is dropped and raw_input is renamed input therefore...
if sys.version_info.major == 3:
    raw_input = input

if __name__ == '__main__':
    t0 = time.time()

    logfile = os.path.join(os.path.split(sys.argv[0])[0], r'logfile.log')
    print os.path.join(os.path.split(sys.argv[0])[0], r'logfile.log')
    # Create a log file to log progress/exceptions
    log.basicConfig(filename=logfile,
                        level=log.DEBUG,
                        filemode='w',# 'w' = overwrite log file, 'a' = append
                        format='%(asctime)s,   Line:%(lineno)d %(levelname)s: %(message)s',
                        datefmt='%a %d/%b/%Y %I:%M:%S %p')
    # Log the path and name of the script used to the logfile
    log.info('Script started: ' + sys.argv[0])
    # Log the workspace to the logfile
    log.info('Workspace: ' + os.path.split(sys.argv[0])[0])

    # Build a list of .msg files from the folder that this script exists in
    msgList = buildMSGList(os.path.split(sys.argv[0])[0])

    dataList = buildDataList(msgList)

    sortedList = sortList(dataList)

    buildFeatureClass(sortedList)

    timer(t0)

    #Clean up variables from memory
    del t0
    del msgList
    del dataList
    del sortedList
    del logfile
