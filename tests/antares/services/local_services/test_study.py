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

import logging
import os
import time
from configparser import ConfigParser
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from antares.config.local_configuration import LocalConfiguration
from antares.exceptions.exceptions import CustomError, LinkCreationError
from antares.model.area import AreaProperties, AreaUi, AreaUiLocal, AreaPropertiesLocal, Area
from antares.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintProperties,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    ConstraintTerm,
)
from antares.model.commons import FilterOption
from antares.model.hydro import Hydro
from antares.model.link import (
    Link,
    LinkProperties,
    LinkPropertiesLocal,
    TransmissionCapacities,
    LinkUi,
    AssetType,
    LinkStyle,
    LinkUiLocal,
)
from antares.model.study import create_study_local
from antares.service.local_services.area_local import AreaLocalService
from antares.service.local_services.link_local import LinkLocalService
from antares.service.local_services.renewable_local import RenewableLocalService
from antares.service.local_services.st_storage_local import ShortTermStorageLocalService
from antares.service.local_services.thermal_local import ThermalLocalService
from antares.tools.ini_tool import IniFileTypes


class TestCreateStudy:
    def test_create_study_success(self, tmp_path, caplog):
        # Given
        study_name = "studyTest"
        version = "850"
        caplog.set_level(logging.INFO)

        expected_subdirectories = ["input", "layers", "output", "settings", "user"]

        expected_study_path = tmp_path / "studyTest"

        # When
        create_study_local(study_name, version, LocalConfiguration(tmp_path, study_name))

        # Then
        assert os.path.exists(expected_study_path)
        assert os.path.isdir(expected_study_path)

        for subdirectory in expected_subdirectories:
            subdirectory_path = expected_study_path / subdirectory
            assert subdirectory_path.exists()
            assert subdirectory_path.is_dir()

        # Then
        assert caplog.records[0].msg == f"Study successfully created: {study_name}"

    def test_desktop_ini_creation(self, tmp_path, local_study):
        # Given
        expected_desktop_path = tmp_path / local_study.name / "Desktop.ini"
        desktop_ini_content = f"""[.ShellClassInfo]
IconFile = settings/resources/study.ico
IconIndex = 0
InfoTip = Antares Study {local_study.version}: {local_study.name}
"""

        # When
        with open(expected_desktop_path, "r") as file:
            actual_content = file.read()

        # Then
        assert actual_content == desktop_ini_content
        assert expected_desktop_path.exists()
        assert expected_desktop_path.is_file()

    def test_study_antares_content(self, monkeypatch, tmp_path):
        # Given
        study_name = "studyTest"
        version = "850"
        expected_study_antares_path = tmp_path / "studyTest/study.antares"
        antares_content = f"""[antares]
version = {version}
caption = {study_name}
created = {"123"}
lastsave = {"123"}
author = Unknown
"""

        monkeypatch.setattr(time, "time", lambda: "123")

        # When
        create_study_local(study_name, version, LocalConfiguration(tmp_path, study_name))
        with open(expected_study_antares_path, "r") as file:
            actual_content = file.read()

        # Then
        assert actual_content == antares_content

    def test_verify_study_already_exists_error(self, monkeypatch, tmp_path, caplog):
        # Given
        study_name = "studyTest"
        version = "850"

        def mock_verify_study_already_exists(study_directory):
            raise FileExistsError(f"Failed to create study. Study {study_directory} already exists")

        monkeypatch.setattr("antares.model.study._verify_study_already_exists", mock_verify_study_already_exists)

        # When
        with caplog.at_level(logging.ERROR):
            with pytest.raises(
                FileExistsError, match=f"Failed to create study. Study {tmp_path}/{study_name} already exists"
            ):
                create_study_local(study_name, version, LocalConfiguration(tmp_path, study_name))

    def test_solar_correlation_ini_exists(self, local_study_with_hydro):
        # Given
        expected_ini_path = local_study_with_hydro.service.config.study_path / "input/solar/prepro/correlation.ini"

        # Then
        assert expected_ini_path.exists()
        assert expected_ini_path.is_file()
        assert local_study_with_hydro._ini_files["solar_correlation"].ini_path == expected_ini_path

    def test_solar_correlation_ini_has_default_values(self, local_study_with_hydro):
        # Given
        expected_ini_content = """[general]
mode = annual

[annual]

[0]

[1]

[2]

[3]

[4]

[5]

[6]

[7]

[8]

[9]

[10]

[11]

"""
        expected_ini = ConfigParser()
        actual_ini = local_study_with_hydro._ini_files["solar_correlation"]

        # When
        expected_ini.read_string(expected_ini_content)
        with actual_ini.ini_path.open("r") as ini_file:
            actual_ini_content = ini_file.read()

        # Then
        assert actual_ini_content == expected_ini_content
        assert actual_ini.parsed_ini.sections() == expected_ini.sections()
        assert actual_ini.parsed_ini == expected_ini

    def test_wind_correlation_ini_exists(self, local_study_with_hydro):
        # Given
        expected_ini_path = local_study_with_hydro.service.config.study_path / "input/wind/prepro/correlation.ini"

        # Then
        assert expected_ini_path.exists()
        assert expected_ini_path.is_file()
        assert local_study_with_hydro._ini_files["wind_correlation"].ini_path == expected_ini_path

    def test_wind_correlation_ini_has_default_values(self, local_study_with_hydro):
        # Given
        expected_ini_content = """[general]
mode = annual

[annual]

[0]

[1]

[2]

[3]

[4]

[5]

[6]

[7]

[8]

[9]

[10]

[11]

"""
        expected_ini = ConfigParser()
        actual_ini = local_study_with_hydro._ini_files["wind_correlation"]

        # When
        expected_ini.read_string(expected_ini_content)
        with actual_ini.ini_path.open("r") as ini_file:
            actual_ini_content = ini_file.read()

        # Then
        assert actual_ini_content == expected_ini_content
        assert actual_ini.parsed_ini.sections() == expected_ini.sections()
        assert actual_ini.parsed_ini == expected_ini

    def test_load_correlation_ini_exists(self, local_study_with_hydro):
        # Given
        expected_ini_path = local_study_with_hydro.service.config.study_path / "input/load/prepro/correlation.ini"

        # Then
        assert expected_ini_path.exists()
        assert expected_ini_path.is_file()
        assert local_study_with_hydro._ini_files["load_correlation"].ini_path == expected_ini_path

    def test_load_correlation_ini_has_default_values(self, local_study_with_hydro):
        # Given
        expected_ini_content = """[general]
mode = annual

[annual]

[0]

[1]

[2]

[3]

[4]

[5]

[6]

[7]

[8]

[9]

[10]

[11]

"""
        expected_ini = ConfigParser()
        actual_ini = local_study_with_hydro._ini_files["load_correlation"]

        # When
        expected_ini.read_string(expected_ini_content)
        with actual_ini.ini_path.open("r") as ini_file:
            actual_ini_content = ini_file.read()

        # Then
        assert actual_ini_content == expected_ini_content
        assert actual_ini.parsed_ini.sections() == expected_ini.sections()
        assert actual_ini.parsed_ini == expected_ini


