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
import pytest

import os
import re

from configparser import ConfigParser
from pathlib import Path
from unittest.mock import ANY

import numpy as np
import pandas as pd

from antares.craft import Study, create_study_local, read_study_local
from antares.craft.exceptions.exceptions import (
    AreaCreationError,
    BindingConstraintCreationError,
    LinkCreationError,
    MatrixFormatError,
    UnsupportedStudyVersion,
)
from antares.craft.model.area import AreaProperties, AreaUi
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    ConstraintTerm,
    LinkData,
)
from antares.craft.model.commons import FilterOption
from antares.craft.model.hydro import Hydro
from antares.craft.model.link import (
    AssetType,
    Link,
    LinkProperties,
    LinkStyle,
    LinkUi,
    TransmissionCapacities,
)
from antares.craft.model.settings.adequacy_patch import (
    AdequacyPatchParameters,
    PriceTakingOrder,
)
from antares.craft.model.settings.advanced_parameters import (
    AdvancedParameters,
    HydroHeuristicPolicy,
    HydroPricingMode,
    InitialReservoirLevel,
    PowerFluctuation,
    RenewableGenerationModeling,
    SeedParameters,
    SheddingPolicy,
    SimulationCore,
    UnitCommitmentMode,
)
from antares.craft.model.settings.general import (
    BuildingMode,
    GeneralParameters,
    Mode,
    Month,
    WeekDay,
)
from antares.craft.model.settings.optimization import (
    ExportMPS,
    OptimizationParameters,
    OptimizationTransmissionCapacities,
    SimplexOptimizationRange,
    UnfeasibleProblemBehavior,
)
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.settings.thematic_trimming import ThematicTrimmingParameters
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter


class TestCreateStudy:
    def test_create_study_success(self, tmp_path: Path) -> None:
        # Given
        study_name = "studyTest"
        version = "880"

        expected_subdirectories = ["input", "layers", "output", "settings", "user"]

        expected_study_path = tmp_path / "studyTest"

        # When
        create_study_local(study_name, version, tmp_path.absolute())

        # Then
        assert os.path.exists(expected_study_path)
        assert os.path.isdir(expected_study_path)

        for subdirectory in expected_subdirectories:
            subdirectory_path = expected_study_path / subdirectory
            assert subdirectory_path.exists()
            assert subdirectory_path.is_dir()

    def test_creation_with_wrong_version(self, tmp_path: Path) -> None:
        with pytest.raises(
            UnsupportedStudyVersion, match="Unsupported study version: '830', supported ones are '9.2, 8.8'"
        ):
            create_study_local("Study_Test", "830", tmp_path)

    def test_reading_with_wrong_version(self, tmp_path: Path) -> None:
        create_study_local("Study_Test", "880", tmp_path)
        ini_path = tmp_path / "Study_Test" / "study.antares"
        ini_content = IniReader().read(ini_path)
        ini_content["antares"]["version"] = 820
        IniWriter().write(ini_content, ini_path)
        with pytest.raises(
            UnsupportedStudyVersion, match="Unsupported study version: '8.2', supported ones are '9.2, 8.8'"
        ):
            read_study_local(tmp_path / "Study_Test")

    def test_desktop_ini_creation(self, tmp_path: Path, local_study: Study) -> None:
        # Given
        expected_desktop_path = tmp_path / local_study.name / "Desktop.ini"
        assert expected_desktop_path.exists()
        assert expected_desktop_path.is_file()

    def test_study_antares_content(self, tmp_path: Path) -> None:
        # Given
        study_name = "studyTest"
        version = "880"
        expected_study_antares_path = tmp_path / study_name / "study.antares"

        # When
        create_study_local(study_name, version, tmp_path.absolute())

        # Then
        ini_content = IniReader().read(expected_study_antares_path)
        assert ini_content == {
            "antares": {
                "author": ANY,
                "caption": study_name,
                "created": ANY,
                "lastsave": ANY,
                "version": int(version),
            }
        }

    def test_scenario_builder_creation(self, tmp_path: Path, local_study: Study) -> None:
        # Given
        expected_scenario_builder_path = tmp_path / local_study.name / "settings" / "scenariobuilder.dat"
        desktop_ini_content = """[Default Ruleset]

"""
        actual_content = expected_scenario_builder_path.read_text()
        assert actual_content == desktop_ini_content

    def test_verify_study_already_exists_error(self, tmp_path: Path) -> None:
        # Given
        study_name = "studyTest"
        version = "850"
        (tmp_path / study_name).mkdir(parents=True, exist_ok=True)

        # When
        with pytest.raises(FileExistsError, match="Study directory already exists"):
            create_study_local(study_name, version, tmp_path.absolute())

    def test_all_correlation_ini_files_exists(self, local_study: Study) -> None:
        expected_ini_content = """[general]
mode = annual

"""
        study_path = Path(local_study.path)
        for folder in ["hydro", "load", "solar", "wind"]:
            ini_path = study_path / "input" / folder / "prepro" / "correlation.ini"
            assert ini_path.exists()
            assert ini_path.is_file()

            ini_content = ini_path.read_text(encoding="utf-8")
            assert ini_content == expected_ini_content


