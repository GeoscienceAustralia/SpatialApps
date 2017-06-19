# -*- coding: utf-8 -*-
"""
Created on Mon May 15 15:55:09 2017

@author: u82871
"""

import os
from subprocess import Popen, PIPE
import math
import time
#import osgeo
#import arcpy
#import sys, math, os
#import numpy as np
import csv
# import shapefile
import pyproj

import matplotlib.pyplot as plt

from math import sin, cos, radians, pi


# import utm


'''
INPUT DATA
'''

# input the name of the site
site_name = 'Camerons06'

# lat and long Kununurra
lati = -15.77000
longi = 128.74000
x = longi
y = lati

#date
## dd/mm/yyyy format
print "date is " + str((time.strftime("%Y/%m/%d")))

# convert to decimal date
thisDate = (time.strftime("%Y/%m/%d"))
thisDate = thisDate.split('/')

thisDate = float(thisDate[0]) + (float(thisDate[1])/12) + (float(thisDate[2])/364)

print "decimal date is " + str(thisDate)


startPnt = (499885.666, 6792177.434)

azimuth = 5
width = 1000
zone = "54"



#Find distance between midpoint and corners
#d = 0.5*math.sqrt(2*(width**2))

# ask which corner to start from
'''
NW, NE, SE or SW


'''
startingCorner = "SE"

##simplify date
#thisDate = str(thisDate)
#head, sep, tail = thisDate.partition('.')
#print tail
##tail = tail[:2]
#print tail
#thisDate = head + sep + tail
print "Date " + str(thisDate)

#function to convert decimal degrees into DMS for the FORTRAN code input parameters
def convertToDMS(dd):
    deg = math.trunc(dd)
    decimals = abs(dd - deg)
    mins = math.trunc(decimals*60)
    over = decimals * 60
    secs = over - mins
    secs = secs * 60
    #print deg    
    #print decimals
    #print mins
    #print over
    #print secs
    
    return (str(deg) + ', ' + str(mins) + ', ' + str(secs))
    

print convertToDMS(lati)
print convertToDMS(longi)



#os.chdir( r'C:\\Users\\u82871\\Desktop\\Magnetic\\agrf2015' )


#name the output file
outFile = site_name + ' Magnetics.txt'

# open and close the file for the fortran code to work properly
f = open(outFile, 'w')
f.close()



#input the decimal year
decimalYear = str(thisDate)
#decimalYear = '2017.5'

latitude = convertToDMS(lati)
longitude = convertToDMS(longi)

#above sea level in km
hgt = str(0.004)

# open the FORTRAN code and input the parameters
p = Popen(r'agrf15s.exe', stdin=PIPE) #NOTE: no shell=True here
#p.communicate(os.linesep.join([r"magit2.txt", "1", "2", "2017.5", "Ord6", "-12,1,1", "126,4,5", "0.05", "0", ""]))
p.communicate(os.linesep.join([outFile, "1", "1", decimalYear, site_name, latitude, longitude, hgt, "0", ""]))
print
print "Outfile is ' " + outFile
print
print "Saved file contents"
f = open(outFile, 'r')
for item in f:
    print item
    if 'Field = ' in item:
        myData = item
        
print
print
print
print myData
myData = myData.strip()

#remove multiple spaces
myData = myData.replace("  ", " ")
myData = myData.replace("  ", " ")
myData = myData.replace("  ", " ")


print
print myData

# split in single space
myData = myData.split(' ')

print 
print myData

XnT = myData[2]
YnT = myData[3]

print 
print 'XnT is ' + XnT
print 'YnT is ' + YnT


'''






This script takes a site name, x and y coordinate, an azimuth and a width as 
arguments and returns a point shape file with station coordinates.
'''



def point_pos(x0, y0, d, theta):
    theta_rad = pi/2 - radians(theta)
    return x0 + d*cos(theta_rad), y0 + d*sin(theta_rad)
    
    
def calcZone(x,y):
    # error check    
    if x < 106 or x > 156:
        print "Error - must be lat and long in Australia"
    if x > 106 and x <= 114:
        zone = UTM49S
    if x > 114 and x <= 120:
        zone = UTM50S
    if x > 120 and x <= 126:
        zone = UTM51S
    if x > 126 and x <= 132:
        zone = UTM52S
    if x > 132 and x <= 138:
        zone = UTM53S
    if x > 138 and x <= 144:
        zone = UTM54S
    if x > 144 and x <= 150:
        zone = UTM55S
    if x > 150 and x <= 156:
        zone = UTM56S
    return zone    
    
   



print "Processing"
print

#Get variables as arguments from batch file find_gmr_loop_coords.bat
#site_name = sys.argv[1]
#midpoint = (float(sys.argv[2]), float(sys.argv[3]))
#azimuth = float(sys.argv[4])
#width = float(sys.argv[5])
#coordinate_system = int(sys.argv[6])



#If running straight from script, insert varibles below
startPnt = (499885.666, 6792177.434)

azimuth = 5
width = 1000
zone = "54"



#Find distance between midpoint and corners
#d = 0.5*math.sqrt(2*(width**2))

# ask which corner to start from
'''
NW, NE, SE or SW


'''
startingCorner = "SE"


#plan starting corner
if startingCorner == "SW":
    if azimuth > 360:
        azimuth = azimuth - 360
    
if startingCorner == "NW":
    azimuth = azimuth + 90
    if azimuth > 360:
        azimuth = azimuth - 360
    
