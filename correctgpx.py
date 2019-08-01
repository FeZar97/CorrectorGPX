import argparse
import gpxpy.gpx
import math
import copy
from geopy.distance import geodesic
import gpxpy

DISTANCE_THRESHOLD = 150 # max distance between points in meters
PPR = 500 # points per sector

class Coordinate:
    def __init__(self, latitude = 0, longitude = 0):
        self.latitude = latitude
        self.longitude = longitude

    def __eq__(self, other):
        return self.latitude == other.latitude and self.longitude == other.longitude

    def __str__(self):
        return str([self.latitude, self.longitude])

class SimpleTrack:
    def __init__(self):
        self.points = []

    def __add__(self, other):
        summary_track = SimpleTrack()
        if self.get_end_point() == other.get_start_point():
            summary_track.points.append(self.points)
            summary_track.points.append(other.points)
            summary_track.points.remove(self.get_end_point())
            return summary_track
        elif other.get_end_point() == self.get_start_point():
            summary_track.points.append(other.points)
            summary_track.points.append(self.points)
            summary_track.points.remove(other.get_end_point())
            return summary_track
        elif is_connectable(self, other):
            summary_track.points.append(self.points)
            summary_track.points.append(other.points)
            return summary_track
        elif is_connectable(other, self):
            summary_track.points.append(other.points)
            summary_track.points.append(self.points)
            return summary_track

    def is_empty(self):
        return len(self.points) == 0

    def add(self, point):
        self.points.append(point)

    def get_start_point(self):
            return self.points[0]
        # if len(self.points) > 0:
        #     return self.points[0]
        # else:
        #     return None

    def get_end_point(self):
        return self.points[-1]
        # if len(self.points) > 0:
        #     return self.points[-1]
        # else:
        #     return None

    def clear(self):
        self.points.clear()

# ----------- variables to write coordinates in out file -----------
outGpx = gpxpy.gpx.GPX()
gpxTrack = gpxpy.gpx.GPXTrack()
outGpx.tracks.append(gpxTrack)
gpxSegment = gpxpy.gpx.GPXTrackSegment()
gpxTrack.segments.append(gpxSegment)

# ------------ variables ------------
points = [] # container to all point from input file
minCoordinate, maxCoordinate = Coordinate(90, 180), Coordinate(-90, -180)
splittingSectors = [] # sectors with ordered points
someTracks = [] # непрерывные треки

def distance_in_meters(first_point, second_point):
    return geodesic((first_point.latitude, first_point.longitude), (second_point.latitude, second_point.longitude)).meters

def track_distance(first_track, second_track):
    first_end_second_start_distance = distance_in_meters( first_track.get_end_point(),   second_track.get_start_point() )
    second_end_first_start_distance = distance_in_meters( first_track.get_start_point(), second_track.get_end_point()   )
    return min(first_end_second_start_distance, second_end_first_start_distance)

def is_connectable(first_track, second_track):
    return track_distance(first_track, second_track) < DISTANCE_THRESHOLD

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
    gpx_file.close()

def find_boundary_points():
    for point in points:
        if point.latitude  > maxCoordinate.latitude:  maxCoordinate.latitude  = point.latitude
        if point.latitude  < minCoordinate.latitude:  minCoordinate.latitude  = point.latitude
        if point.longitude > maxCoordinate.longitude: maxCoordinate.longitude = point.longitude
        if point.longitude < minCoordinate.longitude: minCoordinate.longitude = point.longitude

    print('max coordinate: {0}\nmin coordinate: {1}'.format(maxCoordinate, minCoordinate))

