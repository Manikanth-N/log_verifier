# UI Integration - Complete Implementation Guide

## Dashboard Updates (app/(tabs)/index.tsx)

### Replace fetchLogs function:
```typescript
const fetchLogs = useCallback(async () => {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const logKeys = keys.filter(k => k.startsWith('log_'));
    const logData = await AsyncStorage.multiGet(logKeys);
    const parsedLogs = logData.map(([key, value]) => JSON.parse(value || '{}'));
    setLogs(parsedLogs);
  } catch (e) {
    console.error('Failed to fetch logs:', e);
  }
}, []);
```

### Replace loadDemo function:
```typescript
const loadDemo = async () => {
  setDemoLoading(true);
  setUploadProgress({ isUploading: true, progress: 0, status: 'Generating demo flight data...' });
  try {
    setUploadProgress({ isUploading: true, progress: 30, status: 'Processing signals...' });
    const logData = await NativeAnalysis.generateDemoLog(120);
    setUploadProgress({ isUploading: true, progress: 80, status: 'Finalizing...' });
    
    // Store in AsyncStorage
    await AsyncStorage.setItem(`log_${logData.log_id}`, JSON.stringify({
      log_id: logData.log_id,
      filename: logData.filename,
      upload_date: new Date().toISOString(),
      duration_sec: logData.duration_sec,
      message_types: logData.message_types,
      is_demo: true,
      signals: logData.signals,
    }));
    
    setCurrentLogId(logData.log_id);
    setCurrentLogName(logData.filename);
    await fetchLogs();
    setUploadProgress({ isUploading: false, progress: 100, status: 'Demo loaded successfully!' });
  } catch (e) {
    Alert.alert('Error', `Failed to generate demo log: ${e.message}`);
    setUploadProgress({ isUploading: false, progress: 0, status: '' });
  }
  setTimeout(() => setUploadProgress({ isUploading: false, progress: 0, status: '' }), 2000);
  setDemoLoading(false);
};
```

### Replace uploadLog function:
```typescript
const uploadLog = async () => {
  try {
    const result = await DocumentPicker.getDocumentAsync({
      type: '*/*',
      copyToCacheDirectory: true,
    });
    if (result.canceled || !result.assets?.[0]) return;

    const file = result.assets[0];
    setLoading(true);
    setUploadProgress({
      isUploading: true,
      progress: 0,
      status: 'Preparing upload...',
      filename: file.name,
    });

    // Copy to permanent location
    const logsDir = `${FileSystem.documentDirectory}logs/`;
    const dirInfo = await FileSystem.getInfoAsync(logsDir);
    if (!dirInfo.exists) {
      await FileSystem.makeDirectoryAsync(logsDir, { intermediates: true });
    }

    const destPath = `${logsDir}${Date.now()}_${file.name}`;
    await FileSystem.copyAsync({ from: file.uri, to: destPath });

    setUploadProgress({ isUploading: true, progress: 30, status: 'Parsing log file...' });
    
    // Parse with native module
    const logData = await NativeAnalysis.parseLog(destPath);
    
    setUploadProgress({ isUploading: true, progress: 80, status: 'Saving metadata...' });
    
    // Store metadata
    await AsyncStorage.setItem(`log_${logData.log_id}`, JSON.stringify({
      log_id: logData.log_id,
      filename: file.name,
      upload_date: new Date().toISOString(),
      duration_sec: logData.duration_sec,
      message_types: logData.message_types,
      is_demo: false,
      file_path: destPath,
      signals: logData.signals,
    }));

    setCurrentLogId(logData.log_id);
    setCurrentLogName(file.name);
    await fetchLogs();
    setUploadProgress({ isUploading: false, progress: 100, status: 'Upload complete!' });
  } catch (e) {
    Alert.alert('Error', `Failed to upload log: ${e.message}`);
    setUploadProgress({ isUploading: false, progress: 0, status: '' });
  } finally {
    setLoading(false);
    setTimeout(() => setUploadProgress({ isUploading: false, progress: 0, status: '' }), 2000);
  }
};
```

### Replace deleteLog function:
```typescript
const deleteLog = async (logId: string) => {
  try {
    const logStr = await AsyncStorage.getItem(`log_${logId}`);
    if (logStr) {
      const log = JSON.parse(logStr);
      if (log.file_path) {
        await FileSystem.deleteAsync(log.file_path, { idempotent: true });
      }
    }
    await AsyncStorage.removeItem(`log_${logId}`);
    await fetchLogs();
    if (currentLogId === logId) {
      setCurrentLogId(null);
      setCurrentLogName('');
    }
  } catch (e) {
    Alert.alert('Error', 'Failed to delete log');
  }
};
```

---

## Diagnostics Updates (app/(tabs)/diagnostics.tsx)

### Replace loadDiagnostics function:
```typescript
const loadDiagnostics = async () => {
  if (!currentLogId) return;
  setLoading(true);
  try {
    const logStr = await AsyncStorage.getItem(`log_${currentLogId}`);
    if (!logStr) {
      Alert.alert('Error', 'Log data not found');
      return;
    }
    const logData = JSON.parse(logStr);
    const result = await NativeAnalysis.analyzeDiagnostics(
      logData.signals,
      analysisType // 'quick' or 'full'
    );
    setDiagnostics(result);
  } catch (e) {
    Alert.alert('Error', `Diagnostics failed: ${e.message}`);
  } finally {
    setLoading(false);
  }
};
```

