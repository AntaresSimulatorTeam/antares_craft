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

import shutil

from pathlib import Path, PurePath

import numpy as np
import pandas as pd

from antares.craft import (
    AdequacyPatchMode,
    AdvancedParametersUpdate,
    AntaresSimulationParameters,
    APIconf,
    AreaProperties,
    AreaPropertiesUpdate,
    AreaUi,
    AreaUiUpdate,
    AssetType,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
    ClusterData,
    ConstraintTerm,
    ConstraintTermUpdate,
    ExportMPS,
    FilterOption,
    GeneralParametersUpdate,
    HydroPropertiesUpdate,
    LawOption,
    LinkData,
    LinkProperties,
    LinkPropertiesUpdate,
    LinkStyle,
    LinkUi,
    LinkUiUpdate,
    Mode,
    OptimizationParametersUpdate,
    PlaylistParameters,
    RenewableClusterGroup,
    RenewableClusterProperties,
    RenewableClusterPropertiesUpdate,
    RenewableGenerationModeling,
    STStorageGroup,
    STStorageProperties,
    STStoragePropertiesUpdate,
    StudySettingsUpdate,
    ThermalClusterGroup,
    ThermalClusterProperties,
    ThermalClusterPropertiesUpdate,
    TimeSeriesInterpretation,
    TransmissionCapacities,
    UnitCommitmentMode,
    create_study_api,
    create_variant_api,
    import_study_api,
    read_study_api,
)
from antares.craft.exceptions.exceptions import (
    AreaDeletionError,
    BindingConstraintCreationError,
    ConstraintMatrixUpdateError,
    InvalidRequestForScenarioBuilder,
    MatrixUploadError,
    STStorageMatrixUploadError,
    StudySettingsUpdateError,
)
from antares.craft.model.hydro import InflowStructureUpdate
from antares.craft.model.output import Frequency, MCAllLinksDataType, MCAllAreasDataType
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.simulation import Job, JobStatus
from tests.integration.antares_web_desktop import AntaresWebDesktop


@pytest.fixture
def antares_web() -> AntaresWebDesktop:
    app = AntaresWebDesktop()
    app.wait_for_server_to_start()
    yield app
    app.kill()


