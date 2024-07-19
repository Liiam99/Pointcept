import argparse
import laspy
import multiprocessing as mp
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from pathlib import Path


def export_result(result_path, test_root, output_dir):
    test_root = Path(test_root)

    # Retrieve the original point cloud.
    las_path = test_root.glob(f"{result_path.stem[:-5]}.[lL][aS][zZ]")
    las_path = next(las_path)
    las = laspy.read(las_path)

    # Add the predicted labels to the point cloud.
    las.add_extra_dim(laspy.ExtraBytesParams(
        name="prediction",
        type=np.uint8,
    ))
    preds = np.load(result_path)
    las.prediction = preds

    save_path = output_dir / las_path.name
    las.write(save_path)

    print(f"Saved {las_path.name} to {output_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result_dir",
        required=True,
        help="Path where the .npy predictions are saved."
    )
    parser.add_argument(
        "--test_root",
        required=True,
        help="Path where the test folder with the point cloud files is located.",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Output directory where the results should be exported to."
    )
    parser.add_argument(
        "--num_workers",
        default=mp.cpu_count(),
        type=int,
        help="Num workers for preprocessing.",
    )
    config = parser.parse_args()

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result_dir = Path(config.result_dir)
    result_list = result_dir.rglob("*.[nN][pP][yY]")

    print("Saving the point clouds with the predicted labels added...")
    pool = ProcessPoolExecutor(max_workers=config.num_workers)
    _ = list(
        pool.map(
            export_result,
            result_list,
            repeat(config.test_root),
            repeat(output_dir),
        )
    )
    pool.shutdown()
