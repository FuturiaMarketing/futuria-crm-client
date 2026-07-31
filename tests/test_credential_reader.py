import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "futuria-crm" / "scripts"
import sys

sys.path.insert(0, str(SCRIPTS))

import credential_reader  # noqa: E402


class CredentialReaderTests(unittest.TestCase):
    def test_environment_credentials_take_precedence(self):
        env = {
            "FUTURIA_CRM_TOKEN": "pit-test-token-value",
            "FUTURIA_CRM_LOCATION": "account123",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("platform.system", return_value="Linux"):
                self.assertEqual(
                    credential_reader.load_credentials(),
                    ("pit-test-token-value", "account123"),
                )

    def test_location_can_come_from_local_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_text(json.dumps({"location": "accountABC"}), encoding="utf-8")
            with mock.patch.dict(os.environ, {"FUTURIA_CRM_TOKEN": "pit-test-token-value"}, clear=True):
                with mock.patch.object(credential_reader, "_config_path", return_value=config):
                    with mock.patch("platform.system", return_value="Linux"):
                        self.assertEqual(
                            credential_reader.load_credentials(),
                            ("pit-test-token-value", "accountABC"),
                        )

    def test_missing_credentials_fail_without_exposing_values(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("platform.system", return_value="Linux"):
                with mock.patch.object(credential_reader, "_config_path", return_value=Path("missing")):
                    with self.assertRaises(credential_reader.CredentialError) as raised:
                        credential_reader.load_credentials()
        self.assertIn("Configurazione Futuria CRM mancante", str(raised.exception))

    def test_invalid_token_is_rejected(self):
        env = {"FUTURIA_CRM_TOKEN": "not-a-pit", "FUTURIA_CRM_LOCATION": "account123"}
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("platform.system", return_value="Linux"):
                with self.assertRaises(credential_reader.CredentialError):
                    credential_reader.load_credentials()


if __name__ == "__main__":
    unittest.main()
