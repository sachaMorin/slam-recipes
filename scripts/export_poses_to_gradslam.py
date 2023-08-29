import os
import sys
import argparse

import numpy as np

_EPS = np.finfo(float).eps * 4.0


def transform44(l: tuple):
    r"""Generate a 4x4 homogeneous transformation matrix from a 3D point and unit quaternion.

    Args:
        l (tuple): tuple consisting of (stamp,tx,ty,tz,qx,qy,qz,qw) where (tx,ty,tz) is the
            3D position and (qx,qy,qz,qw) is the unit quaternion.

    Returns:
        np.ndarray: 4x4 homogeneous transformation matrix

    Shape:
        - Output: `(4, 4)`
    """
    t = l[1:4]
    q = np.array(l[4:8], dtype=np.float64, copy=True)
    nq = np.dot(q, q)
    if nq < _EPS:
        return np.array(
            (
                (1.0, 0.0, 0.0, t[0]),
                (0.0, 1.0, 0.0, t[1]),
                (0.0, 0.0, 1.0, t[2]),
                (0.0, 0.0, 0.0, 1.0),
            ),
            dtype=np.float64,
        )
    q *= np.sqrt(2.0 / nq)
    q = np.outer(q, q)
    return np.array(
        (
            (1.0 - q[1, 1] - q[2, 2], q[0, 1] - q[2, 3], q[0, 2] + q[1, 3], t[0]),
            (q[0, 1] + q[2, 3], 1.0 - q[0, 0] - q[2, 2], q[1, 2] - q[0, 3], t[1]),
            (q[0, 2] - q[1, 3], q[1, 2] + q[0, 3], 1.0 - q[0, 0] - q[1, 1], t[2]),
            (0.0, 0.0, 0.0, 1.0),
        ),
        dtype=np.float64,
    )


def read_trajectory(filename: str, matrix: bool = True):
    r"""Read a trajectory from a text file.

    Args:
        filename: Path of file to be read
        matrix (np.ndarray or tuple): If True, will convert poses to 4x4 homogeneous transformation
            matrices (of type np.ndarray). Else, will return poses as tuples consisting of
            (stamp,tx,ty,tz,qx,qy,qz,qw), where (tx,ty,tz) is the 3D position and (qx,qy,qz,qw)
            is the unit quaternion.

    Returns:
        dict: dictionary of {stamp: pose} where stamp is of type str and pose is a 4x4 np.ndarray if matrix is True,
            or a tuple of position and unit quaternion (tx,ty,tz,qx,qy,qz,qw) if matrix is False.

    """
    file = open(filename)
    data = file.read()
    lines = data.replace(",", " ").replace("\t", " ").split("\n")
    list = []
    for line in lines:
        line_list = []
        if len(line) > 0 and line[0] != "#":
            for n, v in enumerate(line.split(" ")):
                v = v.strip()
                if v != "":
                    v = float(v) if n > 0 else v
                    line_list.append(v)
            list.append(line_list)
    list_ok = []
    for i, l in enumerate(list):
        if l[4:8] == [0, 0, 0, 0]:
            continue
        isnan = False
        for v in l[1:]:
            if np.isnan(v):
                isnan = True
                break
        if isnan:
            sys.stderr.write(
                "Warning: line %d of file '%s' has NaNs, skipping line\n"
                % (i, filename)
            )
            continue
        list_ok.append(l)
    if matrix:
        traj = [transform44(l[0:]) for l in list_ok]
    else:
        traj = [l[1:8] for l in list_ok]
    return traj


# Argparse with a path, input_file and output_file arguments
parser = argparse.ArgumentParser()
parser.add_argument("--path", type=str, help="Path to the sequence")
parser.add_argument("--input_file", type=str, help="Name of the input file", default="poses.txt")
parser.add_argument("--output_file", type=str, help="Name of the output file", default="poses_matrix.txt")
args = parser.parse_args()

poses = read_trajectory(os.path.join(args.path, args.input_file), matrix=True)
outfile = os.path.join(args.path, args.output_file)
print(f"Processing {len(poses)} poses...")
cur_global_pose = np.eye(4)
poses_to_write = []
for i in range(len(poses)):
    cur_global_pose = poses[i]
    poses_to_write.append(cur_global_pose.reshape(-1).tolist())

with open(outfile, "w") as f:
    for pose in poses_to_write:
        linestr = ""
        for item in pose:
            linestr += str(item)
            linestr += " "
        linestr += "\n"
        f.write(linestr)

print("Success!")
print(f"Output saved to {outfile}")