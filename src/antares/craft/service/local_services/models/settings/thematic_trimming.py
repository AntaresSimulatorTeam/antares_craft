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
from typing import Any

from pydantic import Field

from antares.craft import ThematicTrimmingParameters
from antares.craft.model.study import STUDY_VERSION_9_2
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.service.local_services.models.utils import check_min_version, initialize_field_default
from antares.study.version import StudyVersion


class ThematicTrimmingParametersLocal(LocalBaseModel):
    ov_cost: bool | None = Field(default=None, alias="OV. COST")
    op_cost: bool | None = Field(default=None, alias="OP. COST")
    mrg_price: bool | None = Field(default=None, alias="MRG. PRICE")
    co2_emis: bool | None = Field(default=None, alias="CO2 EMIS.")
    dtg_by_plant: bool | None = Field(default=None, alias="DTG by plant")
    balance: bool | None = Field(default=None, alias="BALANCE")
    row_bal: bool | None = Field(default=None, alias="ROW BAL.")
    psp: bool | None = Field(default=None, alias="PSP")
    misc_ndg: bool | None = Field(default=None, alias="MISC. NDG")
    load: bool | None = Field(default=None, alias="LOAD")
    h_ror: bool | None = Field(default=None, alias="H. ROR")
    wind: bool | None = Field(default=None, alias="WIND")
    solar: bool | None = Field(default=None, alias="SOLAR")
    nuclear: bool | None = Field(default=None, alias="NUCLEAR")
    lignite: bool | None = Field(default=None, alias="LIGNITE")
    coal: bool | None = Field(default=None, alias="COAL")
    gas: bool | None = Field(default=None, alias="GAS")
    oil: bool | None = Field(default=None, alias="OIL")
    mix_fuel: bool | None = Field(default=None, alias="MIX. FUEL")
    misc_dtg: bool | None = Field(default=None, alias="MISC. DTG")
    h_stor: bool | None = Field(default=None, alias="H. STOR")
    h_pump: bool | None = Field(default=None, alias="H. PUMP")
    h_lev: bool | None = Field(default=None, alias="H. LEV")
    h_infl: bool | None = Field(default=None, alias="H. INFL")
    h_ovfl: bool | None = Field(default=None, alias="H. OVFL")
    h_val: bool | None = Field(default=None, alias="H. VAL")
    h_cost: bool | None = Field(default=None, alias="H. COST")
    unsp_enrg: bool | None = Field(default=None, alias="UNSP. ENRG")
    spil_enrg: bool | None = Field(default=None, alias="SPIL. ENRG")
    lold: bool | None = Field(default=None, alias="LOLD")
    lolp: bool | None = Field(default=None, alias="LOLP")
    avl_dtg: bool | None = Field(default=None, alias="AVL DTG")
    dtg_mrg: bool | None = Field(default=None, alias="DTG MRG")
    max_mrg: bool | None = Field(default=None, alias="MAX MRG")
    np_cost: bool | None = Field(default=None, alias="NP COST")
    np_cost_by_plant: bool | None = Field(default=None, alias="NP Cost by plant")
    nodu: bool | None = Field(default=None, alias="NODU")
    nodu_by_plant: bool | None = Field(default=None, alias="NODU by plant")
    flow_lin: bool | None = Field(default=None, alias="FLOW LIN.")
    ucap_lin: bool | None = Field(default=None, alias="UCAP LIN.")
    loop_flow: bool | None = Field(default=None, alias="LOOP FLOW")
    flow_quad: bool | None = Field(default=None, alias="FLOW QUAD.")
    cong_fee_alg: bool | None = Field(default=None, alias="CONG. FEE (ALG.)")
    cong_fee_abs: bool | None = Field(default=None, alias="CONG. FEE (ABS.)")
    marg_cost: bool | None = Field(default=None, alias="MARG. COST")
    cong_prob_plus: bool | None = Field(default=None, alias="CONG. PROB +")
    cong_prob_minus: bool | None = Field(default=None, alias="CONG. PROB -")
    hurdle_cost: bool | None = Field(default=None, alias="HURDLE COST")
    # since v8.1
    res_generation_by_plant: bool | None = Field(default=None, alias="RES generation by plant")
    misc_dtg_2: bool | None = Field(default=None, alias="MISC. DTG 2")
    misc_dtg_3: bool | None = Field(default=None, alias="MISC. DTG 3")
    misc_dtg_4: bool | None = Field(default=None, alias="MISC. DTG 4")
    wind_offshore: bool | None = Field(default=None, alias="WIND OFFSHORE")
    wind_onshore: bool | None = Field(default=None, alias="WIND ONSHORE")
    solar_concrt: bool | None = Field(default=None, alias="SOLAR CONCR")
    solar_pv: bool | None = Field(default=None, alias="SOLAR PV")
    solar_rooft: bool | None = Field(default=None, alias="SOLAR ROOFT")
    renw_1: bool | None = Field(default=None, alias="RENW. 1")
    renw_2: bool | None = Field(default=None, alias="RENW. 2")
    renw_3: bool | None = Field(default=None, alias="RENW. 3")
    renw_4: bool | None = Field(default=None, alias="RENW. 4")
    # since v8.3
    dens: bool | None = Field(default=None, alias="DENS")
    profit_by_plant: bool | None = Field(default=None, alias="Profit by plant")
    # since v8.6
    sts_inj_by_plant: bool | None = Field(default=None, alias="STS inj by plant")
    sts_withdrawal_by_plant: bool | None = Field(default=None, alias="STS withdrawal by plant")
    sts_lvl_by_plant: bool | None = Field(default=None, alias="STS lvl by plant")
    psp_open_injection: bool | None = Field(default=None, alias="PSP_open_injection")
    psp_open_withdrawal: bool | None = Field(default=None, alias="PSP_open_withdrawal")
    psp_open_level: bool | None = Field(default=None, alias="PSP_open_level")
    psp_closed_injection: bool | None = Field(default=None, alias="PSP_closed_injection")
    psp_closed_withdrawal: bool | None = Field(default=None, alias="PSP_closed_withdrawal")
    psp_closed_level: bool | None = Field(default=None, alias="PSP_closed_level")
    pondage_injection: bool | None = Field(default=None, alias="Pondage_injection")
    pondage_withdrawal: bool | None = Field(default=None, alias="Pondage_withdrawal")
    pondage_level: bool | None = Field(default=None, alias="Pondage_level")
    battery_injection: bool | None = Field(default=None, alias="Battery_injection")
    battery_withdrawal: bool | None = Field(default=None, alias="Battery_withdrawal")
    battery_level: bool | None = Field(default=None, alias="Battery_level")
    other1_injection: bool | None = Field(default=None, alias="Other1_injection")
    other1_withdrawal: bool | None = Field(default=None, alias="Other1_withdrawal")
    other1_level: bool | None = Field(default=None, alias="Other1_level")
    other2_injection: bool | None = Field(default=None, alias="Other2_injection")
    other2_withdrawal: bool | None = Field(default=None, alias="Other2_withdrawal")
    other2_level: bool | None = Field(default=None, alias="Other2_level")
    other3_injection: bool | None = Field(default=None, alias="Other3_injection")
    other3_withdrawal: bool | None = Field(default=None, alias="Other3_withdrawal")
    other3_level: bool | None = Field(default=None, alias="Other3_level")
    other4_injection: bool | None = Field(default=None, alias="Other4_injection")
    other4_withdrawal: bool | None = Field(default=None, alias="Other4_withdrawal")
    other4_level: bool | None = Field(default=None, alias="Other4_level")
    other5_injection: bool | None = Field(default=None, alias="Other5_injection")
    other5_withdrawal: bool | None = Field(default=None, alias="Other5_withdrawal")
    other5_level: bool | None = Field(default=None, alias="Other5_level")
    # Since v8.8
    sts_cashflow_by_cluster: bool | None = Field(default=None, alias="STS Cashflow By Cluster")
    npcap_hours: bool | None = Field(default=None, alias="NPCAP HOURS")
    # Since v9.2
    sts_by_group: bool | None = Field(default=None, alias="STS by group")

    @staticmethod
    def get_9_2_fields() -> set[str]:
        return {"sts_by_group"}

    @staticmethod
    def get_sts_group_fields() -> set[str]:
        return {
            "psp_open_injection",
            "psp_open_withdrawal",
            "psp_open_level",
            "psp_closed_injection",
            "psp_closed_withdrawal",
            "psp_closed_level",
            "pondage_injection",
            "pondage_withdrawal",
            "pondage_level",
            "battery_injection",
            "battery_withdrawal",
            "battery_level",
            "other1_injection",
            "other1_withdrawal",
            "other1_level",
            "other2_injection",
            "other2_withdrawal",
            "other2_level",
            "other3_injection",
            "other3_withdrawal",
            "other3_level",
            "other4_injection",
            "other4_withdrawal",
            "other4_level",
            "other5_injection",
            "other5_withdrawal",
            "other5_level",
        }

    def to_user_model(self) -> ThematicTrimmingParameters:
        return ThematicTrimmingParameters(**self.model_dump(exclude_none=True))

    @staticmethod
    def from_user_model(user_class: ThematicTrimmingParameters) -> "ThematicTrimmingParametersLocal":
        return ThematicTrimmingParametersLocal(**asdict(user_class))

    def to_ini(self) -> dict[str, Any]:
        data = self.model_dump(by_alias=True, exclude_none=True)
        content_plus = []
        content_minus = []
        for key, value in data.items():
            if value:
                content_plus.append(key)
            else:
                content_minus.append(key)
        if len(content_minus) >= len(content_plus):
            ini_content: dict[str, Any] = {"selected_vars_reset": False}
            if content_plus:
                ini_content["select_var +"] = content_plus
        else:
            ini_content = {"selected_vars_reset": True}
            if content_minus:
                ini_content["select_var -"] = content_minus
        return ini_content

    @staticmethod
    def from_ini(content: dict[str, Any]) -> "ThematicTrimmingParametersLocal":
        if content.get("selected_vars_reset", True):
            # Means written fields are deactivated and others are activated
            unselected_vars = content.get("select_var -", [])
            args = dict.fromkeys(unselected_vars, False)
            return ThematicTrimmingParametersLocal(**args)

        # Means written fields are activated and others deactivated
        selected_vars = content.get("select_var +", [])
        args = dict.fromkeys(selected_vars, True)
        file_data = ThematicTrimmingParametersLocal(**args)
        return file_data


