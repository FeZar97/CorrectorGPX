# CorrectorGPX
Correct GPX tracks/ways/routes, that have gaps.

## Detailed description
Often, generation of paths and routes using GPS tags is accompanied by small gaps, that do not allow consider path as a whole. This script allows you to combine all sections of the route or path into one structure.
Script accepts two input parameters.
First parameter use flag '-f' or '--filename' and hold name of input file in format '\*.gpx '.
Second parameter use flag '-t' or '--tagname' and hold name of GPX tag, that acts as the origin of the route points:
* `wpt` if the points are stored as waypoints;
* `trk` if the points are stored as traketories;
* `rte` if the points are stored as routes.

## Using
`python corrctgpx.py -f <GPX filename>.gpx -t <tag name>`
