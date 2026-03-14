import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  ActivityIndicator, SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAppState } from '../../components/AppContext';
import PlotlyChart from '../../components/PlotlyChart';

const API = process.env.EXPO_PUBLIC_BACKEND_URL;

const CHART_COLORS = ['#007AFF', '#FF3B30', '#00FF88', '#FF9500', '#BF5AF2', '#FF6B6B', '#4ECDC4', '#45B7D1'];

const PRESETS: Record<string, { type: string; field: string }[]> = {
  'Attitude': [
    { type: 'ATT', field: 'Roll' },
    { type: 'ATT', field: 'Pitch' },
    { type: 'ATT', field: 'Yaw' },
  ],
  'Gyro': [
    { type: 'IMU', field: 'GyrX' },
    { type: 'IMU', field: 'GyrY' },
    { type: 'IMU', field: 'GyrZ' },
  ],
  'Accel': [
    { type: 'IMU', field: 'AccX' },
    { type: 'IMU', field: 'AccY' },
    { type: 'IMU', field: 'AccZ' },
  ],
  'Vibration': [
    { type: 'VIBE', field: 'VibeX' },
    { type: 'VIBE', field: 'VibeY' },
    { type: 'VIBE', field: 'VibeZ' },
  ],
  'Motors': [
    { type: 'RCOU', field: 'C1' },
    { type: 'RCOU', field: 'C2' },
    { type: 'RCOU', field: 'C3' },
    { type: 'RCOU', field: 'C4' },
  ],
  'Battery': [
    { type: 'BAT', field: 'Volt' },
    { type: 'BAT', field: 'Curr' },
  ],
  'GPS': [
    { type: 'GPS', field: 'Alt' },
    { type: 'GPS', field: 'Spd' },
  ],
  'Altitude': [
    { type: 'BARO', field: 'Alt' },
    { type: 'GPS', field: 'Alt' },
  ],
  'EKF': [
    { type: 'EKF', field: 'VN' },
    { type: 'EKF', field: 'VE' },
    { type: 'EKF', field: 'VD' },
  ],
  'Mag': [
    { type: 'MAG', field: 'MagX' },
    { type: 'MAG', field: 'MagY' },
    { type: 'MAG', field: 'MagZ' },
  ],
};

interface SignalTree {
  [msgType: string]: string[];
}

interface PlotData {
  type: string;
  field: string;
  timestamps: number[];
  values: number[];
  count: number;
}