def validate_against_version(parameters: ThematicTrimmingParametersLocal, version: StudyVersion) -> None:
    if version < STUDY_VERSION_9_2:
        for field in ThematicTrimmingParametersLocal.get_9_2_fields():
            check_min_version(parameters, field, version)
    else:
        for field in ThematicTrimmingParametersLocal.get_sts_group_fields():
            check_min_version(parameters, field, version)


def initialize_with_version(parameters: ThematicTrimmingParametersLocal, version: StudyVersion) -> None:
    all_fields = set(ThematicTrimmingParametersLocal.model_fields)
    if version < STUDY_VERSION_9_2:
        for field in ThematicTrimmingParametersLocal.get_9_2_fields():
            all_fields.remove(field)
    else:
        for field in ThematicTrimmingParametersLocal.get_sts_group_fields():
            all_fields.remove(field)

    # Find the right boolean to fill the user model
    args = parameters.model_dump(exclude_none=True)
    boolean = not next(iter(args.values()), False)

    for field in all_fields:
        initialize_field_default(parameters, field, boolean)


def parse_thematic_trimming_local(study_version: StudyVersion, data: Any) -> ThematicTrimmingParameters:
    thematic_trimming_parameters_local = ThematicTrimmingParametersLocal.from_ini(data)
    validate_against_version(thematic_trimming_parameters_local, study_version)
    initialize_with_version(thematic_trimming_parameters_local, study_version)
    return thematic_trimming_parameters_local.to_user_model()


def serialize_thematic_trimming_local(
    study_version: StudyVersion, thematic_trimming: ThematicTrimmingParameters
) -> dict[str, Any]:
    thematic_trimming_parameters_local = ThematicTrimmingParametersLocal.from_user_model(thematic_trimming)
    validate_against_version(thematic_trimming_parameters_local, study_version)
    return thematic_trimming_parameters_local.to_ini()
