#!/usr/bin/env python3
"""
Comprehensive backend API test suite for Vehicle Log Analyzer
Testing Phase 2 features: Report Generation, Chart Export, Parameter Limits
"""

import requests
import json
import tempfile
import os
import time
from typing import Dict, Any, Optional

# Use backend URL from environment 
BACKEND_URL = "https://repo-dev-complete.preview.emergentagent.com/api"

def log_test(message: str, level: str = "INFO"):
    """Simple logging function"""
    print(f"[{level}] {message}")

def test_api_call(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make API call and return structured result"""
    url = f"{BACKEND_URL}{endpoint}"
    log_test(f"Testing {method} {endpoint}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=30, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=30, **kwargs)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=30, **kwargs)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "response": response,
            "error": None if response.status_code < 400 else f"HTTP {response.status_code}"
        }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout (30s)"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_demo_log_creation():
    """Test creating a demo log to get log_id"""
    log_test("=== Testing Demo Log Creation ===")
    result = test_api_call("POST", "/logs/demo")
    
    if not result["success"]:
        log_test(f"❌ Demo log creation failed: {result['error']}", "ERROR")
        return None
        
    try:
        data = result["response"].json()
        log_id = data.get("log_id")
        if not log_id:
            log_test("❌ No log_id in demo response", "ERROR")
            return None
            
        log_test(f"✅ Demo log created successfully: {log_id}")
        log_test(f"   Duration: {data.get('duration_sec', 'N/A')} seconds")
        log_test(f"   Messages: {', '.join(data.get('message_types', []))}")
        return log_id
        
    except json.JSONDecodeError:
        log_test("❌ Invalid JSON response from demo creation", "ERROR")
        return None

def test_report_generation(log_id: str):
    """Test report generation in all formats"""
    log_test("=== Testing Report Generation ===")
    results = {}
    
    formats = ["pdf", "html", "md"]
    for fmt in formats:
        log_test(f"Testing {fmt.upper()} report generation...")
        result = test_api_call("GET", f"/logs/{log_id}/report", params={"format": fmt})
        
        if not result["success"]:
            log_test(f"❌ {fmt.upper()} report failed: {result['error']}", "ERROR")
            results[fmt] = {"success": False, "error": result["error"]}
            continue
            
        response = result["response"]
        expected_types = {
            "pdf": "application/pdf",
            "html": "text/html", 
            "md": "text/markdown"
        }
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        expected_type = expected_types[fmt]
        
        if expected_type not in content_type:
            log_test(f"⚠️ {fmt.upper()} report: Expected content-type '{expected_type}', got '{content_type}'", "WARN")
        
        # Check content length
        content_length = len(response.content)
        if content_length == 0:
            log_test(f"❌ {fmt.upper()} report: Empty response", "ERROR")
            results[fmt] = {"success": False, "error": "Empty response"}
            continue
            
        # Check for basic report content
        if fmt == "md":
            content = response.content.decode('utf-8', errors='ignore')
            if "Vehicle Log Analysis Report" not in content:
                log_test(f"❌ {fmt.upper()} report: Missing title in content", "ERROR")
                results[fmt] = {"success": False, "error": "Missing report title"}
                continue
        
        log_test(f"✅ {fmt.upper()} report generated successfully ({content_length} bytes)")
        results[fmt] = {"success": True, "size": content_length}
    
    return results

def test_chart_export(log_id: str):
    """Test chart export functionality"""
    log_test("=== Testing Chart Export ===")
    results = {}
    
    # Test payload - charts with roll and pitch
    test_payload = {
        "signals": [
            {"type": "ATT", "field": "Roll"},
            {"type": "ATT", "field": "Pitch"}
        ],
        "title": "Test Chart Export",
        "format": "png"
    }
    
    formats = ["png", "svg"]
    for fmt in formats:
        log_test(f"Testing {fmt.upper()} chart export...")
        payload = test_payload.copy()
        payload["format"] = fmt
        
        result = test_api_call("POST", f"/logs/{log_id}/export-chart", 
                             json=payload, 
                             headers={"Content-Type": "application/json"})
        
        if not result["success"]:
            log_test(f"❌ {fmt.upper()} chart export failed: {result['error']}", "ERROR")
            results[fmt] = {"success": False, "error": result["error"]}
            continue
            
        response = result["response"]
        
        # Check content type
        expected_types = {"png": "image/png", "svg": "image/svg+xml"}
        content_type = response.headers.get('content-type', '')
        expected_type = expected_types[fmt]
        
        if expected_type not in content_type:
            log_test(f"⚠️ {fmt.upper()} chart: Expected content-type '{expected_type}', got '{content_type}'", "WARN")
        
        # Check content length
        content_length = len(response.content)
        if content_length == 0:
            log_test(f"❌ {fmt.upper()} chart: Empty response", "ERROR")
            results[fmt] = {"success": False, "error": "Empty response"}
            continue
            
        # Basic content validation
        if fmt == "png" and not response.content.startswith(b'\x89PNG'):
            log_test(f"❌ {fmt.upper()} chart: Invalid PNG header", "ERROR")
            results[fmt] = {"success": False, "error": "Invalid PNG format"}
            continue
            
        if fmt == "svg" and b'<svg' not in response.content[:200]:
            log_test(f"❌ {fmt.upper()} chart: Missing SVG header", "ERROR")  
            results[fmt] = {"success": False, "error": "Invalid SVG format"}
            continue
            
        log_test(f"✅ {fmt.upper()} chart exported successfully ({content_length} bytes)")
        results[fmt] = {"success": True, "size": content_length}
    
    return results

def test_parameter_limits(log_id: str):
    """Test parameter limits in diagnostics response"""
    log_test("=== Testing Parameter Limits ===")
    
    result = test_api_call("GET", f"/logs/{log_id}/diagnostics")
    
    if not result["success"]:
        log_test(f"❌ Diagnostics request failed: {result['error']}", "ERROR")
        return {"success": False, "error": result["error"]}
    
    try:
        data = result["response"].json()
        diagnostics = data.get("diagnostics", {})
        
        # Check if parameter_limits exists
        parameter_limits = diagnostics.get("parameter_limits", [])
        if not parameter_limits:
            log_test("❌ No parameter_limits found in diagnostics response", "ERROR")
            return {"success": False, "error": "Missing parameter_limits"}
        
        if not isinstance(parameter_limits, list):
            log_test("❌ parameter_limits is not a list", "ERROR")
            return {"success": False, "error": "parameter_limits wrong type"}
        
        # Validate structure of parameter limits
        required_fields = ["name", "value", "min_limit", "max_limit", "status", "unit", "description"]
        valid_count = 0
        
        for limit in parameter_limits:
            if not isinstance(limit, dict):
                continue
                
            missing_fields = [field for field in required_fields if field not in limit]
            if missing_fields:
                log_test(f"⚠️ Parameter limit missing fields: {missing_fields}", "WARN")
                continue
                
            valid_count += 1
            
            # Log some example parameter limits
            if valid_count <= 3:
                log_test(f"   {limit['name']}: {limit['value']} {limit['unit']} (status: {limit['status']})")
        
        log_test(f"✅ Parameter limits found: {len(parameter_limits)} total, {valid_count} valid")
        return {"success": True, "count": len(parameter_limits), "valid_count": valid_count}
        
    except json.JSONDecodeError:
        log_test("❌ Invalid JSON response from diagnostics", "ERROR")
        return {"success": False, "error": "Invalid JSON"}

def test_existing_endpoints(log_id: str):
    """Test that existing endpoints still work"""
    log_test("=== Testing Existing Endpoints ===")
    results = {}
    
    # Test signals endpoint
    log_test("Testing signals endpoint...")
    result = test_api_call("GET", f"/logs/{log_id}/signals")
    if result["success"]:
        try:
            data = result["response"].json()
            signals = data.get("signals", {})
            if signals:
                log_test(f"✅ Signals endpoint working: {len(signals)} message types")
                results["signals"] = {"success": True}
            else:
                log_test("❌ Signals endpoint: No signals returned", "ERROR")
                results["signals"] = {"success": False, "error": "No signals"}
        except:
            log_test("❌ Signals endpoint: Invalid JSON", "ERROR")
            results["signals"] = {"success": False, "error": "Invalid JSON"}
    else:
        log_test(f"❌ Signals endpoint failed: {result['error']}", "ERROR")
        results["signals"] = {"success": False, "error": result["error"]}
    
    # Test data endpoint
    log_test("Testing data endpoint...")
    data_payload = {
        "signals": [{"type": "ATT", "field": "Roll"}],
        "max_points": 1000
    }
    result = test_api_call("POST", f"/logs/{log_id}/data", 
                         json=data_payload, 
                         headers={"Content-Type": "application/json"})
    if result["success"]:
        try:
            data = result["response"].json()
            data_points = data.get("data", [])
            if data_points and len(data_points) > 0:
                log_test(f"✅ Data endpoint working: {len(data_points[0].get('values', []))} data points")
                results["data"] = {"success": True}
            else:
                log_test("❌ Data endpoint: No data returned", "ERROR")
                results["data"] = {"success": False, "error": "No data"}
        except:
            log_test("❌ Data endpoint: Invalid JSON", "ERROR")
            results["data"] = {"success": False, "error": "Invalid JSON"}
    else:
        log_test(f"❌ Data endpoint failed: {result['error']}", "ERROR")
        results["data"] = {"success": False, "error": result["error"]}
    
    # Test FFT endpoint
    log_test("Testing FFT endpoint...")
    fft_payload = {
        "signal_type": "ATT",
        "signal_field": "Roll",
        "window_size": 512,
        "overlap": 0.5
    }
    result = test_api_call("POST", f"/logs/{log_id}/fft", 
                         json=fft_payload, 
                         headers={"Content-Type": "application/json"})
    if result["success"]:
        try:
            data = result["response"].json()
            fft_data = data.get("fft", {})
            if fft_data and "frequencies" in fft_data:
                log_test(f"✅ FFT endpoint working: {len(fft_data.get('frequencies', []))} frequency bins")
                results["fft"] = {"success": True}
            else:
                log_test("❌ FFT endpoint: No FFT data returned", "ERROR")
                results["fft"] = {"success": False, "error": "No FFT data"}
        except:
            log_test("❌ FFT endpoint: Invalid JSON", "ERROR")
            results["fft"] = {"success": False, "error": "Invalid JSON"}
    else:
        log_test(f"❌ FFT endpoint failed: {result['error']}", "ERROR")
        results["fft"] = {"success": False, "error": result["error"]}
    
    return results

def test_ai_insights(log_id: str):
    """Test AI insights endpoint"""
    log_test("=== Testing AI Insights ===")
    
    ai_payload = {
        "context": "Please analyze this flight for any issues"
    }
    
    result = test_api_call("POST", f"/logs/{log_id}/ai-insights",
                         json=ai_payload,
                         headers={"Content-Type": "application/json"})
    
    if not result["success"]:
        log_test(f"❌ AI Insights failed: {result['error']}", "ERROR")
        return {"success": False, "error": result["error"]}
    
    try:
        data = result["response"].json()
        insights = data.get("insights", {})
        
        if not insights:
            log_test("❌ AI Insights: No insights returned", "ERROR")
            return {"success": False, "error": "No insights"}
        
        log_test("✅ AI Insights working")
        return {"success": True}
        
    except json.JSONDecodeError:
        log_test("❌ AI Insights: Invalid JSON", "ERROR")
        return {"success": False, "error": "Invalid JSON"}

def main():
    """Main test runner"""
    log_test("Starting Vehicle Log Analyzer Backend API Tests")
    log_test(f"Backend URL: {BACKEND_URL}")
    
    # Step 1: Create demo log
    log_id = test_demo_log_creation()
    if not log_id:
        log_test("❌ Cannot continue without log_id", "ERROR")
        return
    
    # Give the backend a moment to process
    time.sleep(1)
    
    test_results = {
        "log_id": log_id,
        "reports": None,
        "charts": None, 
        "parameter_limits": None,
        "existing_endpoints": None,
        "ai_insights": None
    }
    
    # Step 2: Test report generation
    test_results["reports"] = test_report_generation(log_id)
    
    # Step 3: Test chart export
    test_results["charts"] = test_chart_export(log_id)
    
    # Step 4: Test parameter limits
    test_results["parameter_limits"] = test_parameter_limits(log_id)
    
    # Step 5: Test existing endpoints
    test_results["existing_endpoints"] = test_existing_endpoints(log_id)
    
    # Step 6: Test AI insights
    test_results["ai_insights"] = test_ai_insights(log_id)
    
    # Summary
    log_test("\n=== TEST SUMMARY ===")
    
    # Report tests
    report_passed = 0
    if test_results["reports"]:
        for fmt, result in test_results["reports"].items():
            if result.get("success"):
                report_passed += 1
    log_test(f"Report Generation: {report_passed}/3 formats working")
    
    # Chart tests
    chart_passed = 0
    if test_results["charts"]:
        for fmt, result in test_results["charts"].items():
            if result.get("success"):
                chart_passed += 1
    log_test(f"Chart Export: {chart_passed}/2 formats working")
    
    # Parameter limits
    param_success = test_results["parameter_limits"] and test_results["parameter_limits"].get("success", False)
    log_test(f"Parameter Limits: {'✅ Working' if param_success else '❌ Failed'}")
    
    # Existing endpoints
    existing_passed = 0
    if test_results["existing_endpoints"]:
        for endpoint, result in test_results["existing_endpoints"].items():
            if result.get("success"):
                existing_passed += 1
    log_test(f"Existing Endpoints: {existing_passed}/3 working")
    
    # AI insights
    ai_success = test_results["ai_insights"] and test_results["ai_insights"].get("success", False)
    log_test(f"AI Insights: {'✅ Working' if ai_success else '❌ Failed'}")
    
    # Final status
    critical_failures = []
    if report_passed < 3:
        critical_failures.append("Report Generation")
    if chart_passed < 2:
        critical_failures.append("Chart Export")
    if not param_success:
        critical_failures.append("Parameter Limits")
    
    if critical_failures:
        log_test(f"\n❌ CRITICAL FAILURES: {', '.join(critical_failures)}", "ERROR")
    else:
        log_test("\n✅ ALL PHASE 2 FEATURES WORKING", "INFO")
    
    return test_results

if __name__ == "__main__":
    main()