class TestCreateArea:
    def test_areas_sets_ini_content(self, tmp_path, local_study):
        # Given
        expected_sets_path = tmp_path / local_study.name / "input" / "areas" / "sets.ini"

        expected_sets_ini_content = """[all areas]
caption = All areas
comments = Spatial aggregates on all areas
output = false
apply-filter = add-all

"""

        # When
        local_study.create_area("area_test")

        with open(expected_sets_path, "r") as file:
            actual_content = file.read()

        # Then
        assert actual_content == expected_sets_ini_content

    def test_areas_list_txt_content(self, tmp_path, caplog, local_study):
        # Given
        study_antares_path = tmp_path / local_study.name
        caplog.set_level(logging.INFO)

        expected_list_txt = study_antares_path / "input" / "areas" / "list.txt"

        expected_list_txt_content = """area1
area2
"""

        # When
        local_study.create_area("area1")
        local_study.create_area("area2")

        with open(expected_list_txt, "r") as file:
            actual_content = file.read()

        # Then
        assert actual_content == expected_list_txt_content
        assert caplog.records[0].msg == "Area area1 created successfully!"
        assert caplog.records[1].msg == "Area area2 created successfully!"

    def test_areas_list_sorted_alphabetically(self, tmp_path, local_study):
        # Given
        areas_to_create = ["ghi", "fr", "at", "def", "abc"]
        expected_list_txt = tmp_path / local_study.name / "input" / "areas" / "list.txt"
        expected_list_txt_content = """abc
at
def
fr
ghi
"""

        # When
        for area in areas_to_create:
            local_study.create_area(area)

        with open(expected_list_txt, "r") as file:
            actual_content = file.read()

        assert actual_content == expected_list_txt_content

    def test_area_optimization_ini_content(self, tmp_path, local_study):
        # Given
        study_antares_path = tmp_path / local_study.name

        expected_optimization_ini_path = study_antares_path / "input" / "areas" / "area1" / "optimization.ini"

        expected_optimization_ini_content = """[nodal optimization]
non-dispatchable-power = true
dispatchable-hydro-power = true
other-dispatchable-power = true
spread-unsupplied-energy-cost = 0.000000
spread-spilled-energy-cost = 0.000000
average-unsupplied-energy-cost = 0.000000
average-spilled-energy-cost = 0.000000

[filtering]
filter-synthesis = hourly, daily, weekly, monthly, annual
filter-year-by-year = hourly, daily, weekly, monthly, annual

"""

        expected_optimization_ini = ConfigParser()
        expected_optimization_ini.read_string(expected_optimization_ini_content)

        # When
        local_study.create_area("area1")

        actual_optimization_ini = ConfigParser()
        with open(expected_optimization_ini_path, "r") as file:
            actual_optimization_ini.read_file(file)
            file.seek(0)
            actual_optimization_ini_content = file.read()

        # Then
        assert actual_optimization_ini == expected_optimization_ini
        assert actual_optimization_ini_content == expected_optimization_ini_content

    def test_custom_area_optimization_ini_content(self, tmp_path, local_study):
        # Given
        area_to_create = "area1"
        area_properties = AreaProperties(
            dispatch_hydro_power=False,
            energy_cost_unsupplied=1.04,
            energy_cost_spilled=1,
            filter_by_year={FilterOption.ANNUAL, FilterOption.HOURLY, FilterOption.WEEKLY, FilterOption.HOURLY},
        )
        expected_optimization_ini = ConfigParser()
        actual_optimization_ini = ConfigParser()
        expected_optimization_ini_path = (
            tmp_path / local_study.name / "input/areas" / area_to_create / "optimization.ini"
        )
        expected_optimization_ini_content = """[nodal optimization]
non-dispatchable-power = true
dispatchable-hydro-power = false
other-dispatchable-power = true
spread-unsupplied-energy-cost = 0.000000
spread-spilled-energy-cost = 0.000000
average-unsupplied-energy-cost = 1.040000
average-spilled-energy-cost = 1.000000

[filtering]
filter-synthesis = hourly, daily, weekly, monthly, annual
filter-year-by-year = hourly, weekly, annual

"""

        # When
        local_study.create_area(area_to_create, properties=area_properties)
        expected_optimization_ini.read_string(expected_optimization_ini_content)

        with open(expected_optimization_ini_path, "r") as file:
            actual_optimization_ini.read_file(file)
            file.seek(0)
            actual_optimization_ini_content = file.read()

        assert actual_optimization_ini == expected_optimization_ini
        assert actual_optimization_ini_content == expected_optimization_ini_content

    def test_area_ui_ini_content(self, tmp_path, local_study):
        # Given
        study_antares_path = tmp_path / local_study.name

        expected_ui_ini_path = study_antares_path / "input" / "areas" / "area1" / "ui.ini"

        ui_ini_content = """[ui]
x = 0
y = 0
color_r = 230
color_g = 108
color_b = 44
layers = 0

[layerX]
0 = 0

[layerY]
0 = 0

[layerColor]
0 = 230 , 108 , 44

"""

        # When
        local_study.create_area("area1")

        with open(expected_ui_ini_path, "r") as file:
            actual_content = file.read()

        # Then
        assert actual_content == ui_ini_content

    def test_create_area_with_custom_error(self, monkeypatch, caplog, local_study):
        # Given
        caplog.set_level(logging.INFO)

        def mock_error_in_sets_ini():
            raise CustomError("An error occurred while processing area can not be created")

        monkeypatch.setattr("antares.service.local_services.area_local._sets_ini_content", mock_error_in_sets_ini)
        with pytest.raises(CustomError, match="An error occurred while processing area can not be created"):
            local_study.create_area("test")

    def test_create_area_with_custom_ui(self, tmp_path, local_study):
        # Given
        study_antares_path = tmp_path / local_study.name
        # TODO: This should've been local_study._service.path, but ABCService doesn't have path

        area = "area1"
        ui_ini_path = study_antares_path / "input" / "areas" / area / "ui.ini"
        area_ui = AreaUi(x=123, y=321, color_rgb=[255, 230, 210])

        # When
        local_study.create_area(area, ui=area_ui)

        expected_content = """[ui]
x = 123
y = 321
color_r = 255
color_g = 230
color_b = 210
layers = 0

[layerX]
0 = 123

[layerY]
0 = 321

[layerColor]
0 = 255 , 230 , 210

"""

        with open(ui_ini_path, "r") as file:
            actual_content = file.read()

        assert actual_content == expected_content

    def test_created_area_has_ui(self, tmp_path, local_study):
        # Given
        area = "area1"
        area_ui = AreaUiLocal(AreaUi(x=123, y=321, color_rgb=[255, 230, 210])).yield_area_ui()

        # When
        local_study.create_area(area, ui=area_ui)
        assert local_study.get_areas()[area].ui == area_ui

    def test_areas_have_default_properties(self, tmp_path, local_study_w_areas):
        # Given
        expected_default_properties = {
            "nodal optimization": {
                "non-dispatchable-power": "true",
                "dispatchable-hydro-power": "true",
                "other-dispatchable-power": "true",
                "spread-unsupplied-energy-cost": "0.000000",
                "spread-spilled-energy-cost": "0.000000",
                "average-unsupplied-energy-cost": "0.000000",
                "average-spilled-energy-cost": "0.000000",
            },
            "filtering": {
                "filter-synthesis": "hourly, daily, weekly, monthly, annual",
                "filter-year-by-year": "hourly, daily, weekly, monthly, annual",
            },
        }

        # When
        actual_area_properties = local_study_w_areas.get_areas()["fr"].properties
        created_properties = actual_area_properties.model_dump(mode="json", exclude_none=True)
        actual_properties = AreaPropertiesLocal.model_validate(created_properties).yield_local_dict()

        assert expected_default_properties == actual_properties

    def test_areas_with_custom_properties(self, tmp_path, local_study):
        # Given
        area_to_create = "fr"
        area_properties = AreaProperties(
            dispatch_hydro_power=False,
            spread_unsupplied_energy_cost=1,
            energy_cost_spilled=3.5,
            filter_by_year={FilterOption.ANNUAL, FilterOption.ANNUAL, FilterOption.HOURLY, FilterOption.WEEKLY},
        )
        expected_properties = {
            "nodal optimization": {
                "non-dispatchable-power": "true",
                "dispatchable-hydro-power": "false",
                "other-dispatchable-power": "true",
                "spread-unsupplied-energy-cost": "1.000000",
                "spread-spilled-energy-cost": "0.000000",
                "average-unsupplied-energy-cost": "0.000000",
                "average-spilled-energy-cost": "3.500000",
            },
            "filtering": {
                "filter-synthesis": "hourly, daily, weekly, monthly, annual",
                "filter-year-by-year": "hourly, weekly, annual",
            },
        }

        # When
        created_area = local_study.create_area(area_name=area_to_create, properties=area_properties)
        created_properties = created_area.properties.model_dump(mode="json", exclude_none=True)
        actual_properties = AreaPropertiesLocal.model_validate(created_properties).yield_local_dict()
        assert expected_properties == actual_properties

    def test_areas_ini_has_correct_sections(self, actual_thermal_areas_ini):
        # Given
        expected_areas_ini_sections = ["unserverdenergycost", "spilledenergycost"]

        # Then
        assert actual_thermal_areas_ini.parsed_ini.sections() == expected_areas_ini_sections

    def test_areas_ini_has_correct_default_content(self, actual_thermal_areas_ini):
        # Given
        expected_areas_ini_contents = """[unserverdenergycost]
fr = 0.000000
it = 0.000000
at = 0.000000

[spilledenergycost]
fr = 0.000000
it = 0.000000
at = 0.000000

"""
        expected_areas_ini = ConfigParser()
        expected_areas_ini.read_string(expected_areas_ini_contents)

        # When
        with actual_thermal_areas_ini.ini_path.open("r") as areas_ini_file:
            actual_areas_ini_contents = areas_ini_file.read()

        # Then
        assert actual_areas_ini_contents == expected_areas_ini_contents
        assert actual_thermal_areas_ini.parsed_ini.sections() == expected_areas_ini.sections()
        assert actual_thermal_areas_ini.parsed_ini == expected_areas_ini

    def test_adequacy_patch_ini_has_correct_section(self, actual_adequacy_patch_ini):
        expected_sections = ["adequacy-patch"]
        assert actual_adequacy_patch_ini.parsed_ini.sections() == expected_sections

    def test_adequacy_patch_ini_has_correct_content(self, actual_adequacy_patch_ini):
        # Given
        expected_content = """[adequacy-patch]
adequacy-patch-mode = outside

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_content)

        # When
        with actual_adequacy_patch_ini.ini_path.open("r") as adequacy_patch_ini_file:
            actual_content = adequacy_patch_ini_file.read()

        assert actual_content == expected_content
        assert actual_adequacy_patch_ini.parsed_ini.sections() == expected_ini.sections()
        assert actual_adequacy_patch_ini.parsed_ini == expected_ini

    def test_created_area_has_hydro(self, local_study_w_areas):
        assert local_study_w_areas.get_areas()["fr"].hydro
        assert isinstance(local_study_w_areas.get_areas()["it"].hydro, Hydro)


class TestCreateLink:
    def test_create_link(self, tmp_path, local_study_w_areas):
        # Given
        link_to_create = "fr_it"

        # When
        area_from, area_to = link_to_create.split("_")
        link_created = local_study_w_areas.create_link(
            area_from=local_study_w_areas.get_areas()[area_from],
            area_to=local_study_w_areas.get_areas()[area_to],
            existing_areas=local_study_w_areas.get_areas(),
        )

        assert isinstance(link_created, Link)

    def test_unknown_area_errors(self, tmp_path, local_study_w_areas):
        # Given
        link_to_create = "es_fr"
        fake_study_name = "nonExistantStudy"
        fake_config = LocalConfiguration(Path("/fake/path"), fake_study_name)

        # When
        area_from, area_to = link_to_create.split("_")
        area_from = Area(
            name=area_from,
            area_service=AreaLocalService(fake_config, fake_study_name),
            storage_service=ShortTermStorageLocalService(fake_config, fake_study_name),
            thermal_service=ThermalLocalService(fake_config, fake_study_name),
            renewable_service=RenewableLocalService(fake_config, fake_study_name),
        )
        area_to = local_study_w_areas.get_areas()[area_to]

        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link {area_from.name} / {area_to.name}: {area_from.name} does not exist",
        ):
            local_study_w_areas.create_link(
                area_from=area_from, area_to=area_to, existing_areas=local_study_w_areas.get_areas()
            )

    def test_study_areas_not_provided_errors(self, tmp_path, local_study_w_areas):
        # With
        area_from = local_study_w_areas.get_areas()["fr"]
        area_to = local_study_w_areas.get_areas()["it"]
        test_service = LinkLocalService(
            local_study_w_areas.service.config,
            local_study_w_areas.name,
        )

        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link {area_from.name} / {area_to.name}: Cannot verify existing areas.",
        ):
            test_service.create_link(
                area_from=area_from,
                area_to=area_to,
                existing_areas=None,
            )

    def test_create_link_alphabetically(self, tmp_path, local_study):
        # Given
        areas_to_create = ["fr", "at"]
        for area in areas_to_create:
            local_study.create_area(area)
        link_to_create = "fr_at"

        # When
        area_from, area_to = link_to_create.split("_")
        link_created = local_study.create_link(
            area_from=local_study.get_areas()[area_from],
            area_to=local_study.get_areas()[area_to],
            existing_areas=local_study.get_areas(),
        )

        assert link_created.area_from.name == "at"
        assert link_created.area_to.name == "fr"

    def test_create_link_sets_ini_content(self, tmp_path, local_study_w_areas):
        # Given
        link_to_create = "fr_it"
        expected_content = """[it]