class TestStudyProperties:
    def test_local_study_has_settings(self, local_study: Study) -> None:
        # When
        local_study_settings = local_study.get_settings()
        # Then
        assert local_study.get_settings()
        assert isinstance(local_study_settings, StudySettings)

    def test_local_study_has_correct_default_general_properties(self, local_study: Study) -> None:
        expected_general_properties = GeneralParameters(
            mode=Mode.ECONOMY,
            horizon="",
            nb_years=1,
            simulation_start=1,
            simulation_end=365,
            january_first=WeekDay.MONDAY,
            first_month_in_year=Month.JANUARY,
            first_week_day=WeekDay.MONDAY,
            leap_year=False,
            year_by_year=False,
            simulation_synthesis=True,
            building_mode=BuildingMode.AUTOMATIC,
            user_playlist=False,
            thematic_trimming=False,
            geographic_trimming=False,
            store_new_set=False,
            nb_timeseries_thermal=1,
        )

        assert local_study.get_settings().general_parameters == expected_general_properties

    def test_local_study_has_correct_default_adequacy_patch_properties(
        self, local_study: Study, local_study_92: Study
    ) -> None:
        for study in [local_study, local_study_92]:
            value = True if study == local_study else None  # Depends on the version

            expected_adequacy_patch_properties = AdequacyPatchParameters(
                include_adq_patch=False,
                set_to_null_ntc_from_physical_out_to_physical_in_for_first_step=True,
                price_taking_order=PriceTakingOrder.DENS,
                include_hurdle_cost_csr=False,
                check_csr_cost_function=False,
                threshold_initiate_curtailment_sharing_rule=1,
                threshold_display_local_matching_rule_violations=0,
                threshold_csr_variable_bounds_relaxation=7,
                set_to_null_ntc_between_physical_out_for_first_step=value,
            )

            assert study.get_settings().adequacy_patch_parameters == expected_adequacy_patch_properties

    def test_local_study_has_correct_advanced_parameters(self, local_study: Study, local_study_92: Study) -> None:
        for study in [local_study, local_study_92]:
            value = InitialReservoirLevel.COLD_START if study == local_study else None  # Depends on the version

            expected_advanced_parameters = AdvancedParameters(
                initial_reservoir_levels=value,
                hydro_heuristic_policy=HydroHeuristicPolicy.ACCOMMODATE_RULES_CURVES,
                hydro_pricing_mode=HydroPricingMode.FAST,
                power_fluctuations=PowerFluctuation.FREE_MODULATIONS,
                shedding_policy=SheddingPolicy.SHAVE_PEAKS,
                unit_commitment_mode=UnitCommitmentMode.FAST,
                number_of_cores_mode=SimulationCore.MEDIUM,
                renewable_generation_modelling=RenewableGenerationModeling.CLUSTERS,
                accuracy_on_correlation=set(),
            )

            assert study.get_settings().advanced_parameters == expected_advanced_parameters

    def test_local_study_has_correct_seed_parameters(self, local_study: Study) -> None:
        expected_seed_parameters = SeedParameters(
            **{
                "seed_tsgen_thermal": 3005489,
                "seed_tsnumbers": 5005489,
                "seed_unsupplied_energy_costs": 6005489,
                "seed_spilled_energy_costs": 7005489,
                "seed_thermal_costs": 8005489,
                "seed_hydro_costs": 9005489,
                "seed_initial_reservoir_levels": 10005489,
            }
        )

        assert local_study.get_settings().seed_parameters == expected_seed_parameters

    def test_local_study_has_correct_optimization_parameters(self, local_study: Study) -> None:
        expected_optimization_parameters = OptimizationParameters(
            simplex_range=SimplexOptimizationRange.WEEK,
            transmission_capacities=OptimizationTransmissionCapacities.LOCAL_VALUES,
            include_constraints=True,
            include_hurdlecosts=True,
            include_tc_minstablepower=True,
            include_tc_min_ud_time=True,
            include_dayahead=True,
            include_strategicreserve=True,
            include_spinningreserve=True,
            include_primaryreserve=True,
            include_exportmps=ExportMPS.FALSE,
            include_exportstructure=False,
            include_unfeasible_problem_behavior=UnfeasibleProblemBehavior.ERROR_VERBOSE,
        )

        assert local_study.get_settings().optimization_parameters == expected_optimization_parameters

    def test_local_study_has_correct_playlist_and_thematic_parameters(
        self, local_study: Study, default_thematic_trimming_88: ThematicTrimmingParameters
    ) -> None:
        assert local_study.get_settings().playlist_parameters == {}
        assert local_study.get_settings().thematic_trimming_parameters == default_thematic_trimming_88

    def test_generaldata_ini_exists(self, local_study: Study) -> None:
        # Given
        expected_file = Path(local_study.path) / "settings/generaldata.ini"

        # Then
        assert expected_file.is_file()

    def test_generaldata_ini_has_correct_default_values(self, local_study: Study) -> None:
        # Given
        expected_file_content = """[general]
mode = Economy
horizon = 
nbyears = 1
simulation.start = 1
simulation.end = 365
january.1st = Monday
first-month-in-year = January
first.weekday = Monday
leapyear = False
year-by-year = False
user-playlist = False
thematic-trimming = False
geographic-trimming = False
generate = False
nbtimeseriesload = 1
nbtimeserieshydro = 1
nbtimeserieswind = 1
nbtimeseriesthermal = 1
nbtimeseriessolar = 1
refreshtimeseries = False
intra-modal = False
inter-modal = False
refreshintervalload = 100
refreshintervalhydro = 100
refreshintervalwind = 100
refreshintervalthermal = 100
refreshintervalsolar = 100
readonly = False
derated = False
custom-scenario = False

[input]
import = 

[output]
synthesis = True
storenewset = False
archives = 

[optimization]
simplex-range = week
transmission-capacities = local-values
include-constraints = True
include-hurdlecosts = True
include-tc-minstablepower = True
include-tc-min-ud-time = True
include-dayahead = True
include-strategicreserve = True
include-spinningreserve = True
include-primaryreserve = True
include-exportmps = False
include-exportstructure = False
include-unfeasible-problem-behavior = error-verbose

[adequacy patch]
include-adq-patch = False
set-to-null-ntc-from-physical-out-to-physical-in-for-first-step = True
price-taking-order = DENS
include-hurdle-cost-csr = False
check-csr-cost-function = False
threshold-initiate-curtailment-sharing-rule = 1
threshold-display-local-matching-rule-violations = 0
threshold-csr-variable-bounds-relaxation = 7
enable-first-step = False

[other preferences]
hydro-heuristic-policy = accommodate rule curves
hydro-pricing-mode = fast
power-fluctuations = free modulations
shedding-policy = shave peaks
shedding-strategy = shave margins
unit-commitment-mode = fast
number-of-cores-mode = medium
renewable-generation-modelling = clusters
day-ahead-reserve-management = global

[advanced parameters]
accuracy-on-correlation = 
adequacy-block-size = 100

[seeds - Mersenne Twister]
seed-tsgen-wind = 5489
seed-tsgen-load = 1005489
seed-tsgen-hydro = 2005489
seed-tsgen-thermal = 3005489
seed-tsgen-solar = 4005489
seed-tsnumbers = 5005489
seed-unsupplied-energy-costs = 6005489
seed-spilled-energy-costs = 7005489
seed-thermal-costs = 8005489
seed-hydro-costs = 9005489
seed-initial-reservoir-levels = 10005489

"""

        # When
        ini_content = (Path(local_study.path) / "settings" / "generaldata.ini").read_text()
        assert ini_content == expected_file_content


