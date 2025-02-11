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
from antares.craft.model.thermal import LocalTSGenerationBehavior, ThermalClusterGroup, LawOption, ThermalCostGeneration
from antares.craft.service.local_services.models import LocalBaseModel


class ThermalClusterPropertiesLocal(LocalBaseModel):
    enabled: bool = True
    unit_count: int = 1
    nominal_capacity: float = 0
    group: ThermalClusterGroup = ThermalClusterGroup.OTHER1
    gen_ts: LocalTSGenerationBehavior = LocalTSGenerationBehavior.USE_GLOBAL
    min_stable_power: float = 0
    min_up_time: int = 1
    min_down_time: int = 1
    must_run: bool = False
    spinning: float = 0
    volatility_forced: float = 0
    volatility_planned: float = 0
    law_forced: LawOption = LawOption.UNIFORM
    law_planned: LawOption = LawOption.UNIFORM
    marginal_cost: float = 0
    spread_cost: float = 0
    fixed_cost: float = 0
    startup_cost: float = 0
    market_bid_cost: float = 0
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
    cost_generation: ThermalCostGeneration = ThermalCostGeneration.SET_MANUALLY
    efficiency: float = 100
    variable_o_m_cost: float = 0


class ThermalClusterPropertiesLocal(DefaultThermalProperties):
    thermal_name: str

    @property
    def list_ini_fields(self) -> dict[str, dict[str, str]]:
        return {
            f"{self.thermal_name}": {
                "group": self.group.value,
                "name": self.thermal_name,
                "enabled": f"{self.enabled}",
                "unitcount": f"{self.unit_count}",
                "nominalcapacity": f"{self.nominal_capacity:.6f}",
                "gen-ts": self.gen_ts.value,
                "min-stable-power": f"{self.min_stable_power:.6f}",
                "min-up-time": f"{self.min_up_time}",
                "min-down-time": f"{self.min_down_time}",
                "must-run": f"{self.must_run}",
                "spinning": f"{self.spinning:.6f}",
                "volatility.forced": f"{self.volatility_forced:.6f}",
                "volatility.planned": f"{self.volatility_planned:.6f}",
                "law.forced": self.law_forced.value,
                "law.planned": self.law_planned.value,
                "marginal-cost": f"{self.marginal_cost:.6f}",
                "spread-cost": f"{self.spread_cost:.6f}",
                "fixed-cost": f"{self.fixed_cost:.6f}",
                "startup-cost": f"{self.startup_cost:.6f}",
                "market-bid-cost": f"{self.market_bid_cost:.6f}",
                "co2": f"{self.co2:.6f}",
                "nh3": f"{self.nh3:.6f}",
                "so2": f"{self.so2:.6f}",
                "nox": f"{self.nox:.6f}",
                "pm2_5": f"{self.pm2_5:.6f}",
                "pm5": f"{self.pm5:.6f}",
                "pm10": f"{self.pm10:.6f}",
                "nmvoc": f"{self.nmvoc:.6f}",
                "op1": f"{self.op1:.6f}",
                "op2": f"{self.op2:.6f}",
                "op3": f"{self.op3:.6f}",
                "op4": f"{self.op4:.6f}",
                "op5": f"{self.op5:.6f}",
                "costgeneration": self.cost_generation.value,
                "efficiency": f"{self.efficiency:.6f}",
                "variableomcost": f"{self.variable_o_m_cost:.6f}",
            }
        }

    def yield_thermal_cluster_properties(self) -> ThermalClusterProperties:
        excludes = {"thermal_name", "list_ini_fields"}
        return ThermalClusterProperties.model_validate(self.model_dump(mode="json", exclude=excludes))
