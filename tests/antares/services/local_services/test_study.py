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

import logging
import os
import time
import typing as t

from configparser import ConfigParser
from pathlib import Path

import numpy as np
import pandas as pd

from antares.config.local_configuration import LocalConfiguration
from antares.exceptions.exceptions import (
    AreaCreationError,
    BindingConstraintCreationError,
    CustomError,
    LinkCreationError,
)
from antares.model.area import AreaProperties, AreaPropertiesLocal, AreaUi, AreaUiLocal
from antares.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    BindingConstraintPropertiesLocal,
    ConstraintTerm,
)
from antares.model.commons import FilterOption
from antares.model.hydro import Hydro
from antares.model.link import (
    AssetType,
    Link,
    LinkProperties,
    LinkPropertiesLocal,
    LinkStyle,
    LinkUi,
    LinkUiLocal,
    TransmissionCapacities,
)
from antares.model.settings.adequacy_patch import (
    DefaultAdequacyPatchParameters,
    PriceTakingOrder,
)
from antares.model.settings.advanced_parameters import (
    AdvancedParametersLocal,
    HydroHeuristicPolicy,
    HydroPricingMode,
    InitialReservoirLevel,
    PowerFluctuation,
    RenewableGenerationModeling,
    SheddingPolicy,
    SimulationCore,
    UnitCommitmentMode,
)
from antares.model.settings.general import (
    BuildingMode,
    GeneralParametersLocal,
    Mode,
    Month,
    WeekDay,
)
from antares.model.settings.optimization import (
    ExportMPS,
    OptimizationParametersLocal,
    OptimizationTransmissionCapacities,
    SimplexOptimizationRange,
    UnfeasibleProblemBehavior,
)
from antares.model.settings.playlist_parameters import PlaylistData, PlaylistParameters
from antares.model.settings.study_settings import DefaultStudySettings, StudySettingsLocal
from antares.model.settings.thematic_trimming import DefaultThematicTrimmingParameters, ThematicTrimmingParametersLocal
from antares.model.study import create_study_local
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
        create_study_local(study_name, version, str(tmp_path.absolute()))

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
        create_study_local(study_name, version, str(tmp_path.absolute()))
        with open(expected_study_antares_path, "r") as file:
            actual_content = file.read()

        # Then
        assert actual_content == antares_content

    def test_verify_study_already_exists_error(self, tmp_path):
        # Given
        study_name = "studyTest"
        version = "850"
        (tmp_path / study_name).mkdir(parents=True, exist_ok=True)

        # When
        with pytest.raises(FileExistsError, match=f"Study {study_name} already exists"):
            create_study_local(study_name, version, str(tmp_path.absolute()))

    def test_all_correlation_ini_files_exists(self, local_study):
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
        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        for folder in ["hydro", "load", "solar", "wind"]:
            ini_path = study_path / "input" / folder / "prepro" / "correlation.ini"
            assert ini_path.exists()
            assert ini_path.is_file()

            ini_content = ini_path.read_text(encoding="utf-8")
            assert ini_content == expected_ini_content


