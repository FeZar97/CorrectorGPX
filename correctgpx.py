import argparse
import gpxpy
import gpxpy.gpx
from geopy.distance import distance
from geopy.distance import geodesic
from geopy.distance import great_circle
from gpxpy.gpx import GPXTrackPoint

THRESHOLD = 20000

def getDistance(p1, p2):
    return distance( (p1[0], p1[1]), (p2[0], p2[1])).meters

points = {}

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
                #print([point.latitude, point.longitude])
elif namespace.tagname == 'rte':
    for route in gpx.routes:
        for point in route.points:
            points.append([point.latitude, point.longitude])

outGpx = gpxpy.gpx.GPX()

gpx_track = gpxpy.gpx.GPXTrack()
outGpx.tracks.append(gpx_track)

gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)

maxPointsDistance = 100 # in meters
maxGeodesicDistance = 0.0
maxGreatCircleDistance = 0.0

# for point in points:
    # gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=point[0], longitude=point[1]))

    # if geodesic(point, prevPoint).kilometers > maxGeodesicDistance:
    #     maxGeodesicDistance = geodesic(point, prevPoint).kilometers
    # if great_circle(point, prevPoint).kilometers > maxGreatCircleDistance:
    #     maxGreatCircleDistance = great_circle(point, prevPoint).kilometers
    # prevPoint = point


# FIND START POINT
sourcePointList = points.copy()

startPoint = points[0]
prevPoint = points[0]
nearestPoint = points[1]
isStartFinded = False
isNearestFinded = True

while isNearestFinded is True:

    # print('now in {0}, in list are {1} points'.format(prevPoint, len(sourcePointList)))

    isNearestFinded = False
    sourcePointList.remove(prevPoint)
    minDistance = THRESHOLD

    # finding nearest point
    for point in sourcePointList:
        if getDistance(prevPoint, point) < THRESHOLD and getDistance(prevPoint, point) < minDistance:
            minDistance = getDistance(prevPoint, point)
            nearestPoint = point
            isNearestFinded = True

    # if isNearestFinded is True, then nearest is finded. prevPoint must be equaled to this point and then this point must be removed
    if isNearestFinded is True:
        print('jump from {0} to {1}. dist: {2}'.format(prevPoint, nearestPoint, getDistance(prevPoint, nearestPoint)))
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=prevPoint[0], longitude=prevPoint[1]))
        outFile = open(namespace.filename.replace('.gpx', '') + '_corrected.gpx', 'w')
        outFile.write(outGpx.to_xml())
        outFile.close()
        prevPoint = nearestPoint
    # if can`t finding nearest point, its meaning, that we find start point
    else:
        startPoint = prevPoint

#print('maxGCDistance = {0} km, maxGDistance = {1} km'.format(maxGreatCircleDistance, maxGeodesicDistance))
print('startPoint: {0}, length of sourcePointList: {1}, {2}'.format(startPoint, len(sourcePointList), len(points)))
print('-------------------------------------------------------------------------------')
