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
from enum import Enum

from antares.craft.tools.all_optional_meta import all_optional_model
from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class DefaultThematicTrimmingParameters(BaseModel, alias_generator=to_camel):
    """
    This class manages the configuration of result filtering in a simulation.

    This table allows the user to enable or disable specific variables before running a simulation.
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
    # since v8.1
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
    # since v8.3
    dens: bool = True
    profit_by_plant: bool = True
    # since v8.6
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
    # since v8.8
    sts_cashflow_by_cluster: bool = True

    @property
    def selected_vars_reset(self) -> bool:
        return sum([getattr(self, field) for field in self.model_fields]) > (len(self.model_fields) / 2)


@all_optional_model
class ThematicTrimmingParameters(DefaultThematicTrimmingParameters):
    pass


class ThematicTrimmingParametersLocal(DefaultThematicTrimmingParameters, populate_by_name=True):
    @property
    def ini_fields(self) -> dict:
        variable_list = repr(
            [
                getattr(ThematicVars, to_camel(variable)).value
                for variable in self.model_fields
                if getattr(self, variable) ^ self.selected_vars_reset
            ]
        )
        thematic_trimming_dict = {"select_var " + ("-" if self.selected_vars_reset else "+"): variable_list}

        return {
            "variables selection": {"selected_vars_reset": str(self.selected_vars_reset).lower()}
            | thematic_trimming_dict
        }


class ThematicVars(Enum):
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
