import pandas as pd
import numpy as np
import datetime
import dask.dataframe as dd
import os



def binSearchDatetime(
    Datetime: dd.core.Series, target_datetime: datetime.datetime
) -> int:
    # Searches the dask list for the index of the greatest time smaller than target_datetime
    # Inputs:
    # - Datetime (Sorted list of datetime.datetime objects, in dask series format)
    # - target_datetime (datetime.datetime)
    #
    # Outputs:
    # - L_idx (int) - Index of the greatest datetime in the list smaller than target_datetime

    #  Assume that Datetime is already sorted
    L_idx = 0
    R_idx = len(Datetime) - 1
    L = Datetime.loc[L_idx].compute().item()
    R = Datetime.loc[R_idx].compute().item()

    idx_width = R_idx - L_idx

    assert L < target_datetime < R

    # Binary search
    while idx_width > 1:
        M_idx = np.ceil(np.mean([L_idx, R_idx]))
        M = Datetime.loc[M_idx].compute().item()

        if M > target_datetime:
            R_idx = M_idx
        elif M < target_datetime:
            L_idx = M_idx
        elif M == target_datetime:
            R_idx = M_idx
            L_idx = M_idx
        elif Datetime.loc[L_idx].compute().item() == target_datetime:
            R_idx = L_idx

        idx_width = R_idx - L_idx

    return int(L_idx)


# Based on SO post https://stackoverflow.com/questions/10933838/how-to-read-a-csv-file-in-reverse-order-in-python
def reversed_lines(f):
    # Generate the lines of file in reverse order
    part = ""
    for block in reversed_blocks(f):
        for c in reversed(block):
            if c == "\n" and part:
                yield part[::-1]
                part = ""
            part += c
    if part:
        yield part[::-1]


def reversed_blocks(f, blocksize=4096):
    # Generate blocks of file's contents in reverse order
    f.seek(0, os.SEEK_END)
    here = f.tell()
    while 0 < here:
        delta = min(blocksize, here)
        here -= delta
        f.seek(here, os.SEEK_SET)
        yield f.read(delta)