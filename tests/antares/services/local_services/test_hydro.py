# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from pathlib import Path

from antares.craft import read_study_local
from antares.craft.model.hydro import Hydro, HydroProperties, HydroPropertiesUpdate, InflowStructureUpdate
from antares.craft.tools.serde_local.ini_reader import IniReader


class TestCreateHydro:
    def test_can_create_hydro(self, local_study_with_hydro):
        hydro = local_study_with_hydro.get_areas()["fr"].hydro
        assert isinstance(hydro, Hydro)
        assert hydro.properties == HydroProperties(reservoir_capacity=4.3, use_heuristic=False)

    def test_hydro_has_properties(self, local_study_w_areas):
        assert local_study_w_areas.get_areas()["fr"].hydro.properties

    def test_hydro_has_correct_default_properties_88(self, local_study_w_areas, default_hydro_properties_88):
        assert local_study_w_areas.get_areas()["fr"].hydro.properties == default_hydro_properties_88

    def test_hydro_has_correct_default_properties_92(self, local_study_92, default_hydro_properties_92):
        assert local_study_92.get_areas()["fr"].hydro.properties == default_hydro_properties_92

    def test_files_exist(self, local_study_w_areas):
        """
        Test that calling create_hydro on all areas triggers the creation of all files needed.
        """
        study_path = Path(local_study_w_areas.path)
        areas = local_study_w_areas.get_areas()

        for area_id in areas.keys():
            expected_paths = [
                study_path / f"input/hydro/common/capacity/creditmodulations_{area_id}.txt",
                study_path / f"input/hydro/common/capacity/reservoir_{area_id}.txt",
                study_path / f"input/hydro/common/capacity/waterValues_{area_id}.txt",
                study_path / f"input/hydro/common/capacity/inflowPattern_{area_id}.txt",
                study_path / f"input/hydro/series/{area_id}/ror.txt",
                study_path / f"input/hydro/series/{area_id}/mod.txt",
                study_path / f"input/hydro/series/{area_id}/mingen.txt",
                study_path / f"input/hydro/common/capacity/maxpower_{area_id}.txt",
                study_path / f"input/hydro/prepro/{area_id}/prepro.ini",
                study_path / f"input/hydro/allocation/{area_id}.ini",
                study_path / "input/hydro/hydro.ini",
            ]

            for expected_path in expected_paths:
                assert expected_path.is_file(), f"File not created: {expected_path}"

    def test_hydro_allocation_has_correct_default_values(self, local_study_w_areas):
        areas = local_study_w_areas.get_areas()
        study_path = Path(local_study_w_areas.path)
        for area in areas.values():
            ini_content = IniReader().read(study_path / "input" / "hydro" / "allocation" / f"{area.id}.ini")
            assert ini_content == {"[allocation]": {area.id: 1}}

    def test_hydro_prepro_has_correct_default_values(self, local_study_w_areas):
        areas = local_study_w_areas.get_areas()
        study_path = Path(local_study_w_areas.path)
        for area in areas.values():
            ini_content = IniReader().read(study_path / "input" / "hydro" / "prepro" / area.id / "prepro.ini")
            assert ini_content == {"prepro": {"intermonthly-correlation": 0.5}}

    def test_hydro_ini_has_correct_default_values(self, local_study_w_areas):
        # Given
        expected_hydro_ini_content = """[inter-daily-breakdown]
fr = 1.0
it = 1.0

[intra-daily-modulation]
fr = 24.0
it = 24.0

[inter-monthly-breakdown]
fr = 1.0
it = 1.0

[reservoir]
fr = False
it = False

[reservoir capacity]
fr = 0.0
it = 0.0

[follow load]
fr = True
it = True

[use water]
fr = False
it = False

[hard bounds]
fr = False
it = False

[initialize reservoir date]
fr = 0
it = 0

[use heuristic]
fr = True
it = True

[power to level]
fr = False
it = False

[use leeway]
fr = False
it = False

[leeway low]
fr = 1.0
it = 1.0

[leeway up]
fr = 1.0
it = 1.0

[pumping efficiency]
fr = 1.0
it = 1.0

"""
        study_path = Path(local_study_w_areas.path)
        ini_content = (study_path / "input" / "hydro" / "hydro.ini").read_text()
        assert ini_content == expected_hydro_ini_content

    def test_update_hydro_properties(self, local_study_with_hydro):
        area_fr = local_study_with_hydro.get_areas()["fr"]
        assert area_fr.hydro.properties == HydroProperties(reservoir_capacity=4.3, use_heuristic=False)
        new_properties = HydroPropertiesUpdate(reservoir_capacity=2.4, hard_bounds=True)
        area_fr.hydro.update_properties(new_properties)
        # Checks object value
        assert area_fr.hydro.properties == HydroProperties(
            reservoir_capacity=2.4, hard_bounds=True, use_heuristic=False
        )
        # Checks ini content
        study_path = Path(local_study_with_hydro.path)
        ini_content = IniReader().read(study_path / "input" / "hydro" / "hydro.ini")
        assert ini_content["reservoir capacity"]["fr"] == 2.4
        assert ini_content["hard bounds"]["fr"] is True
        assert ini_content["use heuristic"]["fr"] is False

    def test_update_hydro_inflow_structure(self, local_study_with_hydro):
        area_fr = local_study_with_hydro.get_areas()["fr"]
        assert area_fr.hydro.inflow_structure.intermonthly_correlation == 0.5
        inflow_structure = InflowStructureUpdate(intermonthly_correlation=0.4)
        area_fr.hydro.update_inflow_structure(inflow_structure)
        # Checks object value
        assert area_fr.hydro.inflow_structure.intermonthly_correlation == 0.4
        # Checks ini content
        study_path = Path(local_study_with_hydro.path)
        ini_content = IniReader().read(study_path / "input" / "hydro" / "prepro" / "fr" / "prepro.ini")
        assert ini_content == {"prepro": {"intermonthly-correlation": 0.4}}

    def test_lifecycle_with_area_name(self, local_study):
        local_study.create_area("FR")
        ini_content = """[inter-daily-breakdown]
FR = 0.63

[intra-daily-modulation]
FR?? = 22.7
"""
        study_path = Path(local_study.path)
        hydro_ini_path = study_path / "input" / "hydro" / "hydro.ini"
        hydro_ini_path.write_text(ini_content)
        # Ensure study reading succeeds
        study = read_study_local(study_path)
        assert len(study.get_areas()) == 1
        area_fr = study.get_areas()["fr"]
        hydro_properties = area_fr.hydro.properties
        assert hydro_properties.inter_daily_breakdown == 0.63
        assert hydro_properties.intra_daily_modulation == 22.7
        assert hydro_properties.reservoir is False
        # Asserts properties update succeeds
        new_properties = HydroPropertiesUpdate(reservoir=True, inter_daily_breakdown=0.9)
        area_fr.hydro.update_properties(new_properties)
        hydro_properties = area_fr.hydro.properties
        assert hydro_properties.inter_daily_breakdown == 0.9
        assert hydro_properties.intra_daily_modulation == 22.7
        assert hydro_properties.reservoir is True
        # Checks ini content
        actual_ini_content = hydro_ini_path.read_text()
        expected_ini_content = """[inter-daily-breakdown]
fr = 0.9

[intra-daily-modulation]
fr = 22.7

[reservoir]
fr = True

"""
        assert actual_ini_content == expected_ini_content