hurdles-cost = false
loop-flow = false
use-phase-shifter = false
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1
colorr = 112
colorg = 112
colorb = 112
display-comments = true
filter-synthesis = hourly, daily, weekly, monthly, annual
filter-year-by-year = hourly, daily, weekly, monthly, annual

"""

        # When
        area_from, area_to = link_to_create.split("_")

        local_study_w_areas.create_link(
            area_from=local_study_w_areas.get_areas()[area_from],
            area_to=local_study_w_areas.get_areas()[area_to],
            existing_areas=local_study_w_areas.get_areas(),
        )

        ini_file = tmp_path / local_study_w_areas.name / "input/links" / area_from / "properties.ini"
        with open(ini_file, "r") as file:
            actual_content = file.read()

        assert actual_content == expected_content

    def test_created_link_has_default_local_properties(self, tmp_path, local_study_w_areas):
        # Given
        link_to_create = "fr_it"
        expected_ini_content = """[it]
hurdles-cost = false
loop-flow = false
use-phase-shifter = false
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1
colorr = 112
colorg = 112
colorb = 112
display-comments = true
filter-synthesis = hourly, daily, weekly, monthly, annual
filter-year-by-year = hourly, daily, weekly, monthly, annual

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_content)
        default_properties = LinkPropertiesLocal().yield_link_properties()

        # When
        area_from, area_to = link_to_create.split("_")
        created_link = local_study_w_areas.create_link(
            area_from=local_study_w_areas.get_areas()[area_from],
            area_to=local_study_w_areas.get_areas()[area_to],
            existing_areas=local_study_w_areas.get_areas(),
        )
        ini_file = tmp_path / local_study_w_areas.name / "input/links" / area_from / "properties.ini"
        actual_ini = ConfigParser()
        with open(ini_file, "r") as file:
            actual_ini.read_file(file)
            file.seek(0)
            actual_ini_content = file.read()

        assert isinstance(created_link.properties, LinkProperties)
        assert created_link.properties.model_dump(exclude_none=True)
        assert created_link.properties == default_properties
        assert actual_ini == expected_ini
        assert actual_ini_content == expected_ini_content

    def test_created_link_has_custom_properties(self, tmp_path, local_study_w_areas):
        # Given
        link_to_create = "fr_it"
        link_properties = LinkProperties(
            loop_flow=True,
            use_phase_shifter=True,
            transmission_capacities=TransmissionCapacities.INFINITE,
            filter_year_by_year={FilterOption.WEEKLY, FilterOption.DAILY},
        )
        expected_ini_content = """[it]
hurdles-cost = false
loop-flow = true
use-phase-shifter = true
transmission-capacities = infinite
asset-type = ac
link-style = plain
link-width = 1
colorr = 112
colorg = 112
colorb = 112
display-comments = true
filter-synthesis = hourly, daily, weekly, monthly, annual
filter-year-by-year = daily, weekly

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_content)

        # When
        area_from, area_to = link_to_create.split("_")
        link_created = local_study_w_areas.create_link(
            area_from=local_study_w_areas.get_areas()[area_from],
            area_to=local_study_w_areas.get_areas()[area_to],
            properties=link_properties,
            existing_areas=local_study_w_areas.get_areas(),
        )
        created_ini_file = tmp_path / local_study_w_areas.name / "input/links" / area_from / "properties.ini"
        actual_ini = ConfigParser()
        with open(created_ini_file, "r") as file:
            actual_ini.read_file(file)
            file.seek(0)
            actual_ini_content = file.read()

        # Then
        assert actual_ini_content == expected_ini_content
        created_properties = link_properties.model_dump(mode="json", exclude_none=True)
        assert link_created.properties == LinkPropertiesLocal.model_validate(created_properties).yield_link_properties()
        assert expected_ini == actual_ini

    def test_multiple_links_created_from_same_area(self, tmp_path, local_study_w_areas):
        # Given
        local_study_w_areas.create_area("at")
        links_to_create = ["fr_at", "at_it"]
        expected_ini_string = """[fr]
