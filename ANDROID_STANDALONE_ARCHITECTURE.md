# Vehicle Log Analyzer - Standalone Android Architecture

## 🎯 Architecture Transformation Plan

### **Current Architecture (Client-Server)**
```
┌─────────────────┐         ┌─────────────────┐
│  Expo Frontend  │ ──HTTP─→ │  FastAPI Server │
│  (React Native) │ ←─JSON── │    (Python)     │
└─────────────────┘         └─────────────────┘
                               ↓
                          MongoDB (metadata)
```

### **New Architecture (Standalone)**
```
┌───────────────────────────────────────┐
│         Android Application           │
│  ┌─────────────────────────────────┐  │
│  │   React Native UI Layer         │  │
│  └──────────────┬──────────────────┘  │
│                 │ Native Module       │
│  ┌──────────────▼──────────────────┐  │
│  │   Chaquopy Python Runtime       │  │
│  │  ┌──────────────────────────┐   │  │
│  │  │ log_parser.py            │   │  │
│  │  │ signal_processor.py      │   │  │
│  │  │ diagnostics_engine.py    │   │  │
│  │  │ motor_harmonics.py       │   │  │
│  │  │ correlation_analyzer.py  │   │  │
│  │  │ report_generator.py      │   │  │
│  │  └──────────────────────────┘   │  │
│  └─────────────────────────────────┘  │
│                 │                      │
│  ┌──────────────▼──────────────────┐  │
│  │   SQLite (local metadata)       │  │
│  │   File System (logs, reports)   │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
```

---

## 📦 Implementation Approach

### **Phase 1: Chaquopy Integration**
Chaquopy allows running Python code inside Android apps:
- Python 3.9+ runtime embedded in APK
- Access to NumPy, SciPy, Pandas (ARM64 binaries)
- Direct calls from React Native via Native Modules

### **Phase 2: Backend Migration**
Move Python modules from server to Android:
- Keep existing Python analysis code (90% reusable)
- Remove FastAPI/HTTP layer
- Replace MongoDB with SQLite
- Add Android-specific file handling

### **Phase 3: Native Bridge**
Create React Native Native Module:
- TypeScript ↔ Java ↔ Python bridge
- Async processing for large files
- Progress callbacks for UI updates

---

## 🛠️ Required Dependencies

### **1. Chaquopy (Python in Android)**
```gradle
// android/build.gradle (project level)
buildscript {
    repositories {
        maven { url "https://chaquo.com/maven" }
    }
    dependencies {
        classpath "com.chaquo.python:gradle:14.0.2"
    }
}

// android/app/build.gradle (app level)
plugins {
    id 'com.chaquo.python'
}

python {
    buildPython "python3"
    pip {
        install "numpy==1.24.3"
        install "scipy==1.10.1"
        install "pandas==2.0.3"
        install "pymavlink==2.4.40"  // ArduPilot log parser
        install "pillow==10.0.0"     // Chart generation
        install "reportlab==4.0.4"   // PDF reports
    }
}

android {
    defaultConfig {
        ndk {
            abiFilters "arm64-v8a", "armeabi-v7a"
        }
        python {
            version "3.9"
        }
    }
    splits {
        abi {
            enable true
            reset()
            include "arm64-v8a", "armeabi-v7a"
            universalApk false
        }
    }
}
```

### **2. SQLite (Local Database)**
```typescript
// Already available in React Native
import * as SQLite from 'expo-sqlite';
```

### **3. File System Access**
```typescript
import * as FileSystem from 'expo-file-system';
import * as DocumentPicker from 'expo-document-picker';
```

---

## 🏗️ Implementation Steps

### **Step 1: Eject from Expo to Bare Workflow**
```bash
cd /app/frontend
npx expo prebuild --clean

# This generates android/ and ios/ directories
# Needed for Chaquopy integration
```

### **Step 2: Add Chaquopy to Android Project**

