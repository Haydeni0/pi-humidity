d_idx].compute())
H = deque(data["Humidity"].loc[window_start_idx:window_end_idx].compute())
T = deque(data["Temperature"].loc[window_start_idx:window_end_idx].compute())