hurdles-cost = false
loop-flow = false
use-phase-shifter = false
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1
colorr = 112
colorg = 112
colorb = 112
display-comments = true
filter-synthesis = hourly, daily, weekly, monthly, annual
filter-year-by-year = hourly, daily, weekly, monthly, annual

[it]
hurdles-cost = false
loop-flow = false
use-phase-shifter = false
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1
colorr = 112
colorg = 112
colorb = 112
display-comments = true
filter-synthesis = hourly, daily, weekly, monthly, annual
filter-year-by-year = hourly, daily, weekly, monthly, annual

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_string)
        properties_ini_file = tmp_path / local_study_w_areas.name / "input/links" / "at" / "properties.ini"

        # When
        for link in links_to_create:
            area_from, area_to = link.split("_")
            local_study_w_areas.create_link(
                area_from=local_study_w_areas.get_areas()[area_from],
                area_to=local_study_w_areas.get_areas()[area_to],
                existing_areas=local_study_w_areas.get_areas(),
            )

        # Then
        actual_ini = ConfigParser()
        with open(properties_ini_file, "r") as file:
            actual_ini.read_file(file)
            file.seek(0)
            actual_ini_string = file.read()

        for section in expected_ini.sections():
            assert actual_ini.has_section(section)

        assert actual_ini == expected_ini
        assert actual_ini_string == expected_ini_string

    def test_multiple_links_created_from_same_area_are_alphabetical(self, tmp_path, local_study_w_areas):
        # Given
        local_study_w_areas.create_area("at")
        links_to_create = ["at_it", "fr_at"]
        expected_ini_string = """[fr]
hurdles-cost = false
loop-flow = false
use-phase-shifter = false
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1
colorr = 112
colorg = 112
colorb = 112
display-comments = true
filter-synthesis = hourly, daily, weekly, monthly, annual
filter-year-by-year = hourly, daily, weekly, monthly, annual

[it]
hurdles-cost = false
loop-flow = false
use-phase-shifter = false
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1
colorr = 112
colorg = 112
colorb = 112
display-comments = true
filter-synthesis = hourly, daily, weekly, monthly, annual
filter-year-by-year = hourly, daily, weekly, monthly, annual

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_string)
        properties_ini_file = tmp_path / local_study_w_areas.name / "input/links" / "at" / "properties.ini"

        # When
        for link in links_to_create:
            area_from, area_to = link.split("_")
            local_study_w_areas.create_link(
                area_from=local_study_w_areas.get_areas()[area_from],
                area_to=local_study_w_areas.get_areas()[area_to],
                existing_areas=local_study_w_areas.get_areas(),
            )

        # Then
        actual_ini = ConfigParser()
        with open(properties_ini_file, "r") as file:
            actual_ini.read_file(file)
            file.seek(0)
            actual_ini_string = file.read()

        assert actual_ini == expected_ini
        assert actual_ini_string == expected_ini_string

    def test_duplicate_links_raises_error(self, tmp_path, local_study_w_links):
        # Given
        link_to_create = "fr_it"

        # When
        area_from, area_to = link_to_create.split("_")

        # Then
        with pytest.raises(
            CustomError,
            match="""Link exists already, section already exists in properties.ini:

