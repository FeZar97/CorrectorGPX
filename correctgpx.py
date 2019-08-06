import argparse
import gpxpy.gpx
import copy
from geopy.distance import geodesic
import gpxpy

DISTANCE_THRESHOLD = 400
INACCURACY = DISTANCE_THRESHOLD * 3.25 / 360000 # перевод DISTANCE_THRESHOLD в десятичные градусы
SHORT_TRACK_THRESHOLD = 10

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

def distance_in_meters(first_point, second_point):
    return geodesic((first_point.latitude, first_point.longitude), (second_point.latitude, second_point.longitude)).meters

class SimpleTrack:

    def __init__(self):
        self.points = []
        self.first_tip = Coordinate()
        self.second_tip = Coordinate()
        self.max_coord = Coordinate(-90, -180)
        self.min_coord = Coordinate(90, 180)
        self.length = 0

    def __add__(self, other):
        summary_track = SimpleTrack()

        first_end_second_start_distance   = distance_in_meters( self.second_tip, other.first_tip  )
        first_end_second_end_distance     = distance_in_meters( self.second_tip, other.second_tip )
        first_start_second_start_distance = distance_in_meters( self.first_tip,  other.first_tip  )
        first_start_second_end_distance   = distance_in_meters( self.first_tip,  other.second_tip )

        min_length = min(first_end_second_start_distance, first_end_second_end_distance, first_start_second_start_distance, first_start_second_end_distance)

        if min_length == first_end_second_start_distance:
            summary_track.points.extend(copy.deepcopy(self.points))
            summary_track.points.extend(copy.deepcopy(other.points))
            summary_track.first_tip  = copy.deepcopy(self.first_tip)
            summary_track.second_tip = copy.deepcopy(other.second_tip)

        if min_length == first_end_second_end_distance:
            summary_track.points.extend(copy.deepcopy(self.points))
            summary_track.points.extend(copy.deepcopy(copy.deepcopy(other.points[::-1])))
            summary_track.first_tip  = copy.deepcopy(self.first_tip)
            summary_track.second_tip = copy.deepcopy(other.first_tip)

        if min_length == first_start_second_start_distance:
            summary_track.points.extend(copy.deepcopy(self.points[::-1]))
            summary_track.points.extend(copy.deepcopy(other.points))
            summary_track.first_tip  = copy.deepcopy(self.second_tip)
            summary_track.second_tip = copy.deepcopy(other.second_tip)

        if min_length == first_start_second_end_distance:
            summary_track.points.extend(copy.deepcopy(self.points[::-1]))
            summary_track.points.extend(copy.deepcopy(other.points[::-1]))
            summary_track.first_tip  = copy.deepcopy(self.second_tip)
            summary_track.second_tip = copy.deepcopy(other.second_tip)

        summary_track.length = self.length + other.length + min_length

        summary_track.try_update_boards(self.max_coord)
        summary_track.try_update_boards(self.min_coord)
        summary_track.try_update_boards(other.max_coord)
        summary_track.try_update_boards(other.min_coord)

        return summary_track

    def __eq__(self, other):
        return self.points == other.points and self.points == other.points

    def try_update_boards(self, new_point):
        if new_point.latitude  > self.max_coord.latitude:  self.max_coord.latitude  = new_point.latitude
        if new_point.latitude  < self.min_coord.latitude:  self.min_coord.latitude  = new_point.latitude
        if new_point.longitude > self.max_coord.longitude: self.max_coord.longitude = new_point.longitude
        if new_point.longitude < self.min_coord.longitude: self.min_coord.longitude = new_point.longitude

    def distance_to_track(self, other_track):

        self_first_other_first_distance   = distance_in_meters(self.points[0],  other_track.points[0])
        self_first_other_second_distance  = distance_in_meters(self.points[0],  other_track.points[-1])
        self_second_other_first_distance  = distance_in_meters(self.points[-1], other_track.points[0])
        self_second_other_second_distance = distance_in_meters(self.points[-1], other_track.points[-1])

        return min(self_second_other_first_distance, self_second_other_second_distance, self_first_other_first_distance, self_first_other_second_distance)

    def clear(self):
        self.points.clear()
        self.first_tip = Coordinate()
        self.second_tip = Coordinate()
        self.max_coord = Coordinate(-90, -180)
        self.min_coord = Coordinate(90, 180)

    def print_to_file(self, name):
        gpxSegment.points.clear()
        for track_point in self.points:
            gpxSegment.points.append(gpxpy.gpx.GPXTrackPoint(latitude = track_point.latitude, longitude = track_point.longitude))
        out_file_name = name + '.gpx'
        out_file = open(out_file_name, 'w')
        out_file.write(outGpx.to_xml())
        out_file.close()

    def get_area(self):
        return (self.max_coord.latitude - self.min_coord.latitude) * (self.max_coord.longitude - self.min_coord.longitude)

    def lies_within(self, big_track):
        return (self.max_coord.latitude  <= big_track.max_coord.latitude  + INACCURACY  and\
                self.max_coord.longitude <= big_track.max_coord.longitude + INACCURACY  and\
                self.min_coord.latitude  >= big_track.min_coord.latitude  - INACCURACY  and\
                self.min_coord.longitude >= big_track.min_coord.longitude - INACCURACY)

    def calc_length(self):
        for i in range(1, len(self.points), 1):
            self.length += distance_in_meters(self.points[i - 1], self.points[i])

