import argparse
import multiprocessing as mp
import os
import laspy
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from pathlib import Path


def parse_tile(file_path, split, output_root):
    print(f"Parsing tile {file_path.stem} in {split} split")

    # Extract coordinates [x, y, z], strength [0.->1.] & label [uint]
    las = laspy.read(file_path)
    coord = np.array((las.x, las.y, las.z)).transpose()

    if file_path.stem.startswith("CSX"):
        FEET_TO_METERS = 1200/3937
        coord = coord*FEET_TO_METERS

    #intensity = np.array(las.intensity).reshape([-1, 1])
    #strength = intensity/np.iinfo(intensity.dtype).max
    segment = np.array(las.classification)

    output_root = Path(output_root)
    save_path = output_root / split / file_path.stem
    save_path.mkdir(parents=True, exist_ok=True)
    np.save(save_path / "coord.npy", coord.astype(np.float32))
    #np.save(save_path / "strength.npy", strength.astype(np.float32))
    np.save(save_path / "segment.npy", segment.astype(np.uint8))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset_root",
        required=True,
        help="Path to the InternRail dataset containing train, val, and test folders",
    )
    parser.add_argument(
        "--output_root",
        required=True,
        help="Output path where the preprocessed train, val, and test folders will be located",
    )
    parser.add_argument(
        "--seed",
        default=123,
        help="Seed that determines which tiles from the train, val, and test folders will be sampled."
    )
    parser.add_argument(
        "--num_workers",
        default=mp.cpu_count(),
        type=int,
        help="Num workers for preprocessing.",
    )
    config = parser.parse_args()

    # Create output directories.
    train_output_dir = os.path.join(config.output_root, "train")
    os.makedirs(train_output_dir, exist_ok=True)
    val_output_dir = os.path.join(config.output_root, "val")
    os.makedirs(val_output_dir, exist_ok=True)
    test_output_dir = os.path.join(config.output_root, "test")
    os.makedirs(test_output_dir, exist_ok=True)

    # Retrieve the file paths of the las/laz files per split.
    data_path = Path(config.dataset_root)
    train_list = list(data_path.joinpath("train").glob("*.[lL][aS][zZsS]"))
    val_list = list(data_path.joinpath("val").glob("*.[lL][aS][zZsS]"))
    test_list = list(data_path.joinpath("test").glob("*.[lL][aS][zZsS]"))

    data_list = np.concatenate([train_list, val_list, test_list])
    split_list = np.concatenate(
        [
            np.full_like(train_list, "train"),
            np.full_like(val_list, "val"),
            np.full_like(test_list, "test"),
        ]
    )

    # Preprocess data.
    print("Processing tiles...")
    pool = ProcessPoolExecutor(max_workers=config.num_workers)
    _ = list(
        pool.map(
            parse_tile,
            data_list,
            split_list,
            repeat(config.output_root),
        )
    )
    pool.shutdown()