if startingCorner == "NE":
    azimuth = azimuth + 180
    if azimuth > 360:
        azimuth = azimuth - 360
    
if startingCorner == "SE":
    azimuth = azimuth + 270
    if azimuth > 360:
        azimuth = azimuth - 360


# Calculate the for corners
pnt1 = point_pos(startPnt[0], startPnt[1], width, azimuth)
pnt2 = point_pos(pnt1[0], pnt1[1], width, azimuth+90)
pnt3 = point_pos(pnt2[0], pnt2[1], width, azimuth+180)
pnt4 = point_pos(pnt3[0], pnt3[1], width, azimuth+270)

#find the centre
centroid = ((pnt1[0] + pnt3[0])/2,  (pnt1[1] + pnt3[1])/2)


print
print "corners"
print str(pnt4) + "start point"
print pnt1
print pnt2
print pnt3
print centroid

#make a list of the corners
myCorners = list()
myCorners.append(pnt1)
myCorners.append(pnt2)
myCorners.append(pnt3)
myCorners.append(pnt4)
myCorners.append(centroid)


print "centroid"
for itme in centroid:
    print itme


 



#plot it (optional)
fig1 = plt.figure()
plt.plot([startPnt[0],pnt1[0],pnt2[0],pnt3[0], pnt4[0], centroid[0]], [startPnt[1],pnt1[1],pnt2[1],pnt3[1], pnt4[1], centroid[1]] , 'ro')
#plt.plot([startPnt[0],pnt1[0],pnt2[0],pnt3[0], pnt4[0]], [startPnt[1],pnt1[1],pnt2[1],pnt3[1], pnt4[1]] , 'ro')
plt.title(site_name + " from " + startingCorner + " corner")
plt.xlabel('X')
plt.ylabel('Y')
plt.margins(0.1)
plt.show()

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



# make a list of projected coords in GCS_94
my84corners = list()

for cnr in myCorners:
   projCoords = pyproj.transform(UTM54S, wgs84, cnr[0], cnr[1])
   my84corners.append(projCoords)

print
print


# back calculate to ensure the transforms are working
for item in my84corners:
    # convert back
    backproj = pyproj.transform(wgs84,UTM54S, item[0], item[1])
    
    print item
    print backproj
    print

print
print

#Write corner coordinates into a csv file
with open(r'plotCorners.csv', 'wb') as csvfile:
    w = csv.writer(csvfile, delimiter= '\t')
    w.writerow(['site', 'name', 'X', 'Y'])
    w.writerow([site_name,'cnr1', pnt4[0], pnt4[1]])
    w.writerow([site_name,'cnr2', pnt1[0], pnt1[1]])
    w.writerow([site_name,'cnr3', pnt2[0], pnt2[1]])
    w.writerow([site_name,'cnr4', pnt3[0], pnt3[1]])
    w.writerow([site_name,'Centroid', centroid[0], centroid[1]])
    
    
    
#Write corner coordinates into a csv file
with open(r'plotCorners84.csv', 'wb') as csvfile:
    w = csv.writer(csvfile, delimiter= '\t')
    w.writerow(['site', 'name', 'X', 'Y'])
    w.writerow([site_name,'cnr1', (my84corners[0][0]), (my84corners[0][1])])
    w.writerow([site_name,'cnr2', (my84corners[1][0]), (my84corners[1][1])])
    w.writerow([site_name,'cnr3', (my84corners[2][0]), (my84corners[2][1])])
    w.writerow([site_name,'cnr4', (my84corners[3][0]), (my84corners[3][1])])
    w.writerow([site_name,'Centroid', centroid[0], centroid[1]])


'''
Generate GPX file.
This code takes the four courners that should be already in WGS84 and
converts to simple GPX to be copied to a handheld GPS unit.
It is a simple xml file. It is written in the code so there is no depencies.

'''


#gpxHeader1 = '<?xml version=' + "'1.0'" + " encoding='UTF-8'?><gpx creator=" + '"Esri" version="1.1"'
#gpxHeader2 = 'xalan="http://xml.apache.org/xalan"' 
#gpxHeader3 = 'xmlns="http://www.topografix.com/GPX/1/1"'
#gpxHeader4 = 'xsi=' + '"http://www.w3.org/2001/XMLSchema-instance"' + '>'


# Build gpx file
gpxOut = list()
# the header information
gpxOut.append('<?xml version=' + "'1.0'" + " encoding='UTF-8'?><gpx creator=" + '"Esri" version="1.1"')
gpxOut.append('xalan="http://xml.apache.org/xalan"')
gpxOut.append('xmlns="http://www.topografix.com/GPX/1/1"')
gpxOut.append('xsi=' + '"http://www.w3.org/2001/XMLSchema-instance"' + '>')

#print
#print
#print gpxHeader1
#print gpxHeader2
#print gpxHeader3
#print gpxHeader4






thisCorner = 1
for point in my84corners:
    longi = str(point[0])
    lat = str(point[1])
    name = site_name + str(thisCorner)
    thisCorner += 1
    thisTime = "atime"
    desc = "GMR plot cnr"
    myString = '<wpt lat="' + lat + '" lon="' + longi + '"><ele>0</ele><time>' + thisTime + '</time><name>' + name + '</name><desc> </desc></wpt>'
    gpxOut.append(myString)
    print myString
    
print "</gpx>"
gpxOut.append("</gpx>")


#write out the gpx file
g_out = open((site_name + ".gpx"), 'w')
for item in gpxOut:
    g_out.write(item)



print 'finished'
