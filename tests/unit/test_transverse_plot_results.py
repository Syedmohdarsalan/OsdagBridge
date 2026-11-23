import numpy as np
import xarray as xr

from osdagbridge.core.bridge_types.plate_girder.results_data import (
    END_DIAPHRAGMS,
    INTERMEDIATE_CROSS_BRACINGS,
    transverse_loadcase_values,
    transverse_plot_members,
)


def test_transverse_groups_use_member_tags_and_exclude_overhangs():
    class Grillage:
        def get_element(self, *, member, options):
            assert options == "elements"
            return {"start_edge": [13, 14], "end_edge": [21]}[member]

    members = {12: [1, 2], 13: [1, 3], 14: [5, 1], 21: [2, 4], 35: [7, 8]}
    result_data = {
        "girders": {
            "G1": {"index": 1, "nodes": [1, 2, 7]},
            "G2": {"index": 2, "nodes": [3, 4, 8]},
        },
        "crossbracings": [{"members": ["35"]}, {"members": ["13"]}],
    }
    assert transverse_plot_members(Grillage(), result_data, members) == {
        END_DIAPHRAGMS: [13, 21],
        INTERMEDIATE_CROSS_BRACINGS: [35],
    }


def test_transverse_selection_reads_correct_case_and_element_end_order():
    ds = xr.Dataset(
        {
            "forces": (("Loadcase", "Element", "Component"),
                       np.array([[[9000, 8000], [2000, -3000]], [[0, 0], [4000, -6000]]])),
            "displacements": (("Loadcase", "Node", "Component"),
                              np.array([[[0.001, 0], [0.002, 0]], [[-0.003, 0], [0.006, 0]]])),
        },
        coords={"Loadcase": ["DL", "LL"], "Element": [1, 9], "Node": [4, 2],
                "Component": ["Vy_I", "Vy_J"]},
    )
    assert transverse_loadcase_values(ds, "DL", {9: [2, 4]}, ("Vy_i", "Vy_j")) == {
        9: (2.0, -3.0)
    }
    assert transverse_loadcase_values(ds, "LL", {9: [2, 4]}, ("Vy_i", "Vy_j")) == {
        9: (4.0, -6.0)
    }
    ds = ds[["displacements"]].assign_coords(Component=["y", "theta_y"])
    assert transverse_loadcase_values(
        ds, "LL", {9: [2, 4], 10: [2, 99]}, ("y",), displacement=True
    ) == {9: (6.0, -3.0)}