class TestCreateArea:
    def test_initialization_when_creating_area(self, tmp_path: Path, local_study: Study) -> None:
        study_path = Path(local_study.path)
        area_id = "test_files"
        local_study.create_area(area_id)

        expected_paths = [
            study_path / f"input/reserves/{area_id}.txt",
            study_path / f"input/misc-gen/miscgen-{area_id}.txt",
            study_path / f"input/links/{area_id}/properties.ini",
            study_path / f"input/load/series/load_{area_id}.txt",
            study_path / f"input/solar/series/solar_{area_id}.txt",
            study_path / f"input/wind/series/wind_{area_id}.txt",
            study_path / f"input/thermal/clusters/{area_id}/list.ini",
        ]

        for expected_path in expected_paths:
            assert expected_path.is_file(), f"File not created: {expected_path}"

    def test_areas_sets_ini_content(self, tmp_path: Path, local_study: Study) -> None:
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

    def test_areas_list_txt_content(self, tmp_path: Path, local_study: Study) -> None:
        # Given
        study_antares_path = tmp_path / local_study.name

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

    def test_areas_list_sorted_alphabetically(self, tmp_path: Path, local_study: Study) -> None:
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

    def test_area_optimization_ini_content(self, tmp_path: Path, local_study: Study) -> None:
        # Given
        study_antares_path = tmp_path / local_study.name

        expected_optimization_ini_path = study_antares_path / "input" / "areas" / "area1" / "optimization.ini"

        expected_optimization_ini_content = """[nodal optimization]
non-dispatchable-power = True
dispatchable-hydro-power = True
other-dispatchable-power = True
spread-unsupplied-energy-cost = 0.0
spread-spilled-energy-cost = 0.0

[filtering]
filter-synthesis = annual, daily, hourly, monthly, weekly
filter-year-by-year = annual, daily, hourly, monthly, weekly

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

    def test_custom_area_optimization_ini_content(self, tmp_path: Path, local_study: Study) -> None:
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
non-dispatchable-power = True
dispatchable-hydro-power = False
other-dispatchable-power = True
spread-unsupplied-energy-cost = 0.0
spread-spilled-energy-cost = 0.0

[filtering]
filter-synthesis = annual, daily, hourly, monthly, weekly
filter-year-by-year = annual, hourly, weekly

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

    def test_area_ui_ini_content(self, tmp_path: Path, local_study: Study) -> None:
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
0 = 230,108,44

"""

        # When
        local_study.create_area("area1")

        with open(expected_ui_ini_path, "r") as file:
            actual_content = file.read()

        # Then
        assert actual_content == ui_ini_content

    def test_create_area_with_custom_error(self, local_study: Study) -> None:
        area_id = "?"
        with pytest.raises(
            AreaCreationError,
            match=f"Could not create the area {area_id}",
        ):
            local_study.create_area(area_id)

    def test_create_area_with_custom_ui(self, tmp_path: Path, local_study: Study) -> None:
        # Given
        study_antares_path = Path(local_study.path)

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
0 = 255,230,210

