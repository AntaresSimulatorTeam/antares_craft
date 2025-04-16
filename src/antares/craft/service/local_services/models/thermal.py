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

from pydantic import Field

from antares.craft.model.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalClusterGroup,
    ThermalClusterProperties,
    ThermalClusterPropertiesUpdate,
    ThermalCostGeneration,
)
from antares.craft.service.local_services.models.base_model import LocalBaseModel

ThermalPropertiesType = ThermalClusterProperties | ThermalClusterPropertiesUpdate


class ThermalClusterPropertiesLocal(LocalBaseModel):
    enabled: bool = True
    unit_count: int = Field(default=1, alias="unitcount")
    nominal_capacity: float = Field(default=0, alias="nominalcapacity")
    group: ThermalClusterGroup = ThermalClusterGroup.OTHER1
    gen_ts: LocalTSGenerationBehavior = Field(default=LocalTSGenerationBehavior.USE_GLOBAL, alias="gen-ts")
    min_stable_power: float = Field(default=0, alias="min-stable-power")
    min_up_time: int = Field(default=1, alias="min-up-time")
    min_down_time: int = Field(default=1, alias="min-down-time")
    must_run: bool = Field(default=False, alias="must-run")
    spinning: float = 0
    volatility_forced: float = Field(default=0, alias="volatility.forced")
    volatility_planned: float = Field(default=0, alias="volatility.planned")
    law_forced: LawOption = Field(default=LawOption.UNIFORM, alias="law.forced")
    law_planned: LawOption = Field(default=LawOption.UNIFORM, alias="law.planned")
    marginal_cost: float = Field(default=0, alias="marginal-cost")
    spread_cost: float = Field(default=0, alias="spread-cost")
    fixed_cost: float = Field(default=0, alias="fixed-cost")
    startup_cost: float = Field(default=0, alias="startup-cost")
    market_bid_cost: float = Field(default=0, alias="market-bid-cost")
    co2: float = 0
    nh3: float = 0
    so2: float = 0
    nox: float = 0
    pm2_5: float = 0
    pm5: float = 0
    pm10: float = 0
    nmvoc: float = 0
    op1: float = 0
    op2: float = 0
    op3: float = 0
    op4: float = 0
    op5: float = 0
    cost_generation: ThermalCostGeneration = Field(default=ThermalCostGeneration.SET_MANUALLY, alias="costgeneration")
    efficiency: float = 100
    variable_o_m_cost: float = Field(default=0, alias="variableomcost")

    @staticmethod
    def from_user_model(user_class: ThermalPropertiesType) -> "ThermalClusterPropertiesLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return ThermalClusterPropertiesLocal.model_validate(user_dict)

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
