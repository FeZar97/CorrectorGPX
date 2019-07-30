import argparse
import gpxpy
import gpxpy.gpx
import math
from geopy.distance import distance
from gpxpy.gpx import GPXTrackPoint

# max distance between points in meters
DISTANCE_THRESHOLD = 2000
# points per sector
PPR = 500

def getDistanceInMeters(p1, p2):
    return distance( (p1[0], p1[1]), (p2[0], p2[1])).meters

def findBoundaryPoints(points, minCoords, maxCoords):
    minCoords.latitude = 90
    minCoords.longitude = 180
    maxCoords.latitude = -90
    maxCoords.longitude = -180
    for point in points:
        if point[0] > maxCoords.latitude: maxCoords.latitude = point[0]
        if point[0] < minCoords.latitude: minCoords.latitude = point[0]
        if point[1] > maxCoords.longitude: maxCoords.longitude = point[1]
        if point[1] < minCoords.longitude: minCoords.longitude = point[1]

points = []

parser = argparse.ArgumentParser(prog = 'GPX_Orderer', description = 'Program %(prog)s sorts  contents of the input file in GPX format')
parser.add_argument('-f', '--filename', type=str, required=True, help = 'Name of input file')
parser.add_argument('-t', '--tagname', choices=['wpt', 'trk', 'rte'], required=True, type=str, help = 'Source of points')

namespace = parser.parse_args()

gpx_file = open(namespace.filename, 'r')
gpx = gpxpy.parse(gpx_file)
print('-------------------------------------------------------------------------------')
print('{0} waypoints, {1} routes, {2} tracks'.format(len(gpx.tracks), len(gpx.routes), len(gpx.waypoints)))

if namespace.tagname == 'wpt':
    for waypoint in gpx.waypoints:
        points.append([waypoint.latitude, waypoint.longitude])
elif namespace.tagname == 'trk':
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append([point.latitude, point.longitude])
elif namespace.tagname == 'rte':
    for route in gpx.routes:
        for point in route.points:
            points.append([point.latitude, point.longitude])

# find boundary points
minCoords = GPXTrackPoint(90,180)
maxCoords = GPXTrackPoint(-90,-180)
findBoundaryPoints(points, minCoords, maxCoords)
print('Max longitude: {0}, Max latitude: {1};\nMin longitude: {2}, Min latitude: {3};'.format(maxCoords.longitude, maxCoords.latitude, minCoords.longitude, minCoords.latitude))

# number of sectors
numberOfSectors = math.floor(len(points)/PPR)

width = maxCoords.longitude - minCoords.longitude
height = maxCoords.latitude - minCoords.latitude

# numberOfSectors sectors with ordered points
miniSectors = []

# if "width" > "height", then make split by width (by longitude)
if width > height:
    step =  width/numberOfSectors
    for i in range(numberOfSectors):

        startLongitude = minCoords.longitude + i * step
        endLongitude = minCoords.longitude + (i + 1) * step

        sector = []

        for point in points:
            if point[1] >= startLongitude and point[1] < endLongitude:
                sector.append(point)
                while point in points:
                    points.remove(point)

        miniSectors.append(sector)
# if "width" < "height", then make split by height
else:
    step =  height/numberOfSectors
    for i in range(numberOfSectors):

        startLatitude = minCoords.latitude + i * step
        endLatitude = minCoords.latitude + (i + 1) * step

        sector = []

        for point in points:
            if point[0] >= startLatitude and point[0] < endLatitude:
                sector.append(point)
                while point in points:
                    points.remove(point)

        miniSectors.append(sector)

#  sort every sector
sortedSectors = []
for miniSector in miniSectors:
    print('sector {0}, {1} points'.format(miniSectors.index(miniSector), len(miniSector)))
    # find start point
    tempSector = miniSector.copy()

    startPoint = miniSector[0]
    prevPoint = miniSector[0]
    nearestPoint = miniSector[1]
    isStartFinded = False
    isNearestFinded = True

    while isNearestFinded is True:

       isNearestFinded = False
       tempSector.remove(prevPoint)
       # print('now in tempSector {0} elements, in miniSector {1} elements'.format(len(tempSector), len(miniSector)))
       minDistance = DISTANCE_THRESHOLD

       # finding nearest point
       for point in tempSector:
           if getDistanceInMeters(prevPoint, point) < minDistance:
               minDistance = getDistanceInMeters(prevPoint, point)
               nearestPoint = point
               isNearestFinded = True

       # if nearest is finded, prevPoint must be equaled to this point and then this point must be removed
       if isNearestFinded is True:
           prevPoint = nearestPoint
       # if can`t finding nearest point, its meaning, that we find start point
       else:
           startPoint = prevPoint

    # on this point starting point for this segment is known
    print('    starting point has been found')

    sortedSector = []
    prevPoint = startPoint
    nearestPoint = startPoint

    secLength = len(miniSector)
    while len(miniSector) > 0:

        if len(miniSector) % 100 is 0 : print('    {0} points left'.format(len(miniSector)))

        minDistance = DISTANCE_THRESHOLD
        pointsDistance = DISTANCE_THRESHOLD

        for point in miniSector:
            pointsDistance = getDistanceInMeters(prevPoint, point)
            if pointsDistance < minDistance and pointsDistance < DISTANCE_THRESHOLD:
                minDistance = pointsDistance
                nearestPoint = point

        sortedSector.append(nearestPoint)
        if nearestPoint in miniSector:
            while nearestPoint in miniSector:
                miniSector.remove(nearestPoint)

        if pointsDistance > DISTANCE_THRESHOLD:
            miniSector.clear()

    sortedSectors.append(sortedSector)

#------------------------------------------------------------------------------------------------------

outGpx = gpxpy.gpx.GPX()

gpx_track = gpxpy.gpx.GPXTrack()
outGpx.tracks.append(gpx_track)

gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)

for sector in sortedSectors:
    for point in sector:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=point[0], longitude=point[1]))

outFileName = namespace.filename.replace('.gpx', '') + '_corrected.gpx'
outFile = open(outFileName, 'w')
outFile.write(outGpx.to_xml())
outFile.close()
print('Success! Recovered route saved in ', outFileName)
