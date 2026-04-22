package com.anonymous.frontend;

import android.util.Log;
import com.facebook.react.bridge.*;
import com.chaquo.python.*;
import com.chaquo.python.android.AndroidPlatform;

import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONException;

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;

public class AnalysisBridgeModule extends ReactContextBaseJavaModule {
    private static final String TAG = "AnalysisBridge";
    private Python python;
    private PyObject analysisAPI;

    public AnalysisBridgeModule(ReactApplicationContext reactContext) {
        super(reactContext);
        initializePython();
    }

    @Override
    public String getName() {
        return "AnalysisBridge";
    }

    private void initializePython() {
        try {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(getReactApplicationContext()));
            }
            python = Python.getInstance();
            
            // Import analysis_engine module
            PyObject analysisModule = python.getModule("analysis_engine");
            PyObject analysisAPIClass = analysisModule.get("AnalysisAPI");
            analysisAPI = analysisAPIClass.call();
            
            Log.d(TAG, "Python analysis engine initialized successfully");
        } catch (Exception e) {
            Log.e(TAG, "Failed to initialize Python", e);
        }
    }

    @ReactMethod
    public void parseLog(String filePath, Promise promise) {
        new Thread(() -> {
            try {
                PyObject result = analysisAPI.callAttr("parse_log", filePath);
                WritableMap resultMap = pyObjectToWritableMap(result);
                promise.resolve(resultMap);
            } catch (Exception e) {
                Log.e(TAG, "parseLog failed", e);
                promise.reject("PARSE_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    @ReactMethod
    public void generateDemoLog(double durationSec, Promise promise) {
        new Thread(() -> {
            try {
                PyObject result = analysisAPI.callAttr("generate_demo_log", durationSec);
                WritableMap resultMap = pyObjectToWritableMap(result);
                promise.resolve(resultMap);
            } catch (Exception e) {
                Log.e(TAG, "generateDemoLog failed", e);
                promise.reject("DEMO_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    @ReactMethod
    public void analyzeDiagnostics(ReadableMap signals, String mode, Promise promise) {
        new Thread(() -> {
            try {
                PyObject signalsPy = readableMapToPyObject(signals);
                PyObject result = analysisAPI.callAttr("analyze_diagnostics", signalsPy, mode);
                WritableMap resultMap = pyObjectToWritableMap(result);
                promise.resolve(resultMap);
            } catch (Exception e) {
                Log.e(TAG, "analyzeDiagnostics failed", e);
                promise.reject("DIAGNOSTICS_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    @ReactMethod
    public void analyzeMotorHarmonics(ReadableMap rcouData, double duration, Promise promise) {
        new Thread(() -> {
            try {
                PyObject rcouPy = readableMapToPyObject(rcouData);
                PyObject result = analysisAPI.callAttr("analyze_motor_harmonics", rcouPy, duration);
                WritableMap resultMap = pyObjectToWritableMap(result);
                promise.resolve(resultMap);
            } catch (Exception e) {
                Log.e(TAG, "analyzeMotorHarmonics failed", e);
                promise.reject("HARMONICS_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    @ReactMethod
    public void analyzeVibrationThrottleCorrelation(ReadableMap signals, Promise promise) {
        new Thread(() -> {
            try {
                PyObject signalsPy = readableMapToPyObject(signals);
                PyObject result = analysisAPI.callAttr("analyze_vibration_throttle_correlation", signalsPy);
                WritableMap resultMap = pyObjectToWritableMap(result);
                promise.resolve(resultMap);
            } catch (Exception e) {
                Log.e(TAG, "analyzeCorrelation failed", e);
                promise.reject("CORRELATION_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    @ReactMethod
    public void analyzeBatteryLoadCorrelation(ReadableMap signals, Promise promise) {
        new Thread(() -> {
            try {
                PyObject signalsPy = readableMapToPyObject(signals);
                PyObject result = analysisAPI.callAttr("analyze_battery_load_correlation", signalsPy);
                WritableMap resultMap = pyObjectToWritableMap(result);
                promise.resolve(resultMap);
            } catch (Exception e) {
                Log.e(TAG, "analyzeBatteryCorrelation failed", e);
                promise.reject("BATTERY_CORRELATION_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    @ReactMethod
    public void analyzeFFT(ReadableArray timestamps, ReadableArray values, int windowSize, Promise promise) {
        new Thread(() -> {
            try {
                PyObject timestampsPy = readableArrayToPyList(timestamps);
                PyObject valuesPy = readableArrayToPyList(values);
                PyObject result = analysisAPI.callAttr("analyze_fft", timestampsPy, valuesPy, windowSize);
                WritableMap resultMap = pyObjectToWritableMap(result);
                promise.resolve(resultMap);
            } catch (Exception e) {
                Log.e(TAG, "analyzeFFT failed", e);
                promise.reject("FFT_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    @ReactMethod
    public void getSignalData(ReadableMap signals, ReadableArray signalRequests, int maxPoints, Promise promise) {
        new Thread(() -> {
            try {
                PyObject signalsPy = readableMapToPyObject(signals);
                PyObject requestsPy = readableArrayToPyList(signalRequests);
                PyObject result = analysisAPI.callAttr("get_signal_data", signalsPy, requestsPy, maxPoints);
                WritableArray resultArray = pyObjectToWritableArray(result);
                promise.resolve(resultArray);
            } catch (Exception e) {
                Log.e(TAG, "getSignalData failed", e);
                promise.reject("SIGNAL_DATA_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    @ReactMethod
    public void exportCSV(ReadableMap signalData, Promise promise) {
        new Thread(() -> {
            try {
                PyObject dataPy = readableMapToPyObject(signalData);
                PyObject result = analysisAPI.callAttr("export_csv", dataPy);
                String csvString = result.toString();
                promise.resolve(csvString);
            } catch (Exception e) {
                Log.e(TAG, "exportCSV failed", e);
                promise.reject("CSV_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    @ReactMethod
    public void generateReport(ReadableMap logData, ReadableMap diagnostics, String format, Promise promise) {
        new Thread(() -> {
            try {
                PyObject logDataPy = readableMapToPyObject(logData);
                PyObject diagnosticsPy = readableMapToPyObject(diagnostics);
                PyObject result = analysisAPI.callAttr("generate_report", logDataPy, diagnosticsPy, format, null);
                
                // Convert bytes to base64 string for transfer
                String base64Content = android.util.Base64.encodeToString(result.toJava(byte[].class), android.util.Base64.DEFAULT);
                promise.resolve(base64Content);
            } catch (Exception e) {
                Log.e(TAG, "generateReport failed", e);
                promise.reject("REPORT_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    @ReactMethod
    public void getVersion(Promise promise) {
        try {
            PyObject version = analysisAPI.callAttr("get_version");
            promise.resolve(version.toString());
        } catch (Exception e) {
            Log.e(TAG, "getVersion failed", e);
            promise.reject("VERSION_ERROR", e.getMessage(), e);
        }
    }

    @ReactMethod
    public void verifyLog(String logPath, String pubkeyPath, String mode, Promise promise) {
        new Thread(() -> {
            try {
                // Import the security module
                PyObject securityModule = python.getModule("analysis_engine.security.log_verifier");
                PyObject verifierClass = securityModule.get("SecureLogVerifier");
                PyObject verifier = verifierClass.call();
                
                // Call verify_log with the mode parameter
                PyObject result;
                if (pubkeyPath != null && !pubkeyPath.isEmpty()) {
                    result = verifier.callAttr("verify_log", logPath, pubkeyPath, mode);
                } else {
                    result = verifier.callAttr("verify_log", logPath, (Object) null, mode);
                }
                
                // Convert result to dict and then to WritableMap
                PyObject resultDict = result.callAttr("to_dict");
                WritableMap resultMap = pyObjectToWritableMap(resultDict);
                promise.resolve(resultMap);
            } catch (Exception e) {
                Log.e(TAG, "verifyLog failed", e);
                promise.reject("VERIFY_ERROR", e.getMessage(), e);
            }
        }).start();
    }

    // ==================== Helper Methods ====================

    private PyObject readableMapToPyObject(ReadableMap map) {
        try {
            JSONObject json = convertMapToJson(map);
            String jsonString = json.toString();
            PyObject jsonModule = python.getModule("json");
            return jsonModule.callAttr("loads", jsonString);
        } catch (Exception e) {
            Log.e(TAG, "Failed to convert ReadableMap to PyObject", e);
            return python.getBuiltins().get("dict").call();
        }
    }

    private PyObject readableArrayToPyList(ReadableArray array) {
        try {
            JSONArray json = convertArrayToJson(array);
            String jsonString = json.toString();
            PyObject jsonModule = python.getModule("json");
            return jsonModule.callAttr("loads", jsonString);
        } catch (Exception e) {
            Log.e(TAG, "Failed to convert ReadableArray to PyObject", e);
            return python.getBuiltins().get("list").call();
        }
    }

    private WritableMap pyObjectToWritableMap(PyObject pyObj) {
        try {
            PyObject jsonModule = python.getModule("json");
            PyObject jsonString = jsonModule.callAttr("dumps", pyObj);
            JSONObject json = new JSONObject(jsonString.toString());
            return convertJsonToMap(json);
        } catch (Exception e) {
            Log.e(TAG, "Failed to convert PyObject to WritableMap", e);
            return Arguments.createMap();
        }
    }

    private WritableArray pyObjectToWritableArray(PyObject pyObj) {
        try {
            PyObject jsonModule = python.getModule("json");
            PyObject jsonString = jsonModule.callAttr("dumps", pyObj);
            JSONArray json = new JSONArray(jsonString.toString());
            return convertJsonToArray(json);
        } catch (Exception e) {
            Log.e(TAG, "Failed to convert PyObject to WritableArray", e);
            return Arguments.createArray();
        }
    }

    // JSON conversion helpers
    private static JSONObject convertMapToJson(ReadableMap readableMap) throws JSONException {
        JSONObject object = new JSONObject();
        ReadableMapKeySetIterator iterator = readableMap.keySetIterator();
        while (iterator.hasNextKey()) {
            String key = iterator.nextKey();
            switch (readableMap.getType(key)) {
                case Null:
                    object.put(key, JSONObject.NULL);
                    break;
                case Boolean:
                    object.put(key, readableMap.getBoolean(key));
                    break;
                case Number:
                    object.put(key, readableMap.getDouble(key));
                    break;
                case String:
                    object.put(key, readableMap.getString(key));
                    break;
                case Map:
                    object.put(key, convertMapToJson(readableMap.getMap(key)));
                    break;
                case Array:
                    object.put(key, convertArrayToJson(readableMap.getArray(key)));
                    break;
            }
        }
        return object;
    }

    private static JSONArray convertArrayToJson(ReadableArray readableArray) throws JSONException {
        JSONArray array = new JSONArray();
        for (int i = 0; i < readableArray.size(); i++) {
            switch (readableArray.getType(i)) {
                case Null:
                    array.put(JSONObject.NULL);
                    break;
                case Boolean:
                    array.put(readableArray.getBoolean(i));
                    break;
                case Number:
                    array.put(readableArray.getDouble(i));
                    break;
                case String:
                    array.put(readableArray.getString(i));
                    break;
                case Map:
                    array.put(convertMapToJson(readableArray.getMap(i)));
                    break;
                case Array:
                    array.put(convertArrayToJson(readableArray.getArray(i)));
                    break;
            }
        }
        return array;
    }

    private static WritableMap convertJsonToMap(JSONObject jsonObject) throws JSONException {
        WritableMap map = Arguments.createMap();
        JSONArray keys = jsonObject.names();
        if (keys != null) {
            for (int i = 0; i < keys.length(); i++) {
                String key = keys.getString(i);
                Object value = jsonObject.get(key);
                if (value instanceof JSONObject) {
                    map.putMap(key, convertJsonToMap((JSONObject) value));
                } else if (value instanceof JSONArray) {
                    map.putArray(key, convertJsonToArray((JSONArray) value));
                } else if (value instanceof Boolean) {
                    map.putBoolean(key, (Boolean) value);
                } else if (value instanceof Integer) {
                    map.putInt(key, (Integer) value);
                } else if (value instanceof Double) {
                    map.putDouble(key, (Double) value);
                } else if (value instanceof String) {
                    map.putString(key, (String) value);
                } else if (value == JSONObject.NULL) {
                    map.putNull(key);
                }
            }
        }
        return map;
    }

    private static WritableArray convertJsonToArray(JSONArray jsonArray) throws JSONException {
        WritableArray array = Arguments.createArray();
        for (int i = 0; i < jsonArray.length(); i++) {
            Object value = jsonArray.get(i);
            if (value instanceof JSONObject) {
                array.pushMap(convertJsonToMap((JSONObject) value));
            } else if (value instanceof JSONArray) {
                array.pushArray(convertJsonToArray((JSONArray) value));
            } else if (value instanceof Boolean) {
                array.pushBoolean((Boolean) value);
            } else if (value instanceof Integer) {
                array.pushInt((Integer) value);
            } else if (value instanceof Double) {
                array.pushDouble((Double) value);
            } else if (value instanceof String) {
                array.pushString((String) value);
            } else if (value == JSONObject.NULL) {
                array.pushNull();
            }
        }
        return array;
    }
}
