import argparse
import laspy
import os
import random
import re


def merge_las_files(root_dir, output_path, sample_prop):
    """
    PLACEHOLDER.

    Credit: https://gis.stackexchange.com/questions/410809/append-las-files-using-laspy
    """
    # Gets all las/laz files from all subdirectories to merge.
    las_files = []
    for (dir_path, dir_names, file_names) in os.walk(root_dir):
        for file_name in file_names:
            if (re.search(r'.[lL][aA][sSzZ]$', file_name)):
                las_files.append(os.path.join(dir_path, file_name))

    merged_las = laspy.create()
    merged_las.write(output_path)
    random.seed(123)
    print(f"Merging {len(las_files)} las/laz files...")

    for file_nr, las_file in enumerate(las_files):
        # Takes the specified fraction of the full point cloud.
        las = laspy.read(las_file)
        random_indices = random.sample(range(0, len(las) - 1), round((len(las) - 1)/sample_prop))
        sampled_points = las[random_indices]

        # Converts points if the points are in a different LAS format.
        if (las.point_format != merged_las.point_format):
            sampled_points = laspy.convert(sampled_points, point_format_id=merged_las.point_format.id)

        # Appends the points to the merged output.
        with laspy.open(output_path, mode="a") as output:
            # The points must be rescaled to update their coordinates.
            sampled_points.change_scaling(merged_las.header.scales, merged_las.header.offsets)
            output.append_points(sampled_points.points)

        print(f"Progress: {file_nr + 1}/{len(las_files)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_dir",
        required=True,
        help="Directory where the point clouds in las or laz format are stored.",
    )
    parser.add_argument(
        "--output_path",
        required=True,
        help="Output file path of the merged output ending in .las or .laz",
    )
    parser.add_argument(
        "--sample_prop",
        default=1,
        help="Integer that specifies the fraction of points that should be merged. 1 = everything"
    )
    config = parser.parse_args()

    merge_las_files(config.input_dir, config.output_path, config.sample_prop)
