# Vehicle Log Analyzer

A professional flight/vehicle telemetry log analysis application for Android.

## Overview

**Vehicle Log Analyzer** is a fully standalone Android application that performs complete flight log analysis directly on your phone without requiring any server or internet connection.

### Features

- 🛩️ **Log Parsing**: Parse ArduPilot .BIN and .LOG files
- 📊 **FFT Analysis**: Real-time frequency analysis with spectrograms
- 🔍 **Diagnostics**: Automated flight health checks (9 diagnostic modules)
- ⚡ **Motor Analysis**: Harmonic detection and imbalance analysis
- 📈 **Correlations**: Vibration-throttle and battery-load correlations
- 📄 **Reports**: Generate PDF, HTML, and Markdown reports
- 📤 **Export**: PNG/SVG charts and CSV data export
- 🔒 **100% Offline**: All processing happens on device using embedded Python

### Architecture

- **Frontend**: React Native (Expo bare workflow)
- **Analysis Engine**: Python 3.9 with NumPy, SciPy, Pandas
- **Integration**: Chaquopy (embedded Python in Android)
- **Native Bridge**: Java ↔ Python communication layer

---

## Prerequisites

Before building the APK, ensure you have:

- **Node.js** 18+ and **Yarn** installed
- **Android Studio** with Android SDK
- **Java JDK** 17 or higher
- **Python 3.9+** (for local development/testing)
- **Git** for cloning the repository

---

## Building the Android APK

### Step 1: Clone the Repository

```bash
git clone https://github.com/Manikanth-N/vehicle_log_analyzer.git
cd vehicle_log_analyzer
```

### Step 2: Install Frontend Dependencies

```bash
cd frontend
yarn install
```

This will install all required npm packages including React Native, Expo, and supporting libraries.

### Step 3: Build the Android APK

```bash
cd android
./gradlew assembleDebug
```

**Build Time:** 5-10 minutes (first build downloads Python dependencies)

**APK Output Location:**
```
frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

**Expected APK Size:** ~120-150 MB (includes Python runtime and scientific libraries)

### Step 4: Install on Android Device

```bash
# Connect Android device via USB with USB debugging enabled
adb devices

# Install the APK
adb install frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

---

## Building Release APK (for Production)

For a production-ready release APK:

```bash
cd frontend/android

# Build release APK
./gradlew assembleRelease

# Output location:
# frontend/android/app/build/outputs/apk/release/app-release.apk
```

**Note:** Release builds require a signing key. See Android documentation for signing configuration.

---

## Project Structure

```
vehicle_log_analyzer/
├── analysis_engine/              # Standalone Python analysis engine
│   ├── api.py                   # Unified API interface
│   ├── core/                    # Log parsing and signal processing
│   ├── analysis/                # Diagnostics, FFT, harmonics, correlations
│   └── reporting/               # PDF/HTML/MD report generation
│
├── frontend/                    # React Native mobile app
│   ├── android/                 # Android project (bare workflow)
│   │   ├── app/
│   │   │   ├── src/main/
│   │   │   │   ├── python/      # Python engine deployed here
│   │   │   │   └── java/        # Native bridge (Java ↔ Python)
│   │   │   └── build.gradle     # Chaquopy configuration
│   │   └── build.gradle
│   │
│   ├── app/                     # React Native screens
│   │   └── (tabs)/              # Tab-based navigation
│   ├── components/              # Reusable components
│   ├── modules/                 # Native module interfaces
│   └── package.json
│
└── backend/                     # Original FastAPI server (deprecated)
```

---

## Key Technologies

### Frontend Stack
- **React Native** - Mobile UI framework
- **Expo** (bare workflow) - Development and build tooling
- **TypeScript** - Type-safe development
- **AsyncStorage** - Local data persistence

### Python Analysis Engine
- **NumPy 1.24.3** - Numerical computing
- **SciPy 1.10.1** - Scientific computing (FFT, signal processing)
- **Pandas 2.0.3** - Data manipulation
- **Pymavlink 2.4.40** - ArduPilot log parsing
- **Matplotlib 3.7.2** - Chart generation
- **ReportLab 4.0.4** - PDF report generation

### Android Integration
- **Chaquopy 15.0.1** - Python for Android
- **Java Native Bridge** - React Native ↔ Python communication
- **Gradle** - Build automation

---

## Analysis Engine Features

