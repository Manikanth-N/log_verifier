# ArduPilot Flight Log Analyzer - PRD

## Overview
A professional cross-platform ArduPilot flight log analysis application built with Expo React Native (mobile + web) and FastAPI Python backend. Designed for beginners, hobbyists, professional UAV developers, and flight control researchers.

## Architecture
- **Frontend**: Expo React Native (SDK 54) with tab-based navigation
- **Backend**: FastAPI (Python) with NumPy, SciPy, Pandas for signal processing
- **Database**: MongoDB for log metadata storage
- **Charts**: Plotly.js via WebView for interactive scientific visualization
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key for diagnostic insights

## Core Features (MVP)

### 1. ArduPilot Log Parsing
- Supports .BIN (DataFlash binary) and .LOG (text) formats
- Decodes all major message types: ATT, IMU, RATE, VIBE, GPS, BARO, RCIN, RCOU, NTUN, CTUN, EKF, MAG, BAT, MODE, EV, PM
- Demo flight generator with realistic 120s QuadCopter flight simulation
- Server-side parsing for large files (200MB+)

### 2. Signal Analysis & Visualization
- Interactive Plotly.js charts with zoom, pan, crosshair, multi-signal overlay
- 10 quick presets: Attitude, Gyro, Accel, Vibration, Motors, Battery, GPS, Altitude, EKF, Mag
- LTTB downsampling for efficient large dataset rendering (up to 3000 points)
- Professional signal tree selector for individual field selection

### 3. FFT & Frequency Analysis
- Fast Fourier Transform with configurable window sizes (256-4096)
- DC removal (detrending) for clean frequency analysis
- Peak detection with harmonic relationship identification
- Spectrogram (time-frequency) visualization
- Support for all IMU and VIBE signals

### 4. Automated Flight Diagnostics
- Vibration analysis (X/Y/Z axes with severity scoring)
- Sensor clipping detection
- GPS accuracy and satellite tracking
- EKF innovation monitoring (North/East/Down)
- Battery voltage health assessment
- Motor balance analysis (PWM output comparison)
- IMU calibration verification
- Attitude control quality check
- Health score (0-100) with critical/warning/passed breakdown

### 5. Beginner Mode
- Plain language explanations for all diagnostics
- "Getting Started" guide on dashboard
- Simplified health report with actionable advice
- FFT explanation for non-technical users

### 6. Professional Mode
- Raw signal tree with per-field selection
- Configurable FFT window sizes
- Detailed diagnostic parameters and thresholds
- Raw data table with message type filtering
- CSV export per message type

### 7. AI-Assisted Insights
- GPT-5.2 powered flight analysis
- Comprehensive diagnostic summary with recommendations
- Beginner-friendly and professional technical analysis
- On-demand analysis (user-triggered)

## API Endpoints
- `POST /api/logs/demo` - Generate demo log
- `POST /api/logs/upload` - Upload .BIN/.LOG file
- `GET /api/logs` - List all logs
- `GET /api/logs/{id}` - Get log details
- `DELETE /api/logs/{id}` - Delete log
- `GET /api/logs/{id}/signals` - Get signal tree
- `POST /api/logs/{id}/data` - Get plot data (with downsampling)
- `POST /api/logs/{id}/fft` - FFT analysis
- `GET /api/logs/{id}/diagnostics` - Automated diagnostics
- `POST /api/logs/{id}/ai-insights` - AI analysis
- `GET /api/logs/{id}/export` - CSV export

## Tech Stack
- Expo SDK 54 / React Native 0.81
- FastAPI / Uvicorn
- NumPy, SciPy, Pandas
- pymavlink (for .BIN parsing)
- MongoDB / Motor (async)
- Plotly.js (via WebView)
- emergentintegrations (OpenAI GPT-5.2)

## Future Enhancements
- Git preset sharing
- Plugin system for custom analysis modules
- ML-based fault detection
- GPS trajectory map
- PID tuning visualization
- Real-time telemetry support
- Advanced EKF state analysis
- Motor harmonic detection
