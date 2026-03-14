import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  ActivityIndicator, SafeAreaView, FlatList, Linking, Platform, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAppState } from '../../components/AppContext';

const API = process.env.EXPO_PUBLIC_BACKEND_URL;

interface SignalTree {
  [msgType: string]: string[];
}

export default function DataScreen() {
  const { currentLogId, mode } = useAppState();
  const [signals, setSignals] = useState<SignalTree>({});
  const [selectedType, setSelectedType] = useState<string>('ATT');
  const [tableData, setTableData] = useState<any[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalRows, setTotalRows] = useState(0);

  useEffect(() => {
    if (currentLogId) loadSignals();
    else { setSignals({}); setTableData([]); }
  }, [currentLogId]);

  const loadSignals = async () => {
    if (!currentLogId) return;
    try {
      const res = await fetch(`${API}/api/logs/${currentLogId}/signals`);
      if (res.ok) {
        const data = await res.json();
        setSignals(data.signals || {});
        const types = Object.keys(data.signals || {});
        if (types.length > 0) {
          setSelectedType(types[0]);
          loadTableData(types[0], data.signals);
        }
      }
    } catch (e) {
      console.error('Failed to load signals:', e);
    }
  };

  const loadTableData = async (msgType: string, sigs?: SignalTree) => {
    if (!currentLogId) return;
    setLoading(true);
    const available = sigs || signals;
    const fields = available[msgType] || [];
    const allSignals = fields.map(f => ({ type: msgType, field: f }));

    try {
      const res = await fetch(`${API}/api/logs/${currentLogId}/data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signals: allSignals, max_points: 500 }),
      });
      if (res.ok) {
        const data = await res.json();
        const cols = ['Time', ...fields];
        setColumns(cols);

        // Build rows from returned data
        const timeData = data.data?.find((d: any) => true)?.timestamps || [];
        const rows = timeData.map((t: number, i: number) => {
          const row: any = { Time: t.toFixed(3) };
          for (const d of data.data) {
            row[d.field] = d.values[i] !== undefined ? (typeof d.values[i] === 'number' ? d.values[i].toFixed(4) : d.values[i]) : '';
          }
          return row;
        });
        setTableData(rows);
        setTotalRows(data.data?.[0]?.count || rows.length);
      }
    } catch (e) {
      console.error('Failed to load table data:', e);
    }
    setLoading(false);
  };

  const selectType = (type: string) => {
    setSelectedType(type);
    loadTableData(type);
  };

  const exportCSV = async () => {
    if (!currentLogId) return;
    const url = `${API}/api/logs/${currentLogId}/export?message_type=${selectedType}`;
    try {
      if (Platform.OS === 'web') {
        window.open(url, '_blank');
      } else {
        await Linking.openURL(url);
      }
    } catch {
      Alert.alert('Export', 'Download started. Check your browser downloads.');
    }
  };

  if (!currentLogId) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.emptyContainer}>
          <Ionicons name="document-text-outline" size={56} color="#3F3F46" />
          <Text style={styles.emptyTitle}>No Log Selected</Text>
          <Text style={styles.emptyHint}>Load a log to inspect raw data</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <View style={styles.headerRow}>
          <Text style={styles.title}>Raw Data</Text>
          <TouchableOpacity testID="export-csv-btn" style={styles.exportBtn} onPress={exportCSV}>
            <Ionicons name="download-outline" size={16} color="#007AFF" />
            <Text style={styles.exportText}>Export CSV</Text>
          </TouchableOpacity>
        </View>

        {/* Message Type Selector */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.typeRow}>
          {Object.keys(signals).map((type) => (
            <TouchableOpacity
              key={type}
              testID={`data-type-${type}`}
              style={[styles.typeChip, selectedType === type && styles.typeChipActive]}
              onPress={() => selectType(type)}
            >
              <Text style={[styles.typeText, selectedType === type && styles.typeTextActive]}>{type}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <Text style={styles.rowInfo}>
          {totalRows.toLocaleString()} rows · {columns.length} columns · Showing first 500
        </Text>

        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator color="#007AFF" />
          </View>
        ) : (
          <ScrollView horizontal style={styles.tableScroll}>
            <View>
              {/* Table Header */}
              <View style={styles.tableHeader}>
                {columns.map((col) => (
                  <View key={col} style={styles.headerCell}>
                    <Text style={styles.headerCellText} numberOfLines={1}>{col}</Text>
                  </View>
                ))}
              </View>
              {/* Table Body */}
              <FlatList
                data={tableData}
                keyExtractor={(_, i) => String(i)}
                renderItem={({ item, index }) => (
                  <View style={[styles.tableRow, index % 2 === 0 && styles.tableRowAlt]}>
                    {columns.map((col) => (
                      <View key={col} style={styles.dataCell}>
                        <Text style={styles.dataCellText} numberOfLines={1}>
                          {item[col] ?? ''}
                        </Text>
                      </View>
                    ))}
                  </View>
                )}
                style={styles.tableBody}
                getItemLayout={(_, index) => ({ length: 32, offset: 32 * index, index })}
                initialNumToRender={30}
                maxToRenderPerBatch={30}
              />
            </View>
          </ScrollView>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#050505' },
  container: { flex: 1, padding: 16 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, marginTop: 8 },
  title: { color: '#FFFFFF', fontSize: 20, fontWeight: '700' },
  exportBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#171717', borderWidth: 1, borderColor: '#27272A', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 7 },
  exportText: { color: '#007AFF', fontSize: 12, fontWeight: '600' },
  typeRow: { marginBottom: 10 },
  typeChip: { backgroundColor: '#171717', borderWidth: 1, borderColor: '#27272A', borderRadius: 6, paddingHorizontal: 12, paddingVertical: 6, marginRight: 6 },
  typeChipActive: { borderColor: '#007AFF', backgroundColor: 'rgba(0,122,255,0.12)' },
  typeText: { color: '#A1A1AA', fontSize: 11, fontWeight: '600' },
  typeTextActive: { color: '#007AFF' },
  rowInfo: { color: '#52525B', fontSize: 10, marginBottom: 8 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  tableScroll: { flex: 1 },
  tableHeader: { flexDirection: 'row', backgroundColor: '#171717', borderBottomWidth: 1, borderColor: '#27272A' },
  headerCell: { width: 100, paddingHorizontal: 8, paddingVertical: 8, justifyContent: 'center' },
  headerCellText: { color: '#FFFFFF', fontSize: 11, fontWeight: '700' },
  tableBody: { flex: 1 },
  tableRow: { flexDirection: 'row', borderBottomWidth: 1, borderColor: '#1A1A1A' },
  tableRowAlt: { backgroundColor: '#0A0A0A' },
  dataCell: { width: 100, paddingHorizontal: 8, paddingVertical: 6, justifyContent: 'center' },
  dataCellText: { color: '#A1A1AA', fontSize: 10, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace' },
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyTitle: { color: '#A1A1AA', fontSize: 18, fontWeight: '600', marginTop: 16 },
  emptyHint: { color: '#52525B', fontSize: 13, textAlign: 'center', marginTop: 6 },
});
