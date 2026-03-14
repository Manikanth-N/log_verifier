"""
Export functionality tests
"""
import pytest


class TestExport:
    """Test CSV export endpoint"""

    def test_export_csv_basic(self, base_url, api_client, demo_log_id):
        """Test GET /api/logs/{id}/export returns CSV data"""
        response = api_client.get(
            f"{base_url}/api/logs/{demo_log_id}/export",
            params={"message_type": "ATT"}
        )
        assert response.status_code == 200, f"CSV export failed: {response.text}"
        
        # Verify headers
        assert response.headers.get("Content-Type") == "text/csv", "Wrong content type"
        assert "Content-Disposition" in response.headers, "Missing Content-Disposition header"
        assert "ATT_export.csv" in response.headers["Content-Disposition"], "Wrong filename"
        
        # Verify CSV content
        csv_content = response.text
        assert len(csv_content) > 0, "CSV should not be empty"
        
        lines = csv_content.strip().split('\n')
        assert len(lines) > 1, "CSV should have header + data rows"
        
        # Verify header row has expected fields
        header = lines[0]
        assert "TimeUS" in header or "Time" in header, "CSV should have time column"
        assert "Roll" in header, "ATT CSV should have Roll column"
        
        print(f"✓ CSV export: ATT data, {len(lines)-1} rows exported")

    def test_export_different_message_types(self, base_url, api_client, demo_log_id):
        """Test CSV export for different message types"""
        message_types = ["ATT", "IMU", "GPS", "BAT"]
        
        for msg_type in message_types:
            response = api_client.get(
                f"{base_url}/api/logs/{demo_log_id}/export",
                params={"message_type": msg_type}
            )
            assert response.status_code == 200, f"Export failed for {msg_type}: {response.text}"
            
            lines = response.text.strip().split('\n')
            assert len(lines) > 1, f"{msg_type} export should have data"
        
        print(f"✓ CSV export tested for {len(message_types)} message types")

    def test_export_invalid_message_type(self, base_url, api_client, demo_log_id):
        """Test CSV export with invalid message type"""
        response = api_client.get(
            f"{base_url}/api/logs/{demo_log_id}/export",
            params={"message_type": "NONEXISTENT"}
        )
        assert response.status_code == 400, "Should return 400 for invalid message type"
        print("✓ CSV export rejects invalid message types")

    def test_export_nonexistent_log(self, base_url, api_client):
        """Test CSV export on non-existent log"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(
            f"{base_url}/api/logs/{fake_id}/export",
            params={"message_type": "ATT"}
        )
        assert response.status_code == 404, "Should return 404 for non-existent log"
        print("✓ CSV export returns 404 for non-existent log")

    def test_export_default_message_type(self, base_url, api_client, demo_log_id):
        """Test CSV export with default message type (ATT)"""
        response = api_client.get(f"{base_url}/api/logs/{demo_log_id}/export")
        assert response.status_code == 200, f"Default export failed: {response.text}"
        assert "ATT_export.csv" in response.headers["Content-Disposition"], "Default should be ATT"
        print("✓ CSV export defaults to ATT message type")
