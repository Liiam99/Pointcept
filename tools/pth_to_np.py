import numpy as np
import os
import torch

from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from pathlib import Path


def pth_to_np(pth_file, dataset_root, output_root):
    dataset_root = Path(dataset_root)
    output_root = Path(output_root)

    save_dir = output_root / pth_file.parent.name / pth_file.stem

    os.makedirs(save_dir, exist_ok=True)

    data = torch.load(pth_file)
    coord = data["coord"]
    color = data["color"]
    normal = data["normal"]
    segment = data["semantic_gt"]
    instance = data["instance_gt"]
    np.save(os.path.join(save_dir, "coord.npy"), coord)
    np.save(os.path.join(save_dir, "color.npy"), color)
    np.save(os.path.join(save_dir, "normal.npy"), normal)
    np.save(os.path.join(save_dir, "segment.npy"), segment)
    np.save(os.path.join(save_dir, "instance.npy"), instance)


if __name__ == "__main__":
    dataset_root = "./data/s3disss"
    output_root = "./data/s3dis"

    # Retrieve the file paths of the las/laz files per split.
    data_path = Path(dataset_root)
    data_list = list(data_path.rglob("*[pP][tT][hH]"))

    # Preprocess data.
    print("Processing .pth files...")
    pool = ProcessPoolExecutor(max_workers=16)
    _ = list(
        pool.map(
            pth_to_np,
            data_list,
            repeat(dataset_root),
            repeat(output_root),
        )
    )
    pool.shutdown()