**File: `android/build.gradle`**
```gradle
buildscript {
    ext {
        buildToolsVersion = "33.0.0"
        minSdkVersion = 21
        compileSdkVersion = 33
        targetSdkVersion = 33
    }
    repositories {
        google()
        mavenCentral()
        maven { url "https://chaquo.com/maven" }
    }
    dependencies {
        classpath("com.android.tools.build:gradle:7.4.2")
        classpath("com.facebook.react:react-native-gradle-plugin")
        classpath("com.chaquo.python:gradle:14.0.2")
    }
}
```

**File: `android/app/build.gradle`**
```gradle
apply plugin: "com.android.application"
apply plugin: "com.facebook.react"
apply plugin: "com.chaquo.python"

python {
    buildPython "/usr/bin/python3"
    pip {
        install "numpy==1.24.3"
        install "scipy==1.10.1"
        install "pandas==2.0.3"
        install "pymavlink==2.4.40"
    }
}

android {
    namespace "com.vehicleloganalyzer"
    compileSdkVersion rootProject.ext.compileSdkVersion
    
    defaultConfig {
        applicationId "com.vehicleloganalyzer"
        minSdkVersion rootProject.ext.minSdkVersion
        targetSdkVersion rootProject.ext.targetSdkVersion
        versionCode 1
        versionName "1.0"
        
        ndk {
            abiFilters "arm64-v8a", "armeabi-v7a"
        }
        
        python {
            version "3.9"
            pip {
                install "numpy"
                install "scipy"
                install "pandas"
            }
        }
    }
    
    splits {
        abi {
            enable true
            reset()
            include "arm64-v8a", "armeabi-v7a"
            universalApk false
        }
    }
}
```

### **Step 3: Copy Python Modules to Android Assets**

Create directory structure:
```
android/app/src/main/python/
├── log_parser.py
├── signal_processor.py
├── diagnostics_engine.py
├── motor_harmonics.py
├── correlation_analyzer.py
└── report_generator.py
```

### **Step 4: Create Native Module Bridge**

