"""
Blog endpoint tests.
Tests blog CRUD operations and approval workflow.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_blog(client: AsyncClient, user_token: str):
    """Test blog creation."""
    response = await client.post(
        "/api/v1/blogs/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "title": "Test Blog Post",
            "content": "This is test content for the blog post.",
            "images": ["https://example.com/image1.jpg"]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Blog Post"
    assert data["content"] == "This is test content for the blog post."
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_blog_without_auth(client: AsyncClient):
    """Test blog creation without authentication."""
    response = await client.post(
        "/api/v1/blogs/",
        json={
            "title": "Test Blog Post",
            "content": "This is test content."
        }
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_public_blogs(client: AsyncClient):
    """Test listing public blogs (no auth required)."""
    response = await client.get("/api/v1/blogs/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_my_blogs(client: AsyncClient, user_token: str):
    """Test getting user's own blogs."""
    # Create a blog first
    await client.post(
        "/api/v1/blogs/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "title": "My Blog",
            "content": "My blog content"
        }
    )

    # Get user's blogs
    response = await client.get(
        "/api/v1/blogs/user/my-blogs",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) > 0
    assert blogs[0]["title"] == "My Blog"


@pytest.mark.asyncio
async def test_approve_blog(client: AsyncClient, user_token: str, approver_token: str):
    """Test blog approval by approver."""
    # Create blog
    create_response = await client.post(
        "/api/v1/blogs/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "title": "Blog to Approve",
            "content": "Content to be approved"
        }
    )
    blog_id = create_response.json()["id"]

    # Approve blog
    approve_response = await client.post(
        f"/api/v1/blogs/{blog_id}/approve",
        headers={"Authorization": f"Bearer {approver_token}"},
        json={"reason": "Looks good"}
    )

    assert approve_response.status_code == 200
    data = approve_response.json()
    assert data["status"] == "approved"
    assert data["approved_by"] is not None


@pytest.mark.asyncio
async def test_approve_blog_without_permission(client: AsyncClient, user_token: str):
    """Test blog approval without approver role."""
    # Create blog
    create_response = await client.post(
        "/api/v1/blogs/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "title": "Blog to Approve",
            "content": "Content"
        }
    )
    blog_id = create_response.json()["id"]

    # Try to approve with regular user
    approve_response = await client.post(
        f"/api/v1/blogs/{blog_id}/approve",
        headers={"Authorization": f"Bearer {user_token}"},
        json={}
    )

    assert approve_response.status_code == 403


@pytest.mark.asyncio
async def test_update_blog(client: AsyncClient, user_token: str):
    """Test blog update by author."""
    # Create blog
    create_response = await client.post(
        "/api/v1/blogs/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "title": "Original Title",
            "content": "Original content"
        }
    )
    blog_id = create_response.json()["id"]

    # Update blog
    update_response = await client.put(
        f"/api/v1/blogs/{blog_id}",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "title": "Updated Title",
            "content": "Updated content"
        }
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "Updated content"


@pytest.mark.asyncio
async def test_delete_blog(client: AsyncClient, user_token: str):
    """Test blog deletion by author."""
    # Create blog
    create_response = await client.post(
        "/api/v1/blogs/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "title": "Blog to Delete",
            "content": "Content"
        }
    )
    blog_id = create_response.json()["id"]

    # Delete blog
    delete_response = await client.delete(
        f"/api/v1/blogs/{blog_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert delete_response.status_code == 204