class TestStudyProperties:
    def test_local_study_has_settings(self, local_study):
        # When
        local_study_settings = local_study.get_settings()
        # Then
        assert local_study.get_settings()
        assert isinstance(local_study_settings, DefaultStudySettings)

    def test_local_study_has_correct_default_general_properties(self, local_study):
        # Given
        # https://antares-simulator.readthedocs.io/en/latest/user-guide/solver/04-parameters/
        expected_general_properties = GeneralParametersLocal.model_validate(
            {
                "mode": Mode.ECONOMY,
                "horizon": "",
                "nb_years": 1,
                "first_day": 1,
                "last_day": 365,
                "first_january": WeekDay.MONDAY,
                "first_month": Month.JANUARY,
                "first_week_day": WeekDay.MONDAY,
                "leap_year": False,
                "year_by_year": False,
                "building_mode": BuildingMode.AUTOMATIC,
                "selection_mode": False,
                "thematic_trimming": False,
                "geographic_trimming": False,
                "active_rules_scenario": "default ruleset",
                "read_only": False,
                "simulation_synthesis": True,
                "mc_scenario": False,
            }
        )
        # When
        expected_study_settings = StudySettingsLocal(general_properties=expected_general_properties)

        # Then
        assert local_study.get_settings().general_parameters == expected_general_properties
        assert local_study.get_settings() == expected_study_settings

    def test_local_study_has_correct_default_adequacy_patch_properties(self, local_study):
        # Given
        expected_adequacy_patch_properties = DefaultAdequacyPatchParameters.model_validate(
            {
                "enable_adequacy_patch": False,
                "ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch": True,
                "ntc_between_physical_areas_out_adequacy_patch": True,
                "price_taking_order": PriceTakingOrder.DENS,
                "include_hurdle_cost_csr": False,
                "check_csr_cost_function": False,
                "enable_first_step": False,
                "threshold_initiate_curtailment_sharing_rule": 0,
                "threshold_display_local_matching_rule_violations": 0,
                "threshold_csr_variable_bounds_relaxation": 3,
            }
        )
        expected_study_settings = StudySettingsLocal(
            adequacy_patch_properties=DefaultAdequacyPatchParameters.model_validate(
                expected_adequacy_patch_properties.model_dump(exclude_none=True)
            )
        )

        # When
        actual_adequacy_patch_properties = DefaultAdequacyPatchParameters.model_validate(
            local_study.get_settings().adequacy_patch_parameters.model_dump(exclude_none=True)
        )
        actual_study_settings = StudySettingsLocal.model_validate(
            local_study.get_settings().model_dump(exclude_none=True)
        )

        # Then
        assert actual_adequacy_patch_properties == expected_adequacy_patch_properties
        assert actual_study_settings == expected_study_settings

    def test_local_study_has_correct_advanced_parameters(self, local_study):
        # Given
        expected_advanced_parameters = AdvancedParametersLocal.model_validate(
            {
                "accuracy_on_correlation": "",
                "initial_reservoir_levels": InitialReservoirLevel.COLD_START,
                "hydro_heuristic_policy": HydroHeuristicPolicy.ACCOMMODATE_RULES_CURVES,
                "hydro_pricing_mode": HydroPricingMode.FAST,
                "power_fluctuations": PowerFluctuation.FREE_MODULATIONS,
                "shedding_policy": SheddingPolicy.SHAVE_PEAKS,
                "unit_commitment_mode": UnitCommitmentMode.FAST,
                "number_of_cores_mode": SimulationCore.MEDIUM,
                "renewable_generation_modelling": RenewableGenerationModeling.AGGREGATED,
                "seed_tsgen_wind": 5489,
                "seed_tsgen_load": 1005489,
                "seed_tsgen_hydro": 2005489,
                "seed_tsgen_thermal": 3005489,
                "seed_tsgen_solar": 4005489,
                "seed_tsnumbers": 5005489,
                "seed_unsupplied_energy_costs": 6005489,
                "seed_spilled_energy_costs": 7005489,
                "seed_thermal_costs": 8005489,
                "seed_hydro_costs": 9005489,
                "seed_initial_reservoir_levels": 10005489,
            }
        )
        expected_study_settings = StudySettingsLocal(advanced_parameters=expected_advanced_parameters)

        # When
        actual_advanced_parameters = AdvancedParametersLocal.model_validate(
            local_study.get_settings().advanced_parameters.model_dump(exclude_none=True)
        )
        actual_study_settings = StudySettingsLocal.model_validate(
            local_study.get_settings().model_dump(exclude_none=True)
        )

        # Then
        assert actual_advanced_parameters == expected_advanced_parameters
        assert actual_study_settings == expected_study_settings

    def test_local_study_has_correct_optimization_parameters(self, local_study):
        # Given
        expected_optimization_parameters = OptimizationParametersLocal.model_validate(
            {
                "simplex_optimization_range": SimplexOptimizationRange.WEEK,
                "transmission_capacities": OptimizationTransmissionCapacities.LOCAL_VALUES,
                "binding_constraints": True,
                "hurdle_costs": True,
                "thermal_clusters_min_stable_power": True,
                "thermal_clusters_min_ud_time": True,
                "day_ahead_reserve": True,
                "strategic_reserve": True,
                "spinning_reserve": True,
                "primary_reserve": True,
                "export_mps": ExportMPS.NONE,
                "include_exportstructure": False,
                "unfeasible_problem_behavior": UnfeasibleProblemBehavior.ERROR_VERBOSE,
            }
        )
        expected_study_settings = StudySettingsLocal(optimization_parameters=expected_optimization_parameters)

        # When
        actual_optimization_parameters = OptimizationParametersLocal.model_validate(
            local_study.get_settings().optimization_parameters.model_dump(exclude_none=True)
        )
        actual_study_settings = StudySettingsLocal.model_validate(
            local_study.get_settings().model_dump(exclude_none=True)
        )

        # Then
        assert actual_optimization_parameters == expected_optimization_parameters
        assert actual_study_settings == expected_study_settings

    def test_local_study_with_playlist_has_correct_defaults(self, tmp_path):
        # Given
        nb_years = 2
        playlist_study = create_study_local(
            "test_study",
            "880",
            str(tmp_path.absolute()),
            StudySettingsLocal(
                general_parameters=GeneralParametersLocal(nb_years=nb_years, selection_mode=True),
                playlist_parameters=PlaylistParameters(playlist=[PlaylistData()] * nb_years),
            ),
        )

        # When
        expected_playlist_parameters_dict = {1: {"status": True, "weight": 1.0}, 2: {"status": True, "weight": 1.0}}
        expected_playlist_parameters = PlaylistParameters(playlist=expected_playlist_parameters_dict)

        actual_playlist_parameters_dict = playlist_study.get_settings().playlist_parameters.model_dump()
        actual_playlist_parameters = playlist_study.get_settings().playlist_parameters

        # Then
        assert actual_playlist_parameters_dict == expected_playlist_parameters_dict
        assert actual_playlist_parameters == expected_playlist_parameters

    def test_local_study_has_correct_thematic_trimming_parameters(self, tmp_path):
        # Given
        expected_thematic_trimming_parameters = ThematicTrimmingParametersLocal.model_validate(
            {
                "ov_cost": True,
                "op_cost": True,
                "mrg_price": True,
                "co2_emis": True,
                "dtg_by_plant": True,
                "balance": True,
                "row_bal": True,
                "psp": True,
                "misc_ndg": True,
                "load": True,
                "h_ror": True,
                "wind": True,
                "solar": True,
                "nuclear": True,
                "lignite": True,
                "coal": True,
                "gas": True,
                "oil": True,
                "mix_fuel": True,
                "misc_dtg": True,
                "h_stor": True,
                "h_pump": True,
                "h_lev": True,
                "h_infl": True,
                "h_ovfl": True,
                "h_val": True,
                "h_cost": True,
                "unsp_enrg": True,
                "spil_enrg": True,
                "lold": True,
                "lolp": True,
                "avl_dtg": True,
                "dtg_mrg": True,
                "max_mrg": True,
                "np_cost": True,
                "np_cost_by_plant": True,
                "nodu": True,
                "nodu_by_plant": True,
                "flow_lin": True,
                "ucap_lin": True,
                "loop_flow": True,
                "flow_quad": True,
                "cong_fee_alg": True,
                "cong_fee_abs": True,
                "marg_cost": True,
                "cong_prob_plus": True,
                "cong_prob_minus": True,
                "hurdle_cost": True,
                "res_generation_by_plant": True,
                "misc_dtg_2": True,
                "misc_dtg_3": True,
                "misc_dtg_4": True,
                "wind_offshore": True,
                "wind_onshore": True,
                "solar_concrt": True,
                "solar_pv": True,
                "solar_rooft": True,
                "renw_1": True,
                "renw_2": True,
                "renw_3": True,
                "renw_4": True,
                "dens": True,
                "profit_by_plant": True,
                "sts_inj_by_plant": True,
                "sts_withdrawal_by_plant": True,
                "sts_lvl_by_plant": True,
                "psp_open_injection": True,
                "psp_open_withdrawal": True,
                "psp_open_level": True,
                "psp_closed_injection": True,
                "psp_closed_withdrawal": True,
                "psp_closed_level": True,
                "pondage_injection": True,
                "pondage_withdrawal": True,
                "pondage_level": True,
                "battery_injection": True,
                "battery_withdrawal": True,
                "battery_level": True,
                "other1_injection": True,
                "other1_withdrawal": True,
                "other1_level": True,
                "other2_injection": True,
                "other2_withdrawal": True,
                "other2_level": True,
                "other3_injection": True,
                "other3_withdrawal": True,
                "other3_level": True,
                "other4_injection": True,
                "other4_withdrawal": True,
                "other4_level": True,
                "other5_injection": True,
                "other5_withdrawal": True,
                "other5_level": True,
                "sts_cashflow_by_cluster": True,
            }
        )
        expected_study_settings = StudySettingsLocal(
            general_parameters=GeneralParametersLocal(thematic_trimming=True),
            thematic_trimming_parameters=expected_thematic_trimming_parameters,
        )
        thematic_trimming_study = create_study_local(
            "test_study",
            "880",
            str(tmp_path.absolute()),
            StudySettingsLocal(
                general_parameters=GeneralParametersLocal(thematic_trimming=True),
                thematic_trimming_parameters=ThematicTrimmingParametersLocal(),
            ),
        )

        # When
        actual_thematic_trimming_parameters = DefaultThematicTrimmingParameters.model_validate(
            thematic_trimming_study.get_settings().thematic_trimming_parameters
        )
        actual_study_settings = DefaultStudySettings.model_validate(thematic_trimming_study.get_settings())

        # Then
        assert actual_thematic_trimming_parameters == expected_thematic_trimming_parameters
        assert actual_study_settings == expected_study_settings

    def test_generaldata_ini_exists(self, local_study):
        # Given
        expected_file = local_study.service.config.study_path / "settings/generaldata.ini"

        # Then
        assert expected_file.is_file()

    def test_generaldata_ini_has_correct_default_values(self, local_study):
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
leapyear = false
year-by-year = false
derated = false
custom-scenario = false
user-playlist = false
thematic-trimming = false
geographic-trimming = false
generate = 
nbtimeseriesload = 1
nbtimeserieshydro = 1
nbtimeseriesthermal = 1
nbtimeserieswind = 1
nbtimeseriessolar = 1
refreshtimeseries = 
intra-modal = 
inter-modal = 
refreshintervalload = 100
refreshintervalhydro = 100
refreshintervalthermal = 100
refreshintervalwind = 100
refreshintervalsolar = 100
readonly = false

