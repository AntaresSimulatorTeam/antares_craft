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

import numpy as np
import pandas as pd

from antares.api_conf.api_conf import APIconf
from antares.exceptions.exceptions import (
    AreaDeletionError,
    BindingConstraintCreationError,
    ConstraintMatrixUpdateError,
    MatrixUploadError,
    STStorageMatrixUploadError,
)
from antares.model.area import AdequacyPatchMode, AreaProperties, AreaUi, FilterOption
from antares.model.binding_constraint import BindingConstraintProperties, ClusterData, ConstraintTerm, LinkData
from antares.model.link import LinkProperties, LinkStyle, LinkUi
from antares.model.renewable import RenewableClusterGroup, RenewableClusterProperties, TimeSeriesInterpretation
from antares.model.settings.advanced_parameters import AdvancedParameters, UnitCommitmentMode
from antares.model.settings.general import GeneralParameters, Mode
from antares.model.settings.study_settings import PlaylistParameters, StudySettings
from antares.model.st_storage import STStorageGroup, STStorageMatrixName, STStorageProperties
from antares.model.study import create_study_api, read_study_api
from antares.model.thermal import ThermalClusterGroup, ThermalClusterProperties

from tests.integration.antares_web_desktop import AntaresWebDesktop


@pytest.fixture
def antares_web() -> AntaresWebDesktop:
    app = AntaresWebDesktop()
    app.wait_for_server_to_start()
    yield app
    app.kill()


