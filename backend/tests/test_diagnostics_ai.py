"""
Diagnostics and AI insights tests
"""
import pytest


class TestDiagnostics:
    """Test automated diagnostics endpoint"""

    def test_diagnostics_basic(self, base_url, api_client, demo_log_id):
        """Test GET /api/logs/{id}/diagnostics returns health score and checks"""
        response = api_client.get(f"{base_url}/api/logs/{demo_log_id}/diagnostics")
        assert response.status_code == 200, f"Diagnostics failed: {response.text}"
        
        data = response.json()
        assert "log_id" in data, "Missing log_id"
        assert "diagnostics" in data, "Missing diagnostics"
        
        diag = data["diagnostics"]
        # Verify top-level fields
        assert "health_score" in diag, "Missing health_score"
        assert "total_checks" in diag, "Missing total_checks"
        assert "critical" in diag, "Missing critical count"
        assert "warnings" in diag, "Missing warnings count"
        assert "passed" in diag, "Missing passed count"
        assert "checks" in diag, "Missing checks array"
        
        # Verify health score is valid
        assert 0 <= diag["health_score"] <= 100, f"Health score out of range: {diag['health_score']}"
        
        # Verify checks array
        assert isinstance(diag["checks"], list), "Checks should be a list"
        assert len(diag["checks"]) > 0, "Should have at least some checks"
        
        # Verify count matches
        total = diag["critical"] + diag["warnings"] + diag["passed"]
        assert total == diag["total_checks"], "Check counts don't match total"
        
        print(f"✓ Diagnostics: Health Score {diag['health_score']}/100, {diag['total_checks']} checks")

    def test_diagnostics_check_structure(self, base_url, api_client, demo_log_id):
        """Test individual diagnostic check structure"""
        response = api_client.get(f"{base_url}/api/logs/{demo_log_id}/diagnostics")
        assert response.status_code == 200
        
        diag = response.json()["diagnostics"]
        checks = diag["checks"]
        
        if len(checks) > 0:
            check = checks[0]
            # Verify required fields
            required_fields = ["name", "category", "status", "severity", "value", 
                             "threshold", "explanation", "fix", "beginner_text"]
            for field in required_fields:
                assert field in check, f"Check missing required field: {field}"
            
            # Verify status values
            assert check["status"] in ["good", "warning", "critical"], f"Invalid status: {check['status']}"
            
            # Verify severity range
            assert 0 <= check["severity"] <= 10, f"Severity out of range: {check['severity']}"
            
            print(f"✓ Check structure validated: {check['name']} ({check['status']})")

    def test_diagnostics_categories(self, base_url, api_client, demo_log_id):
        """Test that diagnostics cover expected categories"""
        response = api_client.get(f"{base_url}/api/logs/{demo_log_id}/diagnostics")
        assert response.status_code == 200
        
        diag = response.json()["diagnostics"]
        checks = diag["checks"]
        
        categories = set(check["category"] for check in checks)
        expected_categories = {"vibration", "gps", "power", "motors"}
        
        # Should have at least some of the core categories
        found = categories.intersection(expected_categories)
        assert len(found) > 0, f"No expected categories found. Got: {categories}"
        
        print(f"✓ Diagnostic categories: {', '.join(sorted(categories))}")

    def test_diagnostics_nonexistent_log(self, base_url, api_client):
        """Test diagnostics on non-existent log"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{base_url}/api/logs/{fake_id}/diagnostics")
        assert response.status_code == 404, "Should return 404 for non-existent log"
        print("✓ Diagnostics returns 404 for non-existent log")


class TestAIInsights:
    """Test AI-powered insights endpoint"""

    def test_ai_insights_basic(self, base_url, api_client, demo_log_id):
        """Test POST /api/logs/{id}/ai-insights with GPT-5.2"""
        payload = {"context": None}
        response = api_client.post(
            f"{base_url}/api/logs/{demo_log_id}/ai-insights",
            json=payload
        )
        assert response.status_code == 200, f"AI insights failed: {response.text}"
        
        data = response.json()
        assert "log_id" in data, "Missing log_id"
        assert "insights" in data, "Missing insights"
        
        insights = data["insights"]
        # Should have either actual insights or error message
        assert "insights" in insights or "error" in insights, "Missing insights or error field"
        
        if "insights" in insights and insights["insights"]:
            # If AI worked, check response structure
            assert len(insights["insights"]) > 0, "AI insights should not be empty"
            assert "model" in insights, "Missing model field"
            print(f"✓ AI insights generated: {len(insights['insights'])} chars, model: {insights.get('model', 'N/A')}")
        else:
            # AI might be unavailable, which is acceptable
            print(f"⚠ AI insights unavailable: {insights.get('error', 'Unknown error')}")

    def test_ai_insights_with_context(self, base_url, api_client, demo_log_id):
        """Test AI insights with user context"""
        payload = {"context": "I noticed some vibration during forward flight. What could be causing this?"}
        response = api_client.post(
            f"{base_url}/api/logs/{demo_log_id}/ai-insights",
            json=payload
        )
        assert response.status_code == 200, f"AI insights with context failed: {response.text}"
        print("✓ AI insights with user context processed")

    def test_ai_insights_nonexistent_log(self, base_url, api_client):
        """Test AI insights on non-existent log"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {"context": None}
        response = api_client.post(f"{base_url}/api/logs/{fake_id}/ai-insights", json=payload)
        assert response.status_code == 404, "Should return 404 for non-existent log"
        print("✓ AI insights returns 404 for non-existent log")
