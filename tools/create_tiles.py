import argparse
import geopandas as gpd
import laspy
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pygeoops
import random

from pathlib import Path
from shapely import concave_hull, LineString, MultiPoint, Point
from shapely.ops import split, substring


def export_tiles(las, tiles, output_dir, prefix):
    """PLACEHOLDER."""
    # calculate polygon by connecting the points
    # extract points from las using polygon
    # export as las/laz


def create_tiles(las, length, width):
    """PLACEHOLDER."""
    centerline = get_centerline(las, length, 10000)
    transects = create_transects(centerline, length)
    buffer = centerline.buffer(width/2, join_style="bevel", cap_style="flat")

    tiles = []
    for transect in transects[:-1]:
        # Gets the final two points of a transect.
        last_point = Point(transect.coords[-1])
        penultimate_point = Point(transect.coords[-2])

        # Creates a line perpendicular to the last line segment's direction.
        angle = get_angle(last_point, penultimate_point)
        divider = create_divider(last_point, angle, width)

        # Divides the buffer and tile.
        buffer_tile_split = split(buffer, divider)
        polygon_1 = buffer_tile_split.geoms[0]
        polygon_2 = buffer_tile_split.geoms[1]

        # The smaller polygon is the tile.
        if polygon_1.area > polygon_2.area:
            buffer = polygon_1
            tile = polygon_2
        else:
            buffer = polygon_2
            tile = polygon_1

        tiles.append(tile)

    # Last tile is just the remainder of the buffer.
    tiles.append(buffer)

    return tiles


def create_divider(point, bearing, line_length):
    """Credit to: https://glenbambrick.com/tag/shapely/"""
    # Makes the line a bit longer to avoid floating precision problems with splitting.
    line_length = line_length*1.1

    # Calculates one line end on one edge of the buffer.
    # This edge is parallel to the last point.
    angle = bearing + 90
    point_1_bearing = math.radians(angle)
    x_1 = point.x + (line_length/2) * math.cos(point_1_bearing)
    y_1 = point.y + (line_length/2) * math.sin(point_1_bearing)

    # Calculates the other line end which is on the other edge of the buffer.
    point_2_bearing = point_1_bearing + math.radians(180)
    x_2 = x_1 + line_length*math.cos(point_2_bearing)
    y_2 = y_1 + line_length*math.sin(point_2_bearing)

    # Returns a line that is perpendicular to the orientation of the transect.
    return(LineString([[x_1, y_1], [x_2, y_2]]))


def get_angle(point_1, point_2):
    """PLACEHOLDER."""
    x_diff = point_1.x - point_2.x
    y_diff = point_1.y - point_2.y
    return math.degrees(math.atan2(y_diff, x_diff))


def create_transects(centerline, length):
    """PLACEHOLDER."""
    transects = []
    start = 0

    while (True):
        transect = substring(centerline, start, start + length)

        # A point is returned if there is no segment left.
        if type(transect) is Point:
            break

        transects.append(transect)
        start += length

    return transects


def get_centerline(las, length, sample_prop):
    """PLACEHOLDER."""
    # Most points are distributed close to the scanner.
    random.seed(123)
    random_indices = random.sample(range(0, len(las) - 1), round(len(las)/sample_prop))
    las_sample = las[random_indices]

    # Creates a concave hull that encapsulates the majority of the points.
    las_sample_xy = np.column_stack((las_sample.x, las_sample.y))
    las_sample_xy_mp = MultiPoint(las_sample_xy)
    hull = concave_hull(las_sample_xy_mp, ratio=0.01)

    # Creates a line that represents the main trajectory of the scanner.
    centerline = pygeoops.centerline(
        hull,
        simplifytolerance=length,
        densify_distance=length,
        min_branch_length=2*length,
        extend=True
    )

    return centerline


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--las_path",
        required=True,
        help="Location where the point cloud in las or laz format is stored.",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory where the tiles should be stored.",
    )
    parser.add_argument(
        "--tile_length",
        default=25,
        help="The desired length of each tile.",
    )
    parser.add_argument(
        "--prefix",
        default="tile",
        help="The prefix of each tile that will be included in the file name."
    )
    config = parser.parse_args()

    os.makedirs(config.output_dir, exist_ok=True)

    las_path = Path(config.las_path)
    las = laspy.read(las_path)
    tiles = create_tiles(las, config.tile_length, 20)
