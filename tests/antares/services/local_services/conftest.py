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

from pathlib import Path

import pandas as pd

from antares.craft import LinkProperties, LinkUi, create_study_local
from antares.craft.model.area import Area, AreaProperties, AreaUi
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintOperator,
    BindingConstraintProperties,
    ConstraintTerm,
    LinkData,
)
from antares.craft.model.commons import FilterOption
from antares.craft.model.hydro import HydroProperties, HydroPropertiesUpdate
from antares.craft.model.renewable import RenewableClusterProperties
from antares.craft.model.st_storage import STStorageProperties
from antares.craft.model.study import Study
from antares.craft.model.thermal import (
    ThermalClusterGroup,
    ThermalClusterProperties,
)


@pytest.fixture
def local_study(tmp_path: Path) -> Study:
    study_name = "studyTest"
    study_version = "880"
    return create_study_local(study_name, study_version, tmp_path.absolute())


@pytest.fixture
def local_study_w_areas(tmp_path: Path, local_study: Study) -> Study:
    areas_to_create = ["fr", "it"]
    for area in areas_to_create:
        area_properties = AreaProperties(
            energy_cost_spilled=1, energy_cost_unsupplied=0.5, filter_synthesis={FilterOption.WEEKLY}
        )
        area_ui = AreaUi(x=56)
        local_study.create_area(area, properties=area_properties, ui=area_ui)
    return local_study


@pytest.fixture
def local_study_w_links(tmp_path: Path, local_study_w_areas: Study):
    local_study_w_areas.create_area("at")
    links_to_create = ["fr_at", "at_it", "fr_it"]
    for link in links_to_create:
        area_from, area_to = link.split("_")
        properties = LinkProperties(use_phase_shifter=True, filter_synthesis={FilterOption.WEEKLY})
        ui = LinkUi(colorr=1, link_width=29)
        local_study_w_areas.create_link(area_from=area_from, area_to=area_to, properties=properties, ui=ui)

    return local_study_w_areas


@pytest.fixture
def local_study_w_constraints(tmp_path: Path, local_study_w_links: Study) -> Study:
    bc_props = BindingConstraintProperties(operator=BindingConstraintOperator.GREATER, enabled=False)
    local_study_w_links.create_binding_constraint(name="bc_1", properties=bc_props)

    term = ConstraintTerm(data=LinkData(area1="at", area2="fr"), weight=2)
    local_study_w_links.create_binding_constraint(name="bc_2", terms=[term])
    return local_study_w_links


@pytest.fixture
def local_study_w_thermal(tmp_path: Path, local_study_w_links: Study) -> Study:
    thermal_name = "test thermal cluster"
    thermal_properties = ThermalClusterProperties(must_run=True, group=ThermalClusterGroup.NUCLEAR)
    local_study_w_links.get_areas()["fr"].create_thermal_cluster(thermal_name, properties=thermal_properties)
    return local_study_w_links


@pytest.fixture
def local_study_w_thermals(tmp_path: Path, local_study_w_thermal: Study) -> Study:
    local_study_w_thermal.get_areas()["fr"].create_thermal_cluster("thermal_fr_2")
    local_study_w_thermal.get_areas()["it"].create_thermal_cluster("thermal_it")
    return local_study_w_thermal


@pytest.fixture
def local_study_w_storage(tmp_path: Path, local_study_w_areas: Study) -> Study:
    st_properties = STStorageProperties(efficiency=0.4, initial_level_optim=True)
    local_study_w_areas.get_areas()["fr"].create_st_storage("sts_1", st_properties)
    local_study_w_areas.get_areas()["fr"].create_st_storage("sts_2", st_properties)
    return local_study_w_areas


@pytest.fixture
def local_study_with_renewable(local_study_w_thermal: Study) -> Study:
    cluster_name = "renewable cluster"
    renewable_properties = RenewableClusterProperties(enabled=False, unit_count=44)
    local_study_w_thermal.get_areas()["fr"].create_renewable_cluster(cluster_name, properties=renewable_properties)
    return local_study_w_thermal


@pytest.fixture
def local_study_with_st_storage(local_study_with_renewable: Study) -> Study:
    storage_name = "short term storage"
    local_study_with_renewable.get_areas()["fr"].create_st_storage(storage_name)
    return local_study_with_renewable


@pytest.fixture
def local_study_with_hydro(local_study_with_st_storage: Study) -> Study:
    hydro_properties = HydroPropertiesUpdate(reservoir_capacity=4.3, use_heuristic=False)
    local_study_with_st_storage.get_areas()["fr"].hydro.update_properties(hydro_properties)
    return local_study_with_st_storage


@pytest.fixture
def default_hydro_properties() -> HydroProperties:
    return HydroProperties(
        inter_daily_breakdown=1,
        intra_daily_modulation=24,
        inter_monthly_breakdown=1,
        reservoir=False,
        reservoir_capacity=0,
        follow_load=True,
        use_water=False,
        hard_bounds=False,
        initialize_reservoir_date=0,
        use_heuristic=True,
        power_to_level=False,
        use_leeway=False,
        leeway_low=1,
        leeway_up=1,
        pumping_efficiency=1,
    )


@pytest.fixture
def area_fr(local_study_with_hydro: Study) -> Area:
    return local_study_with_hydro.get_areas()["fr"]


@pytest.fixture
def fr_solar(area_fr: Area) -> None:
    return area_fr.set_solar(pd.DataFrame())


@pytest.fixture
def fr_wind(area_fr: Area) -> None:
    return area_fr.set_wind(pd.DataFrame())


@pytest.fixture
def fr_load(area_fr: Area) -> None:
    return area_fr.set_load(pd.DataFrame())


@pytest.fixture
def local_study_with_constraint(local_study_with_hydro: Study) -> Study:
    local_study_with_hydro.create_binding_constraint(name="test constraint")
    return local_study_with_hydro


@pytest.fixture
def test_constraint(local_study_with_constraint: Study) -> BindingConstraint:
    return local_study_with_constraint.get_binding_constraints()["test constraint"]