Section 'it' already exists""",
        ):
            local_study_w_links.create_link(
                area_from=local_study_w_links.get_areas()[area_from],
                area_to=local_study_w_links.get_areas()[area_to],
                existing_areas=local_study_w_links.get_areas(),
            )

    def test_created_link_has_default_ui_values(self, tmp_path, local_study_w_areas):
        # Given
        link_to_create = "fr / it"
        actual_ini_file = tmp_path / local_study_w_areas.name / "input" / "links" / "fr" / "properties.ini"
        actual_ini = ConfigParser()
        expected_ini_string = """[it]
hurdles-cost = false
loop-flow = false
use-phase-shifter = false
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1
colorr = 112
colorg = 112
colorb = 112
display-comments = true
filter-synthesis = hourly, daily, weekly, monthly, annual
filter-year-by-year = hourly, daily, weekly, monthly, annual

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_string)

        # When
        area_from, area_to = link_to_create.split(" / ")
        local_study_w_areas.create_link(
            area_from=local_study_w_areas.get_areas()[area_from],
            area_to=local_study_w_areas.get_areas()[area_to],
            existing_areas=local_study_w_areas.get_areas(),
        )
        with open(actual_ini_file, "r") as file:
            actual_ini.read_file(file)
            file.seek(0)
            actual_ini_string = file.read()

        # Then
        assert isinstance(local_study_w_areas.get_links()[link_to_create].ui, LinkUi)
        assert actual_ini == expected_ini
        assert actual_ini_string == expected_ini_string

    def test_created_link_with_custom_ui_values(self, tmp_path, local_study_w_areas):
        # Given
        link_to_create = "fr / it"
        actual_ini_file = tmp_path / local_study_w_areas.name / "input" / "links" / "fr" / "properties.ini"
        actual_ini = ConfigParser()
        expected_ini_string = """[it]
hurdles-cost = true
loop-flow = false
use-phase-shifter = false
transmission-capacities = ignore
asset-type = gaz
link-style = dot
link-width = 1
colorr = 234
colorg = 123
colorb = 0
display-comments = true
filter-synthesis = hourly, weekly, monthly
filter-year-by-year = hourly, daily, weekly, monthly, annual

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_string)
        expected_properties = LinkProperties(
            hurdles_cost=True,
            transmission_capacities=TransmissionCapacities.DISABLED,
            asset_type=AssetType.GAZ,
            filter_synthesis={FilterOption.MONTHLY, FilterOption.HOURLY, FilterOption.WEEKLY},
        )
        expected_ui = LinkUi(link_style=LinkStyle.DOT, colorr=234, colorg=123, colorb=0)

        # When
        area_from, area_to = link_to_create.split(" / ")
        created_link = local_study_w_areas.create_link(
            area_from=local_study_w_areas.get_areas()[area_from],
            area_to=local_study_w_areas.get_areas()[area_to],
            properties=expected_properties,
            ui=expected_ui,
            existing_areas=local_study_w_areas.get_areas(),
        )
        with open(actual_ini_file, "r") as file:
            actual_ini.read_file(file)
            file.seek(0)
            actual_ini_string = file.read()
        actual_properties = created_link.properties
        actual_ui = created_link.ui

        # Then
        assert isinstance(local_study_w_areas.get_links()[link_to_create].ui, LinkUi)
        assert actual_ini == expected_ini
        assert actual_ini_string == expected_ini_string
        created_properties = expected_properties.model_dump(mode="json", exclude_none=True)
        assert actual_properties == LinkPropertiesLocal.model_validate(created_properties).yield_link_properties()
        created_ui = expected_ui.model_dump(mode="json", exclude_none=True)
        assert actual_ui == LinkUiLocal.model_validate(created_ui).yield_link_ui()


class TestCreateBindingconstraint:
    def test_can_be_created(self, local_study_with_hydro):
        # When
        binding_constraint_name = "test constraint"
        binding_constraint = local_study_with_hydro.create_binding_constraint(name=binding_constraint_name)

        # Then
        assert isinstance(binding_constraint, BindingConstraint)

    def test_constraints_have_default_properties(self, local_study_with_constraint):
        # Given
        constraint = local_study_with_constraint.get_binding_constraints()["test constraint"]

        # Then
        assert constraint.properties.model_dump(exclude_none=True)

    def test_constraints_have_correct_default_properties(self, test_constraint, default_constraint_properties):
        assert test_constraint.properties == default_constraint_properties

    def test_creating_constraints_creates_ini(self, local_study_with_constraint):
        # Given
        expected_ini_file_path = (
            local_study_with_constraint.service.config.study_path / "input/bindingconstraints/bindingconstraints.ini"
        )

        # Then
        assert expected_ini_file_path.exists()
        assert expected_ini_file_path.is_file()

    def test_constraints_ini_have_correct_default_content(
        self, local_study_with_constraint, test_constraint, default_constraint_properties
    ):
        # Given
        expected_ini_contents = """[0]