export default function Analysis() {
  const { currentLogId, mode } = useAppState();
  const [signals, setSignals] = useState<SignalTree>({});
  const [selected, setSelected] = useState<{ type: string; field: string }[]>([]);
  const [plotData, setPlotData] = useState<PlotData[]>([]);
  const [loading, setLoading] = useState(false);
  const [signalLoading, setSignalLoading] = useState(false);
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set());
  const [activePreset, setActivePreset] = useState<string | null>(null);

  useEffect(() => {
    if (currentLogId) loadSignals();
    else { setSignals({}); setSelected([]); setPlotData([]); }
  }, [currentLogId]);

  const loadSignals = async () => {
    if (!currentLogId) return;
    setSignalLoading(true);
    try {
      const res = await fetch(`${API}/api/logs/${currentLogId}/signals`);
      if (res.ok) {
        const data = await res.json();
        setSignals(data.signals || {});
      }
    } catch (e) {
      console.error('Failed to load signals:', e);
    }
    setSignalLoading(false);
  };

  const loadPreset = async (presetName: string) => {
    setActivePreset(presetName);
    const presetSignals = PRESETS[presetName];
    setSelected(presetSignals);
    await fetchData(presetSignals);
  };

  const toggleSignal = (type: string, field: string) => {
    const exists = selected.some(s => s.type === type && s.field === field);
    const newSelected = exists
      ? selected.filter(s => !(s.type === type && s.field === field))
      : [...selected, { type, field }];
    setSelected(newSelected);
    setActivePreset(null);
  };

  const fetchData = async (sigs?: { type: string; field: string }[]) => {
    const toFetch = sigs || selected;
    if (!currentLogId || toFetch.length === 0) { setPlotData([]); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/logs/${currentLogId}/data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signals: toFetch, max_points: 3000 }),
      });
      if (res.ok) {
        const data = await res.json();
        setPlotData(data.data || []);
      }
    } catch (e) {
      console.error('Failed to fetch data:', e);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (selected.length > 0 && !activePreset) {
      const timeout = setTimeout(() => fetchData(), 300);
      return () => clearTimeout(timeout);
    }
  }, [selected]);

  const toggleExpand = (type: string) => {
    const newExpanded = new Set(expandedTypes);
    if (newExpanded.has(type)) newExpanded.delete(type);
    else newExpanded.add(type);
    setExpandedTypes(newExpanded);
  };

  const traces = plotData.map((d, i) => ({
    x: d.timestamps,
    y: d.values,
    name: `${d.type}.${d.field}`,
    type: 'scatter' as const,
    mode: 'lines' as const,
    line: { color: CHART_COLORS[i % CHART_COLORS.length], width: 1.5 },
  }));

  if (!currentLogId) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.emptyContainer}>
          <Ionicons name="analytics-outline" size={56} color="#3F3F46" />
          <Text style={styles.emptyTitle}>No Log Selected</Text>
          <Text style={styles.emptyHint}>Go to Dashboard and load a demo or upload a log file</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Signal Analysis</Text>

        {/* Quick Presets */}
        <Text style={styles.sectionLabel}>Quick Presets</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.presetsRow}>
          {Object.keys(PRESETS).map((name) => (
            <TouchableOpacity
              key={name}
              testID={`preset-${name.toLowerCase()}`}
              style={[styles.presetChip, activePreset === name && styles.presetChipActive]}
              onPress={() => loadPreset(name)}
            >
              <Text style={[styles.presetText, activePreset === name && styles.presetTextActive]}>
                {name}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Chart */}
        {loading ? (
          <View style={styles.chartPlaceholder}>
            <ActivityIndicator color="#007AFF" />
            <Text style={styles.chartLoadText}>Loading signal data...</Text>
          </View>
        ) : plotData.length > 0 ? (
          <PlotlyChart
            testID="analysis-chart"
            traces={traces}
            layout={{ title: activePreset || 'Signal Plot' }}
            height={350}
          />
        ) : (
          <View style={styles.chartPlaceholder}>
            <Ionicons name="pulse-outline" size={40} color="#3F3F46" />
            <Text style={styles.chartLoadText}>Select signals or a preset to plot</Text>
          </View>
        )}

        {/* Signal count */}
        {plotData.length > 0 && (
          <Text style={styles.dataInfo}>
            Showing {plotData.length} signals · {plotData.reduce((a, d) => a + d.count, 0).toLocaleString()} data points
          </Text>
        )}

        {/* Signal Tree (Pro mode or expanded) */}
        {mode === 'professional' && (
          <>
            <Text style={[styles.sectionLabel, { marginTop: 16 }]}>Signal Selector</Text>
            {signalLoading ? (
              <ActivityIndicator color="#007AFF" style={{ marginTop: 12 }} />
            ) : (
              Object.entries(signals).map(([msgType, fields]) => (
                <View key={msgType} style={styles.treeGroup}>
                  <TouchableOpacity
                    testID={`expand-${msgType}`}
                    style={styles.treeHeader}
                    onPress={() => toggleExpand(msgType)}
                  >
                    <Ionicons
                      name={expandedTypes.has(msgType) ? 'chevron-down' : 'chevron-forward'}
                      size={14} color="#A1A1AA"
                    />
                    <Text style={styles.treeName}>{msgType}</Text>
                    <Text style={styles.treeCount}>{fields.length}</Text>
                  </TouchableOpacity>
                  {expandedTypes.has(msgType) && (
                    <View style={styles.treeFields}>
                      {fields.map((field) => {
                        const isSelected = selected.some(s => s.type === msgType && s.field === field);
                        return (
                          <TouchableOpacity
                            key={field}
                            testID={`signal-${msgType}-${field}`}
                            style={[styles.fieldChip, isSelected && styles.fieldChipSelected]}
                            onPress={() => toggleSignal(msgType, field)}
                          >
                            <Text style={[styles.fieldText, isSelected && styles.fieldTextSelected]}>
                              {field}
                            </Text>
                          </TouchableOpacity>
                        );
                      })}
                    </View>
                  )}
                </View>
              ))
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
  sectionLabel: { color: '#A1A1AA', fontSize: 11, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 8 },
  presetsRow: { marginBottom: 16 },
  presetChip: { backgroundColor: '#171717', borderWidth: 1, borderColor: '#27272A', borderRadius: 8, paddingHorizontal: 14, paddingVertical: 8, marginRight: 8 },
  presetChipActive: { borderColor: '#007AFF', backgroundColor: 'rgba(0,122,255,0.12)' },
  presetText: { color: '#A1A1AA', fontSize: 12, fontWeight: '600' },
  presetTextActive: { color: '#007AFF' },
  chartPlaceholder: { height: 350, backgroundColor: '#0A0A0A', borderRadius: 8, borderWidth: 1, borderColor: '#27272A', justifyContent: 'center', alignItems: 'center' },
  chartLoadText: { color: '#52525B', fontSize: 13, marginTop: 8 },
  dataInfo: { color: '#52525B', fontSize: 11, marginTop: 8, textAlign: 'right' },
  treeGroup: { marginBottom: 4 },
  treeHeader: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, paddingHorizontal: 4, gap: 6 },
  treeName: { color: '#FFFFFF', fontSize: 13, fontWeight: '600', flex: 1 },
  treeCount: { color: '#52525B', fontSize: 11 },
  treeFields: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, paddingLeft: 20, paddingBottom: 8 },
  fieldChip: { backgroundColor: '#171717', borderWidth: 1, borderColor: '#27272A', borderRadius: 6, paddingHorizontal: 10, paddingVertical: 5 },
  fieldChipSelected: { borderColor: '#007AFF', backgroundColor: 'rgba(0,122,255,0.12)' },
  fieldText: { color: '#A1A1AA', fontSize: 11, fontWeight: '500' },
  fieldTextSelected: { color: '#007AFF' },
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyTitle: { color: '#A1A1AA', fontSize: 18, fontWeight: '600', marginTop: 16 },
  emptyHint: { color: '#52525B', fontSize: 13, textAlign: 'center', marginTop: 6 },
});
