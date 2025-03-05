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


from antares.craft import Study
from antares.craft.model.binding_constraint import (
    BindingConstraintOperator,
    BindingConstraintProperties,
    ConstraintTerm,
    LinkData,
)


class TestBindingConstraints:
    def test_read_constraints(self, local_study_w_constraints: Study) -> None:
        constraints = local_study_w_constraints.read_binding_constraints()
        assert len(constraints) == 2
        bc_1 = constraints[0]
        assert bc_1.name == "bc_1"
        assert bc_1.properties == BindingConstraintProperties(operator=BindingConstraintOperator.GREATER, enabled=False)
        assert bc_1.get_terms() == {}

        bc_2 = constraints[1]
        assert bc_2.name == "bc_2"
        assert bc_2.properties == BindingConstraintProperties()
        assert bc_2.get_terms() == {"at%fr": ConstraintTerm(data=LinkData(area1="at", area2="fr"), weight=2)}
