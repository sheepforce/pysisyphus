#!/usr/bin/env python3

from pysisyphus.calculators.AnaPot import AnaPot
from pysisyphus.cos.AdaptiveNEB import AdaptiveNEB
from pysisyphus.optimizers.SteepestDescent import SteepestDescent


def test_anapot_aneb():
    image_num = 5
    calc = AnaPot()
    all_geoms = calc.get_path(image_num)
    aneb_kwargs = {
        # "keep_hei": True,
    }
    aneb = AdaptiveNEB(all_geoms, **aneb_kwargs)

    opt = SteepestDescent(aneb)
    opt.run()

    ap = calc.anim_opt(opt, show=True)

    return opt