def split_area_to_sectors():
    number_of_sectors = math.floor(len(points)/PPR) # number of sectors

    width = maxCoordinate.longitude - minCoordinate.longitude
    height = maxCoordinate.latitude - minCoordinate.latitude

    # if "width" > "height", then make split by width (by longitude)
    if width > height:
        longitude_step = width / number_of_sectors
        for i in range(number_of_sectors):

            start_longitude = minCoordinate.longitude + i * longitude_step
            end_longitude = minCoordinate.longitude + (i + 1) * longitude_step

            sector = []

            for point in points:
                if point.longitude >= start_longitude and point.longitude < end_longitude: # -------------------------------------------------------------- FIX IT ---------------------------------------------------------------------------------------------
                #if point.longitude in (start_longitude, end_longitude):
                    sector.append(point)
                    while point in points:
                        points.remove(point)

            splittingSectors.append(sector)
    # if "width" < "height", then make split by height
    else:
        latitude_step = height / number_of_sectors
        for i in range(number_of_sectors):

            start_latitude = minCoordinate.latitude + i * latitude_step
            end_latitude = minCoordinate.latitude + (i + 1) * latitude_step

            sector = []

            for point in points:
                if point.latitude in (start_latitude, end_latitude): # point.latitude >= startLatitude and point.latitude < endLatitude:
                    sector.append(point)
                    while point in points:
                        points.remove(point)

            splittingSectors.append(sector)

def build_tracks():

    someTracks.clear()
    simple_track = SimpleTrack()

    for sector in splittingSectors:

        print('sector {0}'.format(splittingSectors.index(sector)))

        while len(sector) > 0:
            # поиск ближайшей точки
            global nearest_point
            global prev_point
            prev_point = sector[0]
            simple_track.add(prev_point)
            sector.remove(prev_point)

            # если в секторе есть другие точки, то пытаемся их соединить
            if len(sector) > 0:

                nearest_point = sector[0]
                min_points_distance = min(distance_in_meters(prev_point, nearest_point), DISTANCE_THRESHOLD)

                for point in sector:
                    if point is not prev_point and distance_in_meters(point, prev_point) < min_points_distance:
                        min_points_distance = distance_in_meters(point, prev_point)
                        nearest_point = point

                # если расстояние до ближайшей точки меньше порога, то добавляем точку в трэк
                if min_points_distance < DISTANCE_THRESHOLD:
                    prev_point = nearest_point

            # если в секторе уже нет точек, то итоговый трек добавляется в общий список треков
            else:
                someTracks.append(copy.deepcopy(simple_track))
                print('track {0}, {1} points'.format(len(someTracks), len(simple_track.points)))
                simple_track.clear()

        # если после обработки сектора в временном трэке что то есть, то добавляем это как отдельный трек
        if not simple_track.is_empty():
            someTracks.append(copy.deepcopy(simple_track))
            print('track {0}, {1} points'.format(len(someTracks), len(simple_track)))
            simple_track.clear()

def connect_tracks():

    for track in someTracks:
        print('track {0} has {1} points'.format(someTracks.index(track), len(track.points)))

    while True:

        print('len of someTracks = ', len(someTracks))

        if len(someTracks) > 1:
            prev_track = someTracks[0]
            nearest_track = someTracks[1]
            min_distance = track_distance(prev_track, nearest_track)

            for track in someTracks:
                if track_distance(track, prev_track) < min_distance and track is not prev_track:
                    min_distance = track_distance(track, prev_track)
                    nearest_track = track

            someTracks.remove(prev_track)
            someTracks.remove(nearest_track)
            someTracks.append(prev_track + nearest_track)
        else:
            break

# ------------ work ------------
parser = get_parser() # create parser to program input keys
parse_input_file() # open *.gpx file and extract current info
find_boundary_points() # find boundary points of area
split_area_to_sectors()
build_tracks()
connect_tracks()

outFileName = 'result.gpx'
outFile = open(outFileName, 'w')
outFile.write(outGpx.to_xml())
outFile.close()
print('Success! Recovered route saved in ', outFileName)

# for sector in sortedSectors:
#     for point in sector:
#         gpxSegment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=point[0], longitude=point[1]))
#
# outFileName = namespace.filename.replace('.gpx', '') + '_corrected.gpx'
# outFile = open(outFileName, 'w')
# outFile.write(outGpx.to_xml())
# outFile.close()
# print('Success! Recovered route saved in ', outFileName)
