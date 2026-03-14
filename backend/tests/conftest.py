import pytest
import requests
import os


@pytest.fixture(scope="session")
def base_url():
    """Get backend URL from environment."""
    url = os.environ.get('EXPO_PUBLIC_BACKEND_URL', '').rstrip('/')
    if not url:
        pytest.fail("EXPO_PUBLIC_BACKEND_URL not set in environment")
    return url


@pytest.fixture(scope="session")
def api_client(base_url):
    """Shared requests session for API calls."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def demo_log_id(base_url, api_client):
    """Create a demo log once for the entire test session."""
    response = api_client.post(f"{base_url}/api/logs/demo")
    assert response.status_code == 200, f"Failed to create demo log: {response.text}"
    data = response.json()
    log_id = data.get('log_id')
    assert log_id, "Demo log creation did not return log_id"
    print(f"\n✓ Demo log created: {log_id}")
    return log_id
