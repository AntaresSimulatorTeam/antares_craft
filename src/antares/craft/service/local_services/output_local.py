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
from typing import Any

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.output import AggregationEntry
from antares.craft.service.base_services import BaseOutputService


class OutputLocalService(BaseOutputService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def get_matrix(self, output_id: str, file_path: str) -> pd.DataFrame:
        raise NotImplementedError

    def aggregate_values(
        self, output_id: str, aggregation_entry: AggregationEntry, object_type: str, mc_type: str
    ) -> pd.DataFrame:
        raise NotImplementedError
