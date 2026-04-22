/**
 * Native Analysis Bridge
 * 
 * TypeScript interface to the embedded Python analysis engine
 * running via Chaquopy on Android.
 */

import { NativeModules, Platform } from 'react-native';

interface AnalysisBridgeInterface {
  parseLog(filePath: string): Promise<LogData>;
  generateDemoLog(durationSec: number): Promise<LogData>;
  analyzeDiagnostics(signals: Record<string, any>, mode: string): Promise<DiagnosticsResult>;
  analyzeMotorHarmonics(rcouData: Record<string, any>, duration: number): Promise<MotorHarmonicsResult>;
  analyzeVibrationThrottleCorrelation(signals: Record<string, any>): Promise<CorrelationResult>;
  analyzeBatteryLoadCorrelation(signals: Record<string, any>): Promise<BatteryCorrelationResult>;
  analyzeFFT(timestamps: number[], values: number[], windowSize: number): Promise<FFTResult>;
  getSignalData(signals: Record<string, any>, signalRequests: SignalRequest[], maxPoints: number): Promise<SignalDataResult[]>;
  exportCSV(signalData: Record<string, any>): Promise<string>;
  generateReport(logData: Record<string, any>, diagnostics: Record<string, any>, format: 'pdf' | 'html' | 'md'): Promise<string>;
  getVersion(): Promise<string>;
}

// ==================== Type Definitions ====================

export interface LogData {
  log_id: string;
  filename: string;
  duration_sec: number;
  message_types: string[];
  signals: Record<string, Record<string, number[]>>;
  metadata?: Record<string, any>;
}

export interface DiagnosticsResult {
  health_score: number;
  checks: DiagnosticCheck[];
  critical: number;
  warnings: number;
  passed: number;
  parameter_limits?: ParameterLimit[];
}

export interface DiagnosticCheck {
  name: string;
  status: 'pass' | 'warning' | 'critical';
  explanation: string;
  details?: string;
  recommendation?: string;
}

export interface ParameterLimit {
  name: string;
  value: number;
  min_limit?: number;
  max_limit?: number;
  status: 'normal' | 'warning' | 'critical';
  unit?: string;
  description?: string;
}

export interface MotorHarmonicsResult {
  motor_harmonics: MotorHarmonic[];
  motor_imbalance: MotorImbalance;
}

export interface MotorHarmonic {
  motor: string;
  motor_num: number;
  dominant_freq: number;
  total_harmonic_distortion: number;
  harmonics: {
    frequency: number;
    magnitude: number;
    power_db: number;
  }[];
}

export interface MotorImbalance {
  max_deviation: number;
  max_deviation_motor: string;
  imbalance_percentage: number;
  status: 'balanced' | 'warning' | 'critical';
  motor_averages?: Record<string, number>;
  overall_average?: number;
}

export interface CorrelationResult {
  status: string;
  correlations: AxisCorrelation[];
  summary: {
    average_correlation: number;
    interpretation: string;
    significant_axes?: number;
  };
}

export interface AxisCorrelation {
  axis: string;
  pearson_correlation: number;
  pearson_p_value?: number;
  spearman_correlation?: number;
  correlation_strength: 'weak' | 'moderate' | 'strong';
  is_significant: boolean;
  vibration_by_throttle: ThrottleVibration[];
}

export interface ThrottleVibration {
  throttle_range: string;
  throttle_min: number;
  throttle_max: number;
  avg_vibration: number;
  max_vibration: number;
  sample_count?: number;
}

export interface BatteryCorrelationResult {
  status: string;
  correlation?: number;
  p_value?: number;
  sag_events?: SagEvent[];
  interpretation?: string;
}

export interface SagEvent {
  time: number;
  voltage_drop: number;
  current_at_sag: number;
}

export interface FFTResult {
  frequencies: number[];
  magnitudes: number[];
  psd: number[];
  sampling_rate: number;
  window_size: number;
  dominant_frequency: number;
  dominant_magnitude: number;
}

