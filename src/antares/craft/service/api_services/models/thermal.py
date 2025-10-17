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
            enabled=self.enabled,
            unit_count=self.unit_count,
            nominal_capacity=self.nominal_capacity,
            group=self.group,
            gen_ts=self.gen_ts,
            min_stable_power=self.min_stable_power,
            min_up_time=self.min_up_time,
            min_down_time=self.min_down_time,
            must_run=self.must_run,
            spinning=self.spinning,
            volatility_forced=self.volatility_forced,
            volatility_planned=self.volatility_planned,
            law_forced=self.law_forced,
            law_planned=self.law_planned,
            marginal_cost=self.marginal_cost,
            spread_cost=self.spread_cost,
            fixed_cost=self.fixed_cost,
            startup_cost=self.startup_cost,
            market_bid_cost=self.market_bid_cost,
            co2=self.co2,
            nh3=self.nh3,
            so2=self.so2,
            nox=self.nox,
            pm2_5=self.pm2_5,
            pm5=self.pm5,
            pm10=self.pm10,
            nmvoc=self.nmvoc,
            op1=self.op1,
            op2=self.op2,
            op3=self.op3,
            op4=self.op4,
            op5=self.op5,
            cost_generation=self.cost_generation,
            efficiency=self.efficiency,
            variable_o_m_cost=self.variable_o_m_cost,
        )
