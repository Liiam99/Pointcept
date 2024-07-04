import argparse
import fiona
import json
import pdal
import shapely

from pathlib import Path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_path",
        required=True,
        help="Location where the point cloud in las or laz format is stored.",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory where the tiles should be stored",
    )
    parser.add_argument(
        "--tiles_path",
        help="The path of the shapefile containing the polygons that represent the tiles.",
    )
    parser.add_argument(
        "--tiles_selection",
        default=False,
        help="A text file containing the 1-based indices of the tiles to extract."
    )
    config = parser.parse_args()

    #### DEBUGGING ####
    import time
    start_time = time.time()


    tiles = []
    with fiona.open(config.tiles_path, 'r') as file:
        for feature in file:
            geom = shapely.geometry.shape(feature['geometry'])
            tiles.append(shapely.to_wkt(geom))

    # Subsets the tiles to only include the provided selected ones.
    if config.tiles_selection:
        with open(config.tiles_selection, "r") as file:
            tiles_selection = [int(row.rstrip("\n")) for row in file]
            tiles = [tiles[i - 1] for i in tiles_selection]

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Clips the point cloud for each polygon and writes each clip to a seperate file.
    pdal_json = f'''
    [
        "{config.input_path}",
        {{
            "type":"filters.crop",
            "polygon":{json.dumps(tiles)}
        }},
        {{
            "type":"writers.las",
            "filename":"{output_dir}/tile_#.laz"
        }}
    ]
    '''
    pipeline = pdal.Pipeline(pdal_json)
    pipeline.execute()

    print("Process finished --- %s seconds ---" % (time.time() - start_time))
