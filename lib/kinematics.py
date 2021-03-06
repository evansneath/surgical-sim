#!/usr/bin/env python

"""Kinematics module

Calculates kinematics based on the Mitsubishi PA10 robotic arm.

Author:
    Evan Sneath - evansneath@gmail.com

License:
    Open Software License v3.0

Classes:
    PA10Kinematics: The PA10 kinematic calculation class.
"""

import numpy as np


class PA10Kinematics(object):
    """PA10Kinematics class

    Given the tooltip position and rotation of the PA10, the appropriate
    velocities for the PA10 joint will be calculated.
    """
    def __init__(self):
        super(PA10Kinematics, self).__init__()
        return

    def calc_inverse_kinematics(self, pos_init, pos_goal):
        # TODO: Perform PA10 inverse kinematics
        angles = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        return angles


if __name__ == '__main__':
    pass
