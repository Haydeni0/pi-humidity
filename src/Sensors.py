import datetime
import time
import warnings
from collections import deque
from typing import Tuple

import numpy as np
import pandas as pd

from DHT_MySQL_interface import DHTConnection
from utils import timing

from dataclasses import dataclass


@dataclass
class DHTSensorData:
    """
    A class that defines an object connected to a table of the pi_humidity MySQL database
    using another object DHTConnection.
    The object pulls recent data from the table and partitions it into a regular grid with a
    specified number of bins, and can be updated when the update() method is called.
    This attempts to be optimised for a low memory and processing footprint when running consistently.
    """

    # Declarations
    DHT_db: DHTConnection
    table_name: str
    num_grid: int
    history_timedelta: datetime.timedelta
    D_grid_edges: deque
    D_grid_centres: deque
    grid_resolution: datetime.timedelta

    H_raw: deque
    T_raw: deque
    H: deque
    T: deque
    H_was_nan:deque
    H_was_nan:deque
    __D_buffer: deque
    __H_buffer: deque
    __T_buffer: deque

    # Static variables
    # These must be common and 
    # Y axes limits are also contained within this class as a static variable
    YLIM_H_BUFFER: float = 5  # The amount to add on to the top and bottom of the limits
    YLIM_T_BUFFER: float = 1
    # Store ylim in a list to do efficiently (don't repeatedly call max/min on the whole deque)
    ylim_H: tuple = ()
    ylim_T: tuple = ()

    def __init__(
        self,
        DHT_db: DHTConnection,
        table_name: str,
        num_grid: int = 800,
        history_timedelta: datetime.timedelta = datetime.timedelta(minutes=2),
    ):
        self.DHT_db = DHT_db
        self.table_name = table_name
        self.num_grid = num_grid
        self.history_timedelta = history_timedelta

        self.grid_resolution = (
            history_timedelta / num_grid
        )  # Width of one grid bin

        # Load H and T from database (in raw format with possible nans)
        t = time.time()
        self.H_raw, self.T_raw = self.__loadInitialData()
        print(
            f"  Query H and T from database table {self.table_name}: {time.time()-t: 2.4f}"
        )
        # Process H and T to remove nans using last observation carried forward (LOCF)
        # Also record which values were nan
        self.H, self.H_was_nan = DHTSensorData.replaceNanLOCF(self.H_raw)
        self.T, self.T_was_nan = DHTSensorData.replaceNanLOCF(self.T_raw)

        # Initialise deques to hold new data from the next bin in the future
        self.__D_buffer = deque()
        self.__H_buffer = deque()
        self.__T_buffer = deque()

        DHTSensorData.ylim_H = DHTSensorData.updateYlim(
            DHTSensorData.ylim_H, DHTSensorData.YLIM_H_BUFFER, self.H
        )
        DHTSensorData.ylim_T = DHTSensorData.updateYlim(
            DHTSensorData.ylim_T, DHTSensorData.YLIM_T_BUFFER, self.T
        )

        # Remake grid deques with a max length
        self.D_grid_centres = deque(self.D_grid_centres, maxlen=self.num_grid)
        self.D_grid_edges = deque(self.D_grid_edges, maxlen=self.num_grid + 1)
        self.H_raw = deque(self.H_raw, maxlen=self.num_grid)
        self.T_raw = deque(self.T_raw, maxlen=self.num_grid)
        self.H = deque(self.H, maxlen=self.num_grid)
        self.T = deque(self.T, maxlen=self.num_grid)
        self.H_was_nan = deque(self.H_was_nan, maxlen=self.num_grid)
        self.T_was_nan = deque(self.T_was_nan, maxlen=self.num_grid)

    def __loadInitialData(self) -> Tuple[deque, deque]:
        # Inputs:
        #   num_thin - Number of data points after thinning (this increases the resolution
        #       of the line)
        #   window_halflength - Number of array elements to use as the window halflength for moving
        #       median smoothing (this increases the smoothness of the line)
        #
        # Outputs:
        #   (D, H, T) - Datetime, humidity and temperature deques

        # Get the datetime interval to query data from
        current_time = datetime.datetime.now()
        start_dtime = current_time - self.history_timedelta
        # Store the last time that the server was queried
        self.last_queried_time = current_time

        # Define regular (1-dimensional) grid edges and bin centres (for datetime)
        # Leave this as an array for now, convert to deque later
        D_grid_edges = pd.date_range(
            start = pd.Timestamp(start_dtime),
            end = pd.Timestamp(current_time),
            periods = self.num_grid + 1,
        )
        D_grid_centres = D_grid_edges[:-1] + 0.5 * pd.Timedelta(self.grid_resolution)
        # Edges of each bin in the grid
        # D_grid_edges = pd.to_datetime(D_grid_edges)
        # Centre of each bin in the grid
        # D_grid_centres = pd.to_datetime(D_grid_centres)

        # Find and load the data from the database straight into the grid
        use_SQL_loading = (
            False  # I think False is best here, as allocateToGrid is quite fast
        )
        if use_SQL_loading:
            # Method that queries the database multiple times to get data from each bin separately
            # This takes O(num_grid) compute time
            # Replace this with a TimescaleDB optimised query
            H_raw = deque()
            T_raw = deque()
            for grid_idx in range(self.num_grid):
                _, H_bin, T_bin = self.DHT_db.getObservations(
                    self.table_name,
                    D_grid_edges[grid_idx],  # type: ignore
                    D_grid_edges[grid_idx + 1],  # type: ignore
                )
                if len(H_bin) > 0:
                    H_raw.append(np.median(H_bin))
                    T_raw.append(np.median(T_bin))
                else:
                    H_raw.append(np.nan)
                    T_raw.append(np.nan)
        else:
            # Alternate method that queries the database once
            # This takes O(history_timedelta) compute time

            # Find and load the data from the database into arrays
            D_bulk, H_bulk, T_bulk = self.DHT_db.getObservations(
                self.table_name, start_dtime, current_time
            )
            # Allocate the correct data to each bin
            # Take the median within each bin to decide on their final values
            H_raw, T_raw = self.allocateToGrid(
                D_grid_edges, D_bulk, H_bulk, T_bulk
            )

        # Finally, convert the grid values to deques for fast pop/append
        self.D_grid_edges = deque(D_grid_edges)
        self.D_grid_centres = deque(D_grid_centres)

        return H_raw, T_raw

    def update(self) -> bool:
        # Check for new data, and update the grid if required.
        # Returns True if the grid is updated, otherwise returns false

        # Get new data from the database
        D_new, H_new, T_new = self.__loadNewData()
        # Add to the buffer
        self.__D_buffer.extend(deque(D_new))
        self.__H_buffer.extend(deque(H_new))
        self.__T_buffer.extend(deque(T_new))

        current_time = datetime.datetime.now()
        new_time_elapsed = current_time - self.D_grid_edges[-1]
        num_new_bins = int(np.floor(new_time_elapsed / self.grid_resolution))
        num_new_edges = num_new_bins + 1

        # Return if no new bins need to be added
        if num_new_bins < 1:
            return False

        # Check if there are too many new bins
        # If this is the case, then all the data in the grid needs to be overwritten
        overwrite_entire_grid = False
        if num_new_bins > self.num_grid:
            overwrite_entire_grid = True
            num_new_bins = self.num_grid
            num_new_edges = self.num_grid + 1

        if not overwrite_entire_grid:
            # Calculate new grid edges (including the existing final grid edge == first grid edge here)
            new_grid_edges = pd.DatetimeIndex(
                [
                    self.D_grid_edges[-1] + _ * self.grid_resolution
                    for _ in range(num_new_edges)
                ]
            )
        else:
            # When the previous data is too old, and the entire grid needs to be remade
            new_grid_edges = pd.DatetimeIndex(
                [
                    current_time
                    - self.history_timedelta
                    + _ * self.grid_resolution
                    for _ in range(num_new_edges)
                ]
            )
        new_grid_centres = new_grid_edges[:-1] + 0.5 * pd.Timedelta(self.grid_resolution)

        # Remove values to be added to the grid from the buffer
        D_add = deque()
        H_add = deque()
        T_add = deque()

        while len(self.__D_buffer) >= 1 and self.__D_buffer[0] < new_grid_edges[-1]:
            D_temp = self.__D_buffer.popleft()
            if (
                overwrite_entire_grid and D_temp >= new_grid_edges[0]
            ) or not overwrite_entire_grid:
                # Only append relevant (new) data to *_add
                D_add.append(D_temp)
                H_add.append(self.__H_buffer.popleft())
                T_add.append(self.__T_buffer.popleft())
            else:
                self.__H_buffer.popleft()
                self.__T_buffer.popleft()

        # Allocate new data into the new grid
        H_raw_new_grid, T_raw_new_grid = self.allocateToGrid(
            new_grid_edges, np.array(D_add), np.array(H_add), np.array(T_add)
        )

        # Remove nans
        if not overwrite_entire_grid:
            H_new_grid, H_new_was_nan = DHTSensorData.replaceNanLOCF(
                H_raw_new_grid, self.H[-1]
            )
            T_new_grid, T_new_was_nan = DHTSensorData.replaceNanLOCF(
                T_raw_new_grid, self.T[-1]
            )
        else:
            H_new_grid, H_new_was_nan = DHTSensorData.replaceNanLOCF(H_raw_new_grid)
            T_new_grid, T_new_was_nan = DHTSensorData.replaceNanLOCF(T_raw_new_grid)

        # Add these new values to the grid, and update the grid edges & centres
        # Since these deques have a maxlen attribute, old values are popped off the left side
        self.D_grid_edges.extend(deque(new_grid_edges[1:]))
        self.D_grid_centres.extend(deque(new_grid_centres))
        self.H_raw.extend(H_raw_new_grid)
        self.T_raw.extend(T_raw_new_grid)
        self.H.extend(H_new_grid)
        self.T.extend(T_new_grid)
        self.H_was_nan.extend(H_new_was_nan)
        self.T_was_nan.extend(T_new_was_nan)

        # Update y limits, using the new bins
        DHTSensorData.ylim_H = DHTSensorData.updateYlim(
            DHTSensorData.ylim_H, DHTSensorData.YLIM_H_BUFFER, H_new_grid
        )
        DHTSensorData.ylim_T = DHTSensorData.updateYlim(
            DHTSensorData.ylim_T, DHTSensorData.YLIM_T_BUFFER, T_new_grid
        )
        return True

    def __loadNewData(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        # Load new values of D, H and T from the server

        # Query datetimes that are new since we last queried the server
        start_dtime = self.last_queried_time + datetime.timedelta(seconds=0.1)
        current_time = datetime.datetime.now()
        D_new, H_new, T_new = self.DHT_db.getObservations(
            self.table_name, start_dtime, current_time
        )

        if len(D_new) > 0:
            self.last_queried_time = current_time

        return D_new, H_new, T_new

    @staticmethod
    def replaceNanLOCF(data: deque, backup_val: float = 50) -> Tuple[deque, deque]:
        # Replace nans in the deque with the last observation carried forward
        # Also record the locations of where the nans were
        data_LOCF = deque()
        was_nan = deque()

        # If the first value in data is nan, use backup_val instead of LOCF
        last_val = backup_val
        for d in data:
            if np.isnan(d):
                data_LOCF.append(last_val)
                was_nan.append(True)
            else:
                last_val = d
                data_LOCF.append(d)
                was_nan.append(False)

        return data_LOCF, was_nan

    @staticmethod
    def allocateToGrid(
        grid_edges: pd.DatetimeIndex,
        D_bulk: np.ndarray,
        H_bulk: np.ndarray,
        T_bulk: np.ndarray,
    ) -> Tuple[deque, deque]:
        # Given a grid (assortment of bins) of dates and dht values:
        # In each bin assign dht observations by their datetime.
        # Take the median within the bins to assign their grid value.

        # By construction, D_bulk should all be greater than grid_edges[0]
        # Throw an error otherwise

        assert len(grid_edges) >= 2  # "Not enough grid edges given"

        num_grid = len(grid_edges) - 1

        # Get an array the same size as D_bulk that holds the bin indices the dates fall into
        # Note that this starts at 1 and ends at num_grid
        if len(D_bulk) > 0:
            D_bulk_bin_idx = np.searchsorted(grid_edges, D_bulk, side="right")
        else:
            D_bulk_bin_idx = []
        H_raw = deque()
        T_raw = deque()
        for bin_idx in range(num_grid):
            (valid_indices,) = np.where(D_bulk_bin_idx == bin_idx + 1)
            if len(valid_indices) > 0:
                with warnings.catch_warnings():
                    # Catch the warnings these give, as they are useless
                    # RuntimeWarning: Mean of empty slice.
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    H_raw.append(np.median(H_bulk[valid_indices]))
                    T_raw.append(np.median(T_bulk[valid_indices]))
            else:
                # If there are no values assigned to the current bin, assign NaN
                H_raw.append(np.nan)
                T_raw.append(np.nan)

        return H_raw, T_raw

    @staticmethod
    def decayLimits(ylim: list, buffer: float, *data: deque):
        # Decays ylim (mutate)
        # Allows input of multiple sets of data, eg. decayLimits(ylim, buffer, H_inside, H_outside, ...)
        ylim_decay = 0.1  # Proportion to decay each time

        assert len(data) > 0  # "data is empty")
        # For each dataset given, get the minimum and maximum
        mins = []
        maxs = []
        for d in data:
            mins.append(min(d))
            maxs.append(max(d))
        # ymin is the minimum of the minimum of each dataset in data
        ymin = min(mins)
        ymax = max(maxs)

        ymin -= buffer
        ymax += buffer
        if ymin > ylim[0]:
            ylim[0] = ylim[0] + ylim_decay * abs(ylim[0] - ymin)
        if ymax < ylim[1]:
            ylim[1] = ylim[1] - ylim_decay * abs(ylim[1] - ymax)

    @staticmethod
    def updateYlim(ylim: tuple, buffer: float, data: deque) -> tuple:
        # data is a deque of floats
        # Since ylim is a list, it is mutated within this function
        data_min = np.nanmin(np.array(data))
        data_max = np.nanmax(np.array(data))
        
        if len(ylim) == 0:
            lower = data_min - buffer
            upper = data_max + buffer
        else:
            lower = ylim[0]
            upper = ylim[1]
            if data_min < ylim[0]:
                lower = data_min - buffer
            if data_max > ylim[1]:
                upper = data_max + buffer
            
        new_ylim = (lower, upper)

        return new_ylim
