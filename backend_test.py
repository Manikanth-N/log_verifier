#!/usr/bin/env python3
"""
Comprehensive backend API test suite for Vehicle Log Analyzer
Testing NEW analysis features: Motor Harmonics, Correlations, Presets
Plus existing endpoints and Phase 2 features for regression testing
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

def test_motor_harmonics(log_id: str):
    """Test motor harmonics analysis endpoint"""
    log_test("=== Testing Motor Harmonics ===")
    
    result = test_api_call("GET", f"/logs/{log_id}/motor-harmonics")
    
    if not result["success"]:
        log_test(f"❌ Motor harmonics failed: {result['error']}", "ERROR")
        return {"success": False, "error": result["error"]}
    
    try:
        data = result["response"].json()
        
        # Check for motor_harmonics array
        motor_harmonics = data.get("motor_harmonics", [])
        if not isinstance(motor_harmonics, list):
            log_test("❌ Motor harmonics: motor_harmonics not a list", "ERROR")
            return {"success": False, "error": "Invalid motor_harmonics structure"}
        
        # Check for motor_imbalance data
        motor_imbalance = data.get("motor_imbalance")
        if not motor_imbalance:
            log_test("❌ Motor harmonics: Missing motor_imbalance", "ERROR")
            return {"success": False, "error": "Missing motor_imbalance"}
        
        # Validate motor harmonics structure
        valid_motors = 0
        for motor in motor_harmonics:
            required_fields = ["motor", "motor_num", "harmonics", "dominant_freq", "total_harmonic_distortion"]
            if all(field in motor for field in required_fields):
                valid_motors += 1
                # Log details for first motor
                if valid_motors == 1:
                    log_test(f"   Motor {motor['motor']}: {motor['dominant_freq']}Hz dominant, {motor['total_harmonic_distortion']}% THD")
        
        # Validate motor imbalance structure
        imbalance_fields = ["max_deviation", "max_deviation_motor", "imbalance_percentage", "status"]
        missing_imbalance = [field for field in imbalance_fields if field not in motor_imbalance]
        if missing_imbalance:
            log_test(f"⚠️ Motor imbalance missing fields: {missing_imbalance}", "WARN")
        else:
            log_test(f"   Imbalance: {motor_imbalance['imbalance_percentage']}% ({motor_imbalance['status']})")
        
        log_test(f"✅ Motor harmonics analysis working: {len(motor_harmonics)} motors analyzed")
        return {"success": True, "motors_analyzed": len(motor_harmonics), "valid_motors": valid_motors}
        
    except json.JSONDecodeError:
        log_test("❌ Motor harmonics: Invalid JSON", "ERROR")
        return {"success": False, "error": "Invalid JSON"}


def test_correlations(log_id: str):
    """Test correlation analysis endpoint"""
    log_test("=== Testing Correlations ===")
    
    result = test_api_call("GET", f"/logs/{log_id}/correlations")
    
    if not result["success"]:
        log_test(f"❌ Correlations failed: {result['error']}", "ERROR")
        return {"success": False, "error": result["error"]}
    
    try:
        data = result["response"].json()
        
        # Check for vibration_throttle analysis
        vibe_throttle = data.get("vibration_throttle", {})
        if not vibe_throttle:
            log_test("❌ Correlations: Missing vibration_throttle", "ERROR")
            return {"success": False, "error": "Missing vibration_throttle"}
        
        vibe_status = vibe_throttle.get("status")
        if vibe_status != "success":
            log_test(f"❌ Vibration-throttle analysis status: {vibe_status}", "ERROR")
            return {"success": False, "error": f"Vibration analysis failed: {vibe_status}"}
        
        # Check correlations array
        correlations = vibe_throttle.get("correlations", [])
        if not isinstance(correlations, list):
            log_test("❌ Correlations: correlations not a list", "ERROR")
            return {"success": False, "error": "Invalid correlations structure"}
        
        # Validate correlation data for each axis
        valid_axes = 0
        for corr in correlations:
            required_fields = ["axis", "pearson_correlation", "correlation_strength", "vibration_by_throttle"]
            if all(field in corr for field in required_fields):
                valid_axes += 1
                # Log details for each axis
                log_test(f"   {corr['axis']}: {corr['pearson_correlation']} ({corr['correlation_strength']})")
        
        # Check for battery_load analysis
        battery_load = data.get("battery_load", {})
        if not battery_load:
            log_test("❌ Correlations: Missing battery_load", "ERROR")
            return {"success": False, "error": "Missing battery_load"}
        
        battery_status = battery_load.get("status", "unknown")
        log_test(f"   Battery-load analysis: {battery_status}")
        
        log_test(f"✅ Correlation analysis working: {len(correlations)} axes analyzed")
        return {"success": True, "axes_analyzed": len(correlations), "valid_axes": valid_axes}
        
    except json.JSONDecodeError:
        log_test("❌ Correlations: Invalid JSON", "ERROR")
        return {"success": False, "error": "Invalid JSON"}


def test_presets():
    """Test presets endpoint"""
    log_test("=== Testing Presets ===")
    
    result = test_api_call("GET", "/presets")
    
    if not result["success"]:
        log_test(f"❌ Presets failed: {result['error']}", "ERROR")
        return {"success": False, "error": result["error"]}
    
    try:
        data = result["response"].json()
        presets = data.get("presets", [])
        
        if not isinstance(presets, list):
            log_test("❌ Presets: presets not a list", "ERROR")
            return {"success": False, "error": "Invalid presets structure"}
        
        if len(presets) < 4:
            log_test(f"❌ Presets: Expected 4 default presets, got {len(presets)}", "ERROR")
            return {"success": False, "error": f"Missing default presets"}
        
        # Check for expected default presets
        expected_presets = ["attitude", "vibration", "motors", "battery"]
        found_presets = []
        
        for preset in presets:
            if not isinstance(preset, dict):
                continue
            preset_id = preset.get("id", "")
            preset_name = preset.get("name", "")
            if preset_id in expected_presets or preset_name.lower() in expected_presets:
                found_presets.append(preset_name or preset_id)
                # Log details for first few presets
                if len(found_presets) <= 2:
                    signals_count = len(preset.get("signals", []))
                    log_test(f"   {preset_name}: {signals_count} signals")
        
        missing_presets = [p for p in expected_presets if p not in [fp.lower() for fp in found_presets]]
        if missing_presets:
            log_test(f"⚠️ Some expected presets missing: {missing_presets}", "WARN")
        
        log_test(f"✅ Presets endpoint working: {len(presets)} presets available")
        return {"success": True, "presets_count": len(presets), "found_defaults": len(found_presets)}
        
    except json.JSONDecodeError:
        log_test("❌ Presets: Invalid JSON", "ERROR")
        return {"success": False, "error": "Invalid JSON"}


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
        "motor_harmonics": None,
        "correlations": None,
        "presets": None,
        "existing_endpoints": None,
        "parameter_limits": None,
        "reports": None,
        "charts": None, 
        "ai_insights": None
    }
    
    # Step 2: Test NEW endpoints (as requested in review)
    test_results["motor_harmonics"] = test_motor_harmonics(log_id)
    test_results["correlations"] = test_correlations(log_id)
    test_results["presets"] = test_presets()
    
    # Step 3: Test existing endpoints still work
    test_results["existing_endpoints"] = test_existing_endpoints(log_id)
    test_results["parameter_limits"] = test_parameter_limits(log_id)
    
    # Step 4: Test Phase 2 endpoints (for completeness)
    test_results["reports"] = test_report_generation(log_id)
    test_results["charts"] = test_chart_export(log_id)
    
    # Step 5: Test AI insights
    test_results["ai_insights"] = test_ai_insights(log_id)
    
    # Summary
    log_test("\n=== TEST SUMMARY ===")
    
    # NEW FEATURES TESTS (Primary focus)
    motor_success = test_results["motor_harmonics"] and test_results["motor_harmonics"].get("success", False)
    log_test(f"🆕 Motor Harmonics: {'✅ Working' if motor_success else '❌ Failed'}")
    
    corr_success = test_results["correlations"] and test_results["correlations"].get("success", False)
    log_test(f"🆕 Correlations: {'✅ Working' if corr_success else '❌ Failed'}")
    
    preset_success = test_results["presets"] and test_results["presets"].get("success", False)
    log_test(f"🆕 Presets: {'✅ Working' if preset_success else '❌ Failed'}")
    
    # EXISTING ENDPOINTS VERIFICATION
    existing_passed = 0
    if test_results["existing_endpoints"]:
        for endpoint, result in test_results["existing_endpoints"].items():
            if result.get("success"):
                existing_passed += 1
    log_test(f"Existing Endpoints: {existing_passed}/3 working")
    
    # Parameter limits (enhanced diagnostics)
    param_success = test_results["parameter_limits"] and test_results["parameter_limits"].get("success", False)
    log_test(f"Parameter Limits: {'✅ Working' if param_success else '❌ Failed'}")
    
    # PHASE 2 FEATURES (Secondary)
    report_passed = 0
    if test_results["reports"]:
        for fmt, result in test_results["reports"].items():
            if result.get("success"):
                report_passed += 1
    log_test(f"Report Generation: {report_passed}/3 formats working")
    
    chart_passed = 0
    if test_results["charts"]:
        for fmt, result in test_results["charts"].items():
            if result.get("success"):
                chart_passed += 1
    log_test(f"Chart Export: {chart_passed}/2 formats working")
    
    # AI insights
    ai_success = test_results["ai_insights"] and test_results["ai_insights"].get("success", False)
    log_test(f"AI Insights: {'⚠️ Timeout' if not ai_success else '✅ Working'}")
    
    # Final status focusing on NEW features
    critical_failures = []
    if not motor_success:
        critical_failures.append("Motor Harmonics Analysis")
    if not corr_success:
        critical_failures.append("Correlation Analysis")
    if not preset_success:
        critical_failures.append("Presets System")
    if existing_passed < 3:
        critical_failures.append("Core API Endpoints")
    
    if critical_failures:
        log_test(f"\n❌ CRITICAL FAILURES: {', '.join(critical_failures)}", "ERROR")
    else:
        log_test("\n✅ ALL NEW ANALYSIS FEATURES WORKING", "INFO")
    
    return test_results

if __name__ == "__main__":
    main()