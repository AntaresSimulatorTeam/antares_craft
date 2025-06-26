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
        all_enabled = dict.fromkeys(asdict(self), True)
        return ThematicTrimmingParameters(**all_enabled)

    def all_disabled(self) -> "ThematicTrimmingParameters":
        all_disabled = dict.fromkeys(asdict(self), False)
        return ThematicTrimmingParameters(**all_disabled)

    def all_reversed(self) -> "ThematicTrimmingParameters":
        all_reversed = {key: not value for key, value in asdict(self).items()}
        return ThematicTrimmingParameters(**all_reversed)
