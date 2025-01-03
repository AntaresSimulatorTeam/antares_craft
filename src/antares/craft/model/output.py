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

from pydantic import BaseModel


class Output(BaseModel):
    name: str
    archived: bool

    def __init__(self, output_service, **kwargs: Any):  # type: ignore
        super().__init__(**kwargs)
        self._output_service = output_service

    def get_matrix(self, path: str) -> pd.DataFrame:
        """
        Gets the matrix of the output

        Args:
            path: output path, eg: "mc-all/areas/south/values-hourly"

        Returns: Pandas DataFrame
        """
        full_path = f"output/{self.name}/economy/{path}"
        return self._output_service.get_matrix(full_path)
