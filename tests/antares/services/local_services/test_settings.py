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


from pathlib import Path

from antares.craft import (
    AdvancedParametersUpdate,
    GeneralParametersUpdate,
    HydroPricingMode,
    StudySettingsUpdate,
    UnitCommitmentMode,
    create_study_local,
)


def test_update_settings(tmp_path: Path) -> None:
    # test update study settings
    settings = StudySettingsUpdate()
    settings.general_parameters = GeneralParametersUpdate(nb_years=4)
    settings.advanced_parameters = AdvancedParametersUpdate(unit_commitment_mode=UnitCommitmentMode.MILP)
    new_study = create_study_local("second_study", "880", tmp_path)
    new_study.update_settings(settings)
    assert new_study.get_settings().general_parameters.nb_years == 4
    assert new_study.get_settings().advanced_parameters.unit_commitment_mode == UnitCommitmentMode.MILP
    # 2nd update
    settings = StudySettingsUpdate()
    settings.general_parameters = GeneralParametersUpdate(nb_years=2)
    settings.advanced_parameters = AdvancedParametersUpdate(hydro_pricing_mode=HydroPricingMode.ACCURATE)
    new_study.update_settings(settings)
    assert new_study.get_settings().general_parameters.nb_years == 2
    assert new_study.get_settings().advanced_parameters.hydro_pricing_mode == HydroPricingMode.ACCURATE
    assert new_study.get_settings().advanced_parameters.unit_commitment_mode == UnitCommitmentMode.MILP
