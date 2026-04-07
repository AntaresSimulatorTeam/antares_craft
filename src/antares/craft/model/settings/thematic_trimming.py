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
from dataclasses import asdict, dataclass
from typing import Optional


# This class is not frozen as it has so many fields, we want the user to be able to fill some values easily.
@dataclass
class ThematicTrimmingParameters:
    """Thematic trimming allows to disable output columns that are not needed for future post-processing.
    Hence reducing the output size of the simulator.

    This class contains all the possible output column names and whether to enable it or not.

    By default all outputs common to versions < 9.1 and >= 9.1 are enabled.

    Attributes:
        ov_cost: Overall cost = operating cost + unsupplied cost + spilled cost + hydro cost.
        op_cost: Operating cost = proportional costs + non-proportional costs.
        mrg_price: Locational marginal price (overall economic effect of a local 1MW load increase).
        co2_emis: Amount of $\\ce{CO2}$ emitted by all dispatchable thermal plants.
        dtg_by_plant: Dispatchable thermal generation for any active thermal cluster.
        balance: Overall import/export balance of the area (positive value: export).
        row_bal: Import/export with areas outside the modeled system (positive value: import).
            Value identical to that defined under the same name in the "Misc Gen" input section.
        psp: User-defined settings for pumping and subsequent generating.
        misc_ndg: Miscellaneous non dispatchable generation.
        load: Demand including demand side management (DSM) potential if relevant.
        h_ror: Hydro generation, run-of-river share.
        wind: Wind generation (only when using aggregated *Renewable generation modeling*).
        h_stor: Power generated from energy storage units (typically: Hydro reservoir).
        h_pump: Power absorbed by energy storage units (typically: PSP pumps consumption).
        h_lev: Energy level remaining in storage units (percentage of reservoir size).
        h_infl: External input to the energy storage units (typically: natural inflows).
        h_ovfl: Wasted natural inflow overflowing from an already full energy storage unit.
        h_val: Marginal value of stored energy (typically: shadow water value)
        h_cost: Expenses/income brought by energy storage actions (`h_stor`, `h_pump`).
        unsp_enrg: Unsupplied energy: adequacy indicator (Expected Energy Not ServedEENS).
        spil_enrg: Unsupplied enery after curtailment sharing rule (CSR) namely demand that cannot be satisfied.
        lold: Loss of load duration: adequacy indicator (length of shortfalls).
        lolp: Loss of Load probability: adequacy indicator.
            Probability of at least one hour of shortfall within the considered period,
            without normalization by the duration of the considered period.
        avl_dtg: Available dispatchable thermal generation: sum of available power over all plants.
        dtg_mrg: Dispatchable thermal generation : avl_dtg - sum of all dispatched thermal generation.
        max_mrg: Maximum margin: operational margin obtained if the hydro storage energy
            of the week were used to maximise margins instead of minimizing costs.
        np_cost: Non-proportional costs of the dispatchable plants (start-up and fixed costs).
        np_cost_by_plant: Non-proportional costs of the dispatchable plants (start-up and fixed costs),
            but by dispatchable plant.
        nodu: Number of dispatched units.
        nodu_by_plant: Number of dispatched units by plant.
        flow_lin: Flow (signed + from upstream to downstream) assessed by the linear optimization.
            These flows follow Kirchhoff's law only if these laws have been explicitly enforced
            by the means of suitable binding constraints.
        ucap_lin: Used capacity: absolute value of `flow_lin`.
            This indicator may be of interest to differentiate the behavior of interconnectors showing low average flows:
            in some cases this may indicate that the line is little used, while in others this may be the outcome of high symmetric flows.
        loop_flow: Flow circulating through the grid when all areas have a zero import/export balance.
            This flow, to be put down to the simplification of the real grid,
            is not subject to hurdle costs in the course of the optimization.
        flow_quad: Flow computed anew, starting from the linear optimum, by minimizing a quadratic function equivalent to an amount of Joule losses,
            while staying within the transmission capacity limits. This calculation uses for this purpose the impedances found in
            the "Links" Input data. If congestions occur on the grid, these results are not equivalent to those of a DC load flow.
        cong_fee_alg: Algebraic congestion rent = linear flow x (downstream price - upstream price).
        cong_fee_abs: Absolute congestion rent = linear flow x abs(downstream price - upstream price).
        marg_cost: Decrease of the system's overall cost that would be brought by the optimal use
            of an additional 1 MW transmission capacity (in both directions).
        cong_prob_plus: Up>Dwn Congestion probability = (NC+) / (total number of MC years) with:
            NC+ = number of years during which the interconnection was congested in the Up>Dwn way
            for **any** length of time within the time frame relevant with the file.
        cong_prob_minus: Dwn>Up Congestion probability = (NC-) / (total number of MC years) with:
            NC- = number of years during which the interconnection was congested in the Dwn>Up way
            for **any** length of time within the time frame relevant with the file.
        hurdle_cost: Contribution of the flows to the overall economic function through the "hurdle costs" component.
            For each hour:
            ```
            if (flow_lin - loop_flow) > 0:
                hurdle_cost = (hourly direct hurdle cost) * (flow_lin)
            else:
                hurdle_cost = (hourly indirect hurdle cost) * (-1) * (flow_lin)
            ```
        res_generation_by_plant: For any active renewable cluster, its production (necessarily must-run).
            Only when using clustered *Renewable generation modeling*.
        dens: Domestic energy not supplied: the difference between the local production capabilities of an area and its local load.
            Please note that this output variable is only available in the economy mode,
            if adequacy patch is activated and the area the output variable belongs to is inside the adequacy patch domain
        profit_by_plant: Net profit of the cluster in euros:
            (`mrg_price` - marginal cost of the cluster) * (dispatchable production of the cluster).
        sts_inj_by_plant: Short-term storage injection by plant.
        sts_withdrawal_by_plant: Short-term storage withdrawal by plant.
        sts_lvl_by_plant: Short-term storage level by plant.
        sts_cashflow_by_cluster: Short-term storage cashflow by cluster.
        npcap_hours: Near price cap hours.
        bc_marg_cost: Binding constraint marginal cost.
        lmr_viol: Local matching rule violation after the Antares Simulation as defined by the adequacy patch.
            Please note that this output variable is only available in the economy mode,
            if adequacy patch is activated and the area the output variable belongs to is inside the adequacy patch domain.
        dtg_mrg_csr: `dtg_mrg` after curtailment sharing rule.
        nh3_emis: Amount of $\\ce{NH3}$ emitted by all dispatchable thermal plants.
        nox_emis: Amount of $\\ce{NOx}$ emitted by all dispatchable thermal plants.
        pm2_5_emis: Amount of $\\ce{PM_{2.5}}$ emitted by all dispatchable thermal plants.
        pm5_emis: Amount of $\\ce{PM5}$ emitted by all dispatchable thermal plants.
        pm10_emis: Amount of $\\ce{PM10}$ emitted by all dispatchable thermal plants.
        op1_emis: Amount of other polluant 1 emitted by all dispatchable thermal plants.
        op2_emis: Amount of other polluant 2 emitted by all dispatchable thermal plants.
        op3_emis: Amount of other polluant 3 emitted by all dispatchable thermal plants.
        op4_emis: Amount of other polluant 4 emitted by all dispatchable thermal plants.
        op5_emis: Amount of other polluant 5 emitted by all dispatchable thermal plants.
        so2_emis: Amount of $\\ce{SO2}$ emitted by all dispatchable thermal plants.
        nmvoc_emis: Amount of $\\ce{NMVOC}$ emitted by all dispatchable thermal plants.
        sts_by_group: **Added since v9.1** Short-term storage by group
        dispatch_gen: **Added since v9.3** Dispatchable generation.
        renewable_gen: **Added since v9.3** Renewable generation.
        psp_open_injection: **Removed since v9.1**
        psp_open_withdrawal: **Removed since v9.1**
        psp_open_level: **Removed since v9.1**
        psp_closed_injection: **Removed since v9.1**
        psp_closed_withdrawal: **Removed since v9.1**
        psp_closed_level: **Removed since v9.1**
        pondage_injection: **Removed since v9.1**
        pondage_withdrawal: **Removed since v9.1**
        pondage_level: **Removed since v9.1**
        battery_injection: **Removed since v9.1**
        battery_withdrawal: **Removed since v9.1**
        battery_level: **Removed since v9.1**
        other1_injection: **Removed since v9.1**
        other1_withdrawal: **Removed since v9.1**
        other1_level: **Removed since v9.1**
        other2_injection: **Removed since v9.1**
        other2_withdrawal: **Removed since v9.1**
        other2_level: **Removed since v9.1**
        other3_injection: **Removed since v9.1**
        other3_withdrawal: **Removed since v9.1**
        other3_level: **Removed since v9.1**
        other4_injection: **Removed since v9.1**
        other4_withdrawal: **Removed since v9.1**
        other4_level: **Removed since v9.1**
        other5_injection: **Removed since v9.1**
        other5_withdrawal: **Removed since v9.1**
        other5_level: **Removed since v9.1**
        misc_dtg_2: **Removed since v9.3** Overall gen. of disp. thermal clusters using other fuels.
        misc_dtg_3: **Removed since v9.3** Overall gen. of disp. thermal clusters using other fuels.
        misc_dtg_4: **Removed since v9.3** Overall gen. of disp. thermal clusters using other fuels.
        wind_offshore: **Removed since v9.3** Wind onshore generation
            (only when using clustered Renewable generation modeling).
        wind_onshore: **Removed since v9.3** Wind onshore generation
            (only when using clustered Renewable generation modeling).
        solar_concrt: **Removed since v9.3** Concentrated Solar Thermal generation
            (only when using clustered Renewable generation modeling).
        solar_pv: **Removed since v9.3** Solar Photovoltaic generation
            (only when using clustered Renewable generation modeling).
        solar_rooft: **Removed since v9.3** Rooftop Solar generation
            (only when using clustered Renewable generation modeling).
        renw_1: **Removed since v9.3** Overall generation of other Renewable clusters
            (only when using clustered Renewable generation modeling).
        renw_2: **Removed since v9.3** Overall generation of other Renewable clusters
            (only when using clustered Renewable generation modeling).
        renw_3: **Removed since v9.3** Overall generation of other Renewable clusters
            (only when using clustered Renewable generation modeling).
        renw_4: **Removed since v9.3** Overall generation of other Renewable clusters
            (only when using clustered Renewable generation modeling).
        solar: **Removed since v9.3** Solar generation thermal and PV
            (only when using aggregated Renewable generation modeling).
        nuclear: **Removed since v9.3** Overall generation of nuclear clusters.
        lignite: **Removed since v9.3** Overall generation of dispatchable thermal clusters burning brown coal.
        coal: **Removed since v9.3** Overall generation of dispatchable thermal clusters burning hard coal.
        gas: **Removed since v9.3** Overall generation of dispatchable thermal clusters burning gas.
        oil: **Removed since v9.3** Overall generation of dispatchable thermal clusters using petroleum products.
        mix_fuel: **Removed since v9.3** Overall generation of dispatchable thermal clusters using a mix of the previous fuels.
        misc_dtg: **Removed since v9.3**Overall generation of dispatchable thermal clusters using other fuels
    """

    ov_cost: bool = True
    op_cost: bool = True
    mrg_price: bool = True
    co2_emis: bool = True
    dtg_by_plant: bool = True
    balance: bool = True
    row_bal: bool = True
    psp: bool = True
    misc_ndg: bool = True
    load: bool = True
    h_ror: bool = True
    wind: bool = True
    h_stor: bool = True
    h_pump: bool = True
    h_lev: bool = True
    h_infl: bool = True
    h_ovfl: bool = True
    h_val: bool = True
    h_cost: bool = True
    unsp_enrg: bool = True
    spil_enrg: bool = True
    lold: bool = True
    lolp: bool = True
    avl_dtg: bool = True
    dtg_mrg: bool = True
    max_mrg: bool = True
    np_cost: bool = True
    np_cost_by_plant: bool = True
    nodu: bool = True
    nodu_by_plant: bool = True
    flow_lin: bool = True
    ucap_lin: bool = True
    loop_flow: bool = True
    flow_quad: bool = True
    cong_fee_alg: bool = True
    cong_fee_abs: bool = True
    marg_cost: bool = True
    cong_prob_plus: bool = True
    cong_prob_minus: bool = True
    hurdle_cost: bool = True
    res_generation_by_plant: bool = True
    dens: bool = True
    profit_by_plant: bool = True
    sts_inj_by_plant: bool = True
    sts_withdrawal_by_plant: bool = True
    sts_lvl_by_plant: bool = True
    sts_cashflow_by_cluster: bool = True
    npcap_hours: bool = True
    bc_marg_cost: bool = True
    lmr_viol: bool = True
    dtg_mrg_csr: bool = True
    nh3_emis: bool = True
    nox_emis: bool = True
    pm2_5_emis: bool = True
    pm5_emis: bool = True
    pm10_emis: bool = True
    op1_emis: bool = True
    op2_emis: bool = True
    op3_emis: bool = True
    op4_emis: bool = True
    op5_emis: bool = True
    so2_emis: bool = True
    nmvoc_emis: bool = True
    # Simulator v9.1 parameters
    sts_by_group: Optional[bool] = None
    # Simulator v9.3 parameters
    dispatch_gen: Optional[bool] = None
    renewable_gen: Optional[bool] = None
    # Parameters that existed in v8.8 and were removed in v9.1
    psp_open_injection: Optional[bool] = None
    psp_open_withdrawal: Optional[bool] = None
    psp_open_level: Optional[bool] = None
    psp_closed_injection: Optional[bool] = None
    psp_closed_withdrawal: Optional[bool] = None
    psp_closed_level: Optional[bool] = None
    pondage_injection: Optional[bool] = None
    pondage_withdrawal: Optional[bool] = None
    pondage_level: Optional[bool] = None
    battery_injection: Optional[bool] = None
    battery_withdrawal: Optional[bool] = None
    battery_level: Optional[bool] = None
    other1_injection: Optional[bool] = None
    other1_withdrawal: Optional[bool] = None
    other1_level: Optional[bool] = None
    other2_injection: Optional[bool] = None
    other2_withdrawal: Optional[bool] = None
    other2_level: Optional[bool] = None
    other3_injection: Optional[bool] = None
    other3_withdrawal: Optional[bool] = None
    other3_level: Optional[bool] = None
    other4_injection: Optional[bool] = None
    other4_withdrawal: Optional[bool] = None
    other4_level: Optional[bool] = None
    other5_injection: Optional[bool] = None
    other5_withdrawal: Optional[bool] = None
    other5_level: Optional[bool] = None
    # Parameters that existed in v8.8 and were removed in v9.3
    misc_dtg_2: Optional[bool] = None
    misc_dtg_3: Optional[bool] = None
    misc_dtg_4: Optional[bool] = None
    wind_offshore: Optional[bool] = None
    wind_onshore: Optional[bool] = None
    solar_concrt: Optional[bool] = None
    solar_pv: Optional[bool] = None
    solar_rooft: Optional[bool] = None
    renw_1: Optional[bool] = None
    renw_2: Optional[bool] = None
    renw_3: Optional[bool] = None
    renw_4: Optional[bool] = None
    solar: Optional[bool] = None
    nuclear: Optional[bool] = None
    lignite: Optional[bool] = None
    coal: Optional[bool] = None
    gas: Optional[bool] = None
    oil: Optional[bool] = None
    mix_fuel: Optional[bool] = None
    misc_dtg: Optional[bool] = None

    def all_enabled(self) -> "ThematicTrimmingParameters":
        """Enable all outputs.

        Returns:
            All parameters are set to `True` so all outputs will be generated.
        """
        args = {k: v for k, v in asdict(self).items() if v is not None}
        all_enabled = dict.fromkeys(args, True)
        return ThematicTrimmingParameters(**all_enabled)

    def all_disabled(self) -> "ThematicTrimmingParameters":
        """Disable all outputs.

        Returns:
            All parameters are set to `False`.
        """
        args = {k: v for k, v in asdict(self).items() if v is not None}
        all_disabled = dict.fromkeys(args, False)
        return ThematicTrimmingParameters(**all_disabled)

    def all_reversed(self) -> "ThematicTrimmingParameters":
        """Reverse all current settings.

        Returns:
            All parameters are reversed.
        """
        args = {k: v for k, v in asdict(self).items() if v is not None}
        all_reversed = {key: not value for key, value in args.items()}
        return ThematicTrimmingParameters(**all_reversed)
