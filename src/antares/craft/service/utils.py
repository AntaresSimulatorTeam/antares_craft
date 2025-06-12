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
from io import StringIO
from pathlib import Path

import pandas as pd

from antares.craft.model.output import Frequency
from antares.craft.service.local_services.services.output.date_serializer import FactoryDateSerializer, rename_unnamed


def read_output_matrix(data: Path | StringIO, frequency: Frequency) -> pd.DataFrame:
    df = pd.read_csv(data, sep="\t", skiprows=4, header=[0, 1, 2], na_values="N/A", float_precision="legacy")

    date_serializer = FactoryDateSerializer.create(frequency.value, "")
    _, body = date_serializer.extract_date(df)

    final_df = rename_unnamed(body).astype(float)

    return final_df