"""

        with open(ui_ini_path, "r") as file:
            actual_content = file.read()

        assert actual_content == expected_content

    def test_created_area_has_ui(self, tmp_path: Path, local_study: Study) -> None:
        # Given
        area = "area1"
        area_ui = AreaUi(x=123, y=321, color_rgb=[255, 230, 210])

        # When
        local_study.create_area(area, ui=area_ui)
        assert local_study.get_areas()[area].ui == area_ui

    def test_creating_duplicate_area_name_errors(self, local_study_w_areas: Study) -> None:
        # Given
        area_to_create = "fr"

        # Then
        with pytest.raises(
            AreaCreationError,
            match=f"Could not create the area '{area_to_create}': There is already an area '{area_to_create}' in the study '{local_study_w_areas.name}'",
        ):
            local_study_w_areas.create_area(area_to_create)

    def test_areas_have_default_properties(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        actual_area_properties = local_study_w_areas.get_areas()["fr"].properties
        assert actual_area_properties == AreaProperties(
            energy_cost_spilled=1, energy_cost_unsupplied=0.5, filter_synthesis={FilterOption.WEEKLY}
        )

    def test_areas_with_custom_properties(self, tmp_path: Path, local_study: Study) -> None:
        # Given
        area_to_create = "fr"
        area_properties = AreaProperties(
            dispatch_hydro_power=False,
            spread_unsupplied_energy_cost=1,
            energy_cost_spilled=3.5,
            filter_by_year={FilterOption.ANNUAL, FilterOption.ANNUAL, FilterOption.HOURLY, FilterOption.WEEKLY},
        )

        # When
        created_area = local_study.create_area(area_name=area_to_create, properties=area_properties)
        assert created_area.properties == area_properties

    def test_created_area_has_hydro(self, local_study_w_areas: Study) -> None:
        assert local_study_w_areas.get_areas()["fr"].hydro
        assert isinstance(local_study_w_areas.get_areas()["it"].hydro, Hydro)


class TestCreateLink:
    def test_create_link(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # Given
        link_to_create = "fr_it"

        # When
        area_from, area_to = link_to_create.split("_")
        link_created = local_study_w_areas.create_link(
            area_from=area_from,
            area_to=area_to,
        )

        assert isinstance(link_created, Link)

    def test_unknown_area_errors(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # Given
        link_to_create = "es_fr"

        # When
        area_from, area_to = link_to_create.split("_")
        area_from = area_from
        area_to = area_to

        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link '{area_from} / {area_to}': {area_from} does not exist",
        ):
            local_study_w_areas.create_link(area_from=area_from, area_to=area_to)

    def test_create_link_alphabetically(self, tmp_path: Path, local_study: Study) -> None:
        # Given
        areas_to_create = ["fr", "at"]
        for area in areas_to_create:
            local_study.create_area(area)
        link_to_create = "fr_at"

        # When
        area_from, area_to = link_to_create.split("_")
        link_created = local_study.create_link(
            area_from=area_from,
            area_to=area_to,
        )

        assert link_created.area_from_id == "at"
        assert link_created.area_to_id == "fr"

    def test_create_link_sets_ini_content(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # Given
        link_to_create = "fr_it"
        expected_content = """[it]