class TestWebClient:
    def test_lifecycle(self, antares_web: AntaresWebDesktop, tmp_path):
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
            match=f"Error uploading load matrix for area {area_fr.id}: Expected 8760 rows and received 1",
        ):
            area_fr.set_load(wrong_load_matrix)

        # Case that succeeds
        load_matrix = pd.DataFrame(data=np.zeros((8760, 1)))
        area_fr.set_load(load_matrix)

        # tests get load matrix
        assert area_fr.get_load_matrix().equals(load_matrix)

        # asserts solar and wind matrices can be created and read.
        ts_matrix = pd.DataFrame(data=np.ones((8760, 4)))

        area_fr.set_solar(ts_matrix)
        assert area_fr.get_solar_matrix().equals(ts_matrix)

        area_fr.set_wind(ts_matrix)
        assert area_fr.get_wind_matrix().equals(ts_matrix)

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
        thermal_properties = ThermalClusterProperties(efficiency=55, group=ThermalClusterGroup.GAS)
        thermal_be = area_be.create_thermal_cluster(thermal_name, thermal_properties)
        properties = thermal_be.properties
        assert properties.efficiency == 55
        assert properties.group == ThermalClusterGroup.GAS

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
        thermal_value_be = area_fr.create_thermal_cluster(
            thermal_name=thermal_name,
            properties=thermal_properties,
            prepro=prepro_modulation_matrix,
            modulation=modulation_matrix,
            series=series_matrix,
            co2_cost=co2_cost_matrix,
            fuel_cost=fuel_cost_matrix,
        )

        # Updating multiple thermal clusters properties at once
        thermal_update_1 = ThermalClusterPropertiesUpdate(marginal_cost=10.7, enabled=False, nominal_capacity=9.8)
        thermal_update_2 = ThermalClusterPropertiesUpdate(op1=10.2, spread_cost=60.5, group=ThermalClusterGroup.NUCLEAR)
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
        assert be_value_properties.group == ThermalClusterGroup.NUCLEAR
        assert be_value_properties.op2 == 0.0
        assert be_value_properties.marginal_cost == 0.0
        assert be_value_properties.min_up_time == 1

        # Tests get thermal matrices
        prepro = thermal_value_be.get_prepro_data_matrix()
        modulation = thermal_value_be.get_prepro_modulation_matrix()
        series = thermal_value_be.get_series_matrix()
        co2 = thermal_value_be.get_co2_cost_matrix()
        fuel = thermal_value_be.get_fuel_cost_matrix()

        assert prepro.equals(prepro_modulation_matrix)
        assert modulation.equals(modulation_matrix)
        assert series.equals(series_matrix)
        assert co2.equals(co2_cost_matrix)
        assert fuel.equals(fuel_cost_matrix)

        # test renewable cluster creation with default values
        renewable_name = "cluster_test %?"
        renewable_fr = area_fr.create_renewable_cluster(renewable_name, None, None)
        assert renewable_fr.name == renewable_name
        assert renewable_fr.id == "cluster_test"

        # test renewable cluster creation with properties
        renewable_name = "wind_onshore"
        renewable_properties = RenewableClusterProperties(enabled=False, group=RenewableClusterGroup.WIND_ON_SHORE)
        renewable_onshore = area_fr.create_renewable_cluster(renewable_name, renewable_properties, None)
        properties = renewable_onshore.properties
        assert not properties.enabled
        assert properties.group == RenewableClusterGroup.WIND_ON_SHORE

        # Update multiple renewable clusters properties at once
        renewable_update_1 = RenewableClusterPropertiesUpdate(group=RenewableClusterGroup.WIND_ON_SHORE, unit_count=10)
        renewable_update_2 = RenewableClusterPropertiesUpdate(
            group=RenewableClusterGroup.THERMAL_SOLAR, enabled=False, nominal_capacity=1340
        )
        update_for_renewable = {renewable_fr: renewable_update_1, renewable_onshore: renewable_update_2}

        study.update_renewable_clusters(update_for_renewable)

        fr_renew_properties = renewable_fr.properties
        onshore_properties = renewable_onshore.properties

        assert fr_renew_properties.unit_count == 10
        assert fr_renew_properties.group == RenewableClusterGroup.WIND_ON_SHORE
        # checking the old values are not modified
        assert fr_renew_properties.nominal_capacity == 0
        assert fr_renew_properties.enabled

        assert onshore_properties.group == RenewableClusterGroup.THERMAL_SOLAR
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

        # update hydro properties
        hydro_properties = HydroPropertiesUpdate(reservoir=True, reservoir_capacity=4.5)
        area_fr.hydro.update_properties(hydro_properties)
        assert area_fr.hydro.properties.reservoir is True
        assert area_fr.hydro.properties.reservoir_capacity == 4.5

        assert area_fr.hydro.inflow_structure.intermonthly_correlation == 0.5
        # update hydro inflow structure
        area_fr.hydro.update_inflow_structure(InflowStructureUpdate(intermonthly_correlation=0.1))
        assert area_fr.hydro.inflow_structure.intermonthly_correlation == 0.1

        # test short term storage creation with properties
        st_storage_name = "wind_onshore"
        storage_properties = STStorageProperties(reservoir_capacity=0.5, group=STStorageGroup.BATTERY)
        battery_fr = area_fr.create_st_storage(st_storage_name, storage_properties)
        properties = battery_fr.properties
        assert properties.reservoir_capacity == 0.5
        assert properties.group == STStorageGroup.BATTERY

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
        # Case that fails
        wrong_matrix = pd.DataFrame(data=[[0]])
        with pytest.raises(
            STStorageMatrixUploadError,
            match=f"Could not upload inflows matrix for storage {battery_fr.id} inside area {area_fr.id}",
        ):
            battery_fr.set_storage_inflows(wrong_matrix)

        # Case that succeeds
        injection_matrix = pd.DataFrame(data=np.zeros((8760, 1)))
        battery_fr.update_pmax_injection(injection_matrix)

        # tests get pmax_injection matrix
        assert battery_fr.get_pmax_injection().equals(injection_matrix)

        # asserts areas contains the clusters + short term storages
        assert area_be.get_thermals() == {thermal_be.id: thermal_be}
        assert area_fr.get_thermals() == {thermal_fr.id: thermal_fr, thermal_value_be.id: thermal_value_be}
        assert area_be.get_renewables() == {}
        assert area_fr.get_renewables() == {renewable_onshore.id: renewable_onshore, renewable_fr.id: renewable_fr}
        assert area_be.get_st_storages() == {}
        assert area_fr.get_st_storages() == {battery_fr.id: battery_fr, storage_fr.id: storage_fr}

        # using update_st_storages to modify existing storages properties and checking they've been modified
        battery_fr_update = STStoragePropertiesUpdate(
            group=STStorageGroup.PSP_CLOSED, enabled=False, injection_nominal_capacity=1000
        )
        storage_fr_update = STStoragePropertiesUpdate(group=STStorageGroup.PONDAGE, efficiency=0)
        update_for_storages = {battery_fr: battery_fr_update, storage_fr: storage_fr_update}

        study.update_st_storages(update_for_storages)

        battery_fr_properties = battery_fr.properties
        storage_fr_properties = storage_fr.properties
        assert battery_fr_properties.group == STStorageGroup.PSP_CLOSED
        assert not battery_fr_properties.enabled
        assert battery_fr_properties.injection_nominal_capacity == 1000
        # Checking if the other values haven't been modified
        assert battery_fr_properties.initial_level == 0.5
        assert battery_fr_properties.efficiency == 1

        assert storage_fr_properties.group == STStorageGroup.PONDAGE
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
            match="Could not create the binding constraint bc_3",
        ):
            study.create_binding_constraint(name="bc_3", less_term_matrix=wrong_matrix)

        # Other case with failure
        with pytest.raises(
            ConstraintMatrixUpdateError,
            match=f"Could not update matrix eq for binding constraint {constraint_2.id}",
        ):
            constraint_2.set_equal_term(wrong_matrix)

        # Case that succeeds
        properties = BindingConstraintProperties(operator=BindingConstraintOperator.LESS)
        matrix = pd.DataFrame(data=(np.ones((8784, 1))))
        constraint_3 = study.create_binding_constraint(name="bc_3", less_term_matrix=matrix, properties=properties)
        assert constraint_3.get_less_term_matrix().equals(matrix)

        # test update constraint matrices
        new_matrix = pd.DataFrame(data=(np.ones((8784, 1))))
        new_matrix.iloc[0, 0] = 72
        update_properties = BindingConstraintPropertiesUpdate(operator=BindingConstraintOperator.EQUAL)
        constraint_3.update_properties(update_properties)
        constraint_3.set_equal_term(new_matrix)
        assert constraint_3.get_equal_term_matrix().equals(new_matrix)

        # test adding terms to a constraint
        link_data = LinkData(area1=area_de.id, area2=area_fr.id)
        link_term_1 = ConstraintTerm(data=link_data, weight=15)
        cluster_data = ClusterData(area=area_be.id, cluster=thermal_be.id)
        cluster_term = ConstraintTerm(data=cluster_data, weight=100)
        terms = [link_term_1, cluster_term]
        constraint_1.add_terms(terms)
        assert constraint_1.get_terms() == {link_term_1.id: link_term_1, cluster_term.id: cluster_term}

        # asserts study contains the constraints
        assert study.get_binding_constraints() == {
            constraint_1.id: constraint_1,
            constraint_2.id: constraint_2,
            constraint_3.id: constraint_3,
        }

        # tests updating an existing term
        new_term = ConstraintTermUpdate(data=cluster_data, offset=12)
        constraint_1.update_term(new_term)
        updated_term = constraint_1.get_terms()[new_term.id]
        assert updated_term.weight == 100  # Checks the weight wasn't modified
        assert updated_term.offset == 12

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
        new_props.group = ThermalClusterGroup.NUCLEAR
        thermal_fr.update_properties(new_props)
        assert thermal_fr.properties.group == ThermalClusterGroup.NUCLEAR

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
        new_props = STStoragePropertiesUpdate(group=STStorageGroup.PONDAGE)
        battery_fr.update_properties(new_props)
        assert battery_fr.properties.group == STStorageGroup.PONDAGE
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

        # tests constraint term deletion
        constraint_2.delete_term(link_term_2)
        assert link_term_2.id not in constraint_2.get_terms()

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

        assert thermal_fr.get_series_matrix().equals(series_matrix)
        assert thermal_fr.get_prepro_data_matrix().equals(prepro_data_matrix)
        assert thermal_fr.get_prepro_modulation_matrix().equals(prepro_modulation_matrix)
        assert thermal_fr.get_fuel_cost_matrix().equals(series_matrix)
        assert thermal_fr.get_co2_cost_matrix().equals(series_matrix)
        assert renewable_fr.get_timeseries().equals(series_matrix)

        # =======================
        #  SCENARIO BUILDER
        # =======================
        # Sets study nb_years to 4
        study.update_settings(StudySettingsUpdate(general_parameters=GeneralParametersUpdate(nb_years=4)))

        sc_builder = study.get_scenario_builder()

        # Ensures requesting the sc_builder with a wrong name raise a proper issue
        fake_area = "fake_area"
        with pytest.raises(InvalidRequestForScenarioBuilder, match=f"The area {fake_area} does not exist"):
            sc_builder.load.get_area(fake_area)

        # Ensures every value is None as we didn't set anything inside this Study
        assert sc_builder.load.get_area("fr").get_scenario() == [None, None, None, None]

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
            AreaDeletionError,
            match=f"Could not delete the area fr: Area '{area_fr.id}' is not allowed "
            f"to be deleted, because it is referenced in "
            f"the following binding constraints:\n1- 'bc_2'.",
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
        assert actual_settings.advanced_parameters == default_settings.advanced_parameters
        assert actual_settings.thematic_trimming_parameters == default_settings.thematic_trimming_parameters
        # todo: uncomment this check with AntaresWeb 2.20
        # assert actual_settings.adequacy_patch_parameters == default_settings.adequacy_patch_parameters
        assert actual_settings.seed_parameters == default_settings.seed_parameters
        assert actual_settings.playlist_parameters == {1: PlaylistParameters(status=False, weight=1)}

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
        new_study.set_playlist({1: PlaylistParameters(status=True, weight=0.6)})
        assert new_study.get_settings().playlist_parameters == {1: PlaylistParameters(status=True, weight=0.6)}
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
        assert new_settings.playlist_parameters == {1: PlaylistParameters(status=True, weight=0.6)}
        assert new_settings.thematic_trimming_parameters == new_trimming

        # test each hydro matrices returns the good values
        # todo: uncomment this with AntaresWeb version 2.20
        """
        default_reservoir_matrix = np.zeros((365, 3), dtype=np.float64)
        default_reservoir_matrix[:, 1] = 0.5
        default_reservoir_matrix[:, 2] = 1
        default_reservoir = pd.DataFrame(default_reservoir_matrix)
        assert area_fr.hydro.get_reservoir().equals(pd.DataFrame(default_reservoir))

        default_credit_modulation = pd.DataFrame(np.ones((2, 101), dtype=np.float64))
        assert area_fr.hydro.get_credit_modulations().equals(default_credit_modulation)

        default_water_values = pd.DataFrame(np.zeros((365, 101), dtype=np.float64))
        assert area_fr.hydro.get_water_values().equals(default_water_values)

        default_maxpower_matrix = np.zeros((365, 4), dtype=np.float64)
        default_maxpower_matrix[:, 1] = 24
        default_maxpower_matrix[:, 3] = 24
        default_maxpower = pd.DataFrame(default_maxpower_matrix)
        assert area_fr.hydro.get_maxpower().equals(default_maxpower)

        default_inflow_pattern = pd.DataFrame(np.ones((365, 1), dtype=np.float64))
        assert area_fr.hydro.get_inflow_pattern().equals(default_inflow_pattern)

        default_ror = pd.DataFrame(np.zeros((8760, 1), dtype=np.float64))
        assert area_fr.hydro.get_ror_series().equals(default_ror)

        default_mingen = default_ror
        assert area_fr.hydro.get_mingen().equals(default_mingen)

        default_mod = pd.DataFrame(np.zeros((365, 1), dtype=np.float64))
        assert area_fr.hydro.get_mod_series().equals(default_mod)

        default_energy = pd.DataFrame(np.zeros((12, 5), dtype=np.float64))
        assert area_fr.hydro.get_energy().equals(default_energy)
        """

        # tests the update for hydro matrices
        mod_series = pd.DataFrame(data=np.full((365, 1), 100, dtype=np.float64))
        ror_series = pd.DataFrame(data=np.ones((8760, 1)))
        mingen_series = pd.DataFrame(data=np.ones((8760, 1)))
        energy_matrix = pd.DataFrame(data=np.ones((12, 5)))
        max_power = np.full((365, 4), 1000, dtype=np.float64)
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

        assert area_fr.hydro.get_maxpower().equals(maxpower_matrix)
        assert area_fr.hydro.get_reservoir().equals(reservoir_matrix)
        assert area_fr.hydro.get_inflow_pattern().equals(inflow_pattern_matrix)
        assert area_fr.hydro.get_water_values().equals(water_values_matrix)
        assert area_fr.hydro.get_credit_modulations().equals(credits_matrix)
        assert area_fr.hydro.get_ror_series().equals(ror_series)
        assert area_fr.hydro.get_mod_series().equals(mod_series)
        assert area_fr.hydro.get_mingen().equals(mingen_series)
        assert area_fr.hydro.get_energy().equals(energy_matrix)

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
        assert not outputs.get(output.name).archived
        study_with_outputs = read_study_api(api_config, study._study_service.study_id)
        outputs_from_api = study_with_outputs.get_outputs()
        assert all(
            outputs_from_api[output].name == outputs[output].name
            and outputs_from_api[output].archived == outputs[output].archived
            for output in outputs_from_api
        )

        # ===== Output get_matrix =====

        matrix = output.get_matrix("mc-all/grid/links")

        assert isinstance(matrix, pd.DataFrame)
        data = {"upstream": ["be"], "downstream": ["fr"]}
        expected_matrix = pd.DataFrame(data)
        assert matrix.equals(expected_matrix)

        # ===== Output get_mc_all_areas =====

        matrix_all_areas = output.get_mc_all_area(Frequency.DAILY, MCAllAreasDataType.VALUES, area_be.id)

        # ===== Output aggregate_values =====

        aggregated_matrix = output.mc_all_aggregate_links(MCAllLinksDataType.VALUES, Frequency.DAILY)
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
        test_path = Path(antares_web.desktop_path.joinpath("internal_studies").joinpath(study.service.study_id))
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

        # Asserts updating include_exportstructure parameter raises a clear Exception
        update_settings = StudySettingsUpdate()
        update_settings.optimization_parameters = OptimizationParametersUpdate(include_exportstructure=True)
        with pytest.raises(
            StudySettingsUpdateError,
            match=f"Could not update settings for study {imported_study.service.study_id}: AntaresWeb doesn't support editing the parameter include_exportstructure",
        ):
            imported_study.update_settings(update_settings)