**File: `android/app/src/main/java/com/vehicleloganalyzer/PythonAnalysisModule.java`**
```java
package com.vehicleloganalyzer;

import android.util.Log;
import com.facebook.react.bridge.*;
import com.chaquo.python.*;
import com.chaquo.python.android.AndroidPlatform;
import java.util.Map;
import java.util.HashMap;

public class PythonAnalysisModule extends ReactContextBaseJavaModule {
    private static final String TAG = "PythonAnalysis";
    private Python python;
    private PyObject logParser;
    private PyObject diagnosticsEngine;
    private PyObject motorHarmonics;
    private PyObject correlationAnalyzer;

    public PythonAnalysisModule(ReactApplicationContext reactContext) {
        super(reactContext);
        initializePython();
    }

    @Override
    public String getName() {
        return "PythonAnalysis";
    }

    private void initializePython() {
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(getReactApplicationContext()));
        }
        python = Python.getInstance();
        
        // Import Python modules
        logParser = python.getModule("log_parser");
        diagnosticsEngine = python.getModule("diagnostics_engine");
        motorHarmonics = python.getModule("motor_harmonics");
        correlationAnalyzer = python.getModule("correlation_analyzer");
        
        Log.d(TAG, "Python modules loaded successfully");
    }

    @ReactMethod
    public void parseLog(String filePath, Promise promise) {
        try {
            PyObject parser = logParser.callAttr("LogParser");
            PyObject result = parser.callAttr("parse_file", filePath);
            
            // Convert Python dict to React Native map
            Map<String, Object> resultMap = convertPyObjectToMap(result);
            
            WritableMap returnMap = Arguments.createMap();
            returnMap.putString("log_id", resultMap.get("log_id").toString());
            returnMap.putMap("signals", convertMapToWritableMap(
                (Map<String, Object>) resultMap.get("signals")
            ));
            
            promise.resolve(returnMap);
        } catch (Exception e) {
            Log.e(TAG, "Error parsing log", e);
            promise.reject("PARSE_ERROR", e.getMessage());
        }
    }

    @ReactMethod
    public void analyzeDiagnostics(ReadableMap signalsMap, Promise promise) {
        try {
            // Convert React Native map to Python dict
            PyObject signals = convertMapToPyObject(signalsMap);
            
            PyObject engine = diagnosticsEngine.callAttr("DiagnosticsEngine");
            PyObject result = engine.callAttr("analyze", signals);
            
            Map<String, Object> resultMap = convertPyObjectToMap(result);
            WritableMap returnMap = convertMapToWritableMap(resultMap);
            
            promise.resolve(returnMap);
        } catch (Exception e) {
            Log.e(TAG, "Error analyzing diagnostics", e);
            promise.reject("DIAGNOSTICS_ERROR", e.getMessage());
        }
    }

    @ReactMethod
    public void analyzeMotorHarmonics(ReadableMap rcouData, double duration, Promise promise) {
        try {
            PyObject data = convertMapToPyObject(rcouData);
            
            PyObject detector = motorHarmonics.callAttr("MotorHarmonicsDetector");
            PyObject result = detector.callAttr("analyze", data, duration);
            
            Map<String, Object> resultMap = convertPyObjectToMap(result);
            WritableMap returnMap = convertMapToWritableMap(resultMap);
            
            promise.resolve(returnMap);
        } catch (Exception e) {
            Log.e(TAG, "Error analyzing motor harmonics", e);
            promise.reject("HARMONICS_ERROR", e.getMessage());
        }
    }

    @ReactMethod
    public void analyzeCorrelations(ReadableMap signalsMap, Promise promise) {
        try {
            PyObject signals = convertMapToPyObject(signalsMap);
            
            PyObject analyzer = correlationAnalyzer.callAttr("CorrelationAnalyzer");
            PyObject result = analyzer.callAttr("analyze_vibration_throttle_correlation", signals);
            
            Map<String, Object> resultMap = convertPyObjectToMap(result);
            WritableMap returnMap = convertMapToWritableMap(resultMap);
            
            promise.resolve(returnMap);
        } catch (Exception e) {
            Log.e(TAG, "Error analyzing correlations", e);
            promise.reject("CORRELATION_ERROR", e.getMessage());
        }
    }

    // Helper methods for type conversion
    private Map<String, Object> convertPyObjectToMap(PyObject pyObject) {
        // Implementation to convert Python dict to Java Map
        Map<String, Object> map = new HashMap<>();
        PyObject items = pyObject.callAttr("items");
        for (PyObject item : items.asList()) {
            String key = item.asList().get(0).toString();
            Object value = convertPyObjectToJava(item.asList().get(1));
            map.put(key, value);
        }
        return map;
    }

    private Object convertPyObjectToJava(PyObject pyObject) {
        // Convert Python types to Java types
        if (pyObject.isInstance(python.getBuiltins().get("str"))) {
            return pyObject.toString();
        } else if (pyObject.isInstance(python.getBuiltins().get("int"))) {
            return pyObject.toInt();
        } else if (pyObject.isInstance(python.getBuiltins().get("float"))) {
            return pyObject.toFloat();
        } else if (pyObject.isInstance(python.getBuiltins().get("list"))) {
            return pyObject.asList();
        } else if (pyObject.isInstance(python.getBuiltins().get("dict"))) {
            return convertPyObjectToMap(pyObject);
        }
        return pyObject.toString();
    }

    private PyObject convertMapToPyObject(ReadableMap map) {
        // Convert React Native map to Python dict
        PyObject dict = python.getBuiltins().get("dict").call();
        ReadableMapKeySetIterator iterator = map.keySetIterator();
        
        while (iterator.hasNextKey()) {
            String key = iterator.nextKey();
            ReadableType type = map.getType(key);
            
            switch (type) {
                case String:
                    dict.put(PyObject.fromJava(key), PyObject.fromJava(map.getString(key)));
                    break;
                case Number:
                    dict.put(PyObject.fromJava(key), PyObject.fromJava(map.getDouble(key)));
                    break;
                case Map:
                    dict.put(PyObject.fromJava(key), convertMapToPyObject(map.getMap(key)));
                    break;
                case Array:
                    dict.put(PyObject.fromJava(key), convertArrayToPyObject(map.getArray(key)));
                    break;
            }
        }
        return dict;
    }

    private PyObject convertArrayToPyObject(ReadableArray array) {
        PyObject list = python.getBuiltins().get("list").call();
        for (int i = 0; i < array.size(); i++) {
            ReadableType type = array.getType(i);
            switch (type) {
                case String:
                    list.callAttr("append", array.getString(i));
                    break;
                case Number:
                    list.callAttr("append", array.getDouble(i));
                    break;
                case Map:
                    list.callAttr("append", convertMapToPyObject(array.getMap(i)));
                    break;
            }
        }
        return list;
    }

    private WritableMap convertMapToWritableMap(Map<String, Object> map) {
        WritableMap writableMap = Arguments.createMap();
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof String) {
                writableMap.putString(entry.getKey(), (String) value);
            } else if (value instanceof Integer) {
                writableMap.putInt(entry.getKey(), (Integer) value);
            } else if (value instanceof Double) {
                writableMap.putDouble(entry.getKey(), (Double) value);
            } else if (value instanceof Boolean) {
                writableMap.putBoolean(entry.getKey(), (Boolean) value);
            } else if (value instanceof Map) {
                writableMap.putMap(entry.getKey(), convertMapToWritableMap((Map<String, Object>) value));
            }
        }
        return writableMap;
    }
}
```

