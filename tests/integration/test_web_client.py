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
# ruff: noqa: F405
import pytest

import shutil
import zipfile

from pathlib import Path, PurePath
from typing import Generator

import numpy as np
import pandas as pd

from antares.craft import *  # noqa: F403
from antares.craft.exceptions.exceptions import (
    BindingConstraintCreationError,
    ConstraintMatrixUpdateError,
    InvalidRequestForScenarioBuilder,
    MatrixUploadError,
    ReferencedObjectDeletionNotAllowed,
    XpansionFileDeletionError,
    XpansionMatrixReadingError,
)
from antares.craft.model.output import XpansionResult, XpansionSensitivityResult
from antares.craft.model.settings.adequacy_patch import AdequacyPatchParameters
from antares.craft.model.settings.advanced_parameters import AdvancedParameters
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.simulation import Job, JobStatus
from tests.integration.antares_web_desktop import AntaresWebDesktop

ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.fixture
def antares_web() -> Generator[AntaresWebDesktop, None, None]:
    app = AntaresWebDesktop()
    app.wait_for_server_to_start()
    yield app
    app.kill()


class TestWebClient:
    def test_lifecycle(
        self,
        antares_web: AntaresWebDesktop,
        tmp_path: Path,
        default_thematic_trimming_88: ThematicTrimmingParameters,
        xpansion_input_path: Path,
        xpansion_output_path: Path,
        xpansion_expected_output: XpansionResult,
        xpansion_sensitivity_expected_output: XpansionSensitivityResult,
    ) -> None:
        api_config = APIconf(api_host=antares_web.url, token="", verify=False)
        study = create_study_api("antares-craft-test", "880", api_config)
        # tests area creation with default values
        area_name = "FR"
        area_fr = study.create_area(area_name)
        assert area_fr.name == area_name
        assert area_fr.id == area_name.lower()

        # test upload load matrix
        # Case that fails
        wrong_load_matrix = pd.DataFrame(data=[[0]])
        with pytest.raises(
            MatrixUploadError,
            match=f"Error uploading load matrix for area '{area_fr.id}': Expected 8760 rows and received 1",
        ):
            area_fr.set_load(wrong_load_matrix)

        # Case that succeeds
        load_matrix = pd.DataFrame(data=np.zeros((8760, 1)))
        area_fr.set_load(load_matrix)

        # tests get load matrix
        pd.testing.assert_frame_equal(area_fr.get_load_matrix(), load_matrix, check_dtype=False)

        # asserts solar and wind matrices can be created and read.
        ts_matrix = pd.DataFrame(data=np.ones((8760, 4)))

        area_fr.set_solar(ts_matrix)
        pd.testing.assert_frame_equal(area_fr.get_solar_matrix(), ts_matrix, check_dtype=False)

        area_fr.set_wind(ts_matrix)
        pd.testing.assert_frame_equal(area_fr.get_wind_matrix(), ts_matrix, check_dtype=False)

        # tests area creation with ui values
        area_ui = AreaUi(x=100, color_rgb=[255, 0, 0])
        area_name = "BE?"
        area_be = study.create_area(area_name, ui=area_ui)
        assert area_be.name == area_name
        assert area_be.id == "be"

        assert area_be.ui.x == area_ui.x
        assert area_be.ui.color_rgb == area_ui.color_rgb

        # tests area creation with properties
        properties = AreaProperties(
            energy_cost_spilled=100,
            adequacy_patch_mode=AdequacyPatchMode.INSIDE,
            filter_synthesis={FilterOption.HOURLY, FilterOption.DAILY, FilterOption.HOURLY},
        )
        area_name = "DE"
        area_de = study.create_area(area_name, properties=properties)
        assert area_de.properties.energy_cost_spilled == 100
        assert area_de.properties.adequacy_patch_mode == AdequacyPatchMode.INSIDE
        assert area_de.properties.filter_synthesis == {FilterOption.HOURLY, FilterOption.DAILY}

        # tests link creation with default values
        link_de_fr = study.create_link(area_from=area_de.id, area_to=area_fr.id)
        assert link_de_fr.area_from_id == area_de.id
        assert link_de_fr.area_to_id == area_fr.id
        assert link_de_fr.id == f"{area_de.id} / {area_fr.id}"

        # tests link creation with ui and properties
        link_ui = LinkUi(colorr=44)
        link_properties = LinkProperties(hurdles_cost=True, filter_year_by_year={FilterOption.HOURLY})
        link_be_fr = study.create_link(area_from=area_be.id, area_to=area_fr.id, ui=link_ui, properties=link_properties)
        assert link_be_fr.ui.colorr == 44
        assert link_be_fr.properties.hurdles_cost
        assert link_be_fr.properties.filter_year_by_year == {FilterOption.HOURLY}

        # asserts study contains all links and areas
        assert study.get_areas() == {area_be.id: area_be, area_fr.id: area_fr, area_de.id: area_de}
        assert study.get_links() == {link_be_fr.id: link_be_fr, link_de_fr.id: link_de_fr}

        # test thermal cluster creation with default values
        thermal_name = "Cluster_test %?"
        thermal_fr = area_fr.create_thermal_cluster(thermal_name, ThermalClusterProperties(nominal_capacity=1000))
        assert thermal_fr.name == thermal_name.lower()
        # AntaresWeb has id issues for thermal/renewable clusters,
        # so we force the name in lowercase to avoid issues.
        assert thermal_fr.id == "cluster_test"

        # ===== Test generate thermal timeseries =====
        study.generate_thermal_timeseries(2)
        thermal_timeseries = thermal_fr.get_series_matrix()
        assert isinstance(
            thermal_timeseries,
            pd.DataFrame,
        )
        assert thermal_timeseries.shape == (8760, 2)
        assert (
            (thermal_timeseries == 1000).all().all()
        )  # first all() returns a one column matrix with booleans, second all() checks that they're all true

        # test thermal cluster creation with properties
        thermal_name = "gaz_be"
        thermal_properties = ThermalClusterProperties(efficiency=55, group=ThermalClusterGroup.GAS.value)
        thermal_be = area_be.create_thermal_cluster(thermal_name, thermal_properties)
        assert thermal_be.properties.efficiency == 55
        assert thermal_be.properties.group == "gas"

        # test thermal cluster creation with prepro_modulation matrices
        thermal_name = "matrices_be"
        prepro_modulation_matrix = pd.DataFrame(data=np.ones((8760, 6)))
        modulation_matrix = pd.DataFrame(data=np.ones((8760, 4)))
        series_matrix = pd.DataFrame(data=np.ones((8760, 6)))
        co2_cost_matrix = pd.DataFrame(data=np.ones((8760, 1)))
        fuel_cost_matrix = pd.DataFrame(data=np.ones((8760, 1)))

        # creating parameters and capacities for this link and testing them
        link_be_fr.set_parameters(series_matrix)
        link_be_fr.set_capacity_direct(series_matrix)
        link_be_fr.set_capacity_indirect(series_matrix)

        parameters_matrix = link_be_fr.get_parameters()
        direct_matrix = link_be_fr.get_capacity_direct()
        indirect_matrix = link_be_fr.get_capacity_indirect()
        series_matrix.equals(parameters_matrix)
        series_matrix.equals(direct_matrix)
        series_matrix.equals(indirect_matrix)

        # Case that succeeds
        thermal_value_be = area_fr.create_thermal_cluster(thermal_name=thermal_name, properties=thermal_properties)
        thermal_value_be.set_series(series_matrix)
        thermal_value_be.set_prepro_modulation(modulation_matrix)
        thermal_value_be.set_prepro_data(prepro_modulation_matrix)
        thermal_value_be.set_co2_cost(co2_cost_matrix)
        thermal_value_be.set_fuel_cost(fuel_cost_matrix)

        # Updating multiple thermal clusters properties at once
        thermal_update_1 = ThermalClusterPropertiesUpdate(marginal_cost=10.7, enabled=False, nominal_capacity=9.8)
        thermal_update_2 = ThermalClusterPropertiesUpdate(op1=10.2, spread_cost=60.5, group="nuclear")
        update_for_thermals = {thermal_fr: thermal_update_1, thermal_value_be: thermal_update_2}

        study.update_thermal_clusters(update_for_thermals)

        fr_properties = thermal_fr.properties
        assert fr_properties.marginal_cost == 10.7
        assert not fr_properties.enabled
        assert fr_properties.nominal_capacity == 9.8
        # Ensures properties that weren't updated are still the same as before
        assert fr_properties.law_forced == LawOption.UNIFORM
        assert fr_properties.spread_cost == 0.0
        assert fr_properties.unit_count == 1

        be_value_properties = thermal_value_be.properties
        assert be_value_properties.op1 == 10.2
        assert be_value_properties.spread_cost == 60.5
        assert be_value_properties.group == ThermalClusterGroup.NUCLEAR.value
        assert be_value_properties.op2 == 0.0
        assert be_value_properties.marginal_cost == 0.0
        assert be_value_properties.min_up_time == 1

        # Tests get thermal matrices
        prepro = thermal_value_be.get_prepro_data_matrix()
        modulation = thermal_value_be.get_prepro_modulation_matrix()
        series = thermal_value_be.get_series_matrix()
        co2 = thermal_value_be.get_co2_cost_matrix()
        fuel = thermal_value_be.get_fuel_cost_matrix()

        pd.testing.assert_frame_equal(prepro, prepro_modulation_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(modulation, modulation_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(series, series_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(co2, co2_cost_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(fuel, fuel_cost_matrix, check_dtype=False)

        # test renewable cluster creation with default values
        renewable_name = "cluster_test %?"
        renewable_fr = area_fr.create_renewable_cluster(renewable_name, None)
        assert renewable_fr.name == renewable_name
        assert renewable_fr.id == "cluster_test"

        # test renewable cluster creation with properties
        renewable_name = "wind_onshore"
        renewable_properties = RenewableClusterProperties(enabled=False, group="wind onshore")
        renewable_onshore = area_fr.create_renewable_cluster(renewable_name, renewable_properties)
        assert not renewable_onshore.properties.enabled
        assert renewable_onshore.properties.group == RenewableClusterGroup.WIND_ON_SHORE.value

        # Update multiple renewable clusters properties at once
        renewable_update_1 = RenewableClusterPropertiesUpdate(group="wind onshore", unit_count=10)
        renewable_update_2 = RenewableClusterPropertiesUpdate(
            group=RenewableClusterGroup.THERMAL_SOLAR.value, enabled=False, nominal_capacity=1340
        )
        update_for_renewable = {renewable_fr: renewable_update_1, renewable_onshore: renewable_update_2}

        study.update_renewable_clusters(update_for_renewable)

        fr_renew_properties = renewable_fr.properties
        onshore_properties = renewable_onshore.properties

        assert fr_renew_properties.unit_count == 10
        assert fr_renew_properties.group == RenewableClusterGroup.WIND_ON_SHORE.value
        # checking the old values are not modified
        assert fr_renew_properties.nominal_capacity == 0
        assert fr_renew_properties.enabled

        assert onshore_properties.group == RenewableClusterGroup.THERMAL_SOLAR.value
        assert not onshore_properties.enabled
        assert onshore_properties.nominal_capacity == 1340

        assert onshore_properties.unit_count == 1

        # test short term storage creation with default values
        st_storage_name = "cluster_test %?"
        storage_fr = area_fr.create_st_storage(st_storage_name)
        assert storage_fr.name == st_storage_name
        assert storage_fr.id == "cluster_test"

        # test actual_hydro has the same datas (id, properties and matrices) than area_fr hydro
        actual_hydro = area_fr.hydro
        assert actual_hydro.area_id == area_fr.id
        assert actual_hydro.properties == area_fr.hydro.properties
        assert area_fr.hydro.properties.reservoir is False
        assert area_fr.hydro.properties.reservoir_capacity == 0
        assert area_fr.hydro.allocation == [HydroAllocation(area_id=area_fr.id, coefficient=1)]

        # update hydro properties
        hydro_properties = HydroPropertiesUpdate(reservoir=True, reservoir_capacity=4.5)
        area_fr.hydro.update_properties(hydro_properties)
        assert area_fr.hydro.properties.reservoir is True
        assert area_fr.hydro.properties.reservoir_capacity == 4.5

        assert area_fr.hydro.inflow_structure.intermonthly_correlation == 0.5
        # update hydro inflow structure
        area_fr.hydro.update_inflow_structure(InflowStructureUpdate(intermonthly_correlation=0.1))
        assert area_fr.hydro.inflow_structure.intermonthly_correlation == 0.1

        # update hydro allocation
        area_fr.hydro.set_allocation(
            [HydroAllocation(area_id="be", coefficient=0.4), HydroAllocation(area_id="de", coefficient=1.6)]
        )
        assert area_fr.hydro.allocation == [
            HydroAllocation(area_id="be", coefficient=0.4),
            HydroAllocation(area_id="de", coefficient=1.6),
            HydroAllocation(area_id="fr", coefficient=1.0),
        ]

        # test short term storage creation with properties
        st_storage_name = "wind_onshore"
        storage_properties = STStorageProperties(reservoir_capacity=0.5, group=STStorageGroup.BATTERY.value)
        battery_fr = area_fr.create_st_storage(st_storage_name, storage_properties)
        properties = battery_fr.properties
        assert properties.reservoir_capacity == 0.5
        assert properties.group == STStorageGroup.BATTERY.value

        # checking multiple areas properties update
        area_props_update_1 = AreaPropertiesUpdate(
            adequacy_patch_mode=AdequacyPatchMode.VIRTUAL, other_dispatch_power=False
        )
        area_props_update_2 = AreaPropertiesUpdate(
            non_dispatch_power=False, energy_cost_spilled=0.45, energy_cost_unsupplied=3.0
        )
        dict_area_props = {area_fr: area_props_update_1, area_be: area_props_update_2}
        study.update_areas(dict_area_props)

        area_fr_props = area_fr.properties
        area_be_props = area_be.properties

        assert area_fr_props.adequacy_patch_mode == AdequacyPatchMode.VIRTUAL
        assert not area_fr_props.other_dispatch_power
        assert not area_be_props.non_dispatch_power
        assert area_be_props.energy_cost_spilled == 0.45
        assert area_be_props.energy_cost_unsupplied == 3.0

        # checking the non updated properties aren't affected
        assert area_fr_props.non_dispatch_power
        assert area_be_props.dispatch_hydro_power

        # tests upload matrix for short term storage.
        injection_matrix = pd.DataFrame(data=np.zeros((8760, 1)))
        battery_fr.update_pmax_injection(injection_matrix)

        # tests get pmax_injection matrix
        pd.testing.assert_frame_equal(battery_fr.get_pmax_injection(), injection_matrix, check_dtype=False)

        # asserts areas contains the clusters + short term storages
        assert area_be.get_thermals() == {thermal_be.id: thermal_be}
        assert area_fr.get_thermals() == {thermal_fr.id: thermal_fr, thermal_value_be.id: thermal_value_be}
        assert area_be.get_renewables() == {}
        assert area_fr.get_renewables() == {renewable_onshore.id: renewable_onshore, renewable_fr.id: renewable_fr}
        assert area_be.get_st_storages() == {}
        assert area_fr.get_st_storages() == {battery_fr.id: battery_fr, storage_fr.id: storage_fr}

        # using update_st_storages to modify existing storages properties and checking they've been modified
        battery_fr_update = STStoragePropertiesUpdate(
            group=STStorageGroup.PSP_CLOSED.value, enabled=False, injection_nominal_capacity=1000
        )
        storage_fr_update = STStoragePropertiesUpdate(group=STStorageGroup.PONDAGE.value, efficiency=0)
        update_for_storages = {battery_fr: battery_fr_update, storage_fr: storage_fr_update}

        study.update_st_storages(update_for_storages)

        battery_fr_properties = battery_fr.properties
        storage_fr_properties = storage_fr.properties
        assert battery_fr_properties.group == STStorageGroup.PSP_CLOSED.value
        assert not battery_fr_properties.enabled
        assert battery_fr_properties.injection_nominal_capacity == 1000
        # Checking if the other values haven't been modified
        assert battery_fr_properties.initial_level == 0.5
        assert battery_fr_properties.efficiency == 1

        assert storage_fr_properties.group == STStorageGroup.PONDAGE.value
        assert storage_fr_properties.efficiency == 0
        # Checking if the other values haven't been modified
        assert storage_fr_properties.enabled
        assert storage_fr_properties.injection_nominal_capacity == 0
        assert storage_fr_properties.reservoir_capacity == 0

        # test binding constraint creation without terms
        properties = BindingConstraintProperties(enabled=False, group="group_1")
        constraint_1 = study.create_binding_constraint(name="bc_1", properties=properties)
        assert constraint_1.name == "bc_1"
        assert not constraint_1.properties.enabled
        assert constraint_1.properties.group == "group_1"
        assert constraint_1.get_terms() == {}

        # test binding constraint creation with terms
        link_data = LinkData(area1=area_be.id, area2=area_fr.id)
        link_term_2 = ConstraintTerm(data=link_data, weight=2)
        cluster_data = ClusterData(area=area_fr.id, cluster=thermal_fr.id)
        cluster_term = ConstraintTerm(data=cluster_data, weight=4.5, offset=3)
        terms = [link_term_2, cluster_term]
        constraint_2 = study.create_binding_constraint(name="bc_2", terms=terms)
        assert constraint_2.name == "bc_2"
        assert constraint_2.get_terms() == {link_term_2.id: link_term_2, cluster_term.id: cluster_term}

        # test updating constraints
        update_bc_props_1 = BindingConstraintPropertiesUpdate(
            time_step=BindingConstraintFrequency.DAILY,
            enabled=False,
            filter_synthesis={FilterOption.WEEKLY, FilterOption.ANNUAL},
        )
        update_bc_props_2 = BindingConstraintPropertiesUpdate(
            enabled=True, time_step=BindingConstraintFrequency.HOURLY, comments="Bonjour"
        )
        dict_binding_constraints_update = {constraint_1.name: update_bc_props_1, constraint_2.name: update_bc_props_2}

        study.update_binding_constraints(dict_binding_constraints_update)

        assert constraint_1.properties.time_step == BindingConstraintFrequency.DAILY
        assert constraint_1.properties.filter_synthesis == {FilterOption.WEEKLY, FilterOption.ANNUAL}
        assert not constraint_1.properties.enabled
        assert constraint_2.properties.time_step == BindingConstraintFrequency.HOURLY
        assert constraint_2.properties.enabled
        assert constraint_2.properties.comments == "Bonjour"

        # checking an non updated properties of constraint hasn't been changed
        assert constraint_1.properties.comments == ""
        assert constraint_1.properties.operator == BindingConstraintOperator.LESS

        # test constraint creation with matrices
        # Case that fails
        wrong_matrix = pd.DataFrame(data=(np.ones((12, 1))))
        with pytest.raises(
            BindingConstraintCreationError,
            match="Could not create the binding constraint 'bc_3'",
        ):
            study.create_binding_constraint(name="bc_3", less_term_matrix=wrong_matrix)

        # Other case with failure
        with pytest.raises(
            ConstraintMatrixUpdateError,
            match=f"Could not update matrix eq for binding constraint '{constraint_2.id}'",
        ):
            constraint_2.set_equal_term(wrong_matrix)

        # Case that succeeds
        properties = BindingConstraintProperties(operator=BindingConstraintOperator.LESS)
        matrix = pd.DataFrame(data=(np.ones((8784, 1))))
        constraint_3 = study.create_binding_constraint(name="bc_3", less_term_matrix=matrix, properties=properties)
        pd.testing.assert_frame_equal(constraint_3.get_less_term_matrix(), matrix, check_dtype=False)

        # test update constraint matrices
        new_matrix = pd.DataFrame(data=(np.ones((8784, 1))))
        new_matrix.iloc[0, 0] = 72
        update_properties = BindingConstraintPropertiesUpdate(operator=BindingConstraintOperator.EQUAL)
        constraint_3.update_properties(update_properties)
        constraint_3.set_equal_term(new_matrix)
        pd.testing.assert_frame_equal(constraint_3.get_equal_term_matrix(), new_matrix, check_dtype=False)

        # test adding terms to a constraint
        link_data = LinkData(area1=area_de.id, area2=area_fr.id)
        link_term_1 = ConstraintTerm(data=link_data, weight=15)
        cluster_data = ClusterData(area=area_be.id, cluster=thermal_be.id)
        cluster_term = ConstraintTerm(data=cluster_data, weight=100)
        terms = [link_term_1, cluster_term]
        constraint_1.set_terms(terms)
        assert constraint_1.get_terms() == {link_term_1.id: link_term_1, cluster_term.id: cluster_term}

        # test replacing terms
        constraint_term_2 = ConstraintTerm(data=LinkData(area1=area_de.id, area2=area_be.id), weight=3, offset=4)
        constraint_term_3 = ConstraintTerm(data=LinkData(area1=area_fr.id, area2=area_be.id), weight=4, offset=10)
        terms = [constraint_term_2, constraint_term_3]
        constraint_1.set_terms(terms)
        assert list(constraint_1.get_terms().values()) == [constraint_term_2, constraint_term_3]

        # asserts study contains the constraints
        assert study.get_binding_constraints() == {
            constraint_1.id: constraint_1,
            constraint_2.id: constraint_2,
            constraint_3.id: constraint_3,
        }

        # test area property edition
        new_props = AreaPropertiesUpdate(adequacy_patch_mode=AdequacyPatchMode.VIRTUAL)
        area_fr.update_properties(new_props)
        assert area_fr.properties.adequacy_patch_mode == AdequacyPatchMode.VIRTUAL

        # test area ui edition
        assert area_fr.ui.x == 0
        assert area_fr.ui.y == 0
        new_ui = AreaUiUpdate(x=100)
        area_fr.update_ui(new_ui)
        assert area_fr.ui.x == 100
        assert area_fr.ui.y == 0

        # test link property edition
        new_props = LinkPropertiesUpdate(hurdles_cost=False)
        link_be_fr.update_properties(new_props)
        assert not link_be_fr.properties.hurdles_cost

        # tests link ui edition
        new_ui = LinkUiUpdate(link_style=LinkStyle.PLAIN)
        link_be_fr.update_ui(new_ui)
        assert link_be_fr.ui.link_style == LinkStyle.PLAIN

        # tests thermal properties update
        new_props = ThermalClusterPropertiesUpdate()
        new_props.group = "nuclear"
        thermal_fr.update_properties(new_props)
        assert thermal_fr.properties.group == ThermalClusterGroup.NUCLEAR.value

        # tests study reading method returns the same object that the one we created
        actual_study = read_study_api(api_config, study.service.study_id)

        assert study.service.study_id == actual_study.service.study_id
        assert study.name == actual_study.name
        assert study._version == actual_study._version
        assert sorted(list(study.get_areas().keys())) == sorted(list(actual_study.get_areas().keys()))

        expected_area_fr = study.get_areas()["fr"]
        actual_area_fr = actual_study.get_areas()["fr"]
        assert sorted(list(expected_area_fr.get_thermals())) == sorted(list(actual_area_fr.get_thermals()))
        assert sorted(list(expected_area_fr.get_renewables())) == sorted(list(actual_area_fr.get_renewables()))
        assert sorted(list(expected_area_fr.get_st_storages())) == sorted(list(actual_area_fr.get_st_storages()))
        assert study.get_settings() == actual_study.get_settings()

        assert sorted(list(study.get_links().keys())) == sorted(list(actual_study.get_links().keys()))
        expected_link_de_fr = study.get_links()["de / fr"]
        actual_link_de_fr = actual_study.get_links()["de / fr"]
        assert expected_link_de_fr.id == actual_link_de_fr.id
        assert expected_link_de_fr.ui == actual_link_de_fr.ui
        assert expected_link_de_fr.properties == actual_link_de_fr.properties

        assert sorted(list(study.get_binding_constraints().keys())) == sorted(
            list(actual_study.get_binding_constraints().keys())
        )
        actual_constraint = actual_study.get_binding_constraints()["bc_2"]
        assert actual_constraint.properties.enabled is True
        assert actual_constraint.properties.time_step == BindingConstraintFrequency.HOURLY
        assert actual_constraint.properties.operator == BindingConstraintOperator.EQUAL
        assert actual_constraint.properties.group == "default"
        assert len(actual_constraint.get_terms()) == 2
        cluster_term = actual_constraint.get_terms()["fr.cluster_test"]
        assert cluster_term.data.area == "fr"
        assert cluster_term.data.cluster == "cluster_test"
        assert cluster_term.weight == 4.5
        assert cluster_term.offset == 3

        # tests renewable properties update
        new_props = RenewableClusterPropertiesUpdate()
        new_props.ts_interpretation = TimeSeriesInterpretation.POWER_GENERATION
        renewable_onshore.update_properties(new_props)
        assert renewable_onshore.properties.ts_interpretation == TimeSeriesInterpretation.POWER_GENERATION

        # tests short term storage properties update
        new_props = STStoragePropertiesUpdate(group=STStorageGroup.PONDAGE.value)
        battery_fr.update_properties(new_props)
        assert battery_fr.properties.group == STStorageGroup.PONDAGE.value
        assert battery_fr.properties.reservoir_capacity == 0.5  # Checks old value wasn't modified

        # tests constraint properties update
        new_props = BindingConstraintPropertiesUpdate(group="another_group")
        constraint_1.update_properties(new_props)
        assert constraint_1.properties.group == "another_group"
        assert constraint_1.properties.enabled is False  # Checks old value wasn't modified

        # creating link properties update to modify all the actual links
        link_properties_update_1 = LinkPropertiesUpdate(
            hurdles_cost=True, use_phase_shifter=True, filter_synthesis={FilterOption.DAILY}
        )
        link_properties_update_2 = LinkPropertiesUpdate(
            transmission_capacities=TransmissionCapacities.ENABLED, asset_type=AssetType.GAZ
        )

        study.update_links({link_be_fr.id: link_properties_update_1, link_de_fr.id: link_properties_update_2})

        link_be_fr = study.get_links()["be / fr"]

        # Checking given values are well modified
        assert link_be_fr.properties.hurdles_cost
        assert link_be_fr.properties.use_phase_shifter
        assert link_be_fr.properties.filter_synthesis == {FilterOption.DAILY}
        assert link_be_fr.properties.display_comments
        assert not link_be_fr.properties.loop_flow

        link_de_fr = study.get_links()["de / fr"]
        assert link_de_fr.properties.transmission_capacities == TransmissionCapacities.ENABLED
        assert link_de_fr.properties.asset_type == AssetType.GAZ
        assert not link_de_fr.properties.hurdles_cost

        # tests constraint deletion
        study.delete_binding_constraint(constraint_1)
        assert constraint_1.id not in study.get_binding_constraints()

        # tests link deletion
        study.delete_link(link_de_fr)
        assert link_de_fr.id not in study.get_links()

        # tests uploading thermal and renewable matrices
        series_matrix = pd.DataFrame(data=np.zeros((8760, 3)))
        prepro_data_matrix = pd.DataFrame(data=np.ones((365, 6)))
        prepro_modulation_matrix = pd.DataFrame(data=np.ones((8760, 4)))
        thermal_fr.set_prepro_data(prepro_data_matrix)
        thermal_fr.set_prepro_modulation(prepro_modulation_matrix)
        thermal_fr.set_fuel_cost(series_matrix)
        thermal_fr.set_co2_cost(series_matrix)
        thermal_fr.set_series(series_matrix)
        renewable_fr.set_series(series_matrix)

        pd.testing.assert_frame_equal(thermal_fr.get_series_matrix(), series_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(thermal_fr.get_prepro_data_matrix(), prepro_data_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(
            thermal_fr.get_prepro_modulation_matrix(), prepro_modulation_matrix, check_dtype=False
        )
        pd.testing.assert_frame_equal(thermal_fr.get_fuel_cost_matrix(), series_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(thermal_fr.get_co2_cost_matrix(), series_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(renewable_fr.get_timeseries(), series_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(thermal_fr.get_series_matrix(), series_matrix, check_dtype=False)

        # =======================
        #  SCENARIO BUILDER
        # =======================
        # Sets study nb_years to 4
        study.update_settings(
            StudySettingsUpdate(general_parameters=GeneralParametersUpdate(nb_years=4, year_by_year=True))
        )

        sc_builder = study.get_scenario_builder()

        # Ensures requesting the sc_builder with a wrong name raise a proper issue
        fake_area = "fake_area"
        with pytest.raises(InvalidRequestForScenarioBuilder, match=f"The area {fake_area} does not exist"):
            sc_builder.load.get_area(fake_area)

        # Ensures every value is None as we didn't set anything inside this Study
        assert sc_builder.load.get_area("fr").get_scenario() == [None, None, None, None]

        # Ensures the hydro_final_level is None as it only appeared in v9.2
        assert sc_builder.hydro_final_level is None

        # Sets a new scenario builder
        sc_builder.load.get_area("fr").set_new_scenario([1, 2, 3, 4])
        sc_builder.hydro_initial_level.get_area("be").set_new_scenario([0.1, 0.2, None, 0.5])
        sc_builder.thermal.get_cluster("fr", "cluster_test").set_new_scenario([1, 4, 3, 2])
        study.set_scenario_builder(sc_builder)

        # Reads the new scenario builder
        new_sc_builder = study.get_scenario_builder()
        assert new_sc_builder.load.get_area("fr").get_scenario() == [1, 2, 3, 4]
        assert new_sc_builder.hydro_initial_level.get_area("be").get_scenario() == [0.1, 0.2, None, 0.5]
        assert new_sc_builder.thermal.get_cluster("fr", "cluster_test").get_scenario() == [1, 4, 3, 2]

        # Ensures updating just one thing doesn't alter others
        new_sc_builder.load.get_area("be").set_new_scenario([1, 3, 2, 4])
        study.set_scenario_builder(new_sc_builder)
        sc_builder = study.get_scenario_builder()
        assert sc_builder.load.get_area("fr").get_scenario() == [1, 2, 3, 4]
        assert sc_builder.load.get_area("be").get_scenario() == [1, 3, 2, 4]
        assert sc_builder.hydro_initial_level.get_area("be").get_scenario() == [0.1, 0.2, None, 0.5]
        assert sc_builder.thermal.get_cluster("fr", "cluster_test").get_scenario() == [1, 4, 3, 2]

        # =======================
        #  OBJECTS DELETION
        # =======================

        # tests thermal cluster deletion
        area_be.delete_thermal_cluster(thermal_be)
        assert area_be.get_thermals() == {}

        # tests renewable cluster deletion
        area_fr.delete_renewable_clusters([renewable_onshore, renewable_fr])
        assert area_fr.get_renewables() == {}

        # tests short term storage deletion
        area_fr.delete_st_storage(battery_fr)
        assert battery_fr.id not in study.get_areas().get(area_be.id).get_st_storages()

        # tests area deletion error
        with pytest.raises(
            ReferencedObjectDeletionNotAllowed,
            match="Area 'fr' is not allowed to be deleted, because it is referenced in the following binding constraints:\n1- 'bc_2'.",
        ):
            study.delete_area(area_fr)

        # tests area deletion success
        study.delete_area(area_de)
        assert area_de.id not in study.get_areas()

        # test default settings at the study creation
        new_study = create_study_api("second_study", "880", api_config)
        actual_settings = new_study.get_settings()
        default_settings = StudySettings()
        assert actual_settings.general_parameters == default_settings.general_parameters
        assert actual_settings.seed_parameters == default_settings.seed_parameters
        assert actual_settings.playlist_parameters == {1: PlaylistParameters(status=True, weight=1)}
        # Checks default values for study 8.8 are filled even if put at None inside the user class
        assert actual_settings.advanced_parameters == AdvancedParameters(
            initial_reservoir_levels=InitialReservoirLevel.COLD_START
        )
        assert actual_settings.thematic_trimming_parameters == default_thematic_trimming_88
        assert actual_settings.adequacy_patch_parameters == AdequacyPatchParameters(
            set_to_null_ntc_between_physical_out_for_first_step=True
        )

        # tests update settings
        study_settings = StudySettingsUpdate()
        study_settings.general_parameters = GeneralParametersUpdate(mode=Mode.ADEQUACY, year_by_year=True)
        study_settings.optimization_parameters = OptimizationParametersUpdate(include_exportmps=ExportMPS.OPTIM1)
        new_study.update_settings(study_settings)
        updated_settings = new_study.get_settings()
        assert updated_settings.general_parameters.mode == Mode.ADEQUACY
        assert updated_settings.general_parameters.year_by_year
        assert updated_settings.optimization_parameters.include_exportmps == ExportMPS.OPTIM1
        # update playlist
        new_study.set_playlist({1: PlaylistParameters(status=False, weight=0.6)})
        assert new_study.get_settings().playlist_parameters == {1: PlaylistParameters(status=False, weight=0.6)}
        # update thematic trimming
        new_trimming = new_study.get_settings().thematic_trimming_parameters.all_disabled()
        new_study.set_thematic_trimming(new_trimming)
        assert new_study.get_settings().thematic_trimming_parameters == new_trimming

        new_settings = StudySettingsUpdate()
        new_settings.general_parameters = GeneralParametersUpdate(simulation_synthesis=False)
        new_settings.advanced_parameters = AdvancedParametersUpdate(unit_commitment_mode=UnitCommitmentMode.MILP)
        new_settings.optimization_parameters = OptimizationParametersUpdate(include_exportmps=ExportMPS.FALSE)
        new_study.update_settings(new_settings)
        new_settings = new_study.get_settings()
        assert new_settings.general_parameters.mode == Mode.ADEQUACY
        assert new_settings.general_parameters.simulation_synthesis is False
        assert new_settings.optimization_parameters.include_exportmps == ExportMPS.FALSE
        assert new_settings.advanced_parameters.unit_commitment_mode == UnitCommitmentMode.MILP
        assert new_settings.playlist_parameters == {1: PlaylistParameters(status=False, weight=0.6)}
        assert new_settings.thematic_trimming_parameters == new_trimming

        # test each hydro matrices returns the good values
        default_reservoir_matrix = np.zeros((365, 3))
        default_reservoir_matrix[:, 1] = 0.5
        default_reservoir_matrix[:, 2] = 1
        default_reservoir = pd.DataFrame(default_reservoir_matrix)
        assert area_fr.hydro.get_reservoir().equals(pd.DataFrame(default_reservoir))

        default_credit_modulation = pd.DataFrame(np.ones((2, 101)))
        pd.testing.assert_frame_equal(
            area_fr.hydro.get_credit_modulations(), default_credit_modulation, check_dtype=False
        )

        default_water_values = pd.DataFrame(np.zeros((365, 101)))
        pd.testing.assert_frame_equal(area_fr.hydro.get_water_values(), default_water_values, check_dtype=False)

        default_maxpower_matrix = np.zeros((365, 4))
        default_maxpower_matrix[:, 1] = 24
        default_maxpower_matrix[:, 3] = 24
        default_maxpower = pd.DataFrame(default_maxpower_matrix)
        pd.testing.assert_frame_equal(area_fr.hydro.get_maxpower(), default_maxpower, check_dtype=False)

        default_inflow_pattern = pd.DataFrame(np.ones((365, 1)))
        pd.testing.assert_frame_equal(area_fr.hydro.get_inflow_pattern(), default_inflow_pattern, check_dtype=False)

        default_ror = pd.DataFrame(np.zeros((8760, 1)))
        pd.testing.assert_frame_equal(area_fr.hydro.get_ror_series(), default_ror, check_dtype=False)

        default_mingen = default_ror
        pd.testing.assert_frame_equal(area_fr.hydro.get_mingen(), default_mingen, check_dtype=False)

        default_mod = pd.DataFrame(np.zeros((365, 1)))
        pd.testing.assert_frame_equal(area_fr.hydro.get_mod_series(), default_mod, check_dtype=False)

        default_energy = pd.DataFrame(np.zeros((12, 5)))
        pd.testing.assert_frame_equal(area_fr.hydro.get_energy(), default_energy, check_dtype=False)

        # tests the update for hydro matrices
        mod_series = pd.DataFrame(data=np.full((365, 1), 100))
        ror_series = pd.DataFrame(data=np.ones((8760, 1)))
        mingen_series = pd.DataFrame(data=np.ones((8760, 1)))
        energy_matrix = pd.DataFrame(data=np.ones((12, 5)))
        max_power = np.full((365, 4), 1000)
        max_power[:, 1] = 24
        max_power[:, 3] = 24
        maxpower_matrix = pd.DataFrame(data=max_power)
        reservoir_matrix = pd.DataFrame(data=np.ones((365, 3)))
        inflow_pattern_matrix = pd.DataFrame(data=np.zeros((365, 1)))
        credits_matrix = pd.DataFrame(data=np.zeros((2, 101)))
        water_values_matrix = pd.DataFrame(data=np.ones((365, 101)))

        area_fr.hydro.set_maxpower(maxpower_matrix)
        area_fr.hydro.set_reservoir(reservoir_matrix)
        area_fr.hydro.set_inflow_pattern(inflow_pattern_matrix)
        area_fr.hydro.set_water_values(water_values_matrix)
        area_fr.hydro.set_credits_modulation(credits_matrix)
        area_fr.hydro.set_ror_series(ror_series)
        area_fr.hydro.set_mod_series(mod_series)
        area_fr.hydro.set_mingen(mingen_series)
        area_fr.hydro.set_energy(energy_matrix)

        pd.testing.assert_frame_equal(area_fr.hydro.get_maxpower(), maxpower_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(area_fr.hydro.get_reservoir(), reservoir_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(area_fr.hydro.get_inflow_pattern(), inflow_pattern_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(area_fr.hydro.get_water_values(), water_values_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(area_fr.hydro.get_credit_modulations(), credits_matrix, check_dtype=False)
        pd.testing.assert_frame_equal(area_fr.hydro.get_ror_series(), ror_series, check_dtype=False)
        pd.testing.assert_frame_equal(area_fr.hydro.get_mod_series(), mod_series, check_dtype=False)
        pd.testing.assert_frame_equal(area_fr.hydro.get_mingen(), mingen_series, check_dtype=False)
        pd.testing.assert_frame_equal(area_fr.hydro.get_energy(), energy_matrix, check_dtype=False)

        # tests variant creation
        variant_name = "variant_test"
        variant_from_api_name = "variant_from_api_test"
        variant = new_study.create_variant(variant_name)
        variant_from_api = create_variant_api(api_config, new_study.service.study_id, variant_from_api_name)

        # instance asserts
        assert variant.name == variant_name
        assert variant.service.study_id != new_study.service.study_id
        assert variant.get_settings() == new_study.get_settings()
        assert list(variant.get_areas().keys()) == list(new_study.get_areas().keys())
        assert list(variant.get_links().keys()) == list(new_study.get_links().keys())
        assert list(variant.get_binding_constraints().keys()) == list(new_study.get_binding_constraints().keys())
        # from_api asserts
        assert variant_from_api.name == variant_from_api_name
        assert variant_from_api.service.study_id != new_study.service.study_id
        assert variant_from_api.get_settings() == new_study.get_settings()
        assert list(variant_from_api.get_areas().keys()) == list(new_study.get_areas().keys())
        assert list(variant_from_api.get_links().keys()) == list(new_study.get_links().keys())
        assert list(variant_from_api.get_binding_constraints().keys()) == list(
            new_study.get_binding_constraints().keys()
        )

        # ===== Test outputs (Part 1 - before simulation) =====

        assert study.get_outputs() == {}

        # ===== Test run study simulation and wait job completion ======

        parameters = AntaresSimulationParameters(nb_cpu=4)

        job = study.run_antares_simulation(parameters)
        assert isinstance(job, Job)
        assert job.status == JobStatus.PENDING

        study.wait_job_completion(job, time_out=60)
        assert job.status == JobStatus.SUCCESS

        assert job.output_id is not None
        assert job.parameters == parameters
        assert job.parameters.unzip_output is True

        # ===== Test outputs (Part 2 - after simulation) =====

        outputs = study.get_outputs()
        assert len(outputs) == 1
        output = list(outputs.values())[0]
        assert not output.archived
        output_name = output.name
        # Ensures we have the same information when reading the study
        study_with_outputs = read_study_api(api_config, study._study_service.study_id)
        outputs_from_api = study_with_outputs.get_outputs()
        assert len(outputs_from_api) == 1
        new_output = list(outputs.values())[0]
        assert not new_output.archived
        assert new_output.name == output_name

        frequency = Frequency.DAILY

        def _read_matrix(matrix_path: Path, mc_ind: bool = False) -> pd.DataFrame:
            if not mc_ind:
                return pd.read_csv(matrix_path, sep="\t", header=[0, 1, 2], index_col=0, na_values="N/A")

            df = pd.read_csv(matrix_path, sep="\t", header=[0, 1], index_col=0, na_values="N/A")
            new_cols = []
            for k in range(len(df.columns)):
                new_col = list(df.columns[k])
                new_col.append("")
                new_cols.append(tuple(new_col))
            df.columns = pd.MultiIndex.from_tuples(new_cols)
            return df

        # ===== Output get_mc_all_areas =====

        matrix_all_area = output.get_mc_all_area(frequency, MCAllAreasDataType.VALUES, area_be.id)
        expected_all_area = _read_matrix(ASSETS_DIR / "all_area.tsv")
        pd.testing.assert_frame_equal(matrix_all_area, expected_all_area, check_dtype=False)

        # ===== Output get_mc_all_links =====

        matrix_all_links = output.get_mc_all_link(frequency, MCAllLinksDataType.VALUES, area_be.id, area_fr.id)
        expected_all_links = _read_matrix(ASSETS_DIR / "all_links.tsv")
        pd.testing.assert_frame_equal(matrix_all_links, expected_all_links, check_dtype=False)

        # ===== Output get_mc_ind_areas =====

        matrix_ind_area = output.get_mc_ind_area(1, frequency, MCIndAreasDataType.VALUES, area_be.id)
        expected_ind_area = _read_matrix(ASSETS_DIR / "ind_area.tsv", mc_ind=True)
        pd.testing.assert_frame_equal(matrix_ind_area, expected_ind_area, check_dtype=False)

        # ===== Output get_mc_ind_links =====

        matrix_ind_links = output.get_mc_ind_link(1, frequency, MCIndLinksDataType.VALUES, area_be.id, area_fr.id)
        expected_ind_links = _read_matrix(ASSETS_DIR / "ind_links.tsv", mc_ind=True)
        pd.testing.assert_frame_equal(matrix_ind_links, expected_ind_links, check_dtype=False)

        # ===== Output aggregate_values =====

        aggregated_matrix = output.aggregate_mc_all_links(MCAllLinksDataType.VALUES, frequency)
        assert isinstance(aggregated_matrix, pd.DataFrame)
        assert not aggregated_matrix.empty
        assert aggregated_matrix.shape == (364, 30)
        assert aggregated_matrix["link"].apply(lambda x: x == "be - fr").all()
        expected_values = list(range(1, 101))
        matrix_values = aggregated_matrix.loc[0:99, "timeId"].tolist()
        assert expected_values == matrix_values

        # ===== Output deletion =====

        # run two new simulations for creating more outputs
        study.wait_job_completion(
            study.run_antares_simulation(AntaresSimulationParameters(output_suffix="2")), time_out=60
        )
        study.wait_job_completion(
            study.run_antares_simulation(AntaresSimulationParameters(output_suffix="3")), time_out=60
        )
        assert len(study.get_outputs()) == 3

        # delete_output
        study.delete_output(output.name)
        assert output.name not in study.get_outputs()
        study._read_outputs()
        outputs = study.get_outputs()
        assert output.name not in outputs
        assert len(outputs) == 2

        # delete_outputs
        study.delete_outputs()
        assert study.get_outputs() == {}
        study._read_outputs()
        assert study.get_outputs() == {}

        # ===== Test study moving =====

        new_path = Path("/new/path/test")
        assert study.path == PurePath(".")
        study.move(new_path)
        assert study.path == PurePath(new_path) / f"{study.service.study_id}"

        moved_study = read_study_api(api_config, study.service.study_id)
        assert moved_study.path == study.path
        assert moved_study.name == study.name

        new_settings_aggregated = StudySettingsUpdate(
            advanced_parameters=AdvancedParametersUpdate(
                renewable_generation_modelling=RenewableGenerationModeling.AGGREGATED
            ),
            general_parameters=GeneralParametersUpdate(horizon="2018"),
        )
        study_aggregated = create_study_api("test_aggregated", "880", api_config)
        study_aggregated.update_settings(new_settings_aggregated)
        study_aggregated.create_area("area_without_renewables")
        #  read_study_api does not raise an error
        read_study_api(api_config, study_aggregated.service.study_id)

        # testing import study
        # creating a test path to not affect the internal studies created
        test_path = antares_web.desktop_path / "internal_studies" / study.service.study_id
        copy_dir = tmp_path / test_path.name

        tmp_path_zip = tmp_path / copy_dir.name
        shutil.copytree(test_path, copy_dir)

        zip_study = Path(shutil.make_archive(str(tmp_path_zip), "zip", copy_dir))

        # importing without moving the study
        imported_study = import_study_api(api_config, zip_study, None)

        assert imported_study.path == PurePath(".")

        # importing with moving the study
        path_test = Path("/new/test/studies")
        imported_study = import_study_api(api_config, zip_study, path_test)

        assert imported_study.path == path_test / f"{imported_study.service.study_id}"
        assert list(imported_study.get_areas()) == list(study.get_areas())

        ######################
        # Specific tests for Xpansion
        ######################

        # Asserts a random study doesn't contain any Xpansion configuration
        assert not imported_study.has_an_xpansion_configuration

        # Imports a study with a real case Xpansion configuration and a real xpansion output
        study = create_study_local("Xpansion study", "8.8", tmp_path)
        study_path = Path(study.path)
        with zipfile.ZipFile(xpansion_input_path, "r") as zf:
            zf.extractall(study_path / "user" / "expansion")
        with zipfile.ZipFile(xpansion_output_path, "r") as zf:
            zf.extractall(study_path / "output" / "20250724-1040eco")
        zip_study = Path(shutil.make_archive(base_name=str(study_path), base_dir=study_path, format="zip"))

        # Ensures the reading succeeds.
        imported_study = import_study_api(api_config, zip_study)
        xpansion = imported_study.xpansion
        assert xpansion.settings == XpansionSettings(
            optimality_gap=10000, batch_size=0, additional_constraints="contraintes.txt"
        )
        assert xpansion.get_candidates() == {
            "battery": XpansionCandidate(
                name="battery", area_from="Area2", area_to="flex", annual_cost_per_mw=60000, max_investment=1000
            ),
            "peak": XpansionCandidate(
                name="peak", area_from="area1", area_to="peak", annual_cost_per_mw=60000, unit_size=100, max_units=20
            ),
            "pv": XpansionCandidate(
                name="pv",
                area_from="area2",
                area_to="pv",
                annual_cost_per_mw=55400,
                max_investment=1000,
                direct_link_profile="direct_capa_pv.ini",
                indirect_link_profile="direct_capa_pv.ini",
            ),
            "semibase": XpansionCandidate(
                name="semibase",
                area_from="area1",
                area_to="semibase",
                annual_cost_per_mw=126000,
                unit_size=200,
                max_units=10,
            ),
            "transmission_line": XpansionCandidate(
                name="transmission_line",
                area_from="area1",
                area_to="area2",
                annual_cost_per_mw=10000,
                unit_size=400,
                max_units=8,
                direct_link_profile="direct_04_fr-05_fr.txt",
                indirect_link_profile="indirect_04_fr-05_fr.txt",
            ),
        }
        assert xpansion.get_constraints() == {
            "additional_c1": XpansionConstraint(
                name="additional_c1",
                sign=ConstraintSign.LESS_OR_EQUAL,
                right_hand_side=300,
                candidates_coefficients={"semibase": 1, "transmission_line": 1},
            )
        }
        assert xpansion.sensitivity == XpansionSensitivity(epsilon=10000, projection=["battery", "pv"], capex=True)

        ############# Weights ##############
        # Asserts we can get a content
        weight = xpansion.get_weight("weights.txt")
        assert weight.equals(pd.DataFrame([0.2, 0.4, 0.4]))

        # Asserts fetching a fake matrix raises an appropriate exception
        study_id = imported_study.service.study_id
        with pytest.raises(
            XpansionMatrixReadingError,
            match=f"Could not read the xpansion matrix fake_weight for study {study_id}",
        ):
            xpansion.get_weight("fake_weight")

        # Asserts we can modify and create a matrix
        new_weight_matrix = pd.DataFrame([0.1, 0.2, 0.7])
        for file_name in ["weights.txt", "other_weights.ini"]:
            xpansion.set_weight(file_name, new_weight_matrix)
            weight = xpansion.get_weight(file_name)
            assert weight.equals(new_weight_matrix)

        # Asserts there's no default matrix for weights
        empty_matrix = pd.DataFrame()
        xpansion.set_weight("weights.txt", empty_matrix)
        weight = xpansion.get_weight("weights.txt")
        assert weight.equals(empty_matrix)

        # Asserts we can delete a matrix
        xpansion.delete_weight("weights.txt")

        # Asserts deleting a fake matrix raises an appropriate exception
        with pytest.raises(
            XpansionFileDeletionError,
            match=f"Could not delete the xpansion file fake_weight for study {study_id}",
        ):
            xpansion.delete_weight("fake_weight")

        ############# Capacities ##############
        # Asserts we can get a content
        capacity = xpansion.get_capacity("direct_04_fr-05_fr.txt")
        expected_capacity = pd.DataFrame(np.full((8760, 1), 0.95))
        expected_capacity[2208:6576] = 1
        assert capacity.equals(expected_capacity)

        # Asserts fetching a fake matrix raises an appropriate exception
        with pytest.raises(
            XpansionMatrixReadingError,
            match=f"Could not read the xpansion matrix fake_capacity for study {study_id}",
        ):
            xpansion.get_capacity("fake_capacity")

        # Asserts we can modify and create a matrix
        new_capacity_matrix = pd.DataFrame(np.full((8760, 1), 0.87))
        for file_name in ["capa_pv.ini", "other_capa.txt"]:
            xpansion.set_capacity(file_name, new_capacity_matrix)
            capacity = xpansion.get_capacity(file_name)
            assert capacity.equals(new_capacity_matrix)

        # Asserts we can delete a matrix
        xpansion.delete_capacity("04_fr-05_fr.txt")

        # Asserts deleting a fake matrix raises an appropriate exception
        with pytest.raises(
            XpansionFileDeletionError,
            match=f"Could not delete the xpansion file fake_capacity for study {study_id}",
        ):
            xpansion.delete_capacity("fake_capacity")

        ############# Candidates ##############
        # Creates areas and links corresponding to Xpansion candidates
        areas_to_create = ["area1", "area2", "flex", "peak", "pv", "semibase"]
        links_to_create = [
            ("area1", "area2"),
            ("area2", "flex"),
            ("area1", "peak"),
            ("area2", "pv"),
            ("area1", "semibase"),
        ]
        for area in areas_to_create:
            imported_study.create_area(area)
        for link in links_to_create:
            imported_study.create_link(area_from=link[0], area_to=link[1])

        # Creates a candidate
        my_cdt = XpansionCandidate(
            name="my_cdt",
            area_from="area1",
            area_to="area2",
            annual_cost_per_mw=3.17,
            max_investment=2,
            direct_link_profile="capa_pv.ini",
        )
        cdt = xpansion.create_candidate(my_cdt)
        assert cdt == my_cdt

        # Update several properties
        new_properties = XpansionCandidateUpdate(area_from="pv", max_investment=3)
        cdt = xpansion.update_candidate("my_cdt", new_properties)
        assert cdt.name == "my_cdt"
        assert cdt.area_from == "area2"  # Areas were re-ordered by alphabetical name
        assert cdt.area_to == "pv"
        assert cdt.max_investment == 3
        assert cdt.direct_link_profile == "capa_pv.ini"

        # Rename it
        new_properties = XpansionCandidateUpdate(name="new_name")
        cdt = xpansion.update_candidate("my_cdt", new_properties)
        assert cdt.name == "new_name"
        assert cdt.max_investment == 3
        assert cdt.direct_link_profile == "capa_pv.ini"

        # Removes the direct link profile from the candidate
        xpansion.remove_links_profile_from_candidate("new_name", [XpansionLinkProfile.DIRECT_LINK])
        assert xpansion.get_candidates()["new_name"].direct_link_profile is None
        # Ensures that even when reading the candidate we still have `direct_link_profile` to None
        imported_study = read_study_api(api_config, study_id)
        study_id = imported_study.service.study_id
        assert imported_study.xpansion.get_candidates()["new_name"].direct_link_profile is None

        # Removes several candidates
        xpansion.delete_candidates(["peak", "transmission_line"])
        assert len(xpansion.get_candidates()) == 4
        xpansion = read_study_api(api_config, study_id).xpansion
        assert len(xpansion.get_candidates()) == 4

        ############# Constraints ##############
        file_name = "contraintes.txt"

        # Creates a constraint
        new_constraint = XpansionConstraint(
            name="new_constraint",
            sign=ConstraintSign.GREATER_OR_EQUAL,
            right_hand_side=100,
            candidates_coefficients={"semibase": 0.5},
        )
        constraint = xpansion.create_constraint(new_constraint, file_name)
        assert constraint == new_constraint

        # Edits it
        new_properties = XpansionConstraintUpdate(right_hand_side=1000, candidates_coefficients={"test": 0.3})
        modified_constraint = xpansion.update_constraint("new_constraint", new_properties, file_name)
        assert modified_constraint == XpansionConstraint(
            name="new_constraint",
            sign=ConstraintSign.GREATER_OR_EQUAL,
            right_hand_side=1000,
            candidates_coefficients={"semibase": 0.5, "test": 0.3},
        )

        # Ensures the edition for candidates coefficients is working correctly
        new_properties = XpansionConstraintUpdate(
            sign=ConstraintSign.EQUAL, candidates_coefficients={"test": 0.2, "test2": 0.8}
        )
        modified_constraint = xpansion.update_constraint("new_constraint", new_properties, file_name)
        assert modified_constraint == XpansionConstraint(
            name="new_constraint",
            sign=ConstraintSign.EQUAL,
            right_hand_side=1000,
            candidates_coefficients={"semibase": 0.5, "test": 0.2, "test2": 0.8},
        )

        # Rename it
        new_properties = XpansionConstraintUpdate(name="new_name")
        modified_constraint = xpansion.update_constraint("new_constraint", new_properties, file_name)
        assert modified_constraint.name == "new_name"

        # Ensures reading works correctly
        xpansion = read_study_api(api_config, study_id).xpansion
        assert xpansion.get_constraints() == {
            "additional_c1": XpansionConstraint(
                name="additional_c1",
                sign=ConstraintSign.LESS_OR_EQUAL,
                right_hand_side=300.0,
                candidates_coefficients={"semibase": 1, "transmission_line": 1},
            ),
            "new_name": XpansionConstraint(
                name="new_name",
                sign=ConstraintSign.EQUAL,
                right_hand_side=1000.0,
                candidates_coefficients={"semibase": 0.5, "test": 0.2, "test2": 0.8},
            ),
        }

        # Deletes all constraints
        xpansion.delete_constraints(["new_name", "additional_c1"], file_name)
        assert xpansion.get_constraints() == {}

        # Create a constraint in a non-existing file
        constraint = XpansionConstraint(
            name="my_constraint", sign=ConstraintSign.GREATER_OR_EQUAL, right_hand_side=0.1, candidates_coefficients={}
        )
        xpansion.create_constraint(constraint, "new_file.ini")

        ############# Sensitivity ##############
        assert xpansion.sensitivity == XpansionSensitivity(epsilon=10000, projection=["battery", "pv"], capex=True)
        # Updates the sensitivity
        sensitivity_update = XpansionSensitivityUpdate(epsilon=2, projection=["semibase", "pv"])
        new_sensitivity = xpansion.update_sensitivity(sensitivity_update)
        assert new_sensitivity == XpansionSensitivity(epsilon=2, projection=["semibase", "pv"], capex=True)

        # Checks we didn't alter the settings
        xpansion_read = read_study_api(api_config, study_id).xpansion
        assert xpansion_read.sensitivity == XpansionSensitivity(epsilon=2, projection=["semibase", "pv"], capex=True)
        assert xpansion_read.settings == XpansionSettings(
            optimality_gap=10000, batch_size=0, additional_constraints="contraintes.txt"
        )

        ############# Settings ##############
        # Updates the settings
        settings_update = XpansionSettingsUpdate(
            optimality_gap=40.5, solver=XpansionSolver.CBC, additional_constraints="new_file.ini"
        )
        new_settings = xpansion.update_settings(settings_update)
        assert new_settings == XpansionSettings(
            optimality_gap=40.5, solver=XpansionSolver.CBC, additional_constraints="new_file.ini", batch_size=0
        )
        # Removes the constraint from the settings to delete it afterwards.
        xpansion.remove_constraints_and_or_weights_from_settings(constraint=True, weight=False)
        assert xpansion.settings == XpansionSettings(optimality_gap=40.5, solver=XpansionSolver.CBC, batch_size=0)

        ############# Deletion ##############
        # Deletes a constraints file
        xpansion.delete_constraints_file("new_file.ini")

        # Deletes the configuration
        imported_study.delete_xpansion_configuration()
        assert not imported_study.has_an_xpansion_configuration
        study = read_study_api(api_config, study_id)
        assert not study.has_an_xpansion_configuration

        ############# Outputs reading ##############
        output = study.get_outputs().values().__iter__().__next__()

        assert output.name == "20250724-1040eco"
        assert not output.archived

        result = output.get_xpansion_result()
        assert result == xpansion_expected_output

        sensitivity_result = output.get_xpansion_sensitivity_result()
        assert sensitivity_result == xpansion_sensitivity_expected_output

        ######################
        # Specific tests for study version 9.2
        ######################

        # Create a study with an area
        study = create_study_api("Study_92", "9.2", api_config)
        area_fr = study.create_area("FR")

        ########## Short-Term storage ##########

        sts_properties = STStorageProperties(efficiency=0.9, efficiency_withdrawal=0.9, group="free group")
        storage = area_fr.create_st_storage("sts_test", sts_properties)
        assert storage.properties.efficiency_withdrawal == 0.9
        assert storage.properties.efficiency == 0.9
        assert storage.properties.group == "free group"
        assert storage.properties.penalize_variation_injection is False

        new_properties = STStoragePropertiesUpdate(group="new group", penalize_variation_injection=True)
        storage.update_properties(new_properties)
        assert storage.properties.efficiency_withdrawal == 0.9
        assert storage.properties.group == "new group"
        assert storage.properties.penalize_variation_injection is True

        pd.testing.assert_frame_equal(
            storage.get_cost_variation_injection(), pd.DataFrame(np.zeros((8760, 1))), check_dtype=False
        )
        new_matrix = pd.DataFrame(np.full((8760, 4), 10))
        storage.set_cost_variation_withdrawal(new_matrix)
        assert storage.get_cost_variation_withdrawal().equals(new_matrix)

        ########## STS constraints ##########
        second_storage = area_fr.create_st_storage("second_storage")
        area_be = study.create_area("be")
        storage_be = area_be.create_st_storage("storage_be")

        constraints_fr = [
            STStorageAdditionalConstraint(name="constraint_1", occurrences=[Occurrence([1, 3])]),
            STStorageAdditionalConstraint(
                name="Constraint2??", variable=AdditionalConstraintVariable.WITHDRAWAL, occurrences=[Occurrence([167])]
            ),
        ]
        second_storage.create_constraints(constraints_fr)

        constraints_be = STStorageAdditionalConstraint(
            name="constraint_be",
            enabled=False,
            operator=AdditionalConstraintOperator.GREATER,
            occurrences=[Occurrence([1, 2]), Occurrence([4, 5, 6])],
        )
        storage_be.create_constraints([constraints_be])

        # Asserts the reading method succeeds
        study = read_study_api(api_config, study.service.study_id)

        fr_storages = study.get_areas()["fr"].get_st_storages()
        assert len(fr_storages) == 2
        assert fr_storages["sts_test"].get_constraints() == {}
        second_storage = fr_storages["second_storage"]
        assert second_storage.get_constraints() == {
            "constraint_1": STStorageAdditionalConstraint(
                name="constraint_1",
                variable=AdditionalConstraintVariable.NETTING,
                operator=AdditionalConstraintOperator.LESS,
                occurrences=[Occurrence(hours=[1, 3])],
                enabled=True,
            ),
            "constraint2": STStorageAdditionalConstraint(
                name="Constraint2??",
                variable=AdditionalConstraintVariable.WITHDRAWAL,
                operator=AdditionalConstraintOperator.LESS,
                occurrences=[Occurrence(hours=[167])],
                enabled=True,
            ),
        }

        storage_be = study.get_areas()["be"].get_st_storages()["storage_be"]
        assert storage_be.get_constraints() == {
            "constraint_be": STStorageAdditionalConstraint(
                name="constraint_be",
                variable=AdditionalConstraintVariable.NETTING,
                operator=AdditionalConstraintOperator.GREATER,
                occurrences=[Occurrence(hours=[1, 2]), Occurrence(hours=[4, 5, 6])],
                enabled=False,
            )
        }

        # Updates a constraint properties
        new_properties = STStorageAdditionalConstraintUpdate(
            enabled=False, variable=AdditionalConstraintVariable.INJECTION
        )
        new_constraint = second_storage.update_constraint("constraint_1", new_properties)
        assert new_constraint == STStorageAdditionalConstraint(
            name="constraint_1",
            variable=AdditionalConstraintVariable.INJECTION,
            operator=AdditionalConstraintOperator.LESS,
            occurrences=[Occurrence(hours=[1, 3])],
            enabled=False,
        )

        # Updates several constraint properties
        new_constraints_properties = STStorageAdditionalConstraintUpdate(
            occurrences=[Occurrence(hours=[1, 4]), Occurrence(hours=[6, 8, 9])],
            operator=AdditionalConstraintOperator.EQUAL,
        )
        update_for_storages_constraints = {
            second_storage: {"constraint2": new_constraints_properties},
            storage_be: {"constraint_be": new_constraints_properties},
        }

        study.update_st_storages_constraints(update_for_storages_constraints)

        # Ensures the updates were successful
        study = read_study_api(api_config, study.service.study_id)
        assert study.get_areas()["fr"].get_st_storages()["second_storage"].get_constraints() == {
            "constraint_1": STStorageAdditionalConstraint(
                name="constraint_1",
                variable=AdditionalConstraintVariable.INJECTION,
                operator=AdditionalConstraintOperator.LESS,
                occurrences=[Occurrence(hours=[1, 3])],
                enabled=False,
            ),
            "constraint2": STStorageAdditionalConstraint(
                name="Constraint2??",
                variable=AdditionalConstraintVariable.WITHDRAWAL,
                operator=AdditionalConstraintOperator.EQUAL,
                occurrences=[Occurrence(hours=[1, 4]), Occurrence(hours=[6, 8, 9])],
                enabled=True,
            ),
        }

        assert study.get_areas()["be"].get_st_storages()["storage_be"].get_constraints() == {
            "constraint_be": STStorageAdditionalConstraint(
                name="constraint_be",
                variable=AdditionalConstraintVariable.NETTING,
                operator=AdditionalConstraintOperator.EQUAL,
                occurrences=[Occurrence(hours=[1, 4]), Occurrence(hours=[6, 8, 9])],
                enabled=False,
            )
        }

        # Removes a constraint
        second_storage.delete_constraints(["constraint_1"])
        constraints = second_storage.get_constraints()
        assert len(constraints) == 1
        assert "constraint1" not in constraints

        ########## Hydro ##########

        assert area_fr.hydro.properties.overflow_spilled_cost_difference == 1
        assert area_fr.hydro.properties.reservoir is False
        assert area_fr.hydro.properties.reservoir_capacity == 0

        new_hydro_properties = HydroPropertiesUpdate(overflow_spilled_cost_difference=0.3, reservoir_capacity=1)
        area_fr.hydro.update_properties(new_hydro_properties)
        assert area_fr.hydro.properties.overflow_spilled_cost_difference == 0.3
        assert area_fr.hydro.properties.reservoir is False
        assert area_fr.hydro.properties.reservoir_capacity == 1

        ########## Thematic trimming ##########

        thematic_trimming = study.get_settings().thematic_trimming_parameters
        assert thematic_trimming.sts_by_group is True
        assert thematic_trimming.oil is True
        assert thematic_trimming.nuclear is True
        assert thematic_trimming.psp_open_level is None

        new_trimming = ThematicTrimmingParameters(sts_by_group=False, oil=False)
        study.set_thematic_trimming(new_trimming)
        thematic_trimming = study.get_settings().thematic_trimming_parameters
        assert thematic_trimming.sts_by_group is False
        assert thematic_trimming.oil is False
        assert thematic_trimming.nuclear is True
        assert thematic_trimming.psp_open_level is None

        ########## Settings ##########
        settings = study.get_settings()
        assert settings.adequacy_patch_parameters.set_to_null_ntc_between_physical_out_for_first_step is None
        assert settings.advanced_parameters.shedding_policy == SheddingPolicy.ACCURATE_SHAVE_PEAKS
        new_settings = StudySettingsUpdate(general_parameters=GeneralParametersUpdate(nb_years=4))
        study.update_settings(new_settings)
        assert study.get_settings().general_parameters.nb_years == 4

        ########## Scenario Builder ##########
        sc_builder = study.get_scenario_builder()
        assert sc_builder.load.get_area("fr").get_scenario() == [None, None, None, None]
        assert sc_builder.hydro_final_level is not None
        assert sc_builder.hydro_final_level.get_area("fr").get_scenario() == [None, None, None, None]
        assert sc_builder.hydro_initial_level.get_area("fr").get_scenario() == [None, None, None, None]

        sc_builder.load.get_area("fr").set_new_scenario([None, None, 2, 4])
        sc_builder.hydro_final_level.get_area("fr").set_new_scenario([1, 4, 2, 3])
        study.set_scenario_builder(sc_builder)

        sc_builder = study.get_scenario_builder()
        assert sc_builder.load.get_area("fr").get_scenario() == [None, None, 2, 4]
        assert sc_builder.hydro_final_level.get_area("fr").get_scenario() == [1, 4, 2, 3]
        assert sc_builder.hydro_initial_level.get_area("fr").get_scenario() == [None, None, None, None]

        ########## Simulation ##########

        parameters = AntaresSimulationParameters(nb_cpu=4, output_suffix="test_integration")
        job = study.run_antares_simulation(parameters)
        assert isinstance(job, Job)
        assert job.status == JobStatus.PENDING

        study.wait_job_completion(job, time_out=60)
        assert job.status == JobStatus.SUCCESS

        ########## Outputs ##########

        output = list(study.get_outputs().values())[0]
        assert output.name.endswith("test_integration")
        aggregated_df = output.aggregate_mc_all_areas(
            MCAllAreasDataType.VALUES, Frequency.ANNUAL, columns_names=["NODU EXP", "LOLD MAX"]
        )
        cols = ["area", "timeId", "LOLD MAX", "NODU EXP"]
        data = [["be", 1, 0.0, 0.0], ["fr", 1, 0.0, 0.0]]
        expected_df = pd.DataFrame(data=data, columns=cols)
        assert expected_df.equals(aggregated_df)

        ######################
        # Specific tests for study version 9.3
        ######################

        # Create a study with an area
        study = create_study_api("Study_9.3", "9.3", api_config)
        area_fr = study.create_area("FR")

        ####### Clusters #######

        thermal_properties = ThermalClusterProperties(group="free group")
        thermal = area_fr.create_thermal_cluster("thermal", thermal_properties)
        assert thermal.properties.group == "free group"

        renewable_properties = RenewableClusterProperties(group="free group")
        renewable = area_fr.create_renewable_cluster("renewable", renewable_properties)
        assert renewable.properties.group == "free group"

        ####### Short-term storages #######

        sts_properties = STStorageProperties(allow_overflow=True)
        storage = area_fr.create_st_storage("sts", sts_properties)
        assert storage.properties.allow_overflow is True

        sts_properties_upd = STStoragePropertiesUpdate(allow_overflow=False)
        new_sts_properties = storage.update_properties(sts_properties_upd)
        assert new_sts_properties.allow_overflow is False

        ####### Thematic trimming #######

        current_trimming = study.get_settings().thematic_trimming_parameters
        assert current_trimming.renewable_gen is True
        assert current_trimming.dispatch_gen is True
        assert current_trimming.ov_cost is True

        study.set_thematic_trimming(ThematicTrimmingParameters(renewable_gen=False, ov_cost=False))
        new_trimming = study.get_settings().thematic_trimming_parameters
        assert new_trimming.renewable_gen is False
        assert new_trimming.dispatch_gen is True
        assert new_trimming.ov_cost is False

        ####### Scenario Builder #######

        # Set the nb_years to 4
        study.update_settings(StudySettingsUpdate(general_parameters=GeneralParametersUpdate(nb_years=4)))

        # Creates a short-term storage constraint
        sts_constraint = [STStorageAdditionalConstraint(name="c1", occurrences=[Occurrence([1, 3])])]
        sts = study.get_areas()["fr"].get_st_storages()["sts"]
        sts.create_constraints(sts_constraint)

        # Reads the scenario builder
        sc_builder = study.get_scenario_builder()
        assert sc_builder.storage_constraints is not None
        assert sc_builder.storage_inflows is not None
        assert sc_builder.storage_inflows.get_storage("fr", "sts").get_scenario() == [None, None, None, None]

        # Sets a new scenario builder
        sc_builder.storage_inflows.get_storage("fr", "sts").set_new_scenario([1, None, 3, None])
        sc_builder.storage_constraints.get_constraint("fr", "sts", "c1").set_new_scenario([4, 3, 2, 1])
        study.set_scenario_builder(sc_builder)

        # Reads the new scenario builder
        new_sc_builder = study.get_scenario_builder()
        assert new_sc_builder.storage_constraints is not None
        assert new_sc_builder.storage_inflows is not None

        assert new_sc_builder.storage_inflows.get_storage("fr", "sts").get_scenario() == [1, None, 3, None]
        assert new_sc_builder.storage_constraints.get_constraint("fr", "sts", "c1").get_scenario() == [4, 3, 2, 1]
