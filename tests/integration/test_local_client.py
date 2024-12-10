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

import re

import numpy as np
import pandas as pd

from antares import create_study_local
from antares.exceptions.exceptions import (
    AreaCreationError,
    InvalidNameError,
    LinkCreationError,
)
from antares.model.area import AdequacyPatchMode, Area, AreaProperties, AreaUi
from antares.model.binding_constraint import BindingConstraintProperties, ClusterData, ConstraintTerm, LinkData
from antares.model.commons import FilterOption
from antares.model.link import Link, LinkProperties, LinkUi
from antares.model.renewable import RenewableClusterGroup, RenewableClusterProperties
from antares.model.settings.general import GeneralParametersLocal, Mode
from antares.model.settings.playlist_parameters import PlaylistParameters
from antares.model.settings.study_settings import StudySettingsLocal
from antares.model.st_storage import STStorageGroup, STStorageProperties
from antares.model.study import Study
from antares.model.thermal import ThermalCluster, ThermalClusterGroup, ThermalClusterProperties
from antares.tools.ini_tool import IniFile, IniFileTypes
from antares.tools.time_series_tool import TimeSeriesFileType


class TestLocalClient:
    def test_local_study(self, tmp_path, other_area):
        study_name = "test study"
        study_version = "880"

        # Study
        test_study = create_study_local(study_name, study_version, tmp_path.absolute())
        assert isinstance(test_study, Study)

        # Areas
        fr = test_study.create_area("fr")
        at = test_study.create_area("at")

        assert isinstance(fr, Area)
        assert isinstance(at, Area)

        ## Area already exists
        with pytest.raises(
            AreaCreationError,
            match="Could not create the area fr: There is already an area 'fr' in the study 'test study'",
        ):
            test_study.create_area("fr")

        # Link
        at_fr = test_study.create_link(area_from=fr.id, area_to=at.id)

        assert isinstance(at_fr, Link)

        ## Cannot link areas that don't exist in the study
        with pytest.raises(LinkCreationError, match="Could not create the link fr / usa: usa does not exist."):
            test_study.create_link(area_from=fr.id, area_to=other_area.id)

        # Thermal
        fr_nuclear = fr.create_thermal_cluster("nuclear")

        assert isinstance(fr_nuclear, ThermalCluster)

        # Setup time series for following tests
        time_series_rows = 10  # 365 * 24
        time_series_columns = 1
        time_series = pd.DataFrame(np.around(np.random.rand(time_series_rows, time_series_columns)))

        # Load
        fr.create_load(time_series)

        assert test_study.service.config.study_path.joinpath(
            TimeSeriesFileType.LOAD.value.format(area_id=fr.id)
        ).is_file()

        fr_load = fr.get_load_matrix()

        assert fr_load.equals(time_series)

        # Solar
        fr.create_solar(time_series)

        assert test_study.service.config.study_path.joinpath(
            TimeSeriesFileType.SOLAR.value.format(area_id=fr.id)
        ).is_file()

        fr_solar = fr.get_solar_matrix()

        assert fr_solar.equals(time_series)

        # Wind
        fr.create_wind(time_series)

        assert test_study.service.config.study_path.joinpath(
            TimeSeriesFileType.WIND.value.format(area_id=fr.id)
        ).is_file()

        fr_wind = fr.get_wind_matrix()

        assert fr_wind.equals(time_series)

        # Forbidden character errors
        area_name = "BE?"
        with pytest.raises(
            InvalidNameError,
            match=(
                re.escape(
                    f"The name {area_name} contains one or more unauthorized characters."
                    + "\nNames can only contain: a-z, A-Z, 0-9, (, ), &, _, - and , (comma)."
                )
            ),
        ):
            test_study.create_area(area_name)

        # tests area creation with ui values
        area_name = "BE"
        area_ui = AreaUi(x=120, color_rgb=[255, 123, 0])
        area_be = test_study.create_area(area_name, ui=area_ui)

        assert area_be.name == area_name
        assert area_be.id == "be"
        assert area_be.ui.x == area_ui.x
        assert area_be.ui.color_rgb == area_ui.color_rgb
        be_ui_file = test_study.service.config.study_path.joinpath(
            IniFileTypes.AREA_UI_INI.value.format(area_id=area_be.id)
        )
        assert be_ui_file.is_file()

        # tests area creation with properties
        properties = AreaProperties()
        properties.energy_cost_spilled = 123
        properties.adequacy_patch_mode = AdequacyPatchMode.INSIDE
        properties.filter_synthesis = [FilterOption.HOURLY, FilterOption.DAILY, FilterOption.HOURLY]
        area_name = "DE"
        area_de = test_study.create_area(area_name, properties=properties)
        assert area_de.properties.energy_cost_spilled == 123
        assert area_de.properties.adequacy_patch_mode == AdequacyPatchMode.INSIDE
        assert area_de.properties.filter_synthesis == {FilterOption.HOURLY, FilterOption.DAILY}

        # tests link creation with default values
        link_de_fr = test_study.create_link(area_from=area_de.id, area_to=fr.id)
        assert link_de_fr.area_from == area_de.id
        assert link_de_fr.area_to == fr.id
        assert link_de_fr.name == f"{area_de.id} / {fr.id}"

        # tests link creation with ui and properties
        link_ui = LinkUi(colorr=44)
        link_properties = LinkProperties(hurdles_cost=True)
        link_properties.filter_year_by_year = [FilterOption.HOURLY]
        link_be_fr = test_study.create_link(area_from=area_be.id, area_to=fr.id, ui=link_ui, properties=link_properties)
        assert link_be_fr.ui.colorr == 44
        assert link_be_fr.properties.hurdles_cost
        assert link_be_fr.properties.filter_year_by_year == {FilterOption.HOURLY}
        be_link_ini_file = test_study.service.config.study_path.joinpath(
            IniFileTypes.LINK_PROPERTIES_INI.value.format(area_id=area_be.id)
        )
        assert be_link_ini_file.is_file()
        be_links_in_file = IniFile(test_study.service.config.study_path, IniFileTypes.LINK_PROPERTIES_INI, area_be.id)
        assert be_links_in_file.ini_dict["fr"]["hurdles-cost"] == "true"
        assert be_links_in_file.ini_dict["fr"]["filter-year-by-year"] == "hourly"

        # asserts study contains all links and areas
        assert test_study.get_areas() == {at.id: at, area_be.id: area_be, fr.id: fr, area_de.id: area_de}
        assert test_study.get_links() == {at_fr.name: at_fr, link_be_fr.name: link_be_fr, link_de_fr.name: link_de_fr}

        # test thermal cluster creation with default values
        thermal_name = "Cluster_test %?"
        with pytest.raises(InvalidNameError):
            fr.create_thermal_cluster(thermal_name)

        thermal_name = "Cluster_test"
        thermal_fr = fr.create_thermal_cluster(thermal_name)

        assert thermal_fr.id == "cluster_test"

        # test thermal cluster creation with properties
        thermal_name = "gaz_be"
        thermal_properties = ThermalClusterProperties(efficiency=55)
        thermal_properties.group = ThermalClusterGroup.GAS
        thermal_be = area_be.create_thermal_cluster(thermal_name, thermal_properties)
        properties = thermal_be.properties
        assert properties.efficiency == 55
        assert properties.group == ThermalClusterGroup.GAS

        # test renewable cluster creation with default values
        renewable_name = "cluster_test"
        renewable_fr = fr.create_renewable_cluster(renewable_name, None, None)
        assert renewable_fr.name == renewable_name
        assert renewable_fr.id == "cluster_test"

        # test renewable cluster creation with properties
        renewable_name = "wind_onshore"
        renewable_properties = RenewableClusterProperties(enabled=False)
        renewable_properties.group = RenewableClusterGroup.WIND_ON_SHORE
        renewable_onshore = fr.create_renewable_cluster(renewable_name, renewable_properties, None)
        properties = renewable_onshore.properties
        assert not properties.enabled
        assert properties.group == RenewableClusterGroup.WIND_ON_SHORE

        # test short term storage creation with default values
        st_storage_name = "cluster_test"
        storage_fr = fr.create_st_storage(st_storage_name)
        assert storage_fr.name == st_storage_name
        assert storage_fr.id == "cluster_test"

        # test short term storage creation with properties
        st_storage_name = "wind_onshore"
        storage_properties = STStorageProperties(reservoir_capacity=0.5)
        storage_properties.group = STStorageGroup.BATTERY
        battery_fr = fr.create_st_storage(st_storage_name, storage_properties)
        properties = battery_fr.properties
        assert properties.reservoir_capacity == 0.5
        assert properties.group == STStorageGroup.BATTERY

        # test binding constraint creation without terms
        properties = BindingConstraintProperties(enabled=False)
        properties.group = "group_1"
        constraint_1 = test_study.create_binding_constraint(name="bc_1", properties=properties)
        assert constraint_1.name == "bc_1"
        assert not constraint_1.properties.enabled
        assert constraint_1.properties.group == "group_1"
        assert constraint_1.get_terms() == {}

        # test binding constraint creation with terms
        link_data = LinkData(area1=area_be.id, area2=fr.id)
        link_term_2 = ConstraintTerm(data=link_data, weight=2)
        cluster_data = ClusterData(area=fr.id, cluster=thermal_fr.id)
        cluster_term = ConstraintTerm(data=cluster_data, weight=4.5, offset=3)
        terms = [link_term_2, cluster_term]
        constraint_2 = test_study.create_binding_constraint(name="bc_2", terms=terms)
        assert constraint_2.name == "bc_2"
        assert constraint_2.get_terms() == {link_term_2.id: link_term_2, cluster_term.id: cluster_term}

        # test adding terms to a constraint
        link_data = LinkData(area1=area_de.id, area2=fr.id)
        link_term_1 = ConstraintTerm(data=link_data, weight=15)
        cluster_data = ClusterData(area=area_be.id, cluster=thermal_be.id)
        cluster_term = ConstraintTerm(data=cluster_data, weight=100)
        terms = [link_term_1, cluster_term]
        constraint_1.add_terms(terms)
        assert constraint_1.get_terms() == {link_term_1.id: link_term_1, cluster_term.id: cluster_term}

        # Case that succeeds
        properties = BindingConstraintProperties(operator="less")
        matrix = pd.DataFrame(data=(np.ones((8784, 1))))
        constraint_3 = test_study.create_binding_constraint(name="bc_3", less_term_matrix=matrix, properties=properties)
        assert constraint_3.get_less_term_matrix().equals(matrix)

        # asserts study contains the constraints
        assert test_study.get_binding_constraints() == {
            constraint_1.id: constraint_1,
            constraint_2.id: constraint_2,
            constraint_3.id: constraint_3,
        }

        # test study creation with settings
        settings = StudySettingsLocal()
        settings.general_parameters = GeneralParametersLocal(mode="Adequacy")
        settings.general_parameters.year_by_year = False
        settings.playlist_parameters = PlaylistParameters()
        settings.playlist_parameters.playlist = [{"status": False, "weight": 1}]
        new_study = create_study_local("second_study", "880", tmp_path, settings)
        settings = new_study.get_settings()
        assert settings.general_parameters.mode == Mode.ADEQUACY.value
        assert not settings.general_parameters.year_by_year
        assert settings.playlist_parameters.model_dump() == {1: {"status": False, "weight": 1}}
