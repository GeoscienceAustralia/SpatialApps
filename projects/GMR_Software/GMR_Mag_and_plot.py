# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Created on Mon May 15 15:55:09 2017

@author:  Joseph Bell

This software is for calculating some of the inputs into the Surface NMR survey work.
It allows the user to input several paramenters, calculated the properties of the magnetic field at a given 
location and time, then produces various data sheets, shapefile, GPX file and csv file for use by the team.


DEPENDENCIES:
    pyprj and shapefile and the only to dependancies besides a standard Python 2.7 install
    
The script needs to be kept in the folder with the agrf2015 FORTRAN code.
The script runs from the folder and uses the sub-folders in there to store the outputs. 
Subfolder required are:
    GPX
    Output_Data_Sheets
    Plots_Data
    shapefiles
    


"""


''' Imports and initialization '''
import os
from subprocess import Popen, PIPE
import math
import time
#import arcpy

import csv
import shapefile
import pyproj
import matplotlib.pyplot as plt
from math import sin, cos, radians, pi
import sys
lati = 0
longi = 0
site_name = 'error'
thisCorner = ''
plotSize = 0
hgt = 0

#print "working directory is " + os.getcwd()
thisDir = os.getcwd()




# define projections
# project points to WGS84 so can be turned into GPX files
wgs84 = pyproj.Proj("+init=EPSG:4326") # LatLon with WGS84 datum used by GPS units and Google Earth

UTM49S = pyproj.Proj("+init=EPSG:32749")
UTM50S = pyproj.Proj("+init=EPSG:32750")
UTM51S = pyproj.Proj("+init=EPSG:32751")
UTM52S = pyproj.Proj("+init=EPSG:32752")
UTM53S = pyproj.Proj("+init=EPSG:32753")
UTM54S = pyproj.Proj("+init=EPSG:32754") 
UTM55S = pyproj.Proj("+init=EPSG:32755")
UTM56S = pyproj.Proj("+init=EPSG:32756")
UTM57S = pyproj.Proj("+init=EPSG:32757")



#function to convert decimal degrees into DMS for the FORTRAN code input parameters
def convertToDMS(dd):
    deg = math.trunc(dd)
    decimals = abs(dd - deg)
    mins = math.trunc(decimals*60)
    over = decimals * 60
    secs = over - mins
    secs = secs * 60
    return (str(deg) + ', ' + str(mins) + ', ' + str(secs))
    

#find a x,y coordinate for a given point B using the distance from the point A (x0, y0) and the angle
def point_pos(x0, y0, d, theta):
    theta_rad = pi/2 - radians(theta)
    return x0 + d*cos(theta_rad), y0 + d*sin(theta_rad)
    

# figure out which zone the point is in    
def calcZone(x):
    # error check    
    if x < 106 or x > 156:
        print "Error - must be lat and long in Australia"
    if x > 106 and x <= 114:
        projection = pyproj.Proj("+init=EPSG:32749")
        zoneNo = "49"
    if x > 114 and x <= 120:
        projection = pyproj.Proj("+init=EPSG:32750")
        zoneNo = "50"
    if x > 120 and x <= 126:
        projection = pyproj.Proj("+init=EPSG:32751")
        zoneNo = "51"
    if x > 126 and x <= 132:
        projection = pyproj.Proj("+init=EPSG:32752")
        zoneNo = "52"
    if x > 132 and x <= 138:
        projection = pyproj.Proj("+init=EPSG:32753")
        zoneNo = "53"
    if x > 138 and x <= 144:
        projection = pyproj.Proj("+init=EPSG:32754")
        zoneNo = "54"
    if x > 144 and x <= 150:
        projection = pyproj.Proj("+init=EPSG:32755")
        zoneNo = "55"
    if x > 150 and x <= 156:
        projection = pyproj.Proj("+init=EPSG:32757")
        zoneNo = "56"
    return projection, zoneNo    
    

'''
############################################################################################
USER INTERFACE
'''
#data input screen
from Tkinter import *

# function to convert input fields into global variables for use after tkinter is closed
def show_entry_fields():
    global site_name
    site_name = e1.get()
    global plotSize
    plotSize = e5.get()
    global lati
    lati = e2.get()
    global longi
    longi = e3.get()
    global hgt
    hgt = e4.get()
    # convert hgt from m to km
    hgt = float(hgt)/1000
    hgt = str(hgt)
    global changePlotAngleBy
    changePlotAngleBy = e6.get()
    
    



master = Tk()
# window title
master.title('INPUTS: GMR Mag and corner calc')
#window size
master.geometry('650x300')


#set up lables
Label(master, text="                                     Site Name").grid(row=0, padx= 10, pady=10)
Label(master, text="     e.g  Kununurra01").grid(row=0, column = 2)
Label(master, text="                                Plot size (m)").grid(row=1)
Label(master, text="     e.g.  40").grid(row=1, column = 2)

Label(master, text="             Starting corner Latitude dd").grid(row=2)
Label(master, text="    e.g.  -15.783529").grid(row=2, column=2)

Label(master, text="         Starting corner Longitude dd").grid(row=3)
Label(master, text="   e.g. 128.743261").grid(row=3, column = 2)

Label(master, text="  Height Above Sea Level (metres)  ").grid(row=4)
Label(master, text="   e.g 110").grid(row=4, column=2)

Label(master, text="  Adjust plot angle manually from \ndeclination angle (optional) ").grid(row=5)
Label(master, text="   eg. -30 (clockwise is +ve)").grid(row=5, column=2)


# set up user entry fields
e1 = Entry(master)
#e1.insert(END, 'Kununurra01')    # default value
e5 = Entry(master)
e5.insert(END, '60')
e2 = Entry(master)
#e2.insert(END, '-15.783529')   # default value
e3 = Entry(master)
#e3.insert(END, '128.743261')   # default value
e4 = Entry(master)
e4.insert(END, '25')   # default value

e6 = Entry(master)
e6.insert(END, '0')   # default value


#user entry fields location in the winow
e1.grid(row=0, column=1)
e2.grid(row=2, column=1)
e3.grid(row=3, column=1)
e4.grid(row=4, column=1)
e5.grid(row=1, column=1)
e6.grid(row=5, column=1)


# function to return which corner of the plot was selected as the nearest
def sel():
   selection = "Selected corner " + str(var.get())
   
   global thisCorner
   thisCorner = str(var.get())
   label.config(text = selection)


var = IntVar()
# Radio buttons in tkInter
R1 = Radiobutton(master, text="SE Corner", variable=var, value=1, command=sel).grid(row=7, pady = 10)
R2 = Radiobutton(master, text="SW Corner", variable=var, value=2, command=sel).grid(row=7, column = 1)
R3 = Radiobutton(master, text="NE Corner", variable=var, value=3, command=sel).grid(row=7, column = 2)
R3 = Radiobutton(master, text="NW Corner", variable=var, value=4, command=sel).grid(row=7, column = 3)
#R1.invoke()   # set as default
#R1.state['selected']
label = Label(master)
label.grid(row=10)




# get the values out of the input screen

def processing():
    show_entry_fields()
    master.quit
    



# processing and results buttons
print label.grid(row=11)
Button(master, text='1. Process', command= show_entry_fields).grid(row=12, column=1, sticky=W, pady=4)
Button(master, text='2. Get Results', command=master.quit).grid(row=12, column=2, sticky=W, pady=4)
#Button(master, text='Get Results', command=processing()).grid(row=12, column=2, sticky=W, pady=4)



# end the tkinter UI
master.mainloop()




'''
INPUT DATA ###############################################################################
'''
''' set up the output to file for all the console dump
This works by sending all the information normally sent to the console off to a text file.


'''
# output text file name
thisOutput = "Output_Data_Sheets/" + site_name + "_all_data.txt"

fout = open(thisOutput, 'w')
sys.stdout = fout




# generate a date and time 
from time import localtime, strftime
showtime = strftime("%Y-%m-%d %H:%M:%S", localtime())
#print showtime

# begining of the data sheet
print
print 'MAGNETIC CHARACTERISTICS AND CORNER PLAN  @ ' + showtime
print 
print "Site Name = " + site_name
print "Plot size = " + str(plotSize) + " (m)"

print
print "Starting Corner:"
print "   Latitude  = " + str(lati)
print "   Longitude = " + str(longi)
print "Elevation = " + hgt + ' km'
print
print "Change plot angle manually by " + changePlotAngleBy


# collect starting corner from UI
if thisCorner == '1':
    startingCorner = 'SE'
if thisCorner == '2':
    startingCorner = 'SW'
if thisCorner == '3':
    startingCorner = 'NE'
if thisCorner == '4':
    startingCorner = 'NW' 

print "Selected starting corner = " + startingCorner

# convert lat and long to numbers
lati = float(lati)
longi = float(longi)

# information about the zone
thisZone = calcZone(longi)
print "Calculated MGA zone is " + str(thisZone[1])
print "projection is WGS84 (for handheld GPS devices)"
zone = thisZone[1]


# start point for calc of corners
#assumes the lat long in WGS84
inProj = wgs84
# reads out proj from latlong analysis
outProj = thisZone[0]
# print str(outProj) + " is outproj"

# calculate the starting point to meters for the particular zone
x1,y1 = longi, lati
x2,y2 = pyproj.transform(inProj,outProj,x1,y1)

print 
print "starting corner in meters = Eastings " + str(x2) + '    Northings ' + str(y2)
print


startPnt = (x2, y2)

#plot size - plot size varies according to need ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
width = float(plotSize)


# the magnetic calculations need to be done first since some outputs feed into the 
# calculations of the corners.



'''
#############################################################################################
Prepare data for FORTRAN code'''


#date
## dd/mm/yyyy format
print "Date is " + str((time.strftime("%Y/%m/%d")))

# convert to decimal date
thisDate = (time.strftime("%Y/%m/%d"))
dateTime = thisDate
thisDate = thisDate.split('/')


# decimal date required for FORTRAN code
thisDate = float(thisDate[0]) + (float(thisDate[1])/12) + (float(thisDate[2])/364)

print "Decimal Date " + str(thisDate)


print


''' FORTAN CODE ++++++++++++++++++++++++++++++++++++++++++++++++++++   '''
#name the output file for FORTRAN - this temporary and overwritten each time - but he data is saved in the output text file
outFile = 'tempFORTRAN.txt'

# open and close the file for the fortran code to work properly
f = open(outFile, 'w')
f.close()

#input the decimal year
decimalYear = str(thisDate)
#decimalYear = '2017.5'

# convert to DMS for FORTRAN
latitude = convertToDMS(lati)
longitude = convertToDMS(longi)

# open the FORTRAN code and input the parameters then run it - it sends the results to the temp text file
p = Popen(r'agrf15s.exe', stdin=PIPE) #NOTE: no shell=True here
p.communicate(os.linesep.join([outFile, "1", "1", decimalYear, site_name, latitude, longitude, hgt, "0", ""]))
print
print "Output files are in  " + thisOutput

# list to hold the FORTAN output as it is read back in from the tempFORTRAN file
fortranFile = list()
# MAKE A LIST OF THE LINES IN THE FORTRAN OUTPUT FILE
print  
f = open(outFile, 'r')
for item in f:
    # making the list
    fortranFile.append(item)
    # print the temp FORTAN file to the console/out-put file
    print item
    # get the line with the mag data for use later
    if 'Field = ' in item:
        myData = item
        magData = item
        
#    if 'On-cap' in item:
#        magHeader = item[1:]

''' RETRIVE INFO FROM fortran OUTPUT  '''
       
print
print
print
#print myData
myData = myData.strip()

#remove multiple spaces
myData = myData.replace("  ", " ")
myData = myData.replace("  ", " ")
myData = myData.replace("  ", " ")

magData = myData
magData = myData.replace(" ", ", ")
magData = magData.replace("=,", "")


## split in single space
myData = myData.split(' ')
#

azimuth = float(myData[7]) + float(changePlotAngleBy)
print "Declination = " + myData[7]
# record if the user manually changed the plot angle
print "Change plot angle manually by " + changePlotAngleBy


print 'Total Magnetic Field Strength = ' + myData[6]


'''
This part of script takes a site name, x and y coordinate, an azimuth and a width as 
arguments and returns a file with corner coordinates.
'''


#plan starting corner
# how the data is processed depends on the starting corner that was selected
if startingCorner == "SW":
    crns = ['NW', 'NE', 'SE', 'SW', 'centre']
    if azimuth > 360:
        azimuth = azimuth - 360
    if azimuth < 0:
        azimuth = azimuth + 360
        
    
elif startingCorner == "NW":
    crns = ['NE', 'SE', 'SW', 'NW','centre']
    azimuth = azimuth + 90
    if azimuth > 360:
        azimuth = azimuth - 360
    if azimuth < 0:
        azimuth = azimuth + 360
        
    
elif startingCorner == "NE":
    azimuth = azimuth + 180
    crns = ['SE', 'SW', 'NW', 'NE', 'centre']
    if azimuth > 360:
        azimuth = azimuth - 360
    if azimuth < 0:
        azimuth = azimuth + 360
        
    
elif startingCorner == "SE":
    azimuth = azimuth + 270
    crns = ['SW', 'NW', 'NE', 'SE','centre']
    if azimuth > 360:
        azimuth = azimuth - 360
    if azimuth < 0:
        azimuth = azimuth + 360
else:
    print "no starting corner ######################################################" 

# Calculate the four corners
pnt1 = point_pos(startPnt[0], startPnt[1], width, azimuth)
pnt2 = point_pos(pnt1[0], pnt1[1], width, azimuth+90)
pnt3 = point_pos(pnt2[0], pnt2[1], width, azimuth+180)
pnt4 = point_pos(pnt3[0], pnt3[1], width, azimuth+270)

#find the centre
centroid = ((pnt1[0] + pnt3[0])/2,  (pnt1[1] + pnt3[1])/2)


#make a list of the corners
myCorners = list()
myCorners.append(pnt1)
myCorners.append(pnt2)
myCorners.append(pnt3)
myCorners.append(pnt4)
myCorners.append(centroid)

print
print "centre of the plot is ",
for itme in centroid:
    print itme,

print
 



#plot it (optional)
fig1 = plt.figure()
plt.plot([startPnt[0],pnt1[0],pnt2[0],pnt3[0], pnt4[0], centroid[0]], [startPnt[1],pnt1[1],pnt2[1],pnt3[1], pnt4[1], centroid[1]] , 'ro')
#plt.plot([startPnt[0],pnt1[0],pnt2[0],pnt3[0], pnt4[0]], [startPnt[1],pnt1[1],pnt2[1],pnt3[1], pnt4[1]] , 'ro')
plt.title(site_name + " from " + startingCorner + " corner")
plt.xlabel('X')
plt.ylabel('Y')
plt.margins(0.1)
plt.show()




# make a list of projected coords in GCS_84
my84corners = list()
for cnr in myCorners:
   projCoords = pyproj.transform(thisZone[0], wgs84, cnr[0], cnr[1])
   my84corners.append(projCoords)

print
print

print
print
thisCSV = thisDir + '/Plots_Data/' + site_name + 'zone' + zone + '.csv'

#Write corner coordinates into a csv file
with open(thisCSV, 'wb') as csvfile:
    w = csv.writer(csvfile, delimiter= ',')
    w.writerow(['site','Corner','X','Y','LongWGS84','LatWGS84'])
    w.writerow([site_name, crns[0],  pnt4[0], pnt4[1], (my84corners[0][0]),(my84corners[0][1])])
    w.writerow([site_name, crns[1],  pnt1[0], pnt1[1], (my84corners[1][0]),(my84corners[1][1])])
    w.writerow([site_name, crns[2],  pnt2[0], pnt2[1], (my84corners[2][0]),(my84corners[2][1])])
    w.writerow([site_name, crns[3],  pnt3[0], pnt3[1], (my84corners[3][0]),(my84corners[3][1])])
    w.writerow([site_name,'Centre',  centroid[0],  centroid[1], (my84corners[4][0]),(my84corners[4][1])])
    #w.writerow(['Date ' + ',', dateTime, ',','zone', zone])

     
    

#open the file

#print "working directory is " + os.getcwd()
thisDir = os.getcwd()

print
print
print
# write the corner locations to the out-put file
print "CORNER LOCATION TABLE" + 'Date ' + '\t', dateTime, '\t','zone', zone
print
print 'site\t', '\t','corner', '\t\t','X', '\t\t', 'Y\t', 'LongWGS84\t', 'LatWGS84'
print site_name,'\t', crns[0], '\t', pnt4[0], '\t', pnt4[1],'\t',(my84corners[0][0]), '\t',(my84corners[0][1])
print site_name,'\t', crns[1], '\t', pnt1[0], '\t', pnt1[1],'\t',(my84corners[1][0]), '\t',(my84corners[1][1])
print site_name,'\t', crns[2], '\t', pnt2[0], '\t', pnt2[1],'\t',(my84corners[2][0]), '\t',(my84corners[2][1])
print site_name,'\t', crns[3], '\t', pnt3[0], '\t', pnt3[1],'\t',(my84corners[3][0]), '\t',(my84corners[3][1])
print site_name,'\t','Centre', '\t', centroid[0], '\t', centroid[1], '\t', (my84corners[4][0]), '\t',(my84corners[4][1])
print 
print



print




''' generate shapefile from the points '''

# print 'making shapefile'
# depends on a pythin library called 'shapefile' being included in the Lib folder of the python install

wt = shapefile.Writer(shapefile.POINT)
# this script for zone metres
#wt.point(pnt4[0], pnt4[1])
#wt.point(pnt1[0], pnt1[1])
#wt.point(pnt2[0], pnt2[1])
#wt.point(pnt3[0], pnt3[1])
#wt.point(centroid[0], centroid[1])


# this script for GCS 84 - best for import into ArcMap because zoneless
# define the points
wt.point((my84corners[0][0]), (my84corners[0][1]))
wt.point((my84corners[1][0]), (my84corners[1][1]))
wt.point((my84corners[2][0]), (my84corners[2][1]))
wt.point((my84corners[3][0]), (my84corners[3][1]))
wt.point((my84corners[4][0]), (my84corners[4][1]))

# define the fields
wt.field('SITE', 'C', '40')
wt.field('Corner','C','40')
wt.field('X','F')
wt.field('Y','F')

# fill out the attributes table

wt.record(site_name, crns[0], pnt4[0], pnt4[1])
wt.record(site_name, crns[1], pnt1[0], pnt1[1])
wt.record(site_name, crns[2], pnt2[0], pnt2[1])
wt.record(site_name, crns[3], pnt3[0], pnt3[1])
wt.record(site_name, 'Center\n ' + site_name, centroid[0], centroid[1])


# save the shapefile - however it has not been projected yet
wt.save('shapefiles/' + site_name)
thisSite = 'shapefiles/' + site_name

#project the shapefile into 84
# a simple method of writing a single projection

prj = open("%s.prj" % thisSite, "w") 
epsg = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]' 
prj.write(epsg) 
prj.close() 

print
print




'''
Generate GPX file.
This code takes the four courners that should be already in WGS84 and
converts to simple GPX to be copied to a handheld GPS unit.
It is a simple xml file. It is written in the code so there is no XML depencies.

'''


# Build gpx file FROM CODE
gpxOut = list()
# build the header information
# header
gpxOut.append('<?xml version=' + "'1.0'" + " encoding='UTF-8'?><gpx creator=" + '"Esri" version="1.1"')
gpxOut.append(' xalan="http://xml.apache.org/xalan"')
gpxOut.append(' xmlns="http://www.topografix.com/GPX/1/1"')
gpxOut.append(' xsi=' + '"http://www.w3.org/2001/XMLSchema-instance"' + '>')


# write the GPX corners 
# data
thisCorner = 0
for point in my84corners:
    longi = str(point[0])
    lat = str(point[1])
    name = site_name + "cnr" + str(thisCorner)
    name = site_name + crns[thisCorner]
    thisCorner += 1
    thisTime = "atime"
    desc = "GMR plot cnr"
    myString = '<wpt lat="' + lat + '" lon="' + longi + '"><ele>0</ele><time>' + thisTime + '</time><name>' + name + '</name><desc> </desc></wpt>'
    gpxOut.append(myString)
    #print myString
    
#print "</gpx>"
gpxOut.append("</gpx>")


#write out the gpx file
g_out = open(('GPX/' + site_name + ".gpx"), 'w')
for item in gpxOut:
    g_out.write(item)



# tell the user where the files are located on the computer
print "GPX DATA FOR HANDHELD GPS DEVICE is saved as a gpx file at:"
print thisDir + '\GPX/' + site_name + ".gpx"
print
print "Shapefile located:"
print thisDir + '\shapefiles/' + site_name + ".shp"
print
print

print "CORNER csv file is saved at:"
print thisCSV
print
print "This data summarry file is saved at:"
print thisDir + '/' + thisOutput
print
print


print
print 'Computer Name'
print os.environ['COMPUTERNAME']
print
print
print 'NOTES'
print

print '''Magnetic Field elements
 --------------
 The vector field is expressed in terms of 7 elements:
 
   X,Y,Z = northwards, eastwards, vertical(downwards) components
   H,F   = horizontal component, total field intensity
   D     = declination (magnetic variation), positive east of north
   I     =  inclination, positive downwards.'''






fout.close()
os.startfile(thisDir + '/' + thisOutput)
#os.close(outFile)
#os.remove(outFile)









print 'finished'
