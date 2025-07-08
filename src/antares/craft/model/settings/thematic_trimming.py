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
    sts_cashflow_by_cluster: bool = True
    npcap_hours: bool = True
    # Simulator v9.1 parameters
    sts_by_group: Optional[bool] = None
    # Parameters removed since v9.1
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

    def all_enabled(self) -> "ThematicTrimmingParameters":
        args = {k: v for k, v in asdict(self).items() if v is not None}
        all_enabled = dict.fromkeys(args, True)
        return ThematicTrimmingParameters(**all_enabled)

    def all_disabled(self) -> "ThematicTrimmingParameters":
        args = {k: v for k, v in asdict(self).items() if v is not None}
        all_disabled = dict.fromkeys(args, False)
        return ThematicTrimmingParameters(**all_disabled)

    def all_reversed(self) -> "ThematicTrimmingParameters":
        args = {k: v for k, v in asdict(self).items() if v is not None}
        all_reversed = {key: not value for key, value in args.items()}
        return ThematicTrimmingParameters(**all_reversed)
