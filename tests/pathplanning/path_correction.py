#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt

import surgicalsim.lib.datastore as datastore
import surgicalsim.lib.constants as constants
import surgicalsim.lib.pathutils as pathutils


t_total = 20.0 # [s]

def main():
    path_file = '../../results/sample4.dat'
    path = datastore.retrieve(path_file)

    # A list of the the segments of the optimized path
    segments = pathutils._detect_segments(path)

    # The new path generated by original path and corrective algorithm
    new_path = None

    pos_start_col = constants.G_POS_IDX
    pos_end_col = pos_start_col + constants.G_NUM_POS_DIMS

    x_path_offset = np.array([0.0, 0.0, 0.0]) # [m]
    v_curr = np.array([0.0, 0.0, 0.0]) # [m/s]
    a_max = 1.0 # [m/s^2]

    for i, _ in enumerate(path):
        if i == len(path) - 1:
            continue

        # Detect current segment
        seg_idx = 0

        for j in range(len(segments)):
            if i <= segments[j]:
                seg_idx = j
                break

        # Get current time and position
        t_curr = path[i,constants.G_TIME_IDX] * t_total
        t_next = path[i+1,constants.G_TIME_IDX] * t_total

        x_curr = path[i,pos_start_col:pos_end_col] + x_path_offset
        x_next = path[i+1,pos_start_col:pos_end_col] + x_path_offset

        # Calculate next velocity
        dt = (t_next - t_curr)
        dx = x_next - x_curr
        v = dx / dt

        # Get the final tooltip position in the current segment
        x_target = path[segments[seg_idx],pos_start_col:pos_end_col] + x_path_offset

        # Get current gate position
        x_gate = generate_gate_pos(t_curr, path, seg_idx)

        # Calculate the new position with positional change from target to gate
        x_new = x_next + (x_gate - x_target)

        # Calculate the new velocity
        v_new = (x_new - x_curr) / dt

        # Calculate the new acceleration
        a_new = (v_new - v_curr) / dt

        # Calculate the acceleration vector norm
        a_new_norm = np.linalg.norm(a_new)

        # Limit the norm vector
        a_new_norm_clipped = np.clip(a_new_norm, -a_max, a_max)

        # Determine the ratio of the clipped norm
        ratio_unclipped = a_new_norm_clipped / a_new_norm

        # TODO: Scale the acceleration vector by this ratio
        a_new = a_new * ratio_unclipped

        # Calculate the new change in velocity
        dv_new = a_new * dt
        v_new = v_curr + dv_new

        # Calculate the new change in position
        dx_new = v_new * dt
        x_new = x_curr + dx_new

        # Store the next movement for later
        if new_path is None:
            new_path = x_new
        else:
            new_path = np.vstack((new_path, x_new))

        # Store this velocity for the next time step
        v_curr = v_new

        x_path_offset += dx_new - dx

    # Plot the inputted path
    fig = plt.figure(facecolor='white')
    axis = fig.gca(projection='3d')

    full_path = path[:-1].copy()
    full_path[:,pos_start_col:pos_end_col] = new_path

    pathutils.display_path(axis, full_path, title='Path')

    plt.show()

    return


def generate_gate_pos(t, path, segment_num):
    gate_start_col = constants.G_GATE_IDX+(constants.G_NUM_GATE_DIMS*segment_num)
    gate_end_col = gate_start_col + constants.G_NUM_POS_DIMS

    gate_pos = path[0,gate_start_col:gate_end_col].copy()

    f = 4.0
    gate_pos += np.array([0.0, 0.02*np.sin(2.0*np.pi*f*t/t_total), 0.0])

    return gate_pos


if __name__ == '__main__':
    main()
