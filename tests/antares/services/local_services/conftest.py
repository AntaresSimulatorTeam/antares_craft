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

import pandas as pd

from antares.craft import create_study_local
from antares.craft.model.area import Area, AreaProperties, AreaUi
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    ConstraintTerm,
    LinkData,
)
from antares.craft.model.commons import FILTER_VALUES, FilterOption
from antares.craft.model.hydro import HydroProperties, HydroPropertiesUpdate
from antares.craft.model.renewable import RenewableClusterGroup, RenewableClusterProperties, TimeSeriesInterpretation
from antares.craft.model.st_storage import STStorageGroup, STStorageProperties
from antares.craft.model.study import Study
from antares.craft.model.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalClusterGroup,
    ThermalClusterProperties,
    ThermalCostGeneration,
)


@pytest.fixture
def local_study(tmp_path) -> Study:
    study_name = "studyTest"
    study_version = "880"
    return create_study_local(study_name, study_version, tmp_path.absolute())


@pytest.fixture
def local_study_w_areas(tmp_path, local_study) -> Study:
    areas_to_create = ["fr", "it"]
    for area in areas_to_create:
        area_properties = AreaProperties(
            energy_cost_spilled=1, energy_cost_unsupplied=0.5, filter_synthesis={FilterOption.WEEKLY}
        )
        area_ui = AreaUi(x=56)
        local_study.create_area(area, properties=area_properties, ui=area_ui)
    return local_study


@pytest.fixture
def local_study_w_links(tmp_path, local_study_w_areas):
    local_study_w_areas.create_area("at")
    links_to_create = ["fr_at", "at_it", "fr_it"]
    for link in links_to_create:
        area_from, area_to = link.split("_")
        local_study_w_areas.create_link(area_from=area_from, area_to=area_to)

    return local_study_w_areas


@pytest.fixture
def local_study_w_constraints(tmp_path, local_study_w_links) -> Study:
    bc_props = BindingConstraintProperties(operator=BindingConstraintOperator.GREATER, enabled=False)
    local_study_w_links.create_binding_constraint(name="bc_1", properties=bc_props)

    term = ConstraintTerm(data=LinkData(area1="at", area2="fr"), weight=2)
    local_study_w_links.create_binding_constraint(name="bc_2", terms=[term])
    return local_study_w_links


@pytest.fixture
def local_study_w_thermal(tmp_path, local_study_w_links) -> Study:
    thermal_name = "test thermal cluster"
    thermal_properties = ThermalClusterProperties(must_run=True, group=ThermalClusterGroup.NUCLEAR)
    local_study_w_links.get_areas()["fr"].create_thermal_cluster(thermal_name, properties=thermal_properties)
    return local_study_w_links


@pytest.fixture
def local_study_w_thermals(tmp_path, local_study_w_thermal) -> Study:
    local_study_w_thermal.get_areas()["fr"].create_thermal_cluster("thermal_fr_2")
    local_study_w_thermal.get_areas()["it"].create_thermal_cluster("thermal_it")
    return local_study_w_thermal


@pytest.fixture
def local_study_w_storage(tmp_path, local_study_w_areas) -> Study:
    st_properties = STStorageProperties(efficiency=0.4, initial_level_optim=True)
    local_study_w_areas.get_areas()["fr"].create_st_storage("sts_1", st_properties)
    local_study_w_areas.get_areas()["fr"].create_st_storage("sts_2", st_properties)
    return local_study_w_areas


@pytest.fixture
def default_thermal_cluster_properties() -> ThermalClusterProperties:
    return ThermalClusterProperties(
        group=ThermalClusterGroup.OTHER1,
        enabled=True,
        unit_count=1,
        nominal_capacity=0,
        gen_ts=LocalTSGenerationBehavior.USE_GLOBAL,
        min_stable_power=0,
        min_up_time=1,
        min_down_time=1,
        must_run=False,
        spinning=0,
        volatility_forced=0,
        volatility_planned=0,
        law_forced=LawOption.UNIFORM,
        law_planned=LawOption.UNIFORM,
        marginal_cost=0,
        spread_cost=0,
        fixed_cost=0,
        startup_cost=0,
        market_bid_cost=0,
        co2=0,
        nh3=0,
        so2=0,
        nox=0,
        pm2_5=0,
        pm5=0,
        pm10=0,
        nmvoc=0,
        op1=0,
        op2=0,
        op3=0,
        op4=0,
        op5=0,
        cost_generation=ThermalCostGeneration.SET_MANUALLY,
        efficiency=100,
        variable_o_m_cost=0,
    )


@pytest.fixture
def local_study_with_renewable(local_study_w_thermal) -> Study:
    renewable_cluster_name = "renewable cluster"
    local_study_w_thermal.get_areas()["fr"].create_renewable_cluster(renewable_cluster_name)
    return local_study_w_thermal


@pytest.fixture
def default_renewable_cluster_properties() -> RenewableClusterProperties:
    return RenewableClusterProperties(
        enabled=True,
        unit_count=1,
        nominal_capacity=0,
        group=RenewableClusterGroup.OTHER1,
        ts_interpretation=TimeSeriesInterpretation.POWER_GENERATION,
    )


@pytest.fixture
def local_study_with_st_storage(local_study_with_renewable) -> Study:
    storage_name = "short term storage"
    local_study_with_renewable.get_areas()["fr"].create_st_storage(storage_name)
    return local_study_with_renewable


@pytest.fixture
def default_st_storage_properties() -> STStorageProperties:
    return STStorageProperties(
        group=STStorageGroup.OTHER1,
        injection_nominal_capacity=0,
        withdrawal_nominal_capacity=0,
        reservoir_capacity=0,
        efficiency=1,
        initial_level=0.5,
        initial_level_optim=False,
        enabled=True,
    )


@pytest.fixture
def local_study_with_hydro(local_study_with_st_storage) -> Study:
    hydro_properties = HydroPropertiesUpdate(reservoir_capacity=4.3)
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
def area_fr(local_study_with_hydro) -> Area:
    return local_study_with_hydro.get_areas()["fr"]


@pytest.fixture
def fr_solar(area_fr) -> None:
    return area_fr.set_solar(pd.DataFrame())


@pytest.fixture
def fr_wind(area_fr) -> None:
    return area_fr.set_wind(pd.DataFrame())


@pytest.fixture
def fr_load(area_fr) -> None:
    return area_fr.set_load(pd.DataFrame())


@pytest.fixture
def local_study_with_constraint(local_study_with_hydro) -> Study:
    local_study_with_hydro.create_binding_constraint(name="test constraint")
    return local_study_with_hydro


@pytest.fixture
def test_constraint(local_study_with_constraint) -> BindingConstraint:
    return local_study_with_constraint.get_binding_constraints()["test constraint"]


@pytest.fixture
def default_constraint_properties() -> BindingConstraintProperties:
    return BindingConstraintProperties(
        enabled=True,
        time_step=BindingConstraintFrequency.HOURLY,
        operator=BindingConstraintOperator.LESS,
        comments="",
        filter_year_by_year=FILTER_VALUES,
        filter_synthesis=FILTER_VALUES,
        group="default",
    )
