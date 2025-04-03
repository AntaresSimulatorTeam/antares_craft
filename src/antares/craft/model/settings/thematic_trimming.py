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


@dataclass
class ThematicTrimmingParametersUpdate:
    ov_cost: Optional[bool] = None
    op_cost: Optional[bool] = None
    mrg_price: Optional[bool] = None
    co2_emis: Optional[bool] = None
    dtg_by_plant: Optional[bool] = None
    balance: Optional[bool] = None
    row_bal: Optional[bool] = None
    psp: Optional[bool] = None
    misc_ndg: Optional[bool] = None
    load: Optional[bool] = None
    h_ror: Optional[bool] = None
    wind: Optional[bool] = None
    solar: Optional[bool] = None
    nuclear: Optional[bool] = None
    lignite: Optional[bool] = None
    coal: Optional[bool] = None
    gas: Optional[bool] = None
    oil: Optional[bool] = None
    mix_fuel: Optional[bool] = None
    misc_dtg: Optional[bool] = None
    h_stor: Optional[bool] = None
    h_pump: Optional[bool] = None
    h_lev: Optional[bool] = None
    h_infl: Optional[bool] = None
    h_ovfl: Optional[bool] = None
    h_val: Optional[bool] = None
    h_cost: Optional[bool] = None
    unsp_enrg: Optional[bool] = None
    spil_enrg: Optional[bool] = None
    lold: Optional[bool] = None
    lolp: Optional[bool] = None
    avl_dtg: Optional[bool] = None
    dtg_mrg: Optional[bool] = None
    max_mrg: Optional[bool] = None
    np_cost: Optional[bool] = None
    np_cost_by_plant: Optional[bool] = None
    nodu: Optional[bool] = None
    nodu_by_plant: Optional[bool] = None
    flow_lin: Optional[bool] = None
    ucap_lin: Optional[bool] = None
    loop_flow: Optional[bool] = None
    flow_quad: Optional[bool] = None
    cong_fee_alg: Optional[bool] = None
    cong_fee_abs: Optional[bool] = None
    marg_cost: Optional[bool] = None
    cong_prob_plus: Optional[bool] = None
    cong_prob_minus: Optional[bool] = None
    hurdle_cost: Optional[bool] = None
    res_generation_by_plant: Optional[bool] = None
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
    dens: Optional[bool] = None
    profit_by_plant: Optional[bool] = None
    sts_inj_by_plant: Optional[bool] = None
    sts_withdrawal_by_plant: Optional[bool] = None
    sts_lvl_by_plant: Optional[bool] = None
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
    sts_cashflow_by_cluster: Optional[bool] = None


@dataclass(frozen=True)
class ThematicTrimmingParameters:
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
    solar: bool = True
    nuclear: bool = True
    lignite: bool = True
    coal: bool = True
    gas: bool = True
    oil: bool = True
    mix_fuel: bool = True
    misc_dtg: bool = True
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
    misc_dtg_2: bool = True
    misc_dtg_3: bool = True
    misc_dtg_4: bool = True
    wind_offshore: bool = True
    wind_onshore: bool = True
    solar_concrt: bool = True
    solar_pv: bool = True
    solar_rooft: bool = True
    renw_1: bool = True
    renw_2: bool = True
    renw_3: bool = True
    renw_4: bool = True
    dens: bool = True
    profit_by_plant: bool = True
    sts_inj_by_plant: bool = True
    sts_withdrawal_by_plant: bool = True
    sts_lvl_by_plant: bool = True
    psp_open_injection: bool = True
    psp_open_withdrawal: bool = True
    psp_open_level: bool = True
    psp_closed_injection: bool = True
    psp_closed_withdrawal: bool = True
    psp_closed_level: bool = True
    pondage_injection: bool = True
    pondage_withdrawal: bool = True
    pondage_level: bool = True
    battery_injection: bool = True
    battery_withdrawal: bool = True
    battery_level: bool = True
    other1_injection: bool = True
    other1_withdrawal: bool = True
    other1_level: bool = True
    other2_injection: bool = True
    other2_withdrawal: bool = True
    other2_level: bool = True
    other3_injection: bool = True
    other3_withdrawal: bool = True
    other3_level: bool = True
    other4_injection: bool = True
    other4_withdrawal: bool = True
    other4_level: bool = True
    other5_injection: bool = True
    other5_withdrawal: bool = True
    other5_level: bool = True
    sts_cashflow_by_cluster: bool = True

    def all_enabled(self) -> "ThematicTrimmingParameters":
        all_enabled = {key: True for key in asdict(self)}
        return ThematicTrimmingParameters(**all_enabled)

    def all_disabled(self) -> "ThematicTrimmingParameters":
        all_disabled = {key: True for key in asdict(self)}
        return ThematicTrimmingParameters(**all_disabled)

    def all_reversed(self) -> "ThematicTrimmingParameters":
        all_reversed = {key: not value for key, value in asdict(self).items()}
        return ThematicTrimmingParameters(**all_reversed)
