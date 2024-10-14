import logging

from unittest import mock

import pytest
from pathlib import Path
from antares.config.local_configuration import LocalConfiguration
from antares.model.study import read_study_local


class TestReadStudy:
    def test_directory_not_exists_error(self, caplog):
        local_path = r"fake/path/"
        study_name = "study_name"
        with caplog.at_level(logging.ERROR):
            regex_pattern = r"Provided directory fake\\path does not exist\."
            with pytest.raises(ValueError, match=regex_pattern):
                read_study_local(study_name, "880", LocalConfiguration(local_path, study_name))

    def test_directory_permission_denied(self, tmp_path, caplog):
        # Given
        study_name = "studyTest"
        restricted_dir = tmp_path / study_name

        restricted_dir.mkdir(parents=True, exist_ok=True)
        restricted_path = restricted_dir / "file.txt"
        restricted_path.touch(exist_ok=True)
        with caplog.at_level(logging.ERROR):
            with mock.patch(
                "pathlib.Path.iterdir",
                side_effect=PermissionError(f"Some content cannot be accessed in {restricted_dir}"),
            ):
                escaped_path = str(restricted_dir).replace("\\", "\\\\")
                with pytest.raises(
                    PermissionError,
                    match=f"Some content cannot be accessed in {escaped_path}",
                ):
                    read_study_local(study_name, "880", LocalConfiguration(tmp_path, study_name))

    def test_read_study_service(self, caplog):
        local_path = r"../../studies_samples/"
        study_name = "hydro_stockage"
        content = read_study_local(study_name, "880", LocalConfiguration(local_path, study_name))
        study = content._study_service

        expected_keys = ["areas", "hydro", "load", "misc", "renewables", "solar", "storage", "thermals", "wind"]

        for key in expected_keys:
            assert key in study, f"La clé '{key}' est absente du dictionnaire 'study'"
        not_expected_key = "fake_key"
        assert (
            not_expected_key not in study
        ), f"La clé '{not_expected_key}' ne devrait pas être présente dans le dictionnaire 'study'"

    def test_directory_renewable_thermique(self, caplog):
        local_path = r"../../studies_samples/"
        study_name = "renewable_thermique"

        content = read_study_local(study_name, "880", LocalConfiguration(local_path, study_name))
        assert content._study_service["thermals"].get("zone_rt").get("list") == {
            "GAZ": {
                "group": "Gas",
                "name": "GAZ",
                "enabled": "True",
                "unitcount": "1",
                "nominalcapacity": "0.0",
                "gen-ts": "use global parameter",
                "min-stable-power": "0.0",
                "min-up-time": "1",
                "min-down-time": "1",
                "must-run": "False",
                "spinning": "0.0",
                "volatility.forced": "0.0",
                "volatility.planned": "0.0",
                "law.forced": "uniform",
                "law.planned": "uniform",
                "marginal-cost": "0.0",
                "spread-cost": "0.0",
                "fixed-cost": "0.0",
                "startup-cost": "0.0",
                "market-bid-cost": "0.0",
                "co2": "0.0",
                "nh3": "0.0",
                "so2": "0.0",
                "nox": "0.0",
                "pm2_5": "0.0",
                "pm5": "0.0",
                "pm10": "0.0",
                "nmvoc": "0.0",
                "op1": "0.0",
                "op2": "0.0",
                "op3": "0.0",
                "op4": "0.0",
                "op5": "0.0",
            }
        }
        assert content._study_service["renewables"].get("zone_rt").get("list") == {
            "onshore": {
                "group": "Wind Onshore",
                "name": "onshore",
                "enabled": "True",
                "unitcount": "1",
                "nominalcapacity": "0.0",
                "ts-interpretation": "power-generation",
            },
            "offshore": {
                "group": "Wind Offshore",
                "name": "offshore",
                "enabled": "True",
                "unitcount": "1",
                "nominalcapacity": "0.0",
                "ts-interpretation": "power-generation",
            },
            "solar": {
                "group": "Solar PV",
                "name": "solar",
                "enabled": "True",
                "unitcount": "1",
                "nominalcapacity": "0.0",
                "ts-interpretation": "power-generation",
            },
        }

    def test_directory_hydro_stockage(self, caplog):
        local_path = r"../../studies_samples/"
        study_name = "hydro_stockage"
        content = read_study_local(study_name, "880", LocalConfiguration(local_path, study_name))

        assert content._study_service["storage"].get("zone_hs").get("list") == {
            "batterie": {"group": "Battery", "name": "batterie"}
        }

        assert content._study_service["hydro"].get("hydro") == {
            "inter-daily-breakdown": {"zone_hs": "1"},
            "intra-daily-modulation": {"zone_hs": "24"},
            "inter-monthly-breakdown": {"zone_hs": "1"},
            "initialize reservoir date": {"zone_hs": "0"},
            "leeway low": {"zone_hs": "1"},
            "leeway up": {"zone_hs": "1"},
            "pumping efficiency": {"zone_hs": "1"},
        }
