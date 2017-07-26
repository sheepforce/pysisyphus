#!/usr/bin/env python3

import numpy as np

class Optimizer:

    def __init__(self, geometry, **kwargs):
        self.geometry = geometry

        # Setting some default values
        self.max_cycles = 15
        self.max_force_thresh = 0.01
        self.rms_force_thresh = 0.001

        self.max_step = 0.04
        self.force_backtrack_in = 3
        self.cycles_since_backtrack = self.force_backtrack_in

        # Overwrite default values if they are supplied as kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.cur_cycle = 0
        self.coords = list()

        self.forces = list()
        self.steps = list()
        self.max_forces = list()
        self.rms_forces = list()

    def print_convergence(self, cur_cycle, max_force, rms_force):
        print("cycle: {:04d} max(force): {:.5f} rms(force): {:.5f}".format(
            self.cur_cycle, max_force, rms_force)
        )

    def check_convergence(self, forces):
        max_force = forces.max()
        rms_force = np.sqrt(np.mean(np.square(forces)))

        self.max_forces.append(max_force)
        self.rms_forces.append(rms_force)

        self.print_convergence(self.cur_cycle, max_force, rms_force)

        return ((max_force <= self.max_force_thresh) and
                (rms_force <= self.rms_force_thresh)
        )

    def backtrack(self):
        """Accelerated backtracking line search."""
        epsilon = 1e-3
        alpha0 = -0.05
        scale_factor = 0.5

        prev_rms_force, cur_rms_force = self.rms_forces[-2:]
        # chk
        rms_diff = (
            (cur_rms_force - prev_rms_force) /
            np.abs(cur_rms_force+prev_rms_force)
        )
        skip = False

        # Slow alpha
        if rms_diff > epsilon:
            self.alpha *= scale_factor
            skip = True
            self.cycles_since_backtrack = self.force_backtrack_in
        else:
            self.cycles_since_backtrack -= 1
            #print("cycles_since_backtrack", self.cycles_since_backtrack)
            if self.cycles_since_backtrack < 0:
                self.cycles_since_backtrack = self.force_backtrack_in
                if self.alpha > alpha0:
                    # Reset alpha
                    alpha = alpha0
                    skip = True
                else:
                    # Accelerate alpha
                    self.alpha /= scale_factor
        return skip

    def scale_by_max_step(self, step):
        step_max = step.max()
        if step_max > self.max_step:
            step *= self.max_step / step_max
        #print("step_max", step_max, "new", step.max())
        return step

    def optimize(self):
        raise Exception("Not implemented!")

    def run(self, reparam=None):
        while self.cur_cycle < self.max_cycles:
            forces = self.geometry.forces
            self.forces.append(forces)
            self.coords.append(self.geometry.coords)
            if self.check_convergence(forces):
                break
            step = self.optimize()
            step = self.scale_by_max_step(step)
            self.steps.append(step)
            new_coords = self.geometry.coords + step
            if reparam:
                new_coords = reparam(new_coords)
            self.geometry.coords = new_coords

            self.cur_cycle += 1