**File: `android/app/src/main/java/com/vehicleloganalyzer/PythonAnalysisPackage.java`**
```java
package com.vehicleloganalyzer;

import com.facebook.react.ReactPackage;
import com.facebook.react.bridge.NativeModule;
import com.facebook.react.bridge.ReactApplicationContext;
import com.facebook.react.uimanager.ViewManager;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class PythonAnalysisPackage implements ReactPackage {
    @Override
    public List<NativeModule> createNativeModules(ReactApplicationContext reactContext) {
        List<NativeModule> modules = new ArrayList<>();
        modules.add(new PythonAnalysisModule(reactContext));
        return modules;
    }

    @Override
    public List<ViewManager> createViewManagers(ReactApplicationContext reactContext) {
        return Collections.emptyList();
    }
}
```

**Register the package in `MainApplication.java`:**
```java
@Override
protected List<ReactPackage> getPackages() {
    List<ReactPackage> packages = new PackageList(this).getPackages();
    packages.add(new PythonAnalysisPackage());  // Add this line
    return packages;
}
```

### **Step 5: Create TypeScript Native Module Interface**

**File: `frontend/modules/PythonAnalysis.ts`**
```typescript
import { NativeModules } from 'react-native';

interface PythonAnalysisModule {
  parseLog(filePath: string): Promise<{
    log_id: string;
    signals: Record<string, any>;
    duration_sec: number;
    message_types: string[];
  }>;

  analyzeDiagnostics(signals: Record<string, any>): Promise<{
    health_score: number;
    checks: Array<{
      name: string;
      status: 'pass' | 'warning' | 'critical';
      explanation: string;
    }>;
    critical: number;
    warnings: number;
    passed: number;
  }>;

  analyzeMotorHarmonics(
    rcouData: Record<string, any>,
    duration: number
  ): Promise<{
    motor_harmonics: Array<{
      motor: string;
      dominant_freq: number;
      total_harmonic_distortion: number;
      harmonics: Array<{
        frequency: number;
        magnitude: number;
        power_db: number;
      }>;
    }>;
    motor_imbalance: {
      max_deviation: number;
      imbalance_percentage: number;
      status: string;
    };
  }>;

  analyzeCorrelations(signals: Record<string, any>): Promise<{
    status: string;
    correlations: Array<{
      axis: string;
      pearson_correlation: number;
      correlation_strength: string;
      vibration_by_throttle: Array<{
        throttle_range: string;
        avg_vibration: number;
      }>;
    }>;
  }>;
}

const PythonAnalysis = NativeModules.PythonAnalysis as PythonAnalysisModule;

export default PythonAnalysis;
```

