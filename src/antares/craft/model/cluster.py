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

from typing import Optional

from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class ClusterProperties(BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    """
    Common properties for thermal and renewable clusters
    """

    # Activity status:
    # - True: the plant may generate.
    # - False: not yet commissioned, moth-balled, etc.
    enabled: bool = True

    unit_count: int = 1
    nominal_capacity: float = 0

    @property
    def installed_capacity(self) -> Optional[float]:
        if self.unit_count is None or self.nominal_capacity is None:
            return None
        return self.unit_count * self.nominal_capacity

    @property
    def enabled_capacity(self) -> Optional[float]:
        if self.enabled is None or self.installed_capacity is None:
            return None
        return self.enabled * self.installed_capacity