hurdles-cost = False
loop-flow = False
use-phase-shifter = False
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1.0
colorr = 112
colorg = 112
colorb = 112
display-comments = True
filter-synthesis = annual, daily, hourly, monthly, weekly
filter-year-by-year = annual, daily, hourly, monthly, weekly
comments = 

"""

        # When
        area_from, area_to = link_to_create.split("_")

        local_study_w_areas.create_link(
            area_from="fr",
            area_to="it",
        )

        ini_file = tmp_path / local_study_w_areas.name / "input/links" / area_from / "properties.ini"
        with open(ini_file, "r") as file:
            actual_content = file.read()

        assert actual_content == expected_content

    def test_created_link_has_default_local_properties(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # Given
        link_to_create = "fr_it"
        expected_ini_content = """[it]
hurdles-cost = False
loop-flow = False
use-phase-shifter = False
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1.0
colorr = 112
colorg = 112
colorb = 112
display-comments = True
filter-synthesis = annual, daily, hourly, monthly, weekly
filter-year-by-year = annual, daily, hourly, monthly, weekly
comments = 

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_content)

        # When
        area_from, area_to = link_to_create.split("_")
        created_link = local_study_w_areas.create_link(
            area_from="fr",
            area_to="it",
        )
        ini_file = tmp_path / local_study_w_areas.name / "input/links" / area_from / "properties.ini"
        actual_ini = ConfigParser()
        with open(ini_file, "r") as file:
            actual_ini.read_file(file)
            file.seek(0)
            actual_ini_content = file.read()

        assert isinstance(created_link.properties, LinkProperties)
        assert created_link.properties == LinkProperties()
        assert actual_ini == expected_ini
        assert actual_ini_content == expected_ini_content

    def test_created_link_has_custom_properties(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # Given
        link_to_create = "fr_it"
        link_properties = LinkProperties(
            loop_flow=True,
            use_phase_shifter=True,
            transmission_capacities=TransmissionCapacities.INFINITE,
            filter_year_by_year={FilterOption.WEEKLY, FilterOption.DAILY},
        )
        expected_ini_content = """[it]
hurdles-cost = False
loop-flow = True
use-phase-shifter = True
transmission-capacities = infinite
asset-type = ac
link-style = plain
link-width = 1.0
colorr = 112
colorg = 112
colorb = 112
display-comments = True
filter-synthesis = annual, daily, hourly, monthly, weekly
filter-year-by-year = daily, weekly
comments = 

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_content)

        # When
        area_from, area_to = link_to_create.split("_")
        link_created = local_study_w_areas.create_link(area_from="fr", area_to="it", properties=link_properties)
        created_ini_file = tmp_path / local_study_w_areas.name / "input/links" / area_from / "properties.ini"
        actual_ini = ConfigParser()
        with open(created_ini_file, "r") as file:
            actual_ini.read_file(file)
            file.seek(0)
            actual_ini_content = file.read()

        # Then
        assert actual_ini_content == expected_ini_content
        assert link_created.properties == link_properties
        assert expected_ini == actual_ini

    def test_multiple_links_created_from_same_area(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # Given
        local_study_w_areas.create_area("at")
        links_to_create = ["fr_at", "at_it"]
        expected_ini_string = """[fr]
hurdles-cost = False
loop-flow = False
use-phase-shifter = False
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1.0
colorr = 112
colorg = 112
colorb = 112
display-comments = True
filter-synthesis = annual, daily, hourly, monthly, weekly
filter-year-by-year = annual, daily, hourly, monthly, weekly
comments = 

[it]
hurdles-cost = False
loop-flow = False
use-phase-shifter = False
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1.0
colorr = 112
colorg = 112
colorb = 112
display-comments = True
filter-synthesis = annual, daily, hourly, monthly, weekly
filter-year-by-year = annual, daily, hourly, monthly, weekly
comments = 

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_string)
        properties_ini_file = tmp_path / local_study_w_areas.name / "input/links" / "at" / "properties.ini"

        # When
        for link in links_to_create:
            area_from, area_to = link.split("_")
            local_study_w_areas.create_link(area_from=area_from, area_to=area_to)

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

    def test_multiple_links_created_from_same_area_are_alphabetical(
        self, tmp_path: Path, local_study_w_areas: Study
    ) -> None:
        # Given
        local_study_w_areas.create_area("at")
        links_to_create = ["at_it", "fr_at"]
        expected_ini_string = """[it]
hurdles-cost = False
loop-flow = False
use-phase-shifter = False
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1.0
colorr = 112
colorg = 112
colorb = 112
display-comments = True
filter-synthesis = annual, daily, hourly, monthly, weekly
filter-year-by-year = annual, daily, hourly, monthly, weekly
comments = 

[fr]
hurdles-cost = False
loop-flow = False
use-phase-shifter = False
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1.0
colorr = 112
colorg = 112
colorb = 112
display-comments = True
filter-synthesis = annual, daily, hourly, monthly, weekly
filter-year-by-year = annual, daily, hourly, monthly, weekly
comments = 

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_string)
        properties_ini_file = tmp_path / local_study_w_areas.name / "input/links" / "at" / "properties.ini"

        # When
        for link in links_to_create:
            area_from, area_to = link.split("_")
            local_study_w_areas.create_link(area_from=area_from, area_to=area_to)

        # Then
        actual_ini = ConfigParser()
        with open(properties_ini_file, "r") as file:
            actual_ini.read_file(file)
            file.seek(0)
            actual_ini_string = file.read()

        assert actual_ini == expected_ini
        assert actual_ini_string == expected_ini_string

    def test_duplicate_links_raises_error(self, tmp_path: Path, local_study_w_links: Study) -> None:
        # Given
        link_to_create = "fr_it"

        # When
        area_from, area_to = link_to_create.split("_")

        # Then
        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link '{area_from} / {area_to}': A link from {area_from} to {area_to} already exists",
        ):
            local_study_w_links.create_link(
                area_from=area_from,
                area_to=area_to,
            )

    def test_created_link_has_default_ui_values(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # Given
        link_to_create = "fr / it"
        actual_ini_file = tmp_path / local_study_w_areas.name / "input" / "links" / "fr" / "properties.ini"
        actual_ini = ConfigParser()
        expected_ini_string = """[it]