[input]
import = 

[output]
synthesis = true
storenewset = false
archives = 
result-format = txt-files

[optimization]
simplex-range = week
transmission-capacities = local-values
include-constraints = true
include-hurdlecosts = true
include-tc-minstablepower = true
include-tc-min-ud-time = true
include-dayahead = true
include-strategicreserve = true
include-spinningreserve = true
include-primaryreserve = true
include-exportmps = none
include-exportstructure = false
include-unfeasible-problem-behavior = error-verbose

[adequacy patch]
include-adq-patch = false
set-to-null-ntc-from-physical-out-to-physical-in-for-first-step = true
set-to-null-ntc-between-physical-out-for-first-step = true
enable-first-step = false
price-taking-order = DENS
include-hurdle-cost-csr = false
check-csr-cost-function = false
threshold-initiate-curtailment-sharing-rule = 0.000000
threshold-display-local-matching-rule-violations = 0.000000
threshold-csr-variable-bounds-relaxation = 3

[other preferences]
initial-reservoir-levels = cold start
hydro-heuristic-policy = accommodate rule curves
hydro-pricing-mode = fast
power-fluctuations = free modulations
shedding-policy = shave peaks
unit-commitment-mode = fast
number-of-cores-mode = medium
renewable-generation-modelling = aggregated

