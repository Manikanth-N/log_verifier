import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  ActivityIndicator, SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAppState } from '../../components/AppContext';
import { useRouter } from 'expo-router';
import GPSMap from '../../components/GPSMap';
import PlotlyChart from '../../components/PlotlyChart';

const API = process.env.EXPO_PUBLIC_BACKEND_URL;

interface GPSData {
  timestamps: number[];
  lat: number[];
  lng: number[];
  alt: number[];
  spd: number[];
  hdop: number[];
  nsats: number[];
}

interface MotorHarmonics {
  motor_harmonics: Array<{
    motor: string;
    motor_num: number;
    dominant_freq: number;
    harmonics: Array<{
      frequency: number;
      magnitude: number;
      power_db: number;
    }>;
    total_harmonic_distortion: number;
  }>;
  motor_imbalance: {
    max_deviation: number;
    max_deviation_motor: string;
    imbalance_percentage: number;
    status: string;
  };
}

interface VibeThrottleCorr {
  status: string;
  correlations: Array<{
    axis: string;
    pearson_correlation: number;
    correlation_strength: string;
    is_significant: boolean;
    vibration_by_throttle: Array<{
      throttle_range: string;
      avg_vibration: number;
      max_vibration: number;
    }>;
  }>;
  summary: {
    average_correlation: number;
    interpretation: string;
  };
}

