import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  ActivityIndicator, SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAppState } from '../../components/AppContext';
import { useRouter } from 'expo-router';
import PlotlyChart from '../../components/PlotlyChart';

const API = process.env.EXPO_PUBLIC_BACKEND_URL;

const SIGNALS = [
  { label: 'Gyro X', type: 'IMU', field: 'GyrX' },
  { label: 'Gyro Y', type: 'IMU', field: 'GyrY' },
  { label: 'Gyro Z', type: 'IMU', field: 'GyrZ' },
  { label: 'Accel X', type: 'IMU', field: 'AccX' },
  { label: 'Accel Y', type: 'IMU', field: 'AccY' },
  { label: 'Accel Z', type: 'IMU', field: 'AccZ' },
  { label: 'Vibe X', type: 'VIBE', field: 'VibeX' },
  { label: 'Vibe Y', type: 'VIBE', field: 'VibeY' },
  { label: 'Vibe Z', type: 'VIBE', field: 'VibeZ' },
];

const WINDOW_SIZES = [256, 512, 1024, 2048, 4096];

interface FFTResult {
  frequencies: number[];
  magnitude: number[];
  psd: number[];
  sample_rate: number;
  window_size: number;
  peaks: Array<{
    frequency: number;
    magnitude: number;
    harmonic_ratio: number;
    is_harmonic: boolean;
    label: string;
  }>;
  nyquist: number;
}

interface SpectrogramResult {
  times: number[];
  frequencies: number[];
  power: number[][];
  sample_rate: number;
}

