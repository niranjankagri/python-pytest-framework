"""The API answers at all: the first thing to check before anything else."""

import pytest

from framework.api.models import ApiResponse


@pytest.mark.api
@pytest.mark.smoke
def test_api_reports_it_is_running(api_client):
    response = api_client.health_check()

    assert response.status_code == 200
    body = ApiResponse[None].model_validate(response.json())
    assert body.success is True
    assert body.message == "Notes API is Running"