### **Step 6: Update React Native Code to Use Local Processing**

**File: `frontend/services/LogAnalysisService.ts`**
```typescript
import PythonAnalysis from '../modules/PythonAnalysis';
import * as FileSystem from 'expo-file-system';
import * as DocumentPicker from 'expo-document-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';

export class LocalLogAnalysisService {
  private logsDir = `${FileSystem.documentDirectory}logs/`;
  
  async initialize() {
    // Create logs directory
    const dirInfo = await FileSystem.getInfoAsync(this.logsDir);
    if (!dirInfo.exists) {
      await FileSystem.makeDirectoryAsync(this.logsDir, { intermediates: true });
    }
  }

  async pickAndUploadLog(): Promise<string> {
    // Pick log file
    const result = await DocumentPicker.getDocumentAsync({
      type: ['*/*'],
      copyToCacheDirectory: true,
    });

    if (result.type === 'cancel') {
      throw new Error('File selection cancelled');
    }

    // Copy to app's document directory
    const fileName = result.name || 'log.bin';
    const logId = Date.now().toString();
    const destPath = `${this.logsDir}${logId}_${fileName}`;
    
    await FileSystem.copyAsync({
      from: result.uri,
      to: destPath,
    });

    // Parse log using Python module
    const parseResult = await PythonAnalysis.parseLog(destPath);

    // Store metadata in AsyncStorage
    await AsyncStorage.setItem(`log_${logId}`, JSON.stringify({
      log_id: logId,
      filename: fileName,
      path: destPath,
      uploaded_at: new Date().toISOString(),
      ...parseResult,
    }));

    return logId;
  }

  async getLogData(logId: string) {
    const metadataStr = await AsyncStorage.getItem(`log_${logId}`);
    if (!metadataStr) {
      throw new Error('Log not found');
    }
    return JSON.parse(metadataStr);
  }

  async analyzeDiagnostics(logId: string) {
    const logData = await this.getLogData(logId);
    return await PythonAnalysis.analyzeDiagnostics(logData.signals);
  }

  async analyzeMotorHarmonics(logId: string) {
    const logData = await this.getLogData(logId);
    if (!logData.signals.RCOU) {
      throw new Error('No motor data available');
    }
    return await PythonAnalysis.analyzeMotorHarmonics(
      logData.signals.RCOU,
      logData.duration_sec
    );
  }

  async analyzeCorrelations(logId: string) {
    const logData = await this.getLogData(logId);
    return await PythonAnalysis.analyzeCorrelations(logData.signals);
  }

  async deleteLog(logId: string) {
    const logData = await this.getLogData(logId);
    await FileSystem.deleteAsync(logData.path, { idempotent: true });
    await AsyncStorage.removeItem(`log_${logId}`);
  }

  async listLogs() {
    const keys = await AsyncStorage.getAllKeys();
    const logKeys = keys.filter(k => k.startsWith('log_'));
    const logs = await AsyncStorage.multiGet(logKeys);
    return logs.map(([_, value]) => JSON.parse(value));
  }
}

export const logAnalysisService = new LocalLogAnalysisService();
```

### **Step 7: Update Dashboard to Use Local Service**