name = test constraint
id = test constraint
enabled = true
type = hourly
operator = less
filter-year-by-year = hourly
filter-synthesis = hourly
group = default

"""

        # When
        actual_ini_path = (
            local_study_with_constraint.service.config.study_path / IniFileTypes.BINDING_CONSTRAINTS_INI.value
        )
        with actual_ini_path.open("r") as file:
            actual_ini_content = file.read()

        # Then
        assert default_constraint_properties == test_constraint.properties
        assert actual_ini_content == expected_ini_contents

    def test_constraints_and_ini_have_custom_properties(self, local_study_with_constraint):
        # Given
        custom_constraint_properties = BindingConstraintProperties(
            enabled=False,
            time_step=BindingConstraintFrequency.WEEKLY,
            operator=BindingConstraintOperator.BOTH,
            comments="test comment",
            filter_year_by_year="yearly",
            filter_synthesis="monthly",
            group="test group",
        )
        expected_ini_content = """[0]
name = test constraint
id = test constraint
enabled = true
type = hourly
operator = less
filter-year-by-year = hourly
filter-synthesis = hourly
group = default

[1]
name = test constraint two
id = test constraint two
enabled = false
type = weekly
operator = both
comments = test comment
filter-year-by-year = yearly
filter-synthesis = monthly
group = test group

