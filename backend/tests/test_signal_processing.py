"""
Signal processing tests: signals endpoint, data retrieval, downsampling
"""
import pytest


class TestSignalRetrieval:
    """Test signal listing and data retrieval"""

    def test_get_signals_tree(self, base_url, api_client, demo_log_id):
        """Test GET /api/logs/{id}/signals returns signal tree structure"""
        response = api_client.get(f"{base_url}/api/logs/{demo_log_id}/signals")
        assert response.status_code == 200, f"Get signals failed: {response.text}"
        
        data = response.json()
        assert "log_id" in data, "Missing log_id"
        assert "signals" in data, "Missing signals"
        assert data["log_id"] == demo_log_id, "log_id mismatch"
        
        signals = data["signals"]
        assert isinstance(signals, dict), "signals should be a dict"
        
        # Verify expected message types
        expected_types = ["ATT", "IMU", "VIBE", "GPS", "BAT"]
        for msg_type in expected_types:
            assert msg_type in signals, f"Missing message type: {msg_type}"
            assert isinstance(signals[msg_type], list), f"{msg_type} should be a list of fields"
            assert len(signals[msg_type]) > 0, f"{msg_type} should have fields"
        
        # Verify ATT has expected fields
        att_fields = signals.get("ATT", [])
        expected_att = ["Roll", "Pitch", "Yaw", "DesRoll", "DesPitch"]
        for field in expected_att:
            assert field in att_fields, f"ATT missing field: {field}"
        
        print(f"✓ Signals tree: {len(signals)} message types")

    def test_get_signal_data_single(self, base_url, api_client, demo_log_id):
        """Test POST /api/logs/{id}/data for single signal"""
        payload = {
            "signals": [{"type": "ATT", "field": "Roll"}],
            "max_points": 2000
        }
        response = api_client.post(
            f"{base_url}/api/logs/{demo_log_id}/data",
            json=payload
        )
        assert response.status_code == 200, f"Get signal data failed: {response.text}"
        
        data = response.json()
        assert "data" in data, "Missing data array"
        assert len(data["data"]) == 1, "Should return 1 signal"
        
        signal_data = data["data"][0]
        assert signal_data["type"] == "ATT", "Wrong signal type"
        assert signal_data["field"] == "Roll", "Wrong signal field"
        assert "timestamps" in signal_data, "Missing timestamps"
        assert "values" in signal_data, "Missing values"
        assert "count" in signal_data, "Missing count"
        
        # Verify data arrays
        assert len(signal_data["timestamps"]) == len(signal_data["values"]), "Timestamps and values length mismatch"
        assert len(signal_data["timestamps"]) > 0, "Should have data points"
        assert signal_data["count"] > 0, "Count should be positive"
        
        print(f"✓ Signal data: ATT.Roll, {signal_data['count']} points")

    def test_get_signal_data_multiple(self, base_url, api_client, demo_log_id):
        """Test retrieving multiple signals at once"""
        payload = {
            "signals": [
                {"type": "ATT", "field": "Roll"},
                {"type": "ATT", "field": "Pitch"},
                {"type": "IMU", "field": "GyrX"}
            ],
            "max_points": 3000
        }
        response = api_client.post(
            f"{base_url}/api/logs/{demo_log_id}/data",
            json=payload
        )
        assert response.status_code == 200, f"Get multiple signals failed: {response.text}"
        
        data = response.json()
        assert len(data["data"]) == 3, "Should return 3 signals"
        
        # Verify all requested signals are present
        returned_signals = [(d["type"], d["field"]) for d in data["data"]]
        assert ("ATT", "Roll") in returned_signals, "Missing ATT.Roll"
        assert ("ATT", "Pitch") in returned_signals, "Missing ATT.Pitch"
        assert ("IMU", "GyrX") in returned_signals, "Missing IMU.GyrX"
        
        print(f"✓ Multiple signals retrieved: {len(data['data'])} signals")

    def test_get_signal_data_downsampling(self, base_url, api_client, demo_log_id):
        """Test downsampling with max_points parameter"""
        payload = {
            "signals": [{"type": "IMU", "field": "AccZ"}],
            "max_points": 500
        }
        response = api_client.post(
            f"{base_url}/api/logs/{demo_log_id}/data",
            json=payload
        )
        assert response.status_code == 200, f"Downsampling failed: {response.text}"
        
        data = response.json()
        signal_data = data["data"][0]
        
        # Verify downsampling worked (should be <= max_points)
        actual_points = len(signal_data["timestamps"])
        assert actual_points <= 500, f"Downsampling failed: got {actual_points} points, expected <= 500"
        
        print(f"✓ Downsampling: {actual_points} points (max 500)")

    def test_get_signal_data_time_range(self, base_url, api_client, demo_log_id):
        """Test time range filtering"""
        payload = {
            "signals": [{"type": "ATT", "field": "Roll"}],
            "time_range": [10.0, 30.0],  # 10-30 seconds
            "max_points": 2000
        }
        response = api_client.post(
            f"{base_url}/api/logs/{demo_log_id}/data",
            json=payload
        )
        assert response.status_code == 200, f"Time range filter failed: {response.text}"
        
        data = response.json()
        signal_data = data["data"][0]
        timestamps = signal_data["timestamps"]
        
        # Verify all timestamps are within range
        if len(timestamps) > 0:
            assert min(timestamps) >= 10.0, f"Min timestamp {min(timestamps)} < 10.0"
            assert max(timestamps) <= 30.0, f"Max timestamp {max(timestamps)} > 30.0"
        
        print(f"✓ Time range filter: {len(timestamps)} points in [10, 30]s")

    def test_get_signal_nonexistent_log(self, base_url, api_client):
        """Test signal data request for non-existent log"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {"signals": [{"type": "ATT", "field": "Roll"}]}
        response = api_client.post(f"{base_url}/api/logs/{fake_id}/data", json=payload)
        assert response.status_code == 404, "Should return 404 for non-existent log"
        print("✓ Non-existent log in data request returns 404")
