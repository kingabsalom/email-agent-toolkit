import json
import os
import tempfile
from unittest.mock import patch
from tests.conftest import mock_api_response

CORPORATE_RESPONSE = {
    "name":        "Alex Smith",
    "company":     "BigClient Corp",
    "domain_type": "corporate",
    "title":       "Account Executive",
}

PERSONAL_RESPONSE = {
    "name":        "John Doe",
    "company":     "",
    "domain_type": "personal",
    "title":       "",
}

AUTOMATED_RESPONSE = {
    "name":        "IT Alerts",
    "company":     "Company",
    "domain_type": "automated",
    "title":       "",
}


def _call(sender, payload, cache_file):
    from enrich_contact import enrich_contact
    with patch("enrich_contact.CACHE_FILE", cache_file), \
         patch("enrich_contact.client.messages.create", return_value=mock_api_response(payload)):
        return enrich_contact(sender)


def test_returns_required_fields():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        cache_path = f.name
    try:
        result = _call("Alex Smith <alex@bigclient.com>", CORPORATE_RESPONSE, cache_path)
        assert "name" in result
        assert "company" in result
        assert "domain_type" in result
        assert "title" in result
    finally:
        os.unlink(cache_path)


def test_domain_type_is_valid():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        cache_path = f.name
    try:
        result = _call("alex@bigclient.com", CORPORATE_RESPONSE, cache_path)
        assert result["domain_type"] in {"personal", "corporate", "nonprofit", "government", "automated"}
    finally:
        os.unlink(cache_path)


def test_result_cached_after_first_call():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        cache_path = f.name

    try:
        from enrich_contact import enrich_contact
        with patch("enrich_contact.CACHE_FILE", cache_path), \
             patch("enrich_contact.client.messages.create", return_value=mock_api_response(CORPORATE_RESPONSE)) as mock_api:
            enrich_contact("alex@bigclient.com")
            enrich_contact("alex@bigclient.com")
        # API should only be called once — second call hits cache
        assert mock_api.call_count == 1
    finally:
        os.unlink(cache_path)


def test_cache_written_to_disk():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        cache_path = f.name

    try:
        _call("alex@bigclient.com", CORPORATE_RESPONSE, cache_path)
        with open(cache_path) as f:
            cache = json.load(f)
        assert "alex@bigclient.com" in cache
    finally:
        os.unlink(cache_path)


def test_extracts_email_from_display_name_format():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        cache_path = f.name
    try:
        from enrich_contact import enrich_contact
        with patch("enrich_contact.CACHE_FILE", cache_path), \
             patch("enrich_contact.client.messages.create", return_value=mock_api_response(CORPORATE_RESPONSE)) as mock_api:
            enrich_contact("Alex Smith <ALEX@BigClient.COM>")
            enrich_contact("alex@bigclient.com")
        # Both map to same normalized key — API called only once
        assert mock_api.call_count == 1
    finally:
        os.unlink(cache_path)
