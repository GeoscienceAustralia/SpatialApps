# -*- coding: utf-8 -*-
"""
Created on Tue Aug 08 13:26:40 2017

The purpose of this script is to iterate through a field and check for
duplicate content. This script does not compare upper and lower case
strings. The user must convert the field to upper or lower case prior to
running this script if upper case == lower case. Duplicate field content is
returned to the user in the printed statements in the shell. The query can
then be copied into the 'Select By Attributes' window within ArcMap.

When the script is run the user provides the path to the shapefile and the
attribute to consider.

@author: Duncan Moore
"""
import arcpy
import os
import collections

print('Script started...')

shpFile = raw_input('Path including shapefile: ')

if not os.path.exists(shpFile):
    print('Shapefile does not exist, exiting...')

field = raw_input('Field to be investigated: ')


# Initiate an empty list to store field content
content = []
duplicates = []

# Build a list of the attributes, multiple entries for multiple occurrences
with arcpy.da.SearchCursor(shpFile, field) as cursor:
     for row in cursor:
         # row[0] refers to the first item in the tuple
         # There is only one item as only one field is considered
         print(str(row[0]).lower())
         print('\n')
         content.append(str(row[0]))


# Create a dictionary that stores the field content with the number of
# occurrences (key and value respectively) from the content list
contentsDict = {i:content.count(i) for i in content}
duplicates = {}

# Build a dictionary of duplicate attributes only
for key, value in contentsDict.iteritems():
    if value > 1:
        print('Duplicate (value:count) - {}:{}'.format(key, value))
        duplicates[key] = value
    else:
        print('\tNot duplicate (value:count) -- {}:{}'.format(key, value))

#print('\nDuplicates dictionary: \n{}'.format(duplicates))

# Create an orderedDict so as to be able to format the query correctly for the
# last entry
orderDict = collections.OrderedDict(duplicates)

# Create an empty query to build on
query = ''

# If there are no entries in the dictionary then don't build the query
if len(orderDict) == 0:
    print('\tAll rows are unique in the field assessed')
else:
    # Build the query to go into ArcMap select by attributes field =
    print('Building the query from unique list of duplicates...')
    for key, value in orderDict.iteritems():
        # Format all but last entry with a trailing comma
        if not key == orderDict.keys()[-1]:
            query += '\'' + str(key) + '\'' + ','
        else:
            # Last in the list doesn't need the comma
            query += '\'' + str(key) + '\''

    print('\nQuery of {} entries: '.format(len(orderDict)))
    print query

print('\nScript finished')