hurdles-cost = False
loop-flow = False
use-phase-shifter = False
transmission-capacities = enabled
asset-type = ac
link-style = plain
link-width = 1.0
colorr = 112
colorg = 112
colorb = 112
display-comments = True
filter-synthesis = annual, daily, hourly, monthly, weekly
filter-year-by-year = annual, daily, hourly, monthly, weekly
comments = 

"""
        expected_ini = ConfigParser()
        expected_ini.read_string(expected_ini_string)

        # When
        area_from, area_to = link_to_create.split(" / ")
        local_study_w_areas.create_link(area_from=area_from, area_to=area_to)
        with open(actual_ini_file, "r") as file:
            actual_ini.read_file(file)
            file.seek(0)
            actual_ini_string = file.read()

        # Then
        assert isinstance(local_study_w_areas.get_links()[link_to_create].ui, LinkUi)
        assert actual_ini == expected_ini
        assert actual_ini_string == expected_ini_string

    def test_created_link_with_custom_ui_values(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # Given
        link_to_create = "fr / it"
        actual_ini_file = tmp_path / local_study_w_areas.name / "input" / "links" / "fr" / "properties.ini"
        actual_ini = ConfigParser()
        expected_ini_string = """[it]
hurdles-cost = True
loop-flow = False
use-phase-shifter = False
transmission-capacities = ignore
asset-type = gaz
link-style = dot
link-width = 1.0
colorr = 234
colorg = 123
colorb = 0
display-comments = True
filter-synthesis = hourly, monthly, weekly
filter-year-by-year = annual, daily, hourly, monthly, weekly
comments = 

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
            area_from=area_from,
            area_to=area_to,
            properties=expected_properties,
            ui=expected_ui,
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
        assert actual_properties == expected_properties
        assert actual_ui == expected_ui


