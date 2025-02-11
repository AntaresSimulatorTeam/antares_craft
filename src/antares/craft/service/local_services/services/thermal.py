
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
