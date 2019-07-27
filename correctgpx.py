import argparse
import gpxpy
import gpxpy.gpx

points =  []

parser = argparse.ArgumentParser(prog = 'GPX_Orderer', description = 'Program %(prog)s sorts  contents of the input file in GPX format')
parser.add_argument('-f', '--filename', type=str, required=True, help = 'Name of input file')
parser.add_argument('-t', '--tagname', choices=['wpt', 'trk', 'rte'], required=True, type=str, help = 'Source of points')

namespace = parser.parse_args()

gpx_file = open(namespace.filename, 'r')
gpx = gpxpy.parse(gpx_file)

print('{0} waypoints, {1} routes, {2} tracks'.format(len(gpx.tracks), len(gpx.routes), len(gpx.waypoints)))

if namespace.tagname == 'wpt':
    for waypoint in gpx.waypoints:
        points += waypoint.points
elif namespace.tagname == 'trk':
    for track in gpx.tracks:
        for segment in track.segments:
            points += segment.points
elif namespace.tagname == 'rte':
    for route in gpx.routes:
        points += route.points

outGpx = gpxpy.gpx.GPX()

gpx_track = gpxpy.gpx.GPXTrack()
outGpx.tracks.append(gpx_track)

gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)

for point in points:
    gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=point.latitude, longitude=point.longitude))

outFile = open(namespace.filename.replace('.gpx', '') + '_corrected.gpx', 'w')
outFile.write(outGpx.to_xml())
outFile.close()