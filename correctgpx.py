import argparse
import gpxpy.gpx
import math
import copy
from geopy.distance import geodesic
import gpxpy

DISTANCE_THRESHOLD = 150 # max distance between points in meters
PPR = 50 # points per sector

# ----------- variables to write coordinates in out file -----------
outGpx = gpxpy.gpx.GPX()
gpxTrack = gpxpy.gpx.GPXTrack()
outGpx.tracks.append(gpxTrack)
gpxSegment = gpxpy.gpx.GPXTrackSegment()
gpxTrack.segments.append(gpxSegment)

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
        self.first_tip = Coordinate()
        self.second_tip = Coordinate()
        self.len = 0
        self.max_coord = Coordinate(-90, -180)
        self.min_coord = Coordinate(90, 180)

    def is_empty(self):
        return len(self.points) == 0

    def add_point(self, point):
        if self.is_empty():
            self.points.append(point)
            self.first_tip = point
            self.second_tip = point
            self.max_coord = point
            self.min_coord = point
            self.len = 0
        elif distance_in_meters(point, self.first_tip) < distance_in_meters(point, self.second_tip):
            self.points.insert(0, point)
            self.len += distance_in_meters(point, self.first_tip)
            self.first_tip = point
        else:
            self.points.insert(-1, point)
            self.len += distance_in_meters(point, self.second_tip)
            self.second_tip = point
        if point.latitude > self.max_coord.latitude: self.max_coord.latitude = point.latitude
        if point.latitude < self.min_coord.latitude: self.min_coord.latitude = point.latitude
        if point.longitude > self.max_coord.longitude: self.max_coord.longitude = point.longitude
        if point.longitude < self.min_coord.longitude: self.min_coord.longitude = point.longitude

    def clear(self):
        self.points.clear()
        self.first_tip = Coordinate()
        self.second_tip = Coordinate()
        self.len = 0

    def print_to_file(self, idx):
        gpxSegment.points.clear()
        for point in self.points:
            gpxSegment.points.append(gpxpy.gpx.GPXTrackPoint(latitude = point.latitude, longitude = point.longitude))
        out_file_name = 'track_' + str(idx) + '.gpx'
        out_file = open(out_file_name, 'w')
        out_file.write(outGpx.to_xml())
        out_file.close()

    def add_track(self, track):
        # сначала надо найти общие граничные точки

# ------------ variables ------------
points = [] # container to all point from input file
minCoordinate, maxCoordinate = Coordinate(90, 180), Coordinate(-90, -180)
splittingSectors = [] # sectors with not ordered points
someTracks = [] # непрерывные треки

def distance_in_meters(first_point, second_point):
    return geodesic((first_point.latitude, first_point.longitude), (second_point.latitude, second_point.longitude)).meters

def track_distance(first_track, second_track):
    first_end_second_start_distance = distance_in_meters( first_track.second_tip, second_track.first_tip  )
    second_end_first_start_distance = distance_in_meters( first_track.first_tip,  second_track.second_tip )
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

def split_area_to_sectors():

    find_boundary_points() # find boundary points of area

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
                if start_longitude <= point.longitude < end_longitude:
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
                if start_latitude <= point.latitude < end_latitude:
                    sector.append(point)
                    while point in points:
                        points.remove(point)

            splittingSectors.append(sector)

def build_tracks():

    someTracks.clear()
    simple_track = SimpleTrack()

    for sector in splittingSectors:

        simple_track.clear()

        print('sector {0}'.format(splittingSectors.index(sector)))

        while len(sector) > 0:

            if simple_track.is_empty():
                simple_track.add_point(sector[0])
                del sector[0]
            else:
                nearest_point_to_first_tip = sector[0]
                nearest_point_to_second_tip = sector[0]

                for point in sector:
                    # если эта точка ближе всего к первому концу трека, то запоминаем ее как nearest_point_to_first_tip
                    if distance_in_meters(point, simple_track.first_tip) < distance_in_meters(nearest_point_to_first_tip, simple_track.first_tip):
                        nearest_point_to_first_tip = point
                    # если эта точка ближе всего к второму концу трека, то запоминаем ее как nearest_point_to_second_tip
                    if distance_in_meters(point, simple_track.second_tip) < distance_in_meters(nearest_point_to_second_tip, simple_track.second_tip):
                        nearest_point_to_second_tip = point

                # если обе точки разные, то можно их добавить в трек
                if nearest_point_to_first_tip is not nearest_point_to_second_tip:
                    simple_track.add_point(nearest_point_to_first_tip)
                    sector.remove(nearest_point_to_first_tip)
                    simple_track.add_point(nearest_point_to_second_tip)
                    sector.remove(nearest_point_to_second_tip)
                # если обе переменные указывают на одну и ту же точку, то добавляем только один раз
                else:
                    simple_track.add_point(nearest_point_to_first_tip)
                    sector.remove(nearest_point_to_first_tip)

            print('{0} points left'.format(len(sector)))

        someTracks.append(copy.deepcopy(simple_track))
        simple_track.clear()


# def connect_tracks():
#
#     for track in someTracks:
#         print('track {0} has {1} points'.format(someTracks.index(track), len(track.points)))
#
#     while True:
#
#         print('len of someTracks = ', len(someTracks))
#
#         if len(someTracks) > 1:
#             prev_track = someTracks[0]
#             nearest_track = someTracks[1]
#             min_distance = track_distance(prev_track, nearest_track)
#
#             for track in someTracks:
#                 if track_distance(track, prev_track) < min_distance and track is not prev_track:
#                     min_distance = track_distance(track, prev_track)
#                     nearest_track = track
#
#             someTracks.remove(prev_track)
#             someTracks.remove(nearest_track)
#             someTracks.append(prev_track + nearest_track)
#         else:
#             break

# def connect_tracks(first_track, second_track):
#
#     summary_track = SimpleTrack()
#
#     if first_track.get_end_point() == second_track.get_start_point():
#         summary_track.points.extend(first_track.points)
#         summary_track.points.extend(second_track.points)
#         summary_track.points.remove(first_track.get_end_point())
#         return summary_track
#     elif second_track.get_end_point() == first_track.get_start_point():
#         summary_track.points.extend(second_track.points)
#         summary_track.points.extend(first_track.points)
#         summary_track.points.remove(second_track.get_end_point())
#         return summary_track
#     elif is_connectable(first_track, second_track):
#         summary_track.points.extend(first_track.points)
#         summary_track.points.extend(second_track.points)
#         return summary_track
#     elif is_connectable(second_track, first_track):
#         summary_track.points.extend(second_track.points)
#         summary_track.points.extend(first_track.points)
#         return summary_track

# ------------ work ------------
parser = get_parser() # create parser to program input keys
parse_input_file() # open *.gpx file and extract current info
split_area_to_sectors()
build_tracks()
# connect_tracks()

for track in someTracks:
    track.print_to_file(someTracks.index(track))