minCoordinate, maxCoordinate = Coordinate(90, 180), Coordinate(-90, -180)
someTracks = []
cleanTracks = []

def get_parser():
    new_parser = argparse.ArgumentParser(prog = 'GPX_Orderer', description = 'Program %(prog)s sorts  contents of the input file in GPX format')
    new_parser.add_argument('-f', '--filename', type = str, help = 'Name of input file', required = True)
    new_parser.add_argument('-s', '--size',     type = int, help = 'How much percentages of file must be processed', default = 100)
    return new_parser.parse_args()

def parse_input_file():

    parser = get_parser()

    gpx_file = open(parser.filename, 'r')
    gpx = gpxpy.parse(gpx_file)
    # print('{0} waypoints, {1} routes, {2} tracks'.format(len(gpx.tracks), len(gpx.routes), len(gpx.waypoints)))

    simple_track = SimpleTrack()

    for track in gpx.tracks:
        for segment in track.segments:
            simple_track.first_tip = Coordinate(segment.points[0].latitude, segment.points[0].longitude)
            simple_track.second_tip = Coordinate(segment.points[-1].latitude, segment.points[-1].longitude)
            for point in segment.points:
                simple_track.points.append(Coordinate(point.latitude, point.longitude))
                simple_track.try_update_boards(point)
            simple_track.calc_length()
            someTracks.append(copy.deepcopy(simple_track))
            simple_track.clear()
    gpx_file.close()

def delete_short_tracks():
    for track in someTracks:
        if len(track.points) < SHORT_TRACK_THRESHOLD or track.length < DISTANCE_THRESHOLD:
            someTracks.remove(track)

def delete_repeating_tracks():

    while len(someTracks) > 0:

        max_area = 0
        max_area_track = SimpleTrack()

        for track in someTracks:
            if track.get_area() > max_area:
                max_area = track.get_area()
                max_area_track = track

        flag = True
        while flag:
            flag = False
            for track in someTracks:
                if track is not max_area_track and track.lies_within(max_area_track):
                    flag = True
                    someTracks.remove(track)

        cleanTracks.append(copy.deepcopy(max_area_track))
        someTracks.remove(max_area_track)

def connect_tracks():

    while len(cleanTracks) > 1:

        nearest_track = cleanTracks[1]

        for i in range(1, len(cleanTracks), 1):
            if cleanTracks[0].distance_to_track(cleanTracks[i]) < cleanTracks[0].distance_to_track(nearest_track):
                nearest_track = cleanTracks[i]

        summary_track = cleanTracks[0] + nearest_track
        cleanTracks.remove(cleanTracks[0])
        cleanTracks.remove(nearest_track)
        cleanTracks.append(copy.deepcopy(summary_track))
    cleanTracks[0].length = 0
    cleanTracks[0].calc_length()

parse_input_file()
delete_short_tracks()
delete_repeating_tracks()
connect_tracks()
print('Success!\nTotal length of result track: {:f} kilometers'.format(cleanTracks[0].length / 1000))
cleanTracks[0].print_to_file('result')