"""

        # When
        local_study_with_constraint.create_binding_constraint(
            name="test constraint two", properties=custom_constraint_properties
        )
        actual_file_path = (
            local_study_with_constraint.service.config.study_path / IniFileTypes.BINDING_CONSTRAINTS_INI.value
        )
        with actual_file_path.open("r") as file:
            actual_ini_content = file.read()

        # Then
        assert actual_ini_content == expected_ini_content

    def test_constraint_can_add_term(self, test_constraint):
        new_term = [ConstraintTerm(data={"area1": "fr", "area2": "at"})]
        test_constraint.add_terms(new_term)
        assert test_constraint.get_terms()

    def test_constraint_term_and_ini_have_correct_defaults(self, local_study_with_constraint, test_constraint):
        # Given
        expected_ini_contents = """[0]
name = test constraint
id = test constraint
enabled = true
type = hourly
operator = less
filter-year-by-year = hourly
filter-synthesis = hourly
group = default
at%fr = 0

"""
        # When
        new_term = [ConstraintTerm(data={"area1": "fr", "area2": "at"})]
        test_constraint.add_terms(new_term)
        with local_study_with_constraint._binding_constraints_service.ini_file.ini_path.open("r") as file:
            actual_ini_content = file.read()

        assert actual_ini_content == expected_ini_contents

    def test_constraint_term_with_offset_and_ini_have_correct_values(
        self, local_study_with_constraint, test_constraint
    ):
        # Given
        expected_ini_contents = """[0]