export default function FFTScreen() {
  const { currentLogId, verificationMode } = useAppState();
  const router = useRouter();
  const [selectedSignal, setSelectedSignal] = useState(SIGNALS[2]); // GyrZ default
  const [windowSize, setWindowSize] = useState(1024);
  const [loading, setLoading] = useState(false);
  const [fftData, setFftData] = useState<FFTResult | null>(null);
  const [spectrogramData, setSpectrogramData] = useState<SpectrogramResult | null>(null);

  // Redirect if in beginner mode
  if (verificationMode === 'beginner') {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.restrictedContainer}>
          <Ionicons name="lock-closed-outline" size={56} color="#FFD700" />
          <Text style={styles.restrictedTitle}>Pro Feature</Text>
          <Text style={styles.restrictedHint}>
            FFT analysis is available in Pro and Certified modes.{"\n"}
            Switch to Pro mode on the Dashboard to unlock.
          </Text>
          <TouchableOpacity
            style={styles.upgradeBtn}
            onPress={() => router.push('/')}
          >
            <Ionicons name="arrow-back" size={18} color="#FFF" />
            <Text style={styles.upgradeBtnText}>Go to Dashboard</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const runFFT = async () => {
    if (!currentLogId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/logs/${currentLogId}/fft`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signal_type: selectedSignal.type,
          signal_field: selectedSignal.field,
          window_size: windowSize,
          overlap: 0.5,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setFftData(data.fft);
        setSpectrogramData(data.spectrogram);
      }
    } catch (e) {
      console.error('FFT failed:', e);
    }
    setLoading(false);
  };

  const fftTraces = fftData ? [{
    x: fftData.frequencies,
    y: fftData.magnitude,
    name: 'FFT Magnitude',
    type: 'scatter' as const,
    mode: 'lines' as const,
    fill: 'tozeroy' as const,
    fillcolor: 'rgba(0,122,255,0.15)',
    line: { color: '#007AFF', width: 1.5 },
  }] : [];

  const fftLayout = {
    title: `FFT: ${selectedSignal.type}.${selectedSignal.field}`,
    xaxis: { title: { text: 'Frequency (Hz)' }, gridcolor: '#27272A', zerolinecolor: '#3F3F46' },
    yaxis: { title: { text: 'Magnitude' }, gridcolor: '#27272A', zerolinecolor: '#3F3F46' },
  };

  const spectrogramTraces = spectrogramData && spectrogramData.power.length > 0 ? [{
    x: spectrogramData.times,
    y: spectrogramData.frequencies,
    z: spectrogramData.power,
    type: 'heatmap' as const,
    colorscale: 'Viridis' as any,
    colorbar: { title: { text: 'Power (dB)' }, tickfont: { color: '#A1A1AA' }, titlefont: { color: '#A1A1AA' } },
  }] : [];

  const spectrogramLayout = {
    title: 'Spectrogram',
    xaxis: { title: { text: 'Time (s)' }, gridcolor: '#27272A', zerolinecolor: '#3F3F46' },
    yaxis: { title: { text: 'Frequency (Hz)' }, gridcolor: '#27272A', zerolinecolor: '#3F3F46' },
  };

  if (!currentLogId) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.emptyContainer}>
          <Ionicons name="bar-chart-outline" size={56} color="#3F3F46" />
          <Text style={styles.emptyTitle}>No Log Selected</Text>
          <Text style={styles.emptyHint}>Load a log from Dashboard to perform FFT analysis</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Frequency Analysis</Text>

        {/* Signal Selection */}
        <Text style={styles.sectionLabel}>Signal</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.row}>
          {SIGNALS.map((sig) => (
            <TouchableOpacity
              key={`${sig.type}.${sig.field}`}
              testID={`fft-signal-${sig.field}`}
              style={[styles.chip, selectedSignal.field === sig.field && selectedSignal.type === sig.type && styles.chipActive]}
              onPress={() => setSelectedSignal(sig)}
            >
              <Text style={[styles.chipText, selectedSignal.field === sig.field && selectedSignal.type === sig.type && styles.chipTextActive]}>
                {sig.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Window Size */}
        <Text style={styles.sectionLabel}>Window Size</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.row}>
          {WINDOW_SIZES.map((ws) => (
            <TouchableOpacity
              key={ws}
              testID={`fft-window-${ws}`}
              style={[styles.chip, windowSize === ws && styles.chipActive]}
              onPress={() => setWindowSize(ws)}
            >
              <Text style={[styles.chipText, windowSize === ws && styles.chipTextActive]}>{ws}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Run Button */}
        <TouchableOpacity
          testID="run-fft-btn"
          style={styles.runBtn}
          onPress={runFFT}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" size="small" />
          ) : (
            <>
              <Ionicons name="flash-outline" size={18} color="#FFF" />
              <Text style={styles.runBtnText}>Run FFT Analysis</Text>
            </>
          )}
        </TouchableOpacity>

        {/* FFT Chart */}
        {fftData && (
          <>
            <PlotlyChart testID="fft-chart" traces={fftTraces} layout={fftLayout} height={300} />

            {/* Peaks */}
            {fftData.peaks.length > 0 && (
              <View style={styles.peaksSection}>
                <Text style={styles.sectionLabel}>Detected Peaks</Text>
                {fftData.peaks.slice(0, 8).map((peak, i) => (
                  <View key={i} style={styles.peakRow}>
                    <View style={[styles.peakDot, peak.is_harmonic && styles.peakDotHarmonic]} />
                    <Text style={styles.peakFreq}>{peak.label}</Text>
                    <Text style={styles.peakMag}>Mag: {peak.magnitude.toFixed(3)}</Text>
                    {peak.is_harmonic && (
                      <View style={styles.harmonicBadge}>
                        <Text style={styles.harmonicText}>Harmonic</Text>
                      </View>
                    )}
                  </View>
                ))}
              </View>
            )}

            {/* Info bar */}
            <View style={styles.infoBar}>
              <Text style={styles.infoItem}>Fs: {fftData.sample_rate} Hz</Text>
              <Text style={styles.infoItem}>Nyquist: {fftData.nyquist} Hz</Text>
              <Text style={styles.infoItem}>Window: {fftData.window_size}</Text>
            </View>
          </>
        )}

        {/* Spectrogram */}
        {spectrogramData && spectrogramData.power.length > 0 && (
          <>
            <Text style={[styles.sectionLabel, { marginTop: 20 }]}>Spectrogram</Text>
            <PlotlyChart testID="spectrogram-chart" traces={spectrogramTraces} layout={spectrogramLayout} height={300} />
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#050505' },
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 32 },
  title: { color: '#FFFFFF', fontSize: 20, fontWeight: '700', marginBottom: 16, marginTop: 8 },
  sectionLabel: { color: '#A1A1AA', fontSize: 11, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 8 },
  row: { marginBottom: 16 },
  chip: { backgroundColor: '#171717', borderWidth: 1, borderColor: '#27272A', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8, marginRight: 6 },
  chipActive: { borderColor: '#007AFF', backgroundColor: 'rgba(0,122,255,0.12)' },
  chipText: { color: '#A1A1AA', fontSize: 12, fontWeight: '500' },
  chipTextActive: { color: '#007AFF' },
  runBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#007AFF', borderRadius: 10, height: 48, gap: 8, marginBottom: 16 },
  runBtnText: { color: '#FFF', fontWeight: '600', fontSize: 14 },
  peaksSection: { marginTop: 16 },
  peakRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6, gap: 8 },
  peakDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#007AFF' },
  peakDotHarmonic: { backgroundColor: '#FF9500' },
  peakFreq: { color: '#FFFFFF', fontSize: 13, fontWeight: '600', flex: 1 },
  peakMag: { color: '#52525B', fontSize: 11 },
  harmonicBadge: { backgroundColor: 'rgba(255,149,0,0.15)', borderRadius: 4, paddingHorizontal: 6, paddingVertical: 2 },
  harmonicText: { color: '#FF9500', fontSize: 9, fontWeight: '700', textTransform: 'uppercase' },
  infoBar: { flexDirection: 'row', justifyContent: 'space-around', backgroundColor: '#0A0A0A', borderRadius: 8, borderWidth: 1, borderColor: '#27272A', padding: 10, marginTop: 12 },
  infoItem: { color: '#A1A1AA', fontSize: 11, fontWeight: '500' },
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyTitle: { color: '#A1A1AA', fontSize: 18, fontWeight: '600', marginTop: 16 },
  emptyHint: { color: '#52525B', fontSize: 13, textAlign: 'center', marginTop: 6 },
  restrictedContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  restrictedTitle: { color: '#FFD700', fontSize: 20, fontWeight: '700', marginTop: 16 },
  restrictedHint: { color: '#A1A1AA', fontSize: 13, textAlign: 'center', marginTop: 8, lineHeight: 20 },
  upgradeBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#007AFF', borderRadius: 10, paddingHorizontal: 20, paddingVertical: 12, marginTop: 20, gap: 8 },
  upgradeBtnText: { color: '#FFF', fontWeight: '600', fontSize: 14 },
});
