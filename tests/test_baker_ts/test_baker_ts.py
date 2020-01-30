#!/usr/bin/env python3

import itertools as it
from pathlib import Path
from pprint import pprint
import shutil
import time

import numpy as np
import pandas as pd
import pytest

from pysisyphus.calculators.Gaussian16 import Gaussian16
from pysisyphus.calculators.PySCF import PySCF
from pysisyphus.color import red, green
from pysisyphus.helpers import get_baker_ts_geoms, do_final_hessian, \
                               geom_from_library, get_baker_ts_geoms_flat
from pysisyphus.testing import using_pyscf, using_gaussian16
from pysisyphus.tsoptimizers import *


def print_summary(converged, failed, cycles, ran, runid):
    ran_ = f"{ran+1:02d}"
    print(f"converged: {converged:02d}/{ran_}")
    print(f"   failed: {failed:d}")
    print(f"   cycles: {cycles}")
    print(f"      run: {runid}")


def run_baker_ts_opts(geoms, meta, coord_type="cart", thresh="baker", runid=0):
    """From 10.1002/(SICI)1096-987X(199605)17:7<888::AID-JCC12>3.0.CO;2-7"""
    start = time.time()

    converged = 0
    failed = 0
    cycles = 0
    opt_kwargs = {
        "thresh": thresh,
        # "max_cycles": 150,
        "max_cycles": 100,
        # "max_cycles": 50,
        "dump": True,
        "trust_radius": 0.3,
        "trust_max": 0.3,
        # "max_micro_cycles": 1,
    }
    results = dict()
    for i, (name, geom) in enumerate(geoms.items()):
        print(f"@Running {name}")
        charge, mult, ref_energy = meta[name]
        calc_kwargs = {
            "charge": charge,
            "mult": mult,
            "pal": 4,
        }
        geom.set_calculator(Gaussian16(route="HF/3-21G", **calc_kwargs))
        geom = augment_coordinates(geom)
        # geom.set_calculator(PySCF(basis="321g", **calc_kwargs))

        # opt = RSPRFOptimizer(geom, **opt_kwargs)
        opt = RSIRFOptimizer(geom, **opt_kwargs)
        # opt = RSIRFOptimizer(geom, **opt_kwargs)
        # opt = TRIM(geom, **opt_kwargs)
        opt.run()
        if opt.is_converged:
            converged += 1
        else:
            failed += 1
        cycles += opt.cur_cycle + 1
        energies_match = np.allclose(geom.energy, ref_energy)
        try:
            assert np.allclose(geom.energy, ref_energy)
            # Backup TS if optimization succeeded
            # ts_xyz_fn = Path(name).stem + "_opt_ts.xyz"
            # out_path = Path("/scratch/programme/pysisyphus/xyz_files/baker_ts_opt/")
            print(green(f"\t@Energies MATCH for {name}! ({geom.energy:.6f}, {ref_energy:.6f})"))
            # with open(out_path / ts_xyz_fn, "w") as handle:
                # handle.write(geom.as_xyz())
        except AssertionError as err:
            print(red(f"\t@Calculated energy {geom.energy:.6f} and reference "
                      f"energy {ref_energy:.6f} DON'T MATCH'."))
        print()
        print_summary(converged & energies_match, failed, cycles, i, runid)
        print()
        results[name] = (opt.cur_cycle + 1, opt.is_converged)
        pprint(results)
        print()
        # do_final_hessian(geom, False)
        # print()

    end = time.time()
    duration = end - start

    print(f"  runtime: {duration:.1f} s")
    print_summary(converged, failed, cycles, i, runid)
    return results, duration, cycles

