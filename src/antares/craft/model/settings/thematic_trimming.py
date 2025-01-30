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
