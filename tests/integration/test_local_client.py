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
from antares.exceptions.exceptions import AreaCreationError, LinkCreationError
from antares.model.area import AdequacyPatchMode, Area, AreaProperties, AreaUi
from antares.model.commons import FilterOption
from antares.model.link import Link, LinkProperties, LinkUi
from antares.model.study import Study
from antares.model.thermal import ThermalCluster
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
        at_fr = test_study.create_link(area_from=fr, area_to=at)

        assert isinstance(at_fr, Link)

        ## Cannot link areas that don't exist in the study
        with pytest.raises(LinkCreationError, match="Could not create the link fr / usa: usa does not exist."):
            test_study.create_link(area_from=fr, area_to=other_area)

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
            AreaCreationError,
            match=(
                re.escape(
                    f"Could not create the area {area_name}: "
                    + f"The name {area_name} contains one or more unauthorized characters."
                    + "\nArea names can only contain: a-z, A-Z, 0-9, (, ), &, _, - and , (comma)."
                )
            ),
        ):
            test_study.create_area(area_name)

        # tests area creation with ui values
        area_ui = AreaUi(x=120, color_rgb=[255, 123, 0])
        area_name = "BE?"
        area_be = test_study.create_area(area_name, ui=area_ui)
        assert area_be.name == area_name
        assert area_be.id == "be"
        assert area_be.ui.x == area_ui.x
        assert area_be.ui.color_rgb == area_ui.color_rgb

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
        link_de_fr = test_study.create_link(area_from=area_de, area_to=fr)
        assert link_de_fr.area_from == area_de
        assert link_de_fr.area_to == fr
        assert link_de_fr.name == f"{area_de.id} / {fr.id}"

        # tests link creation with ui and properties
        link_ui = LinkUi(colorr=44)
        link_properties = LinkProperties(hurdles_cost=True)
        link_properties.filter_year_by_year = [FilterOption.HOURLY]
        link_be_fr = test_study.create_link(area_from=area_be, area_to=fr, ui=link_ui, properties=link_properties)
        assert link_be_fr.ui.colorr == 44
        assert link_be_fr.properties.hurdles_cost
        assert link_be_fr.properties.filter_year_by_year == {FilterOption.HOURLY}

        # asserts study contains all links and areas
        assert test_study.get_areas() == {at.id: at, area_be.id: area_be, fr.id: fr, area_de.id: area_de}
        assert test_study.get_links() == {at_fr.name: at_fr, link_be_fr.name: link_be_fr, link_de_fr.name: link_de_fr}
