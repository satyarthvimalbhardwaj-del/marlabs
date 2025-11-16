"""
Feature request endpoint tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_feature_request(client: AsyncClient, user_token: str):
    """Test feature request creation."""
    response = await client.post(
        "/api/v1/feature-requests/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "title": "New Feature Request",
            "description": "This is a description of the feature",
            "priority": 5
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Feature Request"
    assert data["status"] == "pending"
    assert data["priority"] == 5


@pytest.mark.asyncio
async def test_list_feature_requests(client: AsyncClient, user_token: str):
    """Test listing feature requests."""
    # Create a feature request first
    await client.post(
        "/api/v1/feature-requests/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "title": "Test Feature",
            "description": "Test description",
            "priority": 3
        }
    )

    # List all requests
    response = await client.get(
        "/api/v1/feature-requests/",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    requests = response.json()
    assert len(requests) > 0


@pytest.mark.asyncio
async def test_update_feature_request_status(
        client: AsyncClient,
        user_token: str,
        admin_token: str
):
    """Test updating feature request status by admin."""
    # Create feature request
    create_response = await client.post(
        "/api/v1/feature-requests/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "title": "Feature to Update",
            "description": "Description",
            "priority": 5
        }
    )
    request_id = create_response.json()["id"]

    # Update status as admin
    update_response = await client.patch(
        f"/api/v1/feature-requests/{request_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "accepted"}
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["status"] == "accepted"
