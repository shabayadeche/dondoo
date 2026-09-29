from __future__ import annotations

import json
import unittest
from unittest.mock import Mock, patch

from app.integrations.odoo_bridge import OdooBridgeClient


class OdooBridgePatientContractTests(unittest.TestCase):
    def test_patient_relationship_request_uses_identifier_endpoint(self) -> None:
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps({
            "result": {"status": "ok", "relationship": {
                "relationshipId": 4,
                "patientIdentifier": "PT-001",
                "facilityCode": "MAIN",
                "facilityLabel": "Main Unit",
                "endoscopistUserId": "dr.njoroge",
                "endoscopistLabel": "Dr. A. Njoroge",
            }}
        }).encode()
        client = OdooBridgeClient("https://odoo.example", "phd_ass", "key")
        with patch("app.integrations.odoo_bridge.urllib_request.urlopen", return_value=response) as open_url:
            result = client.get_patient_relationship("session", "PT-001")
        self.assertEqual(result["patientIdentifier"], "PT-001")
        request = open_url.call_args.args[0]
        self.assertIn("/phd_ass_bridge/patient_relationship", request.full_url)
        self.assertEqual(json.loads(request.data)["params"]["api_key"], "key")

    def test_patient_search_returns_bridge_results(self) -> None:
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps({
            "result": {"status": "ok", "patients": [{
                "patientIdentifier": "PT-001", "displayName": "Patient One",
            }]}
        }).encode()
        client = OdooBridgeClient("https://odoo.example", "phd_ass", "key")
        with patch("app.integrations.odoo_bridge.urllib_request.urlopen", return_value=response):
            result = client.search_patients("session", "Patient")
        self.assertEqual(result[0]["patientIdentifier"], "PT-001")
