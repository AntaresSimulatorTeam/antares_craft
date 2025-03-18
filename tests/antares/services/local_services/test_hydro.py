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

from configparser import ConfigParser
from pathlib import Path

from antares.craft.model.hydro import Hydro, HydroProperties
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes


class TestCreateHydro:
    def test_can_create_hydro(self, local_study_with_hydro):
        hydro = local_study_with_hydro.get_areas()["fr"].hydro
        assert isinstance(hydro, Hydro)
        assert hydro.properties == HydroProperties(reservoir_capacity=4.3)

    def test_hydro_has_properties(self, local_study_w_areas):
        assert local_study_w_areas.get_areas()["fr"].hydro.properties

    def test_hydro_has_correct_default_properties(self, local_study_w_areas, default_hydro_properties):
        assert local_study_w_areas.get_areas()["fr"].hydro.properties == default_hydro_properties

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
        for area in areas.values():
            ini_file = IniFile(
                local_study_w_areas.service.config.study_path,
                InitializationFilesTypes.HYDRO_ALLOCATION_INI,
                area_id=area.id,
            )
            assert ini_file.ini_dict == {"[allocation]": {area.id: "1"}}

    def test_hydro_prepro_has_correct_default_values(self, local_study_w_areas):
        areas = local_study_w_areas.get_areas()
        for area in areas.values():
            ini_file = IniFile(
                local_study_w_areas.service.config.study_path,
                InitializationFilesTypes.HYDRO_PREPRO_INI,
                area_id=area.id,
            )
            assert ini_file.ini_dict == {"prepro": {"intermonthly-correlation": "0.5"}}

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
        expected_hydro_ini = ConfigParser()
        expected_hydro_ini.read_string(expected_hydro_ini_content)
        actual_hydro_ini = IniFile(local_study_w_areas.service.config.study_path, InitializationFilesTypes.HYDRO_INI)

        # When
        with actual_hydro_ini.ini_path.open() as st_storage_list_ini_file:
            actual_hydro_ini_content = st_storage_list_ini_file.read()

        assert actual_hydro_ini_content == expected_hydro_ini_content
        assert actual_hydro_ini.parsed_ini.sections() == expected_hydro_ini.sections()
        assert actual_hydro_ini.parsed_ini == expected_hydro_ini

    def test_hydro_ini_has_correct_sorted_areas(self, actual_hydro_ini):
        # Given
        expected_hydro_ini_content = """[inter-daily-breakdown]
at = 1.0
fr = 1.0
it = 1.0

[intra-daily-modulation]
at = 24.0
fr = 24.0
it = 24.0

[inter-monthly-breakdown]
at = 1.0
fr = 1.0
it = 1.0

[reservoir]
at = False
fr = False
it = False

[reservoir capacity]
at = 0.0
fr = 4.3
it = 0.0

[follow load]
at = True
fr = True
it = True

[use water]
at = False
fr = False
it = False

[hard bounds]
at = False
fr = False
it = False

[initialize reservoir date]
at = 0
fr = 0
it = 0

[use heuristic]
at = True
fr = True
it = True

[power to level]
at = False
fr = False
it = False

[use leeway]
at = False
fr = False
it = False

[leeway low]
at = 1.0
fr = 1.0
it = 1.0

[leeway up]
at = 1.0
fr = 1.0
it = 1.0

[pumping efficiency]
at = 1.0
fr = 1.0
it = 1.0

"""
        expected_hydro_ini = ConfigParser()
        expected_hydro_ini.read_string(expected_hydro_ini_content)

        # When
        with actual_hydro_ini.ini_path.open() as st_storage_list_ini_file:
            actual_hydro_ini_content = st_storage_list_ini_file.read()

        assert actual_hydro_ini_content == expected_hydro_ini_content
        assert actual_hydro_ini.parsed_ini.sections() == expected_hydro_ini.sections()
        assert actual_hydro_ini.parsed_ini == expected_hydro_ini
