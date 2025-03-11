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
from typing import Optional


@dataclass(frozen=True)
class ClusterProperties:
    """
    Common properties for thermal and renewable clusters
    """

    enabled: bool = True
    unit_count: int = 1
    nominal_capacity: float = 0

    @property
    def installed_capacity(self) -> float:
        return self.unit_count * self.nominal_capacity

    @property
    def enabled_capacity(self) -> float:
        return self.enabled * self.installed_capacity


@dataclass
class ClusterPropertiesUpdate:
    enabled: Optional[bool] = None
    unit_count: Optional[int] = None
    nominal_capacity: Optional[float] = None