### Replace report generation:
```typescript
const handleExportReport = async (format: 'pdf' | 'html' | 'md') => {
  try {
    setExporting(true);
    const logStr = await AsyncStorage.getItem(`log_${currentLogId}`);
    const logData = JSON.parse(logStr);
    
    const base64Content = await NativeAnalysis.generateReport(
      logData,
      diagnostics,
      format
    );
    
    // Save to file system
    const reportsDir = `${FileSystem.documentDirectory}reports/`;
    const dirInfo = await FileSystem.getInfoAsync(reportsDir);
    if (!dirInfo.exists) {
      await FileSystem.makeDirectoryAsync(reportsDir, { intermediates: true });
    }
    
    const fileName = `report_${currentLogId}.${format}`;
    const filePath = `${reportsDir}${fileName}`;
    
    await FileSystem.writeAsStringAsync(filePath, base64Content, {
      encoding: format === 'pdf' ? FileSystem.EncodingType.Base64 : FileSystem.EncodingType.UTF8,
    });
    
    Alert.alert('Success', `Report saved to ${filePath}`);
  } catch (e) {
    Alert.alert('Error', `Report generation failed: ${e.message}`);
  } finally {
    setExporting(false);
  }
};
```

---

## Advanced Updates (app/(tabs)/advanced.tsx)

### Replace loadData function:
```typescript
const loadData = async () => {
  if (!currentLogId) return;
  setLoading(true);
  try {
    const logStr = await AsyncStorage.getItem(`log_${currentLogId}`);
    if (!logStr) return;
    const logData = JSON.parse(logStr);

    // Load GPS data
    if (logData.signals.GPS) {
      const timestamps = logData.signals.GPS.TimeUS;
      const gps = {
        timestamps,
        lat: logData.signals.GPS.Lat || [],
        lng: logData.signals.GPS.Lng || [],
        alt: logData.signals.GPS.Alt || [],
        spd: logData.signals.GPS.Spd || [],
      };
      setGpsData(gps);
    }

    // Load motor harmonics
    if (logData.signals.RCOU) {
      const harmonics = await NativeAnalysis.analyzeMotorHarmonics(
        logData.signals.RCOU,
        logData.duration_sec
      );
      setMotorHarmonics(harmonics);
    }

    // Load correlations
    const vibeThrottle = await NativeAnalysis.analyzeVibrationThrottleCorrelation(logData.signals);
    setVibeThrottle(vibeThrottle);
  } catch (e) {
    console.error('Failed to load advanced analysis:', e);
  } finally {
    setLoading(false);
  }
};
```

---

## FFT Updates (app/(tabs)/fft.tsx)

### Replace FFT analysis:
```typescript
const runFFT = async () => {
  if (!selectedSignal) return;
  setAnalyzing(true);
  try {
    const logStr = await AsyncStorage.getItem(`log_${currentLogId}`);
    const logData = JSON.parse(logStr);
    
    const signalData = logData.signals[selectedSignal.type];
    const timestamps = signalData.TimeUS;
    const values = signalData[selectedSignal.field];
    
    const result = await NativeAnalysis.analyzeFFT(
      timestamps,
      values,
      windowSize
    );
    
    setFftResult(result);
  } catch (e) {
    Alert.alert('Error', `FFT analysis failed: ${e.message}`);
  } finally {
    setAnalyzing(false);
  }
};
```

---

## Analysis Updates (app/(tabs)/analysis.tsx)

### Replace signal data loading:
```typescript
const loadSignalData = async () => {
  if (!currentLogId || selectedSignals.length === 0) return;
  setLoading(true);
  try {
    const logStr = await AsyncStorage.getItem(`log_${currentLogId}`);
    const logData = JSON.parse(logStr);
    
    const signalRequests = selectedSignals.map(s => ({
      type: s.type,
      field: s.field
    }));
    
    const data = await NativeAnalysis.getSignalData(
      logData.signals,
      signalRequests,
      3000 // max points
    );
    
    setPlotData(data);
  } catch (e) {
    Alert.alert('Error', `Failed to load signals: ${e.message}`);
  } finally {
    setLoading(false);
  }
};
```

---

## Required Dependencies

Add to package.json:
```json
"dependencies": {
  "@react-native-async-storage/async-storage": "^1.19.0",
  "expo-file-system": "~15.4.0",
  "expo-document-picker": "~11.5.0"
}
```

Install:
```bash
cd /app/frontend
yarn add @react-native-async-storage/async-storage
```

---

## Testing Checklist

After implementation:
- [ ] Demo log generation works
- [ ] Log file upload works
- [ ] Diagnostics analysis works
- [ ] FFT analysis works
- [ ] Motor harmonics detection works
- [ ] Correlation analysis works
- [ ] Report generation works
- [ ] Chart export works
- [ ] Log deletion works
- [ ] Offline operation confirmed

---

## Build Commands

```bash
cd /app/frontend/android
./gradlew assembleDebug

# Output: android/app/build/outputs/apk/debug/app-debug.apk
```

## Install on Device

```bash
adb install android/app/build/outputs/apk/debug/app-debug.apk
```
