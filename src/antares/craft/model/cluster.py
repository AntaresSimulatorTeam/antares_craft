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
    """Common properties for thermal and renewable clusters.

    Attributes:
        enabled: Whether the cluster is enabled in the simulation.
        unit_count: Number of generation units in the cluster.
        nominal_capacity: Nominal capacity of a single unit in MW.
    """

    enabled: bool = True
    unit_count: int = 1
    nominal_capacity: float = 0

    @property
    def installed_capacity(self) -> float:
        """Installed capacity corresponding to the product of 
        the nominal capacity times the number of units.
        """
        return self.unit_count * self.nominal_capacity

    @property
    def enabled_capacity(self) -> float:
        """The enabled capacity is the installed capacity if the cluster is enabled,
        otherwise it's 0.
        """
        return self.enabled * self.installed_capacity


@dataclass
class ClusterPropertiesUpdate:
    """Update of cluster properties
    
    Attributes:
        enabled: Whether the cluster is enabled in the simulation.
        unit_count: Number of generation units in the cluster.
        nominal_capacity: Nominal capacity of a single unit in MW.        
    """
    enabled: Optional[bool] = None
    unit_count: Optional[int] = None
    nominal_capacity: Optional[float] = None
