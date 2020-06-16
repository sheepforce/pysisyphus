from matplotlib.patches import Circle
import matplotlib.pyplot as plt
import numpy as np

from pysisyphus.constants import BOHR2ANG
from pysisyphus.calculators.AnaPot import AnaPot
from pysisyphus.calculators.MullerBrownSympyPot import MullerBrownPot
from pysisyphus.calculators.XTB import XTB
# from pysisyphus.dynamics.helpers import get_velocities
from pysisyphus.dynamics.mdp import mdp
from pysisyphus.dynamics.velocity_verlet import md
from pysisyphus.helpers import geom_loader


def test_mdp():
    coords = (-0.82200156,  0.6243128, 0)
    geom = MullerBrownPot.get_geom(coords)

    # Termination functions
    A = (-0.5592, 1.443, 0)
    B = (0.605, 0.036, 0)
    radius = 0.05
    def stopA(x, rad=radius):
        return np.linalg.norm(x-A) < radius
    def stopB(x, rad=radius):
        return np.linalg.norm(x-B) < radius
    term_funcs = {
        "nearA": stopA,
        "nearB": stopB,
    }

    mdp_kwargs = {
        "E_excess": 0.2,
        "term_funcs": term_funcs,
        "epsilon": 5e-4,
        "ascent_alpha": 0.0125,
        "t_init": 0.15,
        "t": 3,
        "dt": 0.001,
    }
    np.random.seed(25032018)
    res = mdp(geom, **mdp_kwargs)

    calc = geom.calculator
    calc.plot()
    ax = calc.ax
    ax.plot(*res.ascent_xs.T[:2], "ro-")
    ax.plot(*res.md_init_plus.coords.T[:2], "-", lw=3)
    ax.plot(*res.md_init_minus.coords.T[:2], "-", lw=3)
    cA = Circle(A[:2], radius=radius)
    ax.add_artist(cA)
    cB = Circle(B[:2], radius=radius)
    ax.add_artist(cB)
    ax.plot(*res.md_fin_plus.coords.T[:2], "-", lw=3)
    ax.plot(*res.md_fin_minus.coords.T[:2], "-", lw=3)

    plt.show()


def test_so3hcl_diss():
    """See [1]"""
    def get_geom():
        geom = geom_loader("lib:so3hcl_diss_ts_opt.xyz")
        geom.set_calculator(XTB(pal=4))
        return geom

    geom = get_geom()
    mdp_kwargs = {
        # About 5 kcal/mol
        "E_excess": 0.0079,
        "term_funcs": list(),
        "epsilon": 5e-4,
        "ascent_alpha": 0.05,
        "t_init": 20,
        # Paper uses 200
        "t": 100,
        "dt": .5,
        "seed": 25032018,
        # "external_md": True,
        "max_init_trajs": 1,
    }
    res = mdp(geom, **mdp_kwargs)

    # geom = get_geom()
    # mdp_kwargs["E_excess"] = 0
    # res_ee = mdp(geom, **mdp_kwargs)


def test_so3hcl_md():
    geom = geom_loader("lib:so3hcl_diss_ts_opt.xyz")
    geom.set_calculator(XTB(pal=4))

    v0 = .025 * np.random.rand(*geom.coords.shape)
    md_kwargs = {
        "v0": v0,
        "t": 400,
        "dt": 1,
    }
    res = md(geom, **md_kwargs)

    from pysisyphus.xyzloader import make_trj_str
    def dump_coords(coords, trj_fn):
        coords = np.array(coords)
        coords = coords.reshape(-1, len(geom.atoms), 3) * BOHR2ANG
        trj_str = make_trj_str(geom.atoms, coords)
        with open(trj_fn, "w") as handle:
            handle.write(trj_str)
    dump_coords(res.coords, "md.trj")


def test_oniom_md():
    calc_dict = {
        "high": {
            "type": "pypsi4",
            "method": "scf",
            "basis": "sto-3g",
        },
        "low": {
            "type": "pyxtb",
        },
    }
    high_inds = (4,5,6)
    from pysisyphus.calculators.ONIOM import ONIOM
    oniom = ONIOM(calc_dict, high_inds)

    geom = geom_from_library("acetaldehyd_oniom.xyz")
    geom.set_calculator(oniom)

    v0 = .005 * np.random.rand(*geom.coords.shape)
    md_kwargs = {
        "v0": v0,
        "t": 40,
        "dt": 0.5,
    }
    md_result = md(geom, **md_kwargs)
    from pysisyphus.xyzloader import make_trj_str

    coords = md_result.coords.reshape(-1, len(geom.atoms), 3) * BOHR2ANG
    trj_str = make_trj_str(geom.atoms, coords)
    with open("md.trj", "w") as handle:
        handle.write(trj_str)
