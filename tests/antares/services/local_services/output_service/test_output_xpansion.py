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
import zipfile

from pathlib import Path

from antares.craft import Study
from antares.craft.model.output import (
    Output,
    XpansionOutputAntares,
    XpansionOutputCandidateInvest,
    XpansionOutputCandidateSensitivity,
    XpansionOutputSensitivitySolution,
    XpansionResult,
    XpansionSensitivityResult,
)
from antares.craft.service.local_services.factory import read_study_local


class TestXpansionOutputReading:
    def _set_up(self, study: Study, resource: Path) -> Output:
        study_path = Path(study.path)
        # Put a real xpansion output inside the study and tests the reading method.
        with zipfile.ZipFile(resource, "r") as zf:
            zf.extractall(study_path / "output" / "xpansion_output")
        # Read the study
        study = read_study_local(study_path)
        return study.get_outputs().values().__iter__().__next__()

    def test_nominal_case(
        self, local_study: Study, xpansion_output_path: Path, xpansion_expected_output: XpansionResult
    ) -> None:
        output = self._set_up(local_study, xpansion_output_path)
        assert output.name == "xpansion_output"
        assert not output.archived

        result = output.get_xpansion_result()
        assert result == xpansion_expected_output

        sensi_result = output.get_xpansion_sensitivity_result()
        assert sensi_result == XpansionSensitivityResult(
            antares=XpansionOutputAntares(version="9.2.0-rc7"),
            antares_xpansion=XpansionOutputAntares(version="1.4.0"),
            best_benders_cost=132222947226.60637,
            epsilon=100000.0,
            candidates={
                "102_fr_storage_energyconst": XpansionOutputCandidateSensitivity(
                    lb=0.0,
                    ub=2500.0,
                    solution_max=XpansionOutputCandidateInvest(invest=2.520208288663973),
                    solution_min=XpansionOutputCandidateInvest(invest=0.043657588539645076),
                ),
                "102_fr_storage_pump": XpansionOutputCandidateSensitivity(
                    lb=0.0,
                    ub=20000.0,
                    solution_max=XpansionOutputCandidateInvest(invest=20.161666309311784),
                    solution_min=XpansionOutputCandidateInvest(invest=0.3492607083171606),
                ),
                "102_fr_storage_turb": XpansionOutputCandidateSensitivity(
                    lb=0.0,
                    ub=20000.0,
                    solution_max=XpansionOutputCandidateInvest(invest=20.161666309311784),
                    solution_min=XpansionOutputCandidateInvest(invest=0.34926070825895295),
                ),
                "29_be_36_nl67_id_hyb_6": XpansionOutputCandidateSensitivity(
                    lb=0.0,
                    ub=2000.0,
                    solution_max=XpansionOutputCandidateInvest(invest=2000.0),
                    solution_min=XpansionOutputCandidateInvest(invest=-0.0),
                ),
                "30_be_33_nl_id_346": XpansionOutputCandidateSensitivity(
                    lb=0.0,
                    ub=1000.0,
                    solution_max=XpansionOutputCandidateInvest(invest=-0.0),
                    solution_min=XpansionOutputCandidateInvest(invest=-0.0),
                ),
                "30_be_storage_energyconst": XpansionOutputCandidateSensitivity(
                    lb=0.0,
                    ub=2500.0,
                    solution_max=XpansionOutputCandidateInvest(invest=0.0),
                    solution_min=XpansionOutputCandidateInvest(invest=0.0),
                ),
            },
            solution_max=XpansionOutputSensitivitySolution(
                objective=3982100703.915628, problem_type="capex", status=0, system_cost=132223047226.60637
            ),
            solution_min=XpansionOutputSensitivitySolution(
                objective=3295281252.030145, problem_type="capex", status=0, system_cost=132223047226.6064
            ),
        )