**File: `frontend/app/(tabs)/index.tsx`** (update upload logic)
```typescript
import { logAnalysisService } from '../../services/LogAnalysisService';

// Replace API calls with:
const handleUpload = async () => {
  try {
    setUploading(true);
    const logId = await logAnalysisService.pickAndUploadLog();
    setCurrentLogId(logId);
    Alert.alert('Success', 'Log uploaded and parsed successfully');
  } catch (error) {
    Alert.alert('Error', error.message);
  } finally {
    setUploading(false);
  }
};

const handleGenerateDemo = async () => {
  // Generate demo log locally (implement in Python module)
  const logId = await PythonAnalysis.generateDemoLog();
  setCurrentLogId(logId);
};
```

---

## 📊 Performance Optimizations

### **1. Streaming Parser for Large Files**
```python
# log_parser.py (optimized)
def parse_file_streaming(filepath, chunk_size=1024*1024):
    """Parse large files in chunks to reduce memory usage"""
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield parse_chunk(chunk)
```

### **2. Downsampling for Charts**
```python
# signal_processor.py
def downsample_lttb(data, target_points=3000):
    """Largest Triangle Three Buckets algorithm"""
    if len(data) <= target_points:
        return data
    
    # LTTB implementation (already exists in your code)
    return lttb_algorithm(data, target_points)
```

### **3. Background Processing**
```java
// Use Android WorkManager for heavy processing
import androidx.work.Worker;
import androidx.work.WorkRequest;

public class LogAnalysisWorker extends Worker {
    @Override
    public Result doWork() {
        String logPath = getInputData().getString("log_path");
        // Process log in background
        return Result.success();
    }
}
```

---

## 📱 Building the APK

### **Build Commands**
```bash
# 1. Eject from Expo (if not already done)
cd /app/frontend
npx expo prebuild --clean

# 2. Install dependencies
cd android
./gradlew clean

# 3. Build debug APK
./gradlew assembleDebug

# 4. Build release APK (signed)
./gradlew assembleRelease

# APK output:
# android/app/build/outputs/apk/debug/app-debug.apk
# android/app/build/outputs/apk/release/app-release.apk
```

### **APK Size Optimization**
```gradle
android {
    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

**Expected APK sizes:**
- Debug: ~150-200 MB (includes Python runtime + NumPy + SciPy)
- Release (optimized): ~80-120 MB

---

## ✅ Feature Parity Checklist

All features will still work locally:

- ✅ Log parsing (.BIN/.LOG files)
- ✅ FFT analysis (NumPy FFT on device)
- ✅ Vibration diagnostics
- ✅ Motor harmonic detection
- ✅ Correlation analysis
- ✅ Health score calculation
- ✅ GPS trajectory visualization
- ✅ Chart generation (Plotly WebView)
- ✅ Report generation (PDF/HTML/MD)
- ✅ Chart export (PNG/SVG)
- ✅ Data export (CSV)

---

## 🔄 Migration Checklist

- [ ] Eject Expo to bare workflow
- [ ] Add Chaquopy to Android Gradle
- [ ] Copy Python modules to `android/app/src/main/python/`
- [ ] Create Native Module bridge (Java)
- [ ] Create TypeScript interface
- [ ] Replace API calls with Native Module calls
- [ ] Replace MongoDB with AsyncStorage/SQLite
- [ ] Test on physical Android device
- [ ] Optimize APK size
- [ ] Build release APK

---

## 🎯 Summary

**Before:** Client-server architecture requiring backend server
**After:** Fully self-contained Android app with embedded Python

**Advantages:**
- ✅ Works offline
- ✅ No server costs
- ✅ Faster processing (no network latency)
- ✅ Full privacy (data never leaves device)
- ✅ Portable (single APK)

**Trade-offs:**
- ⚠️ Larger APK size (~100-150 MB)
- ⚠️ Limited to Android (iOS needs different approach)
- ⚠️ Processing limited by phone hardware

**Ready to implement?** Let me know and I'll create all the necessary files and code!