name = test constraint
id = test constraint
enabled = true
type = hourly
operator = less
filter-year-by-year = hourly
filter-synthesis = hourly
group = default
at%fr = 0.000000%1

"""
        # When
        new_term = [ConstraintTerm(offset=1, data={"area1": "fr", "area2": "at"})]
        test_constraint.add_terms(new_term)
        with local_study_with_constraint._binding_constraints_service.ini_file.ini_path.open("r") as file:
            actual_ini_content = file.read()

        assert actual_ini_content == expected_ini_contents

    def test_binding_constraint_with_timeseries_stores_ts_file(self, local_study_with_hydro):
        # Given
        ts_matrix = pd.DataFrame(np.zeros([365 * 24, 2]))

        # When
        constraints = {
            "lesser":
            # Less than timeseries
            local_study_with_hydro.create_binding_constraint(
                name="test constraint - less",
                properties=BindingConstraintProperties(
                    operator=BindingConstraintOperator.LESS,
                ),
                less_term_matrix=ts_matrix,
            ),
            "equal":
            # Equal timeseries
            local_study_with_hydro.create_binding_constraint(
                name="test constraint - equal",
                properties=BindingConstraintProperties(
                    operator=BindingConstraintOperator.EQUAL,
                ),
                equal_term_matrix=ts_matrix,
            ),
            "greater":
            # Greater than timeseries
            local_study_with_hydro.create_binding_constraint(
                name="test constraint - greater",
                properties=BindingConstraintProperties(
                    operator=BindingConstraintOperator.GREATER,
                ),
                greater_term_matrix=ts_matrix,
            ),
            "both":
            # Greater than timeseries
            local_study_with_hydro.create_binding_constraint(
                name="test constraint - both",
                properties=BindingConstraintProperties(
                    operator=BindingConstraintOperator.BOTH,
                ),
                less_term_matrix=ts_matrix,
                greater_term_matrix=ts_matrix,
            ),
        }

        # Then
        assert local_study_with_hydro._binding_constraints_service.time_series[
            f"{constraints['lesser'].id.lower()}_lt"
        ].local_file.file_path.is_file()
        assert local_study_with_hydro._binding_constraints_service.time_series[
            f"{constraints['equal'].id.lower()}_eq"
        ].local_file.file_path.is_file()
        assert local_study_with_hydro._binding_constraints_service.time_series[
            f"{constraints['greater'].id.lower()}_gt"
        ].local_file.file_path.is_file()
        assert local_study_with_hydro._binding_constraints_service.time_series[
            f"{constraints['both'].id.lower()}_lt"
        ].local_file.file_path.is_file()
        assert local_study_with_hydro._binding_constraints_service.time_series[
            f"{constraints['both'].id.lower()}_gt"
        ].local_file.file_path.is_file()
