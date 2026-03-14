"""
Core API tests: health check, demo creation, log listing, log retrieval
"""
import pytest


class TestAPIHealth:
    """Test API health and basic endpoints"""

    def test_api_root(self, base_url, api_client):
        """Test API root endpoint returns version info"""
        response = api_client.get(f"{base_url}/api/")
        assert response.status_code == 200, f"API root failed: {response.text}"
        data = response.json()
        assert "message" in data, "Missing 'message' in response"
        assert "version" in data, "Missing 'version' in response"
        print(f"✓ API root: {data['message']} v{data['version']}")


class TestLogManagement:
    """Test log creation, listing, retrieval, deletion"""

    def test_create_demo_log(self, base_url, api_client):
        """Test demo log creation and verify response structure"""
        response = api_client.post(f"{base_url}/api/logs/demo")
        assert response.status_code == 200, f"Demo creation failed: {response.text}"
        
        data = response.json()
        # Verify required fields
        assert "log_id" in data, "Missing log_id"
        assert "filename" in data, "Missing filename"
        assert "upload_date" in data, "Missing upload_date"
        assert "duration_sec" in data, "Missing duration_sec"
        assert "message_types" in data, "Missing message_types"
        assert "vehicle_type" in data, "Missing vehicle_type"
        assert "is_demo" in data, "Missing is_demo"
        
        # Verify demo flag
        assert data["is_demo"] is True, "Demo log should have is_demo=True"
        assert data["filename"] == "demo_flight.bin", "Incorrect demo filename"
        
        # Verify message types
        expected_types = ["ATT", "IMU", "VIBE", "GPS", "BAT", "RCIN", "RCOU", "BARO", "MAG", "EKF", "MODE"]
        for msg_type in expected_types:
            assert msg_type in data["message_types"], f"Missing expected message type: {msg_type}"
        
        print(f"✓ Demo log created: {data['log_id']}, duration: {data['duration_sec']}s, types: {len(data['message_types'])}")

    def test_list_logs(self, base_url, api_client, demo_log_id):
        """Test listing logs and verify demo log is present"""
        response = api_client.get(f"{base_url}/api/logs")
        assert response.status_code == 200, f"List logs failed: {response.text}"
        
        logs = response.json()
        assert isinstance(logs, list), "Response should be a list"
        assert len(logs) > 0, "Should have at least one log (demo)"
        
        # Find demo log
        demo_log = next((log for log in logs if log["log_id"] == demo_log_id), None)
        assert demo_log is not None, f"Demo log {demo_log_id} not found in list"
        assert demo_log["is_demo"] is True, "Demo log should have is_demo=True"
        
        print(f"✓ Listed {len(logs)} logs, demo log found")

    def test_get_log_by_id(self, base_url, api_client, demo_log_id):
        """Test retrieving specific log by ID"""
        response = api_client.get(f"{base_url}/api/logs/{demo_log_id}")
        assert response.status_code == 200, f"Get log failed: {response.text}"
        
        log = response.json()
        assert log["log_id"] == demo_log_id, "Returned log_id doesn't match request"
        assert "filename" in log, "Missing filename"
        assert "message_types" in log, "Missing message_types"
        
        print(f"✓ Retrieved log: {log['filename']}")

    def test_get_nonexistent_log(self, base_url, api_client):
        """Test retrieving non-existent log returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{base_url}/api/logs/{fake_id}")
        assert response.status_code == 404, "Should return 404 for non-existent log"
        print("✓ Non-existent log returns 404")

    def test_delete_log(self, base_url, api_client):
        """Test log deletion - create new log, delete it, verify removal"""
        # Create a new demo log for deletion
        create_response = api_client.post(f"{base_url}/api/logs/demo")
        assert create_response.status_code == 200
        log_id = create_response.json()["log_id"]
        
        # Delete the log
        delete_response = api_client.delete(f"{base_url}/api/logs/{log_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        # Verify log is gone (GET should return 404)
        get_response = api_client.get(f"{base_url}/api/logs/{log_id}")
        assert get_response.status_code == 404, "Log should be deleted"
        
        print(f"✓ Log deleted: {log_id}")
