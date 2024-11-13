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
import os
import socket
import subprocess
import time

from pathlib import Path

import requests


class AntaresWebDesktop:
    """
    Launches an AntaresWebDesktop instance for integration tests
    """

    def __init__(self):
        antares_web_desktop_path = [p for p in Path(__file__).parents if p.name == "antares_craft"][
            0
        ] / "AntaresWebDesktop"
        config_path = antares_web_desktop_path / "config.yaml"
        if os.name != "nt":
            executable_path = antares_web_desktop_path / "AntaresWeb" / "AntaresWebServer"
        else:
            executable_path = antares_web_desktop_path / "AntaresWeb" / "AntaresWebServer.exe"
        args = [str(executable_path), "-c", str(config_path), "--auto-upgrade-db", "--no-front"]
        self.desktop_path = antares_web_desktop_path
        self.host = "127.0.0.1"
        self.port = 8080
        self.url = f"http://{self.host}:{self.port}"
        self.process = subprocess.Popen(args, shell=True, cwd=str(antares_web_desktop_path))

    def _is_server_ready(self):
        healthcheck_url = f"{self.url}/api/health"
        try:
            res = requests.get(healthcheck_url)
            return res.status_code == 200
        except requests.RequestException as exc:
            return False

    def wait_for_server_to_start(self):
        timeout = 10
        interval = 1
        elapsed_time = 0
        while elapsed_time < timeout:
            if self._is_server_ready():
                return
            time.sleep(interval)
            elapsed_time += interval
        raise Exception("The app did not start inside the given delays.")

    def kill(self):
        """
        Removes every study to ensure tests reproductibility + it cleans the database.
        It also kills the AntaresWebDesktop instance.
        """
        session = requests.Session()
        res = session.get(self.url + "/v1/studies")
        studies = res.json()
        for study in studies:
            session.delete(self.url + f"/v1/studies/{study}?children=True")
        self.process.terminate()
        self.process.wait()
        pids = subprocess.run(["pgrep AntaresWeb"], capture_output=True, shell=True).stdout.split()
        for pid in pids:
            subprocess.run([f"kill {int(pid)}"], shell=True)
        time.sleep(0.1)
