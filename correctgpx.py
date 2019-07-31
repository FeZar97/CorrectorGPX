import argparse
#import gpxpy
import gpxpy.gpx
import math
from geopy.distance import distance

# max distance between points in meters
DISTANCE_THRESHOLD = 1000
# points per sector
PPR = 500

class Coordinate:
    def __init__(self, latitude = 0, longitude = 0):
        self.latitude = latitude
        self.longitude = longitude

    def __eq__(self, other):
        return self.latitude == other.latitude and self.longitude == other.longitude

    def __str__(self):
        return str([self.latitude, self.longitude])

    def distance(self, other):
        return distance( (self.latitude, self.longitude), (other.latitude, other.longitude) ).meters

class SimpleTrack:
    def __init__(self):
        self.points = []
        self.startPoint = None
        self.endPoint = None

    def is_connectable(self, other):
        return self.endPoint == other.startPoint or self.startPoint == other.endPoint

    def __add__(self, other):
        summary_track = SimpleTrack()
        if self.endPoint == other.startPoint:
            summary_track.points.append(self.points)
            summary_track.points.append(other.points)
            summary_track.points.remove(self.endPoint)
            return summary_track
        elif other.endPoint == self.startPoint:
            summary_track.points.append(other.points)
            summary_track.points.append(self.points)
            summary_track.points.remove(other.endPoint)
            return summary_track

def find_boundary_points():
    for point in points:
        if point.latitude  > max_coordinate.latitude:  max_coordinate.latitude  = point.latitude
        if point.latitude  < min_coordinate.latitude:  min_coordinate.latitude  = point.latitude
        if point.longitude > max_coordinate.longitude: max_coordinate.longitude = point.longitude
        if point.longitude < min_coordinate.longitude: min_coordinate.longitude = point.longitude

    print('Max coordinate: {0}, min coordinate: {1}'.format(max_coordinate, min_coordinate))

def get_parser():
    new_parser = argparse.ArgumentParser(prog = 'GPX_Orderer', description = 'Program %(prog)s sorts  contents of the input file in GPX format')
    new_parser.add_argument('-f', '--filename', type=str, help = 'Name of input file', required=True)
    new_parser.add_argument('-t', '--tagname',  type=str, help = 'Source of points'  , choices=['wpt', 'trk', 'rte'], required=True)
    new_parser.add_argument('-s', '--size',     type=int, help = 'How much percentages of file must be processed', default=100)
    return new_parser.parse_args()

def parse_input_file():
    gpx_file = open(parser.filename, 'r')
    gpx = gpxpy.parse(gpx_file)
    print('-------------------------------------------------------------------------------')
    print('{0} waypoints, {1} routes, {2} tracks'.format(len(gpx.tracks), len(gpx.routes), len(gpx.waypoints)))
    if parser.tagname == 'wpt':
        for waypoint in gpx.waypoints:
            points.append(Coordinate(waypoint.latitude, waypoint.longitude))
    elif parser.tagname == 'trk':
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    points.append(Coordinate(point.latitude, point.longitude))
    elif parser.tagname == 'rte':
        for route in gpx.routes:
            for point in route.points:
                points.append(Coordinate(point.latitude, point.longitude))

# variables to write coordinates in out file
outGpx = gpxpy.gpx.GPX()
gpx_track = gpxpy.gpx.GPXTrack()
outGpx.tracks.append(gpx_track)
gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)

# ------------ variables ------------
points = [] # container to all point from input file
mini_tracks = [] # container to track
min_coordinate, max_coordinate = Coordinate(90, 180), Coordinate(-90, -180)

# ------------ work ------------
parser = get_parser() # create parser to program input keys
parse_input_file() # open *.gpx file and extract current info
find_boundary_points() # find boundary points of area

numberOfSectors = math.floor(len(points)/PPR) # number of sectors

width = max_coordinate.longitude - min_coordinate.longitude
height = max_coordinate.latitude - min_coordinate.latitude

# sectors with ordered points
miniSectors = []

# if "width" > "height", then make split by width (by longitude)
if width > height:
    step =  width/numberOfSectors
    for i in range(numberOfSectors):

        startLongitude = min_coordinate.longitude + i * step
        endLongitude = min_coordinate.longitude + (i + 1) * step

        sector = []
        gpx_segment.points.clear()

        for point in points:
            if point.longitude >= startLongitude and point.longitude < endLongitude:
                sector.append(point)
                while point in points:
                    points.remove(point)

        for point in sector:
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=point[0], longitude=point[1]))

        miniSectors.append(sector)
        outFile = open('segment' + str(miniSectors.index(sector)) + '_notSorted.gpx', 'w')
        outFile.write(outGpx.to_xml())
        outFile.close()
# if "width" < "height", then make split by height
else:
    step =  height/numberOfSectors
    for i in range(numberOfSectors):

        startLatitude = min_coordinate.latitude + i * step
        endLatitude = min_coordinate.latitude + (i + 1) * step

        sector = []
        gpx_segment.points.clear()

        for point in points:
            if point.latitude in (startLatitude, endLatitude): # point.latitude >= startLatitude and point.latitude < endLatitude:
                sector.append(point)
                while point in points:
                    points.remove(point)

        for point in sector:
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=point[0], longitude=point[1]))

        miniSectors.append(sector)
        outFile = open('segment' + str(miniSectors.index(sector)) + '_notSorted.gpx', 'w')
        outFile.write(outGpx.to_xml())
        outFile.close()

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

for miniSector in miniSectors:

    gpx_segment.points.clear()

    for point in miniSector:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=point[0], longitude=point[1]))

    # write segments to file
    outFile = open('segment' + str(miniSectors.index(miniSector)) + '_sorted.gpx', 'w')
    outFile.write(outGpx.to_xml())
    outFile.close()

for sector in sortedSectors:
    for point in sector:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=point[0], longitude=point[1]))

outFileName = namespace.filename.replace('.gpx', '') + '_corrected.gpx'
outFile = open(outFileName, 'w')
outFile.write(outGpx.to_xml())
outFile.close()
print('Success! Recovered route saved in ', outFileName)
