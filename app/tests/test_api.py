import pytest
from fastapi.testclient import TestClient

def test_terraform_discovery(client):
    response = client.get("/.well-known/terraform.json")
    assert response.status_code == 200
    assert "modules.v1" in response.json()
    assert "providers.v1" in response.json()

def test_list_versions(client, auth_headers):
    response = client.get(
        "/v1/modules/test/module/aws/versions",
        headers=auth_headers
    )
    assert response.status_code in [200, 404]

def test_search_modules(client):
    response = client.get("/v1/modules/search?query=test")
    assert response.status_code == 200
    assert "modules" in response.json()

def test_upload_module(client, auth_headers, test_module_zip):
    with open(test_module_zip, "rb") as f:
        response = client.post(
            "/api/modules/test/module/aws/1.0.0/upload",
            files={"file": ("test.zip", f)},
            headers=auth_headers
        )
        assert response.status_code in [200, 401]
