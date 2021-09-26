import pandas as pd
import numpy as np
import datetime
import dask.dataframe as dd


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

    return L_idx


# filepath = "./WindowsTest/TestData.csv"
# dask_data = dask.dataframe.read_csv(filepath)
# dask_data["Datetime"] = dask.dataframe.to_datetime(dask_data["Datetime"])

# current_time = datetime.datetime.now()
# current_time = current_time.replace(microsecond=0)
# history_window = datetime.timedelta(minutes=30)
# old_time = current_time - history_window

# print(binSearchDatetime(dask_data["Datetime"], old_time))