class TestCreateBindingconstraint:
    def test_can_be_created(self, local_study_with_hydro: Study) -> None:
        # When
        binding_constraint_name = "test constraint"
        binding_constraint = local_study_with_hydro.create_binding_constraint(name=binding_constraint_name)

        # Then
        assert isinstance(binding_constraint, BindingConstraint)

    def test_duplicate_name_errors(self, local_study_with_constraint: Study) -> None:
        # Given
        binding_constraint_name = "test constraint"

        # Then
        with pytest.raises(
            BindingConstraintCreationError,
            match=f"Could not create the binding constraint '{binding_constraint_name}': A binding constraint with the name {binding_constraint_name} already exists.",
        ):
            local_study_with_constraint.create_binding_constraint(name=binding_constraint_name)

    def test_constraints_have_correct_default_properties(self, test_constraint: BindingConstraint) -> None:
        assert test_constraint.properties == BindingConstraintProperties()

    def test_creating_constraints_creates_ini(self, local_study_with_constraint: Study) -> None:
        # Given
        expected_ini_file_path = (
            Path(local_study_with_constraint.path) / "input/bindingconstraints/bindingconstraints.ini"
        )

        # Then
        assert expected_ini_file_path.exists()
        assert expected_ini_file_path.is_file()

    def test_constraints_ini_have_correct_default_content(
        self, local_study_with_constraint: Study, test_constraint: BindingConstraint
    ) -> None:
        # Given
        expected_ini_contents = """[0]
id = test constraint
name = test constraint
enabled = True
type = hourly
operator = less
comments = 
filter-year-by-year = annual, daily, hourly, monthly, weekly
filter-synthesis = annual, daily, hourly, monthly, weekly
group = default

"""

        # When
        study_path = Path(local_study_with_constraint.path)
        ini_content = (study_path / "input" / "bindingconstraints" / "bindingconstraints.ini").read_text()
        assert ini_content == expected_ini_contents

    def test_constraints_and_ini_have_custom_properties(self, local_study_with_constraint: Study) -> None:
        # Given
        custom_constraint_properties = BindingConstraintProperties(
            enabled=False,
            time_step=BindingConstraintFrequency.WEEKLY,
            operator=BindingConstraintOperator.BOTH,
            comments="test comment",
            filter_year_by_year={FilterOption.ANNUAL},
            filter_synthesis={FilterOption.MONTHLY},
            group="test group",
        )
        expected_ini_content = """[0]
id = test constraint
name = test constraint
enabled = True
type = hourly
operator = less
comments = 
filter-year-by-year = annual, daily, hourly, monthly, weekly
filter-synthesis = annual, daily, hourly, monthly, weekly
group = default

[1]
id = test constraint two
name = test constraint two
enabled = False
type = weekly
operator = both
comments = test comment
filter-year-by-year = annual
filter-synthesis = monthly
group = test group

"""

        # When
        local_study_with_constraint.create_binding_constraint(
            name="test constraint two", properties=custom_constraint_properties
        )
        study_path = Path(local_study_with_constraint.path)
        ini_content = (study_path / "input" / "bindingconstraints" / "bindingconstraints.ini").read_text()
        assert ini_content == expected_ini_content

    def test_constraint_can_add_term(self, test_constraint: BindingConstraint) -> None:
        new_term = [ConstraintTerm(data=LinkData(area1="fr", area2="at"))]
        test_constraint.add_terms(new_term)
        assert test_constraint.get_terms()

    def test_constraint_term_and_ini_have_correct_defaults(
        self, local_study_with_constraint: Study, test_constraint: BindingConstraint
    ) -> None:
        # Given
        expected_ini_contents = """[0]
id = test constraint
name = test constraint
enabled = True
type = hourly
operator = less
comments = 
filter-year-by-year = annual, daily, hourly, monthly, weekly
filter-synthesis = annual, daily, hourly, monthly, weekly
group = default
at%fr = 1

"""
        # When
        new_term = [ConstraintTerm(data=LinkData(area1="fr", area2="at"))]
        test_constraint.add_terms(new_term)
        study_path = Path(local_study_with_constraint.path)
        ini_content = (study_path / "input" / "bindingconstraints" / "bindingconstraints.ini").read_text()

        assert ini_content == expected_ini_contents

    def test_constraint_term_with_offset_and_ini_have_correct_values(
        self, local_study_with_constraint: Study, test_constraint: BindingConstraint
    ) -> None:
        # Given
        expected_ini_contents = """[0]
id = test constraint
name = test constraint
enabled = True
type = hourly
operator = less
comments = 
filter-year-by-year = annual, daily, hourly, monthly, weekly
filter-synthesis = annual, daily, hourly, monthly, weekly
group = default
at%fr = 1%1

"""
        # When
        new_term = [ConstraintTerm(offset=1, data=LinkData(area1="fr", area2="at"))]
        test_constraint.add_terms(new_term)
        study_path = Path(local_study_with_constraint.path)
        ini_content = (study_path / "input" / "bindingconstraints" / "bindingconstraints.ini").read_text()

        assert ini_content == expected_ini_contents

    def test_binding_constraints_have_correct_default_time_series(
        self, test_constraint: BindingConstraint, local_study_with_constraint: Study
    ) -> None:
        # Given
        local_study_with_constraint.create_binding_constraint(
            name="test greater",
            properties=BindingConstraintProperties(
                operator=BindingConstraintOperator.GREATER, time_step=BindingConstraintFrequency.WEEKLY
            ),
        )
        local_study_with_constraint.create_binding_constraint(
            name="test equal",
            properties=BindingConstraintProperties(
                operator=BindingConstraintOperator.EQUAL, time_step=BindingConstraintFrequency.DAILY
            ),
        )
        local_study_with_constraint.create_binding_constraint(
            name="test both",
            properties=BindingConstraintProperties(
                operator=BindingConstraintOperator.BOTH, time_step=BindingConstraintFrequency.HOURLY
            ),
        )

        # Then
        study_path = Path(local_study_with_constraint.path)

        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / "test greater_gt.txt")
        assert not actual_file_path.read_text()

        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / "test equal_eq.txt")
        assert not actual_file_path.read_text()

        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / f"{test_constraint.id}_lt.txt")
        assert not actual_file_path.read_text()

        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / "test both_lt.txt")
        assert not actual_file_path.read_text()

        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / "test both_gt.txt")
        assert not actual_file_path.read_text()

    def test_submitted_time_series_is_saved(self, local_study: Study) -> None:
        # Given
        expected_time_series = pd.DataFrame(np.ones([8784, 1]))
        bc_name = "test time series"
        local_study.create_binding_constraint(
            name=bc_name,
            properties=BindingConstraintProperties(
                operator=BindingConstraintOperator.GREATER, time_step=BindingConstraintFrequency.HOURLY
            ),
            greater_term_matrix=expected_time_series,
        )

        study_path = Path(local_study.path)
        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / f"{bc_name}_gt.txt")
        actual_time_series = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=float)

        # Then
        assert actual_time_series.equals(expected_time_series)

    def test_giving_wrongly_formatted_matrix_fails(self, local_study: Study) -> None:
        wrong_time_series = pd.DataFrame(np.ones([3, 1]))
        bc_name = "bc_1"
        # Ensures creation fails
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                f"Wrong format for bindingconstraints/{bc_name}/bc_hourly matrix, expected shape is (8784, Any) and was : (3, 1)"
            ),
        ):
            local_study.create_binding_constraint(name=bc_name, greater_term_matrix=wrong_time_series)

        bc_name = "bc_2"
        bc = local_study.create_binding_constraint(name=bc_name)
        # Ensures edition fails
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                f"Wrong format for bindingconstraints/{bc_name}/bc_hourly matrix, expected shape is (8784, Any) and was : (3, 1)"
            ),
        ):
            bc.set_equal_term(wrong_time_series)

    def test_get_constraint_matrix(self, local_study: Study) -> None:
        # Given
        expected_time_series = pd.DataFrame(np.random.randint(0, 100, [366 * 24, 1]), dtype=np.int64)
        bc_name = "test time series"
        local_study.create_binding_constraint(
            name=bc_name,
            properties=BindingConstraintProperties(
                operator=BindingConstraintOperator.GREATER, time_step=BindingConstraintFrequency.HOURLY
            ),
            greater_term_matrix=expected_time_series,
        )

        # When
        actual_time_series = local_study.get_binding_constraints()[bc_name].get_greater_term_matrix()

        # Then
        assert actual_time_series.equals(expected_time_series)

    def test_study_delete(self, local_study: Study) -> None:
        study_path = Path(local_study.path)
        assert study_path.exists()
        local_study.delete()
        assert not study_path.exists()

    def test_variant_local(self, local_study: Study) -> None:
        with pytest.raises(
            ValueError, match=re.escape("The variant creation should only be used for API studies not for local ones")
        ):
            local_study.create_variant("test")
