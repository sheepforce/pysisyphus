#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
import pytest

from pysisyphus.plotters.AnimPlot import AnimPlot
from pysisyphus.calculators.AnaPot import AnaPot
from pysisyphus.cos.NEB import NEB
from pysisyphus.cos.SimpleZTS import SimpleZTS
from pysisyphus.Geometry import Geometry
from pysisyphus.optimizers.LBFGS import LBFGS
from pysisyphus.optimizers.ConjugateGradient import ConjugateGradient
from pysisyphus.optimizers.QuickMin import QuickMin
from pysisyphus.optimizers.FIRE import FIRE
from pysisyphus.optimizers.SteepestDescent import SteepestDescent
from pysisyphus.optimizers.RFOptimizer import RFOptimizer
from pysisyphus.optimizers.closures import modified_broyden_closure
from pysisyphus.interpolate.Interpolator import Interpolator


def get_geoms():
    initial = AnaPot.get_geom((-1.05274, 1.02776, 0))
    final = AnaPot.get_geom((1.94101, 3.85427, 0))
    geoms = (initial, final)
    return geoms


def run_cos_opt(geoms, between, calc_cls,
                cos_cls, cos_kwargs,
                opt_cls, opt_kwargs):
    interpol = Interpolator(geoms, between=between)
    images = interpol.interpolate_all()

    for image in images:
        image.set_calculator(AnaPot())

    cos = cos_cls(images, **cos_kwargs)

    opt = opt_cls(cos, **opt_kwargs)
    opt.run()

    return opt


def assert_cos_opt(opt, ref_cycle):
    assert opt.is_converged
    assert opt.cur_cycle == ref_cycle


@pytest.mark.parametrize(
    "opt_cls, opt_kwargs_, neb_kwargs_, ref_cycle, between",
    [
        (SteepestDescent, {}, {}, 30, 5),
        (SteepestDescent, {}, {}, 32, 10),
        (ConjugateGradient, {}, {}, 40, 5),
        (QuickMin, {"dt": 0.1,}, {}, 27, 5),
        (FIRE, {"dt_max": 0.2,}, {}, 42, 5),
        (LBFGS, {}, {}, 27, 5),
])
def test_anapot_neb(opt_cls, opt_kwargs_, neb_kwargs_, ref_cycle, between):
    geoms = get_geoms()

    neb_kwargs = {
        "fix_ends": True,
        "k_min": 0.01,
    }
    neb_kwargs.update(neb_kwargs_)

    opt_kwargs = {
    }
    opt_kwargs.update(opt_kwargs_)

    opt = run_cos_opt(geoms, between, AnaPot,
                      NEB, neb_kwargs,
                      opt_cls, opt_kwargs)
    # ap = animate(opt)
    # plt.show()
    assert_cos_opt(opt, ref_cycle)


@pytest.mark.parametrize(
    "between, param, ref_cycle",
    [
        (5, "equal", 49),
        (10, "equal", 49),
        (5, "energy", 41),
        (10, "energy", 46),
])
def test_anapot_szts(between, param, ref_cycle):
    geoms = get_geoms()

    szts_kwargs = {
        "fix_ends": True,
        "param": param,
    }

    opt_cls = SteepestDescent
    opt_kwargs = {
        "max_cycles": 100,
    }
    opt = run_cos_opt(geoms, between, AnaPot,
                      SimpleZTS, szts_kwargs,
                      SteepestDescent, opt_kwargs)
    # ap = animate(opt)
    # plt.show()
    assert_cos_opt(opt, ref_cycle)


def animate(opt):
    xlim = (-2, 2.5)
    ylim = (0, 5)
    levels = (-3, 4, 80)
    ap = AnimPlot(AnaPot(), opt, xlim=xlim, ylim=ylim, levels=levels)
    ap.animate()
    return ap


def animate_bare(opt):
    xlim = (-2, 2.5)
    ylim = (0, 5)
    levels = (-3, 4, 80)
    ap = AnimPlot(AnaPot(), opt, xlim=xlim, ylim=ylim, levels=levels,
                  energy_profile=False, colorbar=False, figsize=(8, 6),
                  save=False, title=False,
    )
    ap.animate()
    return ap