[advanced parameters]
accuracy-on-correlation = 

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
        actual_generaldata_ini_file = local_study.service.config.study_path / IniFileTypes.GENERAL.value
        actual_file_content = actual_generaldata_ini_file.read_text()

        # Then
        assert actual_file_content == expected_file_content

    def test_generaldata_ini_with_thematic_trimming_has_negative_sign(self, tmp_path):
        # Given
        study_name = "test study"
        study_version = "880"
        general_parameters = GeneralParametersLocal(thematic_trimming=True)
        thematic_trimming_parameters = ThematicTrimmingParametersLocal(op_cost=False)
        study_path = str(tmp_path.absolute())
        expected_file_content = """[general]
mode = Economy
horizon = 
nbyears = 1
simulation.start = 1
simulation.end = 365
january.1st = Monday
first-month-in-year = January
first.weekday = Monday
leapyear = false
year-by-year = false
derated = false
custom-scenario = false
user-playlist = false
thematic-trimming = true
geographic-trimming = false
generate = 
nbtimeseriesload = 1
nbtimeserieshydro = 1
nbtimeseriesthermal = 1
nbtimeserieswind = 1
nbtimeseriessolar = 1
refreshtimeseries = 
intra-modal = 
inter-modal = 
refreshintervalload = 100
refreshintervalhydro = 100
refreshintervalthermal = 100
refreshintervalwind = 100
refreshintervalsolar = 100
readonly = false

[input]
import = 

[output]
synthesis = true
storenewset = false
archives = 
result-format = txt-files

[optimization]
simplex-range = week
transmission-capacities = local-values
include-constraints = true
include-hurdlecosts = true
include-tc-minstablepower = true
include-tc-min-ud-time = true
include-dayahead = true
include-strategicreserve = true
include-spinningreserve = true
include-primaryreserve = true
include-exportmps = none
include-exportstructure = false
include-unfeasible-problem-behavior = error-verbose

[adequacy patch]
include-adq-patch = false
set-to-null-ntc-from-physical-out-to-physical-in-for-first-step = true
set-to-null-ntc-between-physical-out-for-first-step = true
enable-first-step = false
price-taking-order = DENS
include-hurdle-cost-csr = false
check-csr-cost-function = false
threshold-initiate-curtailment-sharing-rule = 0.000000
threshold-display-local-matching-rule-violations = 0.000000
threshold-csr-variable-bounds-relaxation = 3

[other preferences]
initial-reservoir-levels = cold start
hydro-heuristic-policy = accommodate rule curves
hydro-pricing-mode = fast
power-fluctuations = free modulations
shedding-policy = shave peaks
unit-commitment-mode = fast
number-of-cores-mode = medium
renewable-generation-modelling = aggregated

[advanced parameters]
accuracy-on-correlation = 

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

[variables selection]
selected_vars_reset = true
select_var - = OP. COST

"""

        # When
        new_study = create_study_local(
            study_name,
            study_version,
            study_path,
            StudySettingsLocal(
                general_parameters=general_parameters, thematic_trimming_parameters=thematic_trimming_parameters
            ),
        )
        actual_generaldata_ini_file = new_study.service.config.study_path / IniFileTypes.GENERAL.value
        actual_file_content = actual_generaldata_ini_file.read_text()

        # Then
        assert actual_file_content == expected_file_content

    def test_generaldata_ini_with_thematic_trimming_has_positive_sign(self, tmp_path):
        # Given
        study_name = "test study"
        study_version = "880"
        general_parameters = GeneralParametersLocal(thematic_trimming=True)
        thematic_trimming_parameters = ThematicTrimmingParametersLocal(op_cost=False)
        thematic_trimming_parameters = {
            key: not value for key, value in thematic_trimming_parameters.model_dump().items()
        }
        study_path = str(tmp_path.absolute())
        expected_file_content = """[general]
mode = Economy
horizon = 
nbyears = 1
simulation.start = 1
simulation.end = 365
january.1st = Monday
first-month-in-year = January
first.weekday = Monday
leapyear = false
year-by-year = false
derated = false
custom-scenario = false
user-playlist = false
thematic-trimming = true
geographic-trimming = false
generate = 
nbtimeseriesload = 1
nbtimeserieshydro = 1
nbtimeseriesthermal = 1
nbtimeserieswind = 1
nbtimeseriessolar = 1
refreshtimeseries = 
intra-modal = 
inter-modal = 
refreshintervalload = 100
refreshintervalhydro = 100
refreshintervalthermal = 100
refreshintervalwind = 100
refreshintervalsolar = 100
readonly = false

[input]
import = 

[output]
synthesis = true
storenewset = false
archives = 
result-format = txt-files

[optimization]
simplex-range = week
transmission-capacities = local-values
include-constraints = true
include-hurdlecosts = true
include-tc-minstablepower = true
include-tc-min-ud-time = true
include-dayahead = true
include-strategicreserve = true
include-spinningreserve = true
include-primaryreserve = true
include-exportmps = none
include-exportstructure = false
include-unfeasible-problem-behavior = error-verbose

[adequacy patch]
include-adq-patch = false
set-to-null-ntc-from-physical-out-to-physical-in-for-first-step = true
set-to-null-ntc-between-physical-out-for-first-step = true
enable-first-step = false
price-taking-order = DENS
include-hurdle-cost-csr = false
check-csr-cost-function = false
threshold-initiate-curtailment-sharing-rule = 0.000000
threshold-display-local-matching-rule-violations = 0.000000
threshold-csr-variable-bounds-relaxation = 3

[other preferences]
initial-reservoir-levels = cold start
hydro-heuristic-policy = accommodate rule curves
hydro-pricing-mode = fast
power-fluctuations = free modulations
shedding-policy = shave peaks
unit-commitment-mode = fast
number-of-cores-mode = medium
renewable-generation-modelling = aggregated

[advanced parameters]
accuracy-on-correlation = 

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

[variables selection]
selected_vars_reset = false
select_var + = OP. COST

"""

        # When
        new_study = create_study_local(
            study_name,
            study_version,
            study_path,
            StudySettingsLocal(
                general_parameters=general_parameters, thematic_trimming_parameters=thematic_trimming_parameters
            ),
        )
        actual_generaldata_ini_file = new_study.service.config.study_path / IniFileTypes.GENERAL.value
        actual_file_content = actual_generaldata_ini_file.read_text()

        # Then
        assert actual_file_content == expected_file_content

    def test_generaldata_ini_with_thematic_trimming_two_variables(self, tmp_path):
        # Given
        study_name = "test study"
        study_version = "880"
        general_parameters = GeneralParametersLocal(thematic_trimming=True)
        thematic_trimming_parameters = ThematicTrimmingParametersLocal(op_cost=False, ov_cost=False)
        # Invert selection
        thematic_trimming_parameters = {
            key: not value for key, value in thematic_trimming_parameters.model_dump().items()
        }

        study_path = str(tmp_path.absolute())
        expected_file_content = """[general]
mode = Economy
horizon = 
nbyears = 1
simulation.start = 1
simulation.end = 365
january.1st = Monday
first-month-in-year = January
first.weekday = Monday
leapyear = false
year-by-year = false
derated = false
custom-scenario = false
user-playlist = false
thematic-trimming = true
geographic-trimming = false
generate = 
nbtimeseriesload = 1
nbtimeserieshydro = 1
nbtimeseriesthermal = 1
nbtimeserieswind = 1
nbtimeseriessolar = 1
refreshtimeseries = 
intra-modal = 
inter-modal = 
refreshintervalload = 100
refreshintervalhydro = 100
refreshintervalthermal = 100
refreshintervalwind = 100
refreshintervalsolar = 100
readonly = false

[input]
import = 

[output]
synthesis = true
storenewset = false
archives = 
result-format = txt-files

[optimization]
simplex-range = week
transmission-capacities = local-values
include-constraints = true
include-hurdlecosts = true
include-tc-minstablepower = true
include-tc-min-ud-time = true
include-dayahead = true
include-strategicreserve = true
include-spinningreserve = true
include-primaryreserve = true
include-exportmps = none
include-exportstructure = false
include-unfeasible-problem-behavior = error-verbose

[adequacy patch]
include-adq-patch = false
set-to-null-ntc-from-physical-out-to-physical-in-for-first-step = true
set-to-null-ntc-between-physical-out-for-first-step = true
enable-first-step = false
price-taking-order = DENS
include-hurdle-cost-csr = false
check-csr-cost-function = false
threshold-initiate-curtailment-sharing-rule = 0.000000
threshold-display-local-matching-rule-violations = 0.000000
threshold-csr-variable-bounds-relaxation = 3

[other preferences]
initial-reservoir-levels = cold start
hydro-heuristic-policy = accommodate rule curves
hydro-pricing-mode = fast
power-fluctuations = free modulations
shedding-policy = shave peaks
unit-commitment-mode = fast
number-of-cores-mode = medium
renewable-generation-modelling = aggregated

[advanced parameters]
accuracy-on-correlation = 

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

[variables selection]
selected_vars_reset = false
"""

        expected_file_content += "select_var + = OV. COST\nselect_var + = OP. COST\n\n"

        # When
        new_study = create_study_local(
            study_name,
            study_version,
            study_path,
            StudySettingsLocal(
                general_parameters=general_parameters, thematic_trimming_parameters=thematic_trimming_parameters
            ),
        )

        actual_generaldata_ini_file_path = new_study.service.config.study_path / IniFileTypes.GENERAL.value
        actual_file_content = actual_generaldata_ini_file_path.read_text()

        # Then
        assert actual_file_content == expected_file_content

    def test_generaldata_ini_with_playlist_has_negative_sign(self, tmp_path):
        # Given
        study_name = "test study"
        study_version = "880"
        general_parameters = GeneralParametersLocal(selection_mode=True, thematic_trimming=True)
        playlist_parameters = PlaylistParameters(playlist=[PlaylistData(), PlaylistData(), PlaylistData(status=False)])
        thematic_trimming_parameters = ThematicTrimmingParametersLocal(op_cost=False)
        thematic_trimming_parameters = ThematicTrimmingParametersLocal.model_validate(
            {key: not value for key, value in thematic_trimming_parameters.model_dump().items()}
        )
        study_path = str(tmp_path.absolute())
        expected_file_content = """[general]
mode = Economy
horizon = 
nbyears = 1
simulation.start = 1
simulation.end = 365
january.1st = Monday
first-month-in-year = January
first.weekday = Monday
leapyear = false
year-by-year = false
derated = false
custom-scenario = false
user-playlist = true
thematic-trimming = true
geographic-trimming = false
generate = 
nbtimeseriesload = 1
nbtimeserieshydro = 1
nbtimeseriesthermal = 1
nbtimeserieswind = 1
nbtimeseriessolar = 1
refreshtimeseries = 
intra-modal = 
inter-modal = 
refreshintervalload = 100
refreshintervalhydro = 100
refreshintervalthermal = 100
refreshintervalwind = 100
refreshintervalsolar = 100
readonly = false

[input]
import = 

[output]
synthesis = true
storenewset = false
archives = 
result-format = txt-files

[optimization]
simplex-range = week
transmission-capacities = local-values
include-constraints = true
include-hurdlecosts = true
include-tc-minstablepower = true
include-tc-min-ud-time = true
include-dayahead = true
include-strategicreserve = true
include-spinningreserve = true
include-primaryreserve = true
include-exportmps = none
include-exportstructure = false
include-unfeasible-problem-behavior = error-verbose

[adequacy patch]
include-adq-patch = false
set-to-null-ntc-from-physical-out-to-physical-in-for-first-step = true
set-to-null-ntc-between-physical-out-for-first-step = true
enable-first-step = false
price-taking-order = DENS
include-hurdle-cost-csr = false
check-csr-cost-function = false
threshold-initiate-curtailment-sharing-rule = 0.000000
threshold-display-local-matching-rule-violations = 0.000000
threshold-csr-variable-bounds-relaxation = 3

[other preferences]
initial-reservoir-levels = cold start
hydro-heuristic-policy = accommodate rule curves
hydro-pricing-mode = fast
power-fluctuations = free modulations
shedding-policy = shave peaks
unit-commitment-mode = fast
number-of-cores-mode = medium
renewable-generation-modelling = aggregated

[advanced parameters]
accuracy-on-correlation = 

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

[playlist]
playlist_reset = true
playlist_year - = 2

[variables selection]
selected_vars_reset = false
select_var + = OP. COST

"""

        # When
        new_study = create_study_local(
            study_name,
            study_version,
            study_path,
            StudySettingsLocal(
                general_parameters=general_parameters,
                playlist_parameters=playlist_parameters,
                thematic_trimming_parameters=thematic_trimming_parameters,
            ),
        )

        actual_general_parameters_file_path = new_study.service.config.study_path / IniFileTypes.GENERAL.value
        actual_file_content = actual_general_parameters_file_path.read_text()

        # Then
        assert actual_file_content == expected_file_content

    def test_generaldata_ini_with_playlist_has_positive_sign(self, tmp_path):
        # Given
        study_name = "test study"
        study_version = "880"
        general_parameters = GeneralParametersLocal(selection_mode=True, thematic_trimming=True)
        playlist_parameters = PlaylistParameters(
            playlist=[PlaylistData(status=False), PlaylistData(status=False), PlaylistData()]
        )
        thematic_trimming_parameters = ThematicTrimmingParametersLocal(op_cost=False)
        thematic_trimming_parameters = ThematicTrimmingParametersLocal.model_validate(
            {key: not value for key, value in thematic_trimming_parameters.model_dump().items()}
        )
        study_path = str(tmp_path.absolute())
        expected_file_content = """[general]
mode = Economy
horizon = 
nbyears = 1
simulation.start = 1
simulation.end = 365
january.1st = Monday
first-month-in-year = January
first.weekday = Monday
leapyear = false
year-by-year = false
derated = false
custom-scenario = false
user-playlist = true
thematic-trimming = true
geographic-trimming = false
generate = 
nbtimeseriesload = 1
nbtimeserieshydro = 1
nbtimeseriesthermal = 1
nbtimeserieswind = 1
nbtimeseriessolar = 1
refreshtimeseries = 
intra-modal = 
inter-modal = 
refreshintervalload = 100
refreshintervalhydro = 100
refreshintervalthermal = 100
refreshintervalwind = 100
refreshintervalsolar = 100
readonly = false

[input]
import = 

[output]
synthesis = true
storenewset = false
archives = 
result-format = txt-files

[optimization]
simplex-range = week
transmission-capacities = local-values
include-constraints = true
include-hurdlecosts = true
include-tc-minstablepower = true
include-tc-min-ud-time = true
include-dayahead = true
include-strategicreserve = true
include-spinningreserve = true
include-primaryreserve = true
include-exportmps = none
include-exportstructure = false
include-unfeasible-problem-behavior = error-verbose

[adequacy patch]
include-adq-patch = false
set-to-null-ntc-from-physical-out-to-physical-in-for-first-step = true
set-to-null-ntc-between-physical-out-for-first-step = true
enable-first-step = false
price-taking-order = DENS
include-hurdle-cost-csr = false
check-csr-cost-function = false
threshold-initiate-curtailment-sharing-rule = 0.000000
threshold-display-local-matching-rule-violations = 0.000000
threshold-csr-variable-bounds-relaxation = 3

[other preferences]
initial-reservoir-levels = cold start
hydro-heuristic-policy = accommodate rule curves
hydro-pricing-mode = fast
power-fluctuations = free modulations
shedding-policy = shave peaks
unit-commitment-mode = fast
number-of-cores-mode = medium
renewable-generation-modelling = aggregated

[advanced parameters]
accuracy-on-correlation = 

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

[playlist]
playlist_reset = false
playlist_year + = 2

[variables selection]
selected_vars_reset = false
select_var + = OP. COST

"""

        # When
        new_study = create_study_local(
            study_name,
            study_version,
            study_path,
            StudySettingsLocal(
                general_parameters=general_parameters,
                playlist_parameters=playlist_parameters,
                thematic_trimming_parameters=thematic_trimming_parameters,
            ),
        )

        actual_general_ini_file_path = new_study.service.config.study_path / IniFileTypes.GENERAL.value
        actual_file_content = actual_general_ini_file_path.read_text()

        # Then
        assert actual_file_content == expected_file_content


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

    def test_create_area_with_custom_error(self, monkeypatch, local_study):
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

    def test_creating_duplicate_area_name_errors(self, local_study_w_areas):
        # Given
        area_to_create = "fr"

        # Then
        with pytest.raises(
            AreaCreationError,
            match=f"Could not create the area {area_to_create}: There is already an area '{area_to_create}' in the study '{local_study_w_areas.name}'",
        ):
            local_study_w_areas.create_area(area_to_create)

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
            area_from=area_from,
            area_to=area_to,
        )

        assert isinstance(link_created, Link)

    def test_unknown_area_errors(self, tmp_path, local_study_w_areas):
        # Given
        link_to_create = "es_fr"

        # When
        area_from, area_to = link_to_create.split("_")
        area_from = area_from
        area_to = area_to

        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link {area_from} / {area_to}: {area_from} does not exist",
        ):
            local_study_w_areas.create_link(area_from=area_from, area_to=area_to)

    def test_create_link_alphabetically(self, tmp_path, local_study):
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

        assert link_created.area_from == "at"
        assert link_created.area_to == "fr"

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
            area_from="fr",
            area_to="it",
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
        link_created = local_study_w_areas.create_link(area_from="fr", area_to="it", properties=link_properties)
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
            local_study_w_areas.create_link(area_from=area_from, area_to=area_to)

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
            LinkCreationError,
            match=f"Could not create the link {area_from} / {area_to}: A link from {area_from} to {area_to} already exists",
        ):
            local_study_w_links.create_link(
                area_from=area_from,
                area_to=area_to,
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
        local_study_w_areas.create_link(area_from=area_from, area_to=area_to)
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

    def test_duplicate_name_errors(self, local_study_with_constraint):
        # Given
        binding_constraint_name = "test constraint"

        # Then
        with pytest.raises(
            BindingConstraintCreationError,
            match=f"Could not create the binding constraint {binding_constraint_name}: A binding constraint with the name {binding_constraint_name} already exists.",
        ):
            local_study_with_constraint.create_binding_constraint(name=binding_constraint_name)

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

    def test_binding_constraints_have_correct_default_time_series(self, test_constraint, local_study_with_constraint):
        # Given
        expected_time_series_hourly = pd.DataFrame(np.zeros([365 * 24 + 24, 1]))
        expected_time_series_daily_weekly = pd.DataFrame(np.zeros([365 + 1, 1]))
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
        local_config = t.cast(LocalConfiguration, local_study_with_constraint.service.config)
        study_path = local_config.study_path

        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / "test greater_gt.txt")
        actual_time_series_greater = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=float)
        assert actual_time_series_greater.equals(expected_time_series_daily_weekly)

        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / "test equal_eq.txt")
        actual_time_series_equal = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=float)
        assert actual_time_series_equal.equals(expected_time_series_daily_weekly)

        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / f"{test_constraint.id}_lt.txt")
        actual_time_series_pre_created = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=float)
        assert actual_time_series_pre_created.equals(expected_time_series_hourly)

        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / "test both_lt.txt")
        actual_time_series_both_lesser = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=float)
        assert actual_time_series_both_lesser.equals(expected_time_series_hourly)

        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / "test both_gt.txt")
        actual_time_series_both_greater = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=float)
        assert actual_time_series_both_greater.equals(expected_time_series_hourly)

    def test_submitted_time_series_is_saved(self, local_study):
        # Given
        expected_time_series = pd.DataFrame(np.ones([3, 1]))
        bc_name = "test time series"
        local_study.create_binding_constraint(
            name=bc_name,
            properties=BindingConstraintProperties(
                operator=BindingConstraintOperator.GREATER, time_step=BindingConstraintFrequency.HOURLY
            ),
            greater_term_matrix=expected_time_series,
        )

        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        actual_file_path = study_path.joinpath(Path("input") / "bindingconstraints" / f"{bc_name}_gt.txt")
        actual_time_series = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=float)

        # Then
        assert actual_time_series.equals(expected_time_series)

    def test_updating_binding_constraint_properties_updates_local(self, local_study_with_constraint, test_constraint):
        # Given
        new_properties = BindingConstraintProperties(comments="testing update")
        local_property_args = {
            "constraint_name": test_constraint.name,
            "constraint_id": test_constraint.id,
            "terms": test_constraint._terms,
            **new_properties.model_dump(mode="json", exclude_none=True),
        }

        # When
        test_constraint.properties = new_properties

        # Then
        assert test_constraint.local_properties == BindingConstraintPropertiesLocal.model_validate(local_property_args)