# todo add integration tests for matrices
class TestWebClient:
    def test_creation_lifecycle(self, antares_web: AntaresWebDesktop):
        api_config = APIconf(api_host=antares_web.url, token="", verify=False)

        study = create_study_api("antares-craft-test", "880", api_config)

        actual_study = read_study_api(api_config, study.service.study_id)

        assert study.service.study_id == actual_study.service.study_id
        assert study.name == actual_study.name
        assert study.version == actual_study.version

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
            area_fr.create_load(wrong_load_matrix)

        # Case that succeeds
        load_matrix = pd.DataFrame(data=np.zeros((8760, 1)))
        area_fr.create_load(load_matrix)

        # tests get load matrix
        assert area_fr.get_load_matrix().equals(load_matrix)

        # asserts solar and wind matrices can be created and read.
        ts_matrix = pd.DataFrame(data=np.ones((4, 4)))

        area_fr.create_solar(ts_matrix)
        assert area_fr.get_solar_matrix().equals(ts_matrix)

        area_fr.create_wind(ts_matrix)
        assert area_fr.get_wind_matrix().equals(ts_matrix)

        # tests area creation with ui values
        area_ui = AreaUi(x=100, color_rgb=[255, 0, 0])
        area_name = "BE?"
        area_be = study.create_area(area_name, ui=area_ui)
        assert area_be.name == area_name
        assert area_be.id == "be"
        area_ui = area_be.ui
        assert area_ui.x == area_ui.x
        assert area_ui.color_rgb == area_ui.color_rgb

        # tests area creation with properties
        properties = AreaProperties()
        properties.energy_cost_spilled = 100
        properties.adequacy_patch_mode = AdequacyPatchMode.INSIDE
        properties.filter_synthesis = [FilterOption.HOURLY, FilterOption.DAILY, FilterOption.HOURLY]
        area_name = "DE"
        area_de = study.create_area(area_name, properties=properties)
        assert area_de.properties.energy_cost_spilled == 100
        assert area_de.properties.adequacy_patch_mode == AdequacyPatchMode.INSIDE
        assert area_de.properties.filter_synthesis == {FilterOption.HOURLY, FilterOption.DAILY}

        # tests link creation with default values
        link_de_fr = study.create_link(area_from=area_de, area_to=area_fr)
        assert link_de_fr.area_from == area_de
        assert link_de_fr.area_to == area_fr
        assert link_de_fr.name == f"{area_de.id} / {area_fr.id}"

        # tests link creation with ui and properties
        link_ui = LinkUi(colorr=44)
        link_properties = LinkProperties(hurdles_cost=True)
        link_properties.filter_year_by_year = [FilterOption.HOURLY]
        link_be_fr = study.create_link(area_from=area_be, area_to=area_fr, ui=link_ui, properties=link_properties)
        assert link_be_fr.ui.colorr == 44
        assert link_be_fr.properties.hurdles_cost
        assert link_be_fr.properties.filter_year_by_year == {FilterOption.HOURLY}

        # asserts study contains all links and areas
        assert study.get_areas() == {area_be.id: area_be, area_fr.id: area_fr, area_de.id: area_de}
        assert study.get_links() == {link_be_fr.name: link_be_fr, link_de_fr.name: link_de_fr}

        # test thermal cluster creation with default values
        thermal_name = "Cluster_test %?"
        thermal_fr = area_fr.create_thermal_cluster(thermal_name)
        assert thermal_fr.name == thermal_name.lower()
        # AntaresWeb has id issues for thermal/renewable clusters,
        # so we force the name in lowercase to avoid issues.
        assert thermal_fr.id == "cluster_test"

        # test thermal cluster creation with properties
        thermal_name = "gaz_be"
        thermal_properties = ThermalClusterProperties(efficiency=55)
        thermal_properties.group = ThermalClusterGroup.GAS
        thermal_be = area_be.create_thermal_cluster(thermal_name, thermal_properties)
        properties = thermal_be.properties
        assert properties.efficiency == 55
        assert properties.group == ThermalClusterGroup.GAS

        # test thermal cluster creation with prepro_modulation matrices
        thermal_name = "matrices_be"
        prepro_modulation_matrix = pd.DataFrame(data=np.ones((8760, 4)))
        modulation_matrix = pd.DataFrame(data=np.ones((8760, 4)))
        series_matrix = pd.DataFrame(data=np.ones((8760, 4)))
        CO2Cost_matrix = pd.DataFrame(data=np.ones((8760, 1)))
        fuelCost_matrix = pd.DataFrame(data=np.ones((8760, 1)))

        # Case that succeeds
        thermal_value_be = area_fr.create_thermal_cluster_with_matrices(
            cluster_name=thermal_name,
            parameters=thermal_properties,
            prepro=prepro_modulation_matrix,
            modulation=modulation_matrix,
            series=series_matrix,
            CO2Cost=CO2Cost_matrix,
            fuelCost=fuelCost_matrix,
        )

        prepro = thermal_value_be.get_prepro_data_matrix()
        modulation = thermal_value_be.get_prepro_modulation_matrix()
        series = thermal_value_be.get_series_matrix()
        CO2 = thermal_value_be.get_co2_cost_matrix()
        fuel = thermal_value_be.get_fuel_cost_matrix()

        # tests get thermal matrix
        assert prepro.equals(prepro_modulation_matrix)
        assert modulation.equals(modulation_matrix)
        assert series.equals(series_matrix)
        assert CO2.equals(CO2Cost_matrix)
        assert fuel.equals(fuelCost_matrix)

        # test renewable cluster creation with default values
        renewable_name = "cluster_test %?"
        renewable_fr = area_fr.create_renewable_cluster(renewable_name, None, None)
        assert renewable_fr.name == renewable_name
        assert renewable_fr.id == "cluster_test"

        # test renewable cluster creation with properties
        renewable_name = "wind_onshore"
        renewable_properties = RenewableClusterProperties(enabled=False)
        renewable_properties.group = RenewableClusterGroup.WIND_ON_SHORE
        renewable_onshore = area_fr.create_renewable_cluster(renewable_name, renewable_properties, None)
        properties = renewable_onshore.properties
        assert not properties.enabled
        assert properties.group == RenewableClusterGroup.WIND_ON_SHORE

        # test short term storage creation with default values
        st_storage_name = "cluster_test %?"
        storage_fr = area_fr.create_st_storage(st_storage_name)
        assert storage_fr.name == st_storage_name
        assert storage_fr.id == "cluster_test"

        # test each list of clusters has the same length and objects by comparing their id
        thermal_list = area_fr.read_thermal_clusters(area_fr.id)
        renewable_list = area_fr.read_renewables(area_fr.id)
        storage_list = area_fr.read_st_storages(area_fr.id)

        assert len(thermal_list) == 2
        assert len(renewable_list) == 2
        assert len(storage_list) == 1

        actual_thermal_cluster_1 = thermal_list[0]
        actual_thermal_cluster_2 = thermal_list[1]
        assert actual_thermal_cluster_1.id == thermal_fr.id
        assert actual_thermal_cluster_2.id == thermal_value_be.id

        actual_renewable_1 = renewable_list[0]
        actual_renewable_2 = renewable_list[1]
        assert actual_renewable_1.id == renewable_fr.id
        assert actual_renewable_2.id == renewable_onshore.id

        actual_storage = storage_list[0]
        assert actual_storage.id == storage_fr.id

        # test actual_hydro has the same datas (id, properties and matrices) than area_fr hydro
        actual_hydro = area_fr.read_hydro()
        assert actual_hydro.area_id == area_fr.id
        assert actual_hydro.properties == area_fr.hydro.properties

        # test short term storage creation with properties
        st_storage_name = "wind_onshore"
        storage_properties = STStorageProperties(reservoir_capacity=0.5)
        storage_properties.group = STStorageGroup.BATTERY
        battery_fr = area_fr.create_st_storage(st_storage_name, storage_properties)
        properties = battery_fr.properties
        assert properties.reservoir_capacity == 0.5
        assert properties.group == STStorageGroup.BATTERY

        # test reading list of areas
        area_list = study.read_areas()
        assert len(area_list) == 3
        # asserts areas are sorted by id
        assert area_list[0].id == area_be.id
        assert area_list[1].id == area_de.id
        assert area_list[2].id == area_fr.id
        third_area = area_list[2]
        # checks various variables the list corresponds to the area we created initially
        assert area_fr.ui.x == third_area.ui.x
        assert area_fr.ui.color_rgb == third_area.ui.color_rgb
        assert thermal_fr.id == third_area.get_thermals().get("cluster_test").id
        assert renewable_fr.id == third_area.get_renewables().get("cluster_test").id
        assert storage_fr.id == third_area.get_st_storages().get("cluster_test").id
        assert thermal_be.id == area_list[0].get_thermals().get("gaz_be").id

        # tests upload matrix for short term storage.
        # Case that fails
        wrong_matrix = pd.DataFrame(data=[[0]])
        with pytest.raises(
            STStorageMatrixUploadError,
            match=f"Could not upload {STStorageMatrixName.INFLOWS.value} matrix for storage {battery_fr.id}"
            f" inside area {area_fr.id}",
        ):
            battery_fr.upload_storage_inflows(wrong_matrix)

        # Case that succeeds
        injection_matrix = pd.DataFrame(data=np.zeros((8760, 1)))
        battery_fr.upload_pmax_injection(injection_matrix)

        # tests get pmax_injection matrix
        assert battery_fr.get_pmax_injection().equals(injection_matrix)

        # asserts areas contains the clusters + short term storages
        assert area_be.get_thermals() == {thermal_be.id: thermal_be}
        assert area_fr.get_thermals() == {thermal_fr.id: thermal_fr, thermal_value_be.id: thermal_value_be}
        assert area_be.get_renewables() == {}
        assert area_fr.get_renewables() == {renewable_onshore.id: renewable_onshore, renewable_fr.id: renewable_fr}
        assert area_be.get_st_storages() == {}
        assert area_fr.get_st_storages() == {battery_fr.id: battery_fr, storage_fr.id: storage_fr}

        # test binding constraint creation without terms
        properties = BindingConstraintProperties(enabled=False)
        properties.group = "group_1"
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
            constraint_2.update_equal_term_matrix(wrong_matrix)

        # Case that succeeds
        properties = BindingConstraintProperties(operator="less")
        matrix = pd.DataFrame(data=(np.ones((8784, 1))))
        constraint_3 = study.create_binding_constraint(name="bc_3", less_term_matrix=matrix, properties=properties)
        assert constraint_3.get_less_term_matrix().equals(matrix)

        # test update constraint matrices
        new_matrix = pd.DataFrame(data=(np.ones((8784, 1))))
        new_matrix.iloc[0, 0] = 72
        properties.operator = "equal"
        constraint_3.update_properties(properties)
        constraint_3.update_equal_term_matrix(new_matrix)
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

        # test area property edition
        new_props = AreaProperties()
        new_props.adequacy_patch_mode = AdequacyPatchMode.VIRTUAL
        area_fr.update_properties(new_props)
        assert area_fr.properties.adequacy_patch_mode == AdequacyPatchMode.VIRTUAL

        # test area ui edition
        new_ui = AreaUi()
        new_ui.x = 100
        area_fr.update_ui(new_ui)
        assert area_fr.ui.x == 100

        # test link property edition
        new_props = LinkProperties()
        new_props.hurdles_cost = False
        link_be_fr.update_properties(new_props)
        assert not link_be_fr.properties.hurdles_cost

        # tests link ui edition
        new_ui = LinkUi()
        new_ui.link_style = LinkStyle.PLAIN
        link_be_fr.update_ui(new_ui)
        assert link_be_fr.ui.link_style == LinkStyle.PLAIN

        # tests thermal properties update
        new_props = ThermalClusterProperties()
        new_props.group = ThermalClusterGroup.NUCLEAR
        thermal_fr.update_properties(new_props)
        assert thermal_fr.properties.group == ThermalClusterGroup.NUCLEAR

        # tests renewable properties update
        new_props = RenewableClusterProperties()
        new_props.ts_interpretation = TimeSeriesInterpretation.POWER_GENERATION
        renewable_onshore.update_properties(new_props)
        assert renewable_onshore.properties.ts_interpretation == TimeSeriesInterpretation.POWER_GENERATION

        # tests short term storage properties update
        new_props = STStorageProperties()
        new_props.group = STStorageGroup.PONDAGE
        battery_fr.update_properties(new_props)
        assert battery_fr.properties.group == STStorageGroup.PONDAGE

        # tests constraint properties update
        new_props = BindingConstraintProperties()
        new_props.group = "another_group"
        constraint_1.update_properties(new_props)
        assert constraint_1.properties.group == "another_group"

        # tests constraint deletion
        study.delete_binding_constraint(constraint_1)
        assert constraint_1.id not in study.get_binding_constraints()

        # tests constraint term deletion
        constraint_2.delete_term(link_term_2)
        assert link_term_2.id not in constraint_2.get_terms()

        # tests link deletion
        study.delete_link(link_de_fr)
        assert link_de_fr.name not in study.get_links()

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

        # test study creation with settings
        settings = StudySettings()
        settings.general_parameters = GeneralParameters(mode="Adequacy")
        settings.general_parameters.year_by_year = False
        settings.playlist_parameters = PlaylistParameters()
        settings.playlist_parameters.playlist = [{"status": False, "weight": 1}]
        new_study = create_study_api("second_study", "880", api_config, settings)
        settings = new_study.get_settings()
        assert settings.general_parameters.mode == Mode.ADEQUACY.value
        assert not settings.general_parameters.year_by_year
        assert settings.playlist_parameters.model_dump() == {1: {"status": False, "weight": 1}}

        # tests update settings
        new_settings = StudySettings()
        # Really important note. To instance such object with value you must respect camel case.
        # Another way to do so is to instance the object and then fill its values
        new_settings.general_parameters = GeneralParameters(nbYears=4)
        new_settings.advanced_parameters = AdvancedParameters()
        new_settings.advanced_parameters.unit_commitment_mode = UnitCommitmentMode.MILP
        new_study.update_settings(new_settings)
        assert new_study.get_settings().general_parameters.mode == Mode.ADEQUACY.value
        assert new_study.get_settings().general_parameters.nb_years == 4
        assert new_study.get_settings().advanced_parameters.unit_commitment_mode == UnitCommitmentMode.MILP.value

        old_settings = new_study.get_settings()
        empty_settings = StudySettings()
        new_study.update_settings(empty_settings)
        assert old_settings == new_study.get_settings()