export interface SignalRequest {
  type: string;
  field: string;
}

export interface SignalDataResult {
  type: string;
  field: string;
  timestamps: number[];
  values: number[];
  unit?: string;
}

// ==================== Native Module ====================

const LINKING_ERROR =
  'The package "AnalysisBridge" doesn\'t seem to be linked. Make sure:\n\n' +
  Platform.select({ ios: '- Run pod install\n', default: '' }) +
  '- Rebuild the app: npx react-native run-android';

const AnalysisBridge: AnalysisBridgeInterface = NativeModules.AnalysisBridge
  ? NativeModules.AnalysisBridge
  : new Proxy(
      {},
      {
        get() {
          throw new Error(LINKING_ERROR);
        },
      }
    );

// ==================== API Wrapper ====================

/**
 * Standalone Analysis API
 * 
 * All analysis runs locally on device via embedded Python engine.
 * No server or internet connection required.
 */
export class NativeAnalysis {
  /**
   * Parse a flight log file (.BIN or .LOG)
   */
  static async parseLog(filePath: string): Promise<LogData> {
    return await AnalysisBridge.parseLog(filePath);
  }

  /**
   * Generate a synthetic demo flight log for testing
   */
  static async generateDemoLog(durationSec: number = 120): Promise<LogData> {
    return await AnalysisBridge.generateDemoLog(durationSec);
  }

  /**
   * Run automated flight diagnostics
   */
  static async analyzeDiagnostics(
    signals: Record<string, any>,
    mode: 'quick' | 'full' = 'full'
  ): Promise<DiagnosticsResult> {
    return await AnalysisBridge.analyzeDiagnostics(signals, mode);
  }

  /**
   * Analyze motor outputs for harmonic content and imbalance
   */
  static async analyzeMotorHarmonics(
    rcouData: Record<string, any>,
    duration: number
  ): Promise<MotorHarmonicsResult> {
    return await AnalysisBridge.analyzeMotorHarmonics(rcouData, duration);
  }

  /**
   * Analyze correlation between vibration and throttle
   */
  static async analyzeVibrationThrottleCorrelation(
    signals: Record<string, any>
  ): Promise<CorrelationResult> {
    return await AnalysisBridge.analyzeVibrationThrottleCorrelation(signals);
  }

  /**
   * Analyze battery voltage vs current correlation
   */
  static async analyzeBatteryLoadCorrelation(
    signals: Record<string, any>
  ): Promise<BatteryCorrelationResult> {
    return await AnalysisBridge.analyzeBatteryLoadCorrelation(signals);
  }

  /**
   * Perform FFT analysis on a signal
   */
  static async analyzeFFT(
    timestamps: number[],
    values: number[],
    windowSize: number = 1024
  ): Promise<FFTResult> {
    return await AnalysisBridge.analyzeFFT(timestamps, values, windowSize);
  }

  /**
   * Get downsampled signal data for plotting
   */
  static async getSignalData(
    signals: Record<string, any>,
    signalRequests: SignalRequest[],
    maxPoints: number = 3000
  ): Promise<SignalDataResult[]> {
    return await AnalysisBridge.getSignalData(signals, signalRequests, maxPoints);
  }

  /**
   * Export signal data to CSV format
   */
  static async exportCSV(signalData: Record<string, any>): Promise<string> {
    return await AnalysisBridge.exportCSV(signalData);
  }

  /**
   * Generate a flight analysis report
   * @returns Base64-encoded report content
   */
  static async generateReport(
    logData: Record<string, any>,
    diagnostics: Record<string, any>,
    format: 'pdf' | 'html' | 'md' = 'pdf'
  ): Promise<string> {
    return await AnalysisBridge.generateReport(logData, diagnostics, format);
  }

  /**
   * Get analysis engine version
   */
  static async getVersion(): Promise<string> {
    return await AnalysisBridge.getVersion();
  }
}

export default NativeAnalysis;