def get_geoms():
    fails = (
        "22_hconhoh.xyz",
        "09_parentdieslalder.xyz",
        "12_ethane_h2_abstraction.xyz",
        "17_claisen.xyz",
        "15_hocl.xyz",
    )
    works = (
        "01_hcn.xyz",
        "04_ch3o.xyz",
        "05_cyclopropyl.xyz",
        "06_bicyclobutane.xyz",
        "07_bicyclobutane.xyz",
        "08_formyloxyethyl.xyz",
        "14_vinyl_alcohol.xyz",
        "16_h2po4_anion.xyz",
        "18_silyene_insertion.xyz",
        # "22_hconhoh.xyz",
        "23_hcn_h2.xyz",
        "25_hcnh2.xyz",
    )
    math_error_but_works = (
        # [..]/intcoords/derivatives.py", line 640, in d2q_d
        # x99 = 1/sqrt(x93)
        #   ValueError: math domain error
        # ZeroDivison Fix
        "20_hconh3_cation.xyz",
        "24_h2cnh.xyz",
        "13_hf_abstraction.xyz",
        "19_hnccs.xyz",
        "21_acrolein_rot.xyz",
        "03_h2co.xyz",
    )
    alpha_negative = (
        "02_hcch.xyz",
    )
    no_imag = (
        "10_tetrazine.xyz",
        "11_trans_butadiene.xyz",
    )
    only = (
        # "18_silyene_insertion.xyz",
        # "21_acrolein_rot.xyz",
        "22_hconhoh.xyz",
    )
    use = (
        # fails,
        works,
        math_error_but_works,
        # alpha_negative,
        # no_imag,
        # only,
        )
    use_names = list(it.chain(*use))
    geom_data = get_baker_ts_geoms_flat(coord_type="redund")
    # _ = [_ for _ in geom_data if _[0] in use_names]
    return [_ for _ in geom_data if _[0] in use_names]


@using_pyscf
@pytest.mark.parametrize(
    "name, geom, charge, mult, ref_energy",
    # get_baker_ts_geoms_flat(coord_type="redund")
    #get_geoms(("works", "math_error_but_works",))
    # get_geoms(("fails", ))
    get_geoms()
)
def test_baker_tsopt(name, geom, charge, mult, ref_energy):
    calc_kwargs = {
        "charge": charge,
        "mult": mult,
        "pal": 4,
    }

    # geom.set_calculator(Gaussian16(route="HF/3-21G", **calc_kwargs))
    geom.set_calculator(PySCF(basis="321g", **calc_kwargs))
    geom = augment_coordinates(geom)

    opt_kwargs = {
        "thresh": "baker",
        "max_cycles": 50,
        "trust_radius": 0.3,
        "trust_max": 0.3,
    }
    # opt = RSPRFOptimizer(geom, **opt_kwargs)
    opt = RSIRFOptimizer(geom, **opt_kwargs)
    # opt = TRIM(geom, **opt_kwargs)
    opt.run()

    assert geom.energy == pytest.approx(ref_energy)


@pytest.mark.benchmark
@using_gaussian16
def _test_baker_ts_optimizations():
    coord_type = "redund"
    # coord_type = "dlc"
    # coord_type = "cart"
    thresh = "baker"
    runs = 1

    all_results = list()
    durations = list()
    all_cycles = list()
    for i in range(runs):
        geoms, meta = get_baker_ts_geoms(coord_type=coord_type)
        # only = "01_hcn.xyz"
        # only = "24_h2cnh.xyz"
        # only = "15_hocl.xyz"
        # only = "02_hcch.xyz"
        # geoms = {
            # only: geoms[only],
        # }

        fails = (
            "09_parentdieslalder.xyz",
            "12_ethane_h2_abstraction.xyz",
            "22_hconhoh.xyz",
            "17_claisen.xyz",
            "15_hocl.xyz",
        )
        works = (
            "05_cyclopropyl.xyz",
            "08_formyloxyethyl.xyz",
            "14_vinyl_alcohol.xyz",
            "16_h2po4_anion.xyz",
            "18_silyene_insertion.xyz",
            "04_ch3o.xyz",
            "06_bicyclobutane.xyz",
            "07_bicyclobutane.xyz",
            "23_hcn_h2.xyz",
            "01_hcn.xyz",
            "25_hcnh2.xyz",
        )
        math_error_but_works = (
            # [..]/intcoords/derivatives.py", line 640, in d2q_d
            # x99 = 1/sqrt(x93)
            #   ValueError: math domain error
            # ZeroDivison Fix
            "20_hconh3_cation.xyz",
            "24_h2cnh.xyz",
            "13_hf_abstraction.xyz",
            "19_hnccs.xyz",
            "21_acrolein_rot.xyz",
            "03_h2co.xyz",
        )
        alpha_negative = (
            "02_hcch.xyz",
        )
        no_imag = (
            "10_tetrazine.xyz",
            "11_trans_butadiene.xyz",
        )
        only = (
            "18_silyene_insertion.xyz",
            # "21_acrolein_rot.xyz",
            # "22_hconhoh.xyz",
        )
        use = (
            # fails,
            works,
            math_error_but_works,
            # alpha_negative,
            # no_imag,
            # only,
        )
        geoms = {key: geoms[key] for key in it.chain(*use)}

        # geoms = {"05_cyclopropyl.xyz": geoms["05_cyclopropyl.xyz"]}

        results, duration, cycles = run_baker_ts_opts(
                                        geoms,
                                        meta,
                                        coord_type,
                                        thresh,
                                        runid=i
        )
        all_results.append(results)
        durations.append(duration)
        all_cycles.append(cycles)
        print(f"@Run {i}, {cycles} cycles")
        print(f"@All cycles: {all_cycles}")
        print(f"@This runtime: {duration:.1f} s")
        print(f"@Total runtime: {sum(durations):.1f} s")
        print(f"@")
    return

    names = list(results.keys())
    cycles = {
        name: [result[name][0] for result in all_results] for name in names
    }
    df = pd.DataFrame.from_dict(cycles)

    df_name = f"cycles_{coord_type}_{runs}_runs_{thresh}.pickle"
    df.to_pickle(df_name)
    print(f"Pickled dataframe to {df_name}")
    print(f"{runs} runs took {sum(durations):.1f} seconds.")