### Diagnostics (9 Health Checks)
1. Vibration analysis (X/Y/Z axes with clipping detection)
2. GPS accuracy (HDop, satellite count)
3. EKF innovation monitoring
4. Battery health (voltage sag, current draw)
5. Motor balance (PWM output comparison)
6. IMU calibration verification
7. Attitude control quality
8. Sensor clipping detection
9. Parameter limit checking

### Advanced Analysis
- **FFT Analysis**: 1024-4096 point windows
- **Motor Harmonics**: FFT on motor outputs with THD calculation
- **Correlation Analysis**: Statistical analysis (Pearson, Spearman)
- **Motor Imbalance**: Percentage deviation between motors
- **Health Score**: 0-100 overall flight health rating

### Export Formats
- **Reports**: PDF, HTML, Markdown
- **Charts**: PNG, SVG
- **Data**: CSV export

---

## Development

### Running in Development Mode

The app is currently configured as a standalone Android app. To run in development:

```bash
cd frontend
npx expo start
```

This will start the Metro bundler for hot reloading during development.

### Testing the Analysis Engine

The Python analysis engine can be tested independently:

```bash
cd analysis_engine
python3 -c "from api import AnalysisAPI; api = AnalysisAPI(); print(api.get_version())"
```

Expected output: `2.0.0`

---

## Documentation

Comprehensive guides are available in the repository:

- **`UI_INTEGRATION_GUIDE.md`** - Complete UI implementation guide
- **`CROSS_PLATFORM_ARCHITECTURE.md`** - Architecture overview
- **`ANDROID_STANDALONE_ARCHITECTURE.md`** - Detailed Android implementation
- **`PROJECT_COMPLETION_SUMMARY.md`** - Full project summary

---

## Troubleshooting

### Build Issues

**Problem:** Gradle build fails with "Python not found"
**Solution:** Chaquopy will download Python automatically. Ensure internet connection on first build.

**Problem:** Out of memory during build
**Solution:** Increase Gradle memory in `gradle.properties`:
```
org.gradle.jvmargs=-Xmx4096m
```

**Problem:** APK installation fails
**Solution:** Enable "Install from Unknown Sources" on Android device.

### Runtime Issues

**Problem:** App crashes on startup
**Solution:** Check logcat for Python errors:
```bash
adb logcat | grep -E "(Python|Chaquopy|AnalysisBridge)"
```

**Problem:** Log parsing fails
**Solution:** Ensure log file is valid ArduPilot format (.BIN or .LOG)

---

## Performance

- **Demo Log Generation**: < 5 seconds
- **Log Parsing**: ~2-5 seconds for 50MB log
- **Diagnostics Analysis**: < 3 seconds
- **FFT (1024-point)**: < 1 second
- **Motor Harmonics**: < 2 seconds
- **PDF Report**: < 5 seconds

**Memory Usage:** Handles logs up to 200 MB with downsampling

---

## Requirements

### Minimum Android Version
- Android 7.0 (API 24) or higher
- ARM architecture (arm64-v8a or armeabi-v7a)
- 100 MB free storage space

### Recommended
- Android 10.0+ (API 29)
- 2 GB RAM
- 200 MB free storage

---

## License

This project is created for UAV developers, robotics engineers, and drone operators.

---

## Contributing

This is a professional telemetry log analysis tool. Contributions are welcome for:
- Additional log format support (PX4, ROS)
- New diagnostic modules
- UI improvements
- Performance optimizations

---

## Support

For issues and questions:
- Check documentation in the `/docs` directory
- Review `UI_INTEGRATION_GUIDE.md` for implementation details
- See `TROUBLESHOOTING.md` for common issues

---

## Roadmap

### Current Version (2.0.0)
- ✅ Android standalone app
- ✅ Embedded Python analysis engine
- ✅ 9 diagnostic modules
- ✅ Motor harmonic detection
- ✅ Correlation analysis
- ✅ PDF/HTML/MD reports

### Future Plans
- 🔄 Windows desktop version
- 🔄 iOS support
- 🔄 PX4 log format support
- 🔄 ROS bag file support
- 🔄 Cloud sync (optional)
- 🔄 Flight replay animation

---

## Credits

**Analysis Engine**: Python 3.9 with NumPy, SciPy, Pandas  
**Mobile Framework**: React Native + Expo  
**Python Integration**: Chaquopy  
**Log Format**: ArduPilot DataFlash  

Built for the UAV and robotics community.

---

**Version:** 2.0.0  
**Last Updated:** March 2026  
**Platform:** Android 7.0+  
**Status:** Production Ready
