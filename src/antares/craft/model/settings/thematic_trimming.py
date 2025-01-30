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
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from antares.craft.tools.all_optional_meta import all_optional_model
from pydantic import BaseModel
from pydantic.alias_generators import to_camel


@dataclass
class ThematicTrimmingParameters:
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


@all_optional_model
class ThematicTrimmingParametersAPI(BaseModel, alias_generator=to_camel):
    ov_cost: bool
    op_cost: bool
    mrg_price: bool
    co2_emis: bool
    dtg_by_plant: bool
    balance: bool
    row_bal: bool
    psp: bool
    misc_ndg: bool
    load: bool
    h_ror: bool
    wind: bool
    solar: bool
    nuclear: bool
    lignite: bool
    coal: bool
    gas: bool
    oil: bool
    mix_fuel: bool
    misc_dtg: bool
    h_stor: bool
    h_pump: bool
    h_lev: bool
    h_infl: bool
    h_ovfl: bool
    h_val: bool
    h_cost: bool
    unsp_enrg: bool
    spil_enrg: bool
    lold: bool
    lolp: bool
    avl_dtg: bool
    dtg_mrg: bool
    max_mrg: bool
    np_cost: bool
    np_cost_by_plant: bool
    nodu: bool
    nodu_by_plant: bool
    flow_lin: bool
    ucap_lin: bool
    loop_flow: bool
    flow_quad: bool
    cong_fee_alg: bool
    cong_fee_abs: bool
    marg_cost: bool
    cong_prob_plus: bool
    cong_prob_minus: bool
    hurdle_cost: bool
    res_generation_by_plant: bool
    misc_dtg_2: bool
    misc_dtg_3: bool
    misc_dtg_4: bool
    wind_offshore: bool
    wind_onshore: bool
    solar_concrt: bool
    solar_pv: bool
    solar_rooft: bool
    renw_1: bool
    renw_2: bool
    renw_3: bool
    renw_4: bool
    dens: bool
    profit_by_plant: bool
    sts_inj_by_plant: bool
    sts_withdrawal_by_plant: bool
    sts_lvl_by_plant: bool
    psp_open_injection: bool
    psp_open_withdrawal: bool
    psp_open_level: bool
    psp_closed_injection: bool
    psp_closed_withdrawal: bool
    psp_closed_level: bool
    pondage_injection: bool
    pondage_withdrawal: bool
    pondage_level: bool
    battery_injection: bool
    battery_withdrawal: bool
    battery_level: bool
    other1_injection: bool
    other1_withdrawal: bool
    other1_level: bool
    other2_injection: bool
    other2_withdrawal: bool
    other2_level: bool
    other3_injection: bool
    other3_withdrawal: bool
    other3_level: bool
    other4_injection: bool
    other4_withdrawal: bool
    other4_level: bool
    other5_injection: bool
    other5_withdrawal: bool
    other5_level: bool
    sts_cashflow_by_cluster: bool


class ThematicVarsLocal(Enum):
    balance = "BALANCE"
    dens = "DENS"
    load = "LOAD"
    lold = "LOLD"
    lolp = "LOLP"
    miscNdg = "MISC. NDG"
    mrgPrice = "MRG. PRICE"
    opCost = "OP. COST"
    ovCost = "OV. COST"
    rowBal = "ROW BAL."
    spilEnrg = "SPIL. ENRG"
    unspEnrg = "UNSP. ENRG"
    hCost = "H. COST"
    hInfl = "H. INFL"
    hLev = "H. LEV"
    hOvfl = "H. OVFL"
    hPump = "H. PUMP"
    hRor = "H. ROR"
    hStor = "H. STOR"
    hVal = "H. VAL"
    psp = "PSP"
    renw1 = "RENW. 1"
    renw2 = "RENW. 2"
    renw3 = "RENW. 3"
    renw4 = "RENW. 4"
    resGenerationByPlant = "RES generation by plant"
    solar = "SOLAR"
    solarConcrt = "SOLAR CONCRT."
    solarPv = "SOLAR PV"
    solarRooft = "SOLAR ROOFT"
    wind = "WIND"
    windOffshore = "WIND OFFSHORE"
    windOnshore = "WIND ONSHORE"
    batteryInjection = "BATTERY_INJECTION"
    batteryLevel = "BATTERY_LEVEL"
    batteryWithdrawal = "BATTERY_WITHDRAWAL"
    other1Injection = "OTHER1_INJECTION"
    other1Level = "OTHER1_LEVEL"
    other1Withdrawal = "OTHER1_WITHDRAWAL"
    other2Injection = "OTHER2_INJECTION"
    other2Level = "OTHER2_LEVEL"
    other2Withdrawal = "OTHER2_WITHDRAWAL"
    other3Injection = "OTHER3_INJECTION"
    other3Level = "OTHER3_LEVEL"
    other3Withdrawal = "OTHER3_WITHDRAWAL"
    other4Injection = "OTHER4_INJECTION"
    other4Level = "OTHER4_LEVEL"
    other4Withdrawal = "OTHER4_WITHDRAWAL"
    other5Injection = "OTHER5_INJECTION"
    other5Level = "OTHER5_LEVEL"
    other5Withdrawal = "OTHER5_WITHDRAWAL"
    pondageInjection = "PONDAGE_INJECTION"
    pondageLevel = "PONDAGE_LEVEL"
    pondageWithdrawal = "PONDAGE_WITHDRAWAL"
    pspClosedInjection = "PSP_CLOSED_INJECTION"
    pspClosedLevel = "PSP_CLOSED_LEVEL"
    pspClosedWithdrawal = "PSP_CLOSED_WITHDRAWAL"
    pspOpenInjection = "PSP_OPEN_INJECTION"
    pspOpenLevel = "PSP_OPEN_LEVEL"
    pspOpenWithdrawal = "PSP_OPEN_WITHDRAWAL"
    stsCashflowByCluster = "STS CASHFLOW BY CLUSTER"
    stsInjByPlant = "STS inj by plant"
    stsLvlByPlant = "STS lvl by plant"
    stsWithdrawalByPlant = "STS withdrawal by plant"
    avlDtg = "AVL DTG"
    co2Emis = "CO2 EMIS."
    coal = "COAL"
    dtgByPlant = "DTG by plant"
    dtgMrg = "DTG MRG"
    gas = "GAS"
    lignite = "LIGNITE"
    maxMrg = "MAX MRG"
    miscDtg = "MISC. DTG"
    miscDtg2 = "MISC. DTG 2"
    miscDtg3 = "MISC. DTG 3"
    miscDtg4 = "MISC. DTG 4"
    mixFuel = "MIX. FUEL"
    nodu = "NODU"
    noduByPlant = "NODU by plant"
    npCost = "NP COST"
    npCostByPlant = "NP Cost by plant"
    nuclear = "NUCLEAR"
    oil = "OIL"
    profitByPlant = "Profit by plant"
    congFeeAbs = "CONG. FEE (ABS.)"
    congFeeAlg = "CONG. FEE (ALG.)"
    congProbMinus = "CONG. PROB -"
    congProbPlus = "CONG. PROB +"
    flowLin = "FLOW LIN."
    flowQuad = "FLOW QUAD."
    hurdleCost = "HURDLE COST"
    loopFlow = "LOOP FLOW"
    margCost = "MARG. COST"
    ucapLin = "UCAP LIN."