def add_coords():
    geom = geom_from_library("baker_ts/18_silyene_insertion.xyz", coord_type="redund")

    hess = np.loadtxt("calculated_init_cart_hessian_")
    missing = find_missing_strong_bonds(geom, hess)
    print(missing)


def augment_coordinates(geom, root=0):
    assert geom.coord_type != "cart"

    hessian = geom.cart_hessian
    energy = geom.energy

    missing_bonds = find_missing_strong_bonds(geom, hessian, root=root)
    from pysisyphus.Geometry import Geometry
    if missing_bonds:
        print("\t@Missing bonds:", missing_bonds)
        new_geom = Geometry(geom.atoms, geom.cart_coords, coord_type=geom.coord_type,
                            define_prims=missing_bonds)
        new_geom.set_calculator(geom.calculator)
        new_geom.energy = energy
        new_geom.cart_hessian = hessian
        return new_geom
    else:
        return geom


def find_missing_strong_bonds(geom, hessian, bond_factor=1.7, thresh=0.3, root=0):
    from pysisyphus.InternalCoordinates import RedundantCoords
    # Define only bonds
    red = RedundantCoords(geom.atoms, geom.cart_coords,
                          bond_factor=bond_factor, bonds_only=True)
    cur_bonds = set([frozenset(b) for b in geom.internal.bond_indices])

    # Transform cartesian hessian to bond hessian
    bond_hess = red.transform_hessian(hessian)
    # Determine transisiton vector
    eigvals, eigvecs = np.linalg.eigh(bond_hess)
    # There are probably no bonds missing if there are no negative eigenvalues
    if sum(eigvals < 0) == 0:
        return list()

    trans_vec = eigvecs[:,root]
    # Find bonds that strongly contribute to the selected transition vector
    strong = np.abs(trans_vec) > thresh
    strong_bonds = red.bond_indices[strong]
    strong_bonds = set([frozenset(b) for b in strong_bonds])

    # Check which strong bonds are missing from the currently defiend bonds
    missing_bonds = strong_bonds - cur_bonds
    missing_bonds = [tuple(_) for _ in missing_bonds]
    return missing_bonds


def test_silyl():
    geom = geom_from_library("baker_ts/18_silyene_insertion.xyz", coord_type="redund")

    opt_kwargs = {
        "thresh": "baker",
        "max_cycles": 100,
        "dump": True,
        "trust_radius": 0.3,
        "trust_max": 0.3,
        # "max_cycles": 1,
    }
    calc_kwargs = {
        "charge": 0,
        "mult": 1,
        "pal": 4,
    }
    geom.set_calculator(Gaussian16(route="HF/3-21G", **calc_kwargs))
    geom = augment_coordinates(geom)

    # opt = RSPRFOptimizer(geom, **opt_kwargs)
    opt = RSIRFOptimizer(geom, **opt_kwargs)
    # opt = TRIM(geom, **opt_kwargs)
    opt.run()
    ref_en = -367.20778
    assert geom.energy == pytest.approx(ref_en)


if __name__ == "__main__":
    _test_baker_ts_optimizations()
    # add_coords()
