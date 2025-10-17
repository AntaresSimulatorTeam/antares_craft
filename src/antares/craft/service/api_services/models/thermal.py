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

from dataclasses import asdict

from antares.craft.model.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalClusterProperties,
    ThermalClusterPropertiesUpdate,
    ThermalCostGeneration,
)
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.service.utils import check_field_is_not_null

ThermalPropertiesType = ThermalClusterProperties | ThermalClusterPropertiesUpdate


class ThermalClusterPropertiesAPI(APIBaseModel):
    enabled: bool | None = None
    unit_count: int | None = None
    nominal_capacity: float | None = None
    group: str | None = None
    gen_ts: LocalTSGenerationBehavior | None = None
    min_stable_power: float | None = None
    min_up_time: int | None = None
    min_down_time: int | None = None
    must_run: bool | None = None
    spinning: float | None = None
    volatility_forced: float | None = None
    volatility_planned: float | None = None
    law_forced: LawOption | None = None
    law_planned: LawOption | None = None
    marginal_cost: float | None = None
    spread_cost: float | None = None
    fixed_cost: float | None = None
    startup_cost: float | None = None
    market_bid_cost: float | None = None
    co2: float | None = None
    nh3: float | None = None
    so2: float | None = None
    nox: float | None = None
    pm2_5: float | None = None
    pm5: float | None = None
    pm10: float | None = None
    nmvoc: float | None = None
    op1: float | None = None
    op2: float | None = None
    op3: float | None = None
    op4: float | None = None
    op5: float | None = None
    cost_generation: ThermalCostGeneration | None = None
    efficiency: float | None = None
    variable_o_m_cost: float | None = None

    @staticmethod
    def from_user_model(user_class: ThermalPropertiesType) -> "ThermalClusterPropertiesAPI":
        user_dict = asdict(user_class)
        return ThermalClusterPropertiesAPI.model_validate(user_dict)

    def to_user_model(self) -> ThermalClusterProperties:
        return ThermalClusterProperties(
            enabled=check_field_is_not_null(self.enabled),
            unit_count=check_field_is_not_null(self.unit_count),
            nominal_capacity=check_field_is_not_null(self.nominal_capacity),
            group=check_field_is_not_null(self.group),
            gen_ts=check_field_is_not_null(self.gen_ts),
            min_stable_power=check_field_is_not_null(self.min_stable_power),
            min_up_time=check_field_is_not_null(self.min_up_time),
            min_down_time=check_field_is_not_null(self.min_down_time),
            must_run=check_field_is_not_null(self.must_run),
            spinning=check_field_is_not_null(self.spinning),
            volatility_forced=check_field_is_not_null(self.volatility_forced),
            volatility_planned=check_field_is_not_null(self.volatility_planned),
            law_forced=check_field_is_not_null(self.law_forced),
            law_planned=check_field_is_not_null(self.law_planned),
            marginal_cost=check_field_is_not_null(self.marginal_cost),
            spread_cost=check_field_is_not_null(self.spread_cost),
            fixed_cost=check_field_is_not_null(self.fixed_cost),
            startup_cost=check_field_is_not_null(self.startup_cost),
            market_bid_cost=check_field_is_not_null(self.market_bid_cost),
            co2=check_field_is_not_null(self.co2),
            nh3=check_field_is_not_null(self.nh3),
            so2=check_field_is_not_null(self.so2),
            nox=check_field_is_not_null(self.nox),
            pm2_5=check_field_is_not_null(self.pm2_5),
            pm5=check_field_is_not_null(self.pm5),
            pm10=check_field_is_not_null(self.pm10),
            nmvoc=check_field_is_not_null(self.nmvoc),
            op1=check_field_is_not_null(self.op1),
            op2=check_field_is_not_null(self.op2),
            op3=check_field_is_not_null(self.op3),
            op4=check_field_is_not_null(self.op4),
            op5=check_field_is_not_null(self.op5),
            cost_generation=check_field_is_not_null(self.cost_generation),
            efficiency=check_field_is_not_null(self.efficiency),
            variable_o_m_cost=check_field_is_not_null(self.variable_o_m_cost),
        )