export default function AdvancedAnalysisScreen() {
  const { currentLogId, verificationMode } = useAppState();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'gps' | 'harmonics' | 'correlation'>('gps');
  const [gpsData, setGpsData] = useState<GPSData | null>(null);
  const [motorHarmonics, setMotorHarmonics] = useState<MotorHarmonics | null>(null);
  const [vibeThrottle, setVibeThrottle] = useState<VibeThrottleCorr | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentLogId && verificationMode !== 'beginner') {
      loadData();
    } else {
      setGpsData(null);
      setMotorHarmonics(null);
      setVibeThrottle(null);
    }
  }, [currentLogId, verificationMode]);

  const loadData = async () => {
    if (!currentLogId) return;
    setLoading(true);
    try {
      // Load GPS data
      const gpsRes = await fetch(`${API}/api/logs/${currentLogId}/data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signals: [
            { type: 'GPS', field: 'Lat' },
            { type: 'GPS', field: 'Lng' },
            { type: 'GPS', field: 'Alt' },
            { type: 'GPS', field: 'Spd' },
            { type: 'GPS', field: 'HDop' },
            { type: 'GPS', field: 'NSats' },
          ],
          max_points: 1000,
        }),
      });
      if (gpsRes.ok) {
        const data = await gpsRes.json();
        if (data.data && data.data.length > 0) {
          const timestamps = data.data[0].timestamps;
          const gps: any = { timestamps };
          for (const d of data.data) {
            gps[d.field.toLowerCase()] = d.values;
          }
          setGpsData(gps);
        }
      }

      // Load motor harmonics
      const harmRes = await fetch(`${API}/api/logs/${currentLogId}/motor-harmonics`);
      if (harmRes.ok) {
        const data = await harmRes.json();
        setMotorHarmonics(data);
      }

      // Load correlations
      const corrRes = await fetch(`${API}/api/logs/${currentLogId}/correlations`);
      if (corrRes.ok) {
        const data = await corrRes.json();
        setVibeThrottle(data.vibration_throttle);
      }
    } catch (e) {
      console.error('Failed to load advanced analysis:', e);
    }
    setLoading(false);
  };

  const gpsPoints = gpsData
    ? gpsData.timestamps.map((time, i) => ({
        lat: gpsData.lat[i],
        lng: gpsData.lng[i],
        alt: gpsData.alt?.[i],
        time,
      }))
    : [];

  // Redirect if in beginner mode
  if (verificationMode === 'beginner') {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.restrictedContainer}>
          <Ionicons name="lock-closed-outline" size={56} color="#FFD700" />
          <Text style={styles.restrictedTitle}>Pro Feature</Text>
          <Text style={styles.restrictedHint}>
            Advanced analysis (Motor Harmonics, Correlations, GPS) is available in Pro and Certified modes.{"\n"}
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

  if (!currentLogId) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.emptyContainer}>
          <Ionicons name="map-outline" size={56} color="#3F3F46" />
          <Text style={styles.emptyTitle}>No Log Selected</Text>
          <Text style={styles.emptyHint}>Load a log to see advanced analysis</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Advanced Analysis</Text>

        {/* Tab Selector */}
        <View style={styles.tabs}>
          <TouchableOpacity
            testID="tab-gps"
            style={[styles.tab, activeTab === 'gps' && styles.tabActive]}
            onPress={() => setActiveTab('gps')}
          >
            <Ionicons name="map-outline" size={18} color={activeTab === 'gps' ? '#007AFF' : '#A1A1AA'} />
            <Text style={[styles.tabText, activeTab === 'gps' && styles.tabTextActive]}>GPS</Text>
          </TouchableOpacity>
          <TouchableOpacity
            testID="tab-harmonics"
            style={[styles.tab, activeTab === 'harmonics' && styles.tabActive]}
            onPress={() => setActiveTab('harmonics')}
          >
            <Ionicons name="pulse-outline" size={18} color={activeTab === 'harmonics' ? '#007AFF' : '#A1A1AA'} />
            <Text style={[styles.tabText, activeTab === 'harmonics' && styles.tabTextActive]}>Motors</Text>
          </TouchableOpacity>
          <TouchableOpacity
            testID="tab-correlation"
            style={[styles.tab, activeTab === 'correlation' && styles.tabActive]}
            onPress={() => setActiveTab('correlation')}
          >
            <Ionicons name="git-compare-outline" size={18} color={activeTab === 'correlation' ? '#007AFF' : '#A1A1AA'} />
            <Text style={[styles.tabText, activeTab === 'correlation' && styles.tabTextActive]}>Correlations</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator color="#007AFF" size="large" />
            <Text style={styles.loadingText}>Analyzing flight data...</Text>
          </View>
        ) : (
          <>
            {/* GPS Trajectory Tab */}
            {activeTab === 'gps' && gpsData && (
              <View>
                <GPSMap points={gpsPoints} height={350} />
                <View style={styles.statsRow}>
                  <View style={styles.statCard}>
                    <Text style={styles.statLabel}>Distance</Text>
                    <Text style={styles.statValue}>—</Text>
                  </View>
                  <View style={styles.statCard}>
                    <Text style={styles.statLabel}>Max Speed</Text>
                    <Text style={styles.statValue}>
                      {gpsData.spd ? Math.max(...gpsData.spd).toFixed(1) : '—'} m/s
                    </Text>
                  </View>
                  <View style={styles.statCard}>
                    <Text style={styles.statLabel}>Max Alt</Text>
                    <Text style={styles.statValue}>
                      {gpsData.alt ? Math.max(...gpsData.alt).toFixed(1) : '—'} m
                    </Text>
                  </View>
                </View>
              </View>
            )}

            {/* Motor Harmonics Tab */}
            {activeTab === 'harmonics' && motorHarmonics && (
              <View>
                {motorHarmonics.motor_imbalance && (
                  <View style={styles.infoCard}>
                    <Text style={styles.infoTitle}>Motor Imbalance</Text>
                    <Text style={styles.infoValue}>
                      {motorHarmonics.motor_imbalance.imbalance_percentage.toFixed(1)}%
                    </Text>
                    <Text style={styles.infoDetail}>
                      {motorHarmonics.motor_imbalance.max_deviation_motor} deviates by{' '}
                      {motorHarmonics.motor_imbalance.max_deviation.toFixed(0)} PWM
                    </Text>
                    <View
                      style={[
                        styles.statusBadge,
                        {
                          backgroundColor:
                            motorHarmonics.motor_imbalance.status === 'balanced'
                              ? 'rgba(0,255,136,0.15)'
                              : motorHarmonics.motor_imbalance.status === 'warning'
                              ? 'rgba(255,149,0,0.15)'
                              : 'rgba(255,59,48,0.15)',
                        },
                      ]}
                    >
                      <Text
                        style={[
                          styles.statusText,
                          {
                            color:
                              motorHarmonics.motor_imbalance.status === 'balanced'
                                ? '#00FF88'
                                : motorHarmonics.motor_imbalance.status === 'warning'
                                ? '#FF9500'
                                : '#FF3B30',
                          },
                        ]}
                      >
                        {motorHarmonics.motor_imbalance.status.toUpperCase()}
                      </Text>
                    </View>
                  </View>
                )}

                {motorHarmonics.motor_harmonics.map((motor, i) => (
                  <View key={i} style={styles.motorCard}>
                    <Text style={styles.motorTitle}>Motor {motor.motor_num}</Text>
                    <Text style={styles.motorFreq}>
                      Dominant: {motor.dominant_freq.toFixed(1)} Hz
                    </Text>
                    <Text style={styles.motorThd}>
                      THD: {motor.total_harmonic_distortion.toFixed(2)}%
                    </Text>
                    <View style={styles.harmonicsList}>
                      {motor.harmonics.slice(0, 3).map((h, j) => (
                        <View key={j} style={styles.harmonicItem}>
                          <Text style={styles.harmonicFreq}>{h.frequency.toFixed(1)} Hz</Text>
                          <Text style={styles.harmonicPower}>{h.power_db.toFixed(1)} dB</Text>
                        </View>
                      ))}
                    </View>
                  </View>
                ))}
              </View>
            )}

            {/* Correlation Tab */}
            {activeTab === 'correlation' && vibeThrottle && vibeThrottle.status === 'success' && (
              <View>
                <View style={styles.summaryCard}>
                  <Text style={styles.summaryTitle}>Vibration-Throttle Analysis</Text>
                  <Text style={styles.summaryText}>{vibeThrottle.summary.interpretation}</Text>
                  <Text style={styles.summaryCorr}>
                    Avg Correlation: {vibeThrottle.summary.average_correlation.toFixed(3)}
                  </Text>
                </View>

                {vibeThrottle.correlations.map((corr, i) => (
                  <View key={i} style={styles.corrCard}>
                    <View style={styles.corrHeader}>
                      <Text style={styles.corrAxis}>{corr.axis}</Text>
                      <View
                        style={[
                          styles.corrBadge,
                          {
                            backgroundColor:
                              corr.correlation_strength === 'strong'
                                ? 'rgba(255,59,48,0.15)'
                                : corr.correlation_strength === 'moderate'
                                ? 'rgba(255,149,0,0.15)'
                                : 'rgba(0,255,136,0.15)',
                          },
                        ]}
                      >
                        <Text style={styles.corrBadgeText}>{corr.correlation_strength.toUpperCase()}</Text>
                      </View>
                    </View>
                    <Text style={styles.corrValue}>Correlation: {corr.pearson_correlation.toFixed(3)}</Text>

                    {corr.vibration_by_throttle.length > 0 && (
                      <View style={styles.throttleRanges}>
                        {corr.vibration_by_throttle.map((tr, j) => (
                          <View key={j} style={styles.throttleItem}>
                            <Text style={styles.throttleLabel}>{tr.throttle_range}</Text>
                            <Text style={styles.throttleValue}>{tr.avg_vibration.toFixed(1)} m/s²</Text>
                          </View>
                        ))}
                      </View>
                    )}
                  </View>
                ))}
              </View>
            )}
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
  tabs: { flexDirection: 'row', marginBottom: 16, backgroundColor: '#0A0A0A', borderRadius: 10, padding: 4 },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    borderRadius: 6,
    gap: 4,
  },
  tabActive: { backgroundColor: 'rgba(0,122,255,0.15)' },
  tabText: { color: '#A1A1AA', fontSize: 11, fontWeight: '600' },
  tabTextActive: { color: '#007AFF' },
  loadingContainer: { alignItems: 'center', paddingVertical: 60 },
  loadingText: { color: '#A1A1AA', fontSize: 14, marginTop: 12 },
  statsRow: { flexDirection: 'row', gap: 8, marginTop: 12 },
  statCard: { flex: 1, backgroundColor: '#0A0A0A', borderRadius: 8, padding: 12, borderWidth: 1, borderColor: '#27272A' },
  statLabel: { color: '#52525B', fontSize: 10, textTransform: 'uppercase', fontWeight: '600', marginBottom: 4 },
  statValue: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  infoCard: {
    backgroundColor: '#0A0A0A',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#27272A',
    marginBottom: 12,
  },
  infoTitle: { color: '#A1A1AA', fontSize: 11, fontWeight: '600', textTransform: 'uppercase' },
  infoValue: { color: '#FFFFFF', fontSize: 32, fontWeight: '800', marginVertical: 8 },
  infoDetail: { color: '#A1A1AA', fontSize: 13, marginBottom: 8 },
  statusBadge: { alignSelf: 'flex-start', borderRadius: 4, paddingHorizontal: 8, paddingVertical: 4 },
  statusText: { fontSize: 10, fontWeight: '700' },
  motorCard: { backgroundColor: '#0A0A0A', borderRadius: 10, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#27272A' },
  motorTitle: { color: '#FFFFFF', fontSize: 14, fontWeight: '600' },
  motorFreq: { color: '#007AFF', fontSize: 12, marginTop: 4 },
  motorThd: { color: '#52525B', fontSize: 11, marginTop: 2 },
  harmonicsList: { flexDirection: 'row', gap: 8, marginTop: 8 },
  harmonicItem: { backgroundColor: '#171717', borderRadius: 6, paddingHorizontal: 10, paddingVertical: 6 },
  harmonicFreq: { color: '#FFFFFF', fontSize: 11, fontWeight: '600' },
  harmonicPower: { color: '#A1A1AA', fontSize: 9, marginTop: 2 },
  summaryCard: { backgroundColor: 'rgba(0,122,255,0.08)', borderRadius: 12, padding: 14, marginBottom: 12, borderWidth: 1, borderColor: 'rgba(0,122,255,0.2)' },
  summaryTitle: { color: '#007AFF', fontSize: 13, fontWeight: '600', marginBottom: 6 },
  summaryText: { color: '#A1A1AA', fontSize: 12, lineHeight: 18, marginBottom: 6 },
  summaryCorr: { color: '#52525B', fontSize: 11 },
  corrCard: { backgroundColor: '#0A0A0A', borderRadius: 10, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#27272A' },
  corrHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  corrAxis: { color: '#FFFFFF', fontSize: 14, fontWeight: '600' },
  corrBadge: { borderRadius: 4, paddingHorizontal: 8, paddingVertical: 3 },
  corrBadgeText: { color: '#A1A1AA', fontSize: 9, fontWeight: '700' },
  corrValue: { color: '#A1A1AA', fontSize: 12, marginBottom: 8 },
  throttleRanges: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  throttleItem: { backgroundColor: '#171717', borderRadius: 6, paddingHorizontal: 10, paddingVertical: 6 },
  throttleLabel: { color: '#A1A1AA', fontSize: 10, textTransform: 'uppercase' },
  throttleValue: { color: '#FFFFFF', fontSize: 11, fontWeight: '600', marginTop: 2 },
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyTitle: { color: '#A1A1AA', fontSize: 18, fontWeight: '600', marginTop: 16 },
  emptyHint: { color: '#52525B', fontSize: 13, textAlign: 'center', marginTop: 6 },
  restrictedContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  restrictedTitle: { color: '#FFD700', fontSize: 20, fontWeight: '700', marginTop: 16 },
  restrictedHint: { color: '#A1A1AA', fontSize: 13, textAlign: 'center', marginTop: 8, lineHeight: 20 },
  upgradeBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#007AFF', borderRadius: 10, paddingHorizontal: 20, paddingVertical: 12, marginTop: 20, gap: 8 },
  upgradeBtnText: { color: '#FFF', fontWeight: '600', fontSize: 14 },
});
