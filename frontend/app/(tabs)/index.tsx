import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  ActivityIndicator, SafeAreaView, Alert, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAppState } from '../../components/AppContext';
import * as DocumentPicker from 'expo-document-picker';

const API = process.env.EXPO_PUBLIC_BACKEND_URL;

interface LogEntry {
  log_id: string;
  filename: string;
  upload_date: string;
  file_size: number;
  duration_sec: number;
  message_types: string[];
  vehicle_type: string;
  is_demo: boolean;
  total_messages?: number;
  firmware?: string;
}

export default function Dashboard() {
  const {
    currentLogId, setCurrentLogId, setCurrentLogName,
    mode, setMode, analysisType, setAnalysisType,
    uploadProgress, setUploadProgress,
  } = useAppState();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/logs`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (e) {
      console.error('Failed to fetch logs:', e);
    }
  }, []);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  const loadDemo = async () => {
    setDemoLoading(true);
    setUploadProgress({ isUploading: true, progress: 0, status: 'Generating demo flight data...' });
    try {
      setUploadProgress({ isUploading: true, progress: 30, status: 'Processing signals...' });
      const res = await fetch(`${API}/api/logs/demo`, { method: 'POST' });
      setUploadProgress({ isUploading: true, progress: 80, status: 'Finalizing...' });
      if (res.ok) {
        const data = await res.json();
        setCurrentLogId(data.log_id);
        setCurrentLogName(data.filename);
        await fetchLogs();
        setUploadProgress({ isUploading: false, progress: 100, status: 'Demo loaded successfully!' });
      } else {
        setUploadProgress({ isUploading: false, progress: 0, status: 'Failed to generate demo' });
      }
    } catch (e) {
      Alert.alert('Error', 'Failed to generate demo log');
      setUploadProgress({ isUploading: false, progress: 0, status: '' });
    }
    setTimeout(() => setUploadProgress({ isUploading: false, progress: 0, status: '' }), 2000);
    setDemoLoading(false);
  };

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

      const formData = new FormData();
      formData.append('file', {
        uri: file.uri,
        name: file.name || 'log.bin',
        type: 'application/octet-stream',
      } as any);

      // Simulate progress during upload
      let progress = 10;
      const progressInterval = setInterval(() => {
        if (progress < 70) {
          progress += 10;
          setUploadProgress(prev => ({
            ...prev,
            progress,
            status: progress < 40 ? 'Uploading file...' :
                   progress < 60 ? 'Parsing log data...' :
                   'Processing signals...',
          }));
        }
      }, 500);

      const res = await fetch(`${API}/api/logs/upload?analysis_type=${analysisType}`, {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);

      if (res.ok) {
        setUploadProgress({ isUploading: true, progress: 90, status: 'Finalizing...' });
        const data = await res.json();
        setCurrentLogId(data.log_id);
        setCurrentLogName(data.filename);
        await fetchLogs();
        setUploadProgress({
          isUploading: false,
          progress: 100,
          status: `${analysisType === 'quick' ? 'Quick' : 'Full'} analysis complete!`,
        });
      } else {
        const err = await res.text();
        Alert.alert('Upload Failed', err);
        setUploadProgress({ isUploading: false, progress: 0, status: '' });
      }
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Upload failed');
      setUploadProgress({ isUploading: false, progress: 0, status: '' });
    }
    setTimeout(() => setUploadProgress({ isUploading: false, progress: 0, status: '' }), 3000);
    setLoading(false);
  };

  const selectLog = (log: LogEntry) => {
    setCurrentLogId(log.log_id);
    setCurrentLogName(log.filename);
  };

  const deleteLog = async (logId: string) => {
    try {
      await fetch(`${API}/api/logs/${logId}`, { method: 'DELETE' });
      if (currentLogId === logId) {
        setCurrentLogId(null);
        setCurrentLogName('');
      }
      await fetchLogs();
    } catch {}
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return 'Demo';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  const formatDuration = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}m ${s}s`;
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>Vehicle Log Analyzer</Text>
            <Text style={styles.subtitle}>Flight data analysis & diagnostics</Text>
          </View>
          <TouchableOpacity
            testID="mode-toggle-btn"
            style={[styles.modeBadge, mode === 'professional' && styles.modeBadgePro]}
            onPress={() => setMode(mode === 'beginner' ? 'professional' : 'beginner')}
          >
            <Ionicons
              name={mode === 'beginner' ? 'school-outline' : 'construct-outline'}
              size={14}
              color={mode === 'professional' ? '#00FF88' : '#007AFF'}
            />
            <Text style={[styles.modeText, mode === 'professional' && styles.modeTextPro]}>
              {mode === 'beginner' ? 'BEGINNER' : 'PRO'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Analysis Type Toggle */}
        <View style={styles.analysisToggle}>
          <Text style={styles.analysisLabel}>Analysis Mode</Text>
          <View style={styles.toggleContainer}>
            <TouchableOpacity
              testID="quick-analysis-btn"
              style={[styles.toggleBtn, analysisType === 'quick' && styles.toggleBtnActive]}
              onPress={() => setAnalysisType('quick')}
            >
              <Ionicons name="flash-outline" size={14} color={analysisType === 'quick' ? '#FFF' : '#A1A1AA'} />
              <Text style={[styles.toggleText, analysisType === 'quick' && styles.toggleTextActive]}>Quick</Text>
            </TouchableOpacity>
            <TouchableOpacity
              testID="full-analysis-btn"
              style={[styles.toggleBtn, analysisType === 'full' && styles.toggleBtnActive]}
              onPress={() => setAnalysisType('full')}
            >
              <Ionicons name="analytics-outline" size={14} color={analysisType === 'full' ? '#FFF' : '#A1A1AA'} />
              <Text style={[styles.toggleText, analysisType === 'full' && styles.toggleTextActive]}>Full</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.analysisHint}>
            {analysisType === 'quick'
              ? 'Faster processing with downsampled data (~2000 points/signal)'
              : 'Complete analysis with all data points (slower for large files)'}
          </Text>
        </View>

        {/* Upload Progress */}
        {uploadProgress.isUploading && (
          <View style={styles.progressCard}>
            <View style={styles.progressHeader}>
              <ActivityIndicator color="#007AFF" size="small" />
              <Text style={styles.progressFilename} numberOfLines={1}>
                {uploadProgress.filename || 'Processing...'}
              </Text>
            </View>
            <View style={styles.progressBarBg}>
              <View style={[styles.progressBarFill, { width: `${uploadProgress.progress}%` }]} />
            </View>
            <View style={styles.progressFooter}>
              <Text style={styles.progressStatus}>{uploadProgress.status}</Text>
              <Text style={styles.progressPercent}>{uploadProgress.progress}%</Text>
            </View>
          </View>
        )}

        {/* Completion Toast */}
        {!uploadProgress.isUploading && uploadProgress.progress === 100 && (
          <View style={styles.successCard}>
            <Ionicons name="checkmark-circle" size={18} color="#00FF88" />
            <Text style={styles.successText}>{uploadProgress.status}</Text>
          </View>
        )}

        {/* Action Buttons */}
        <View style={styles.actions}>
          <TouchableOpacity
            testID="load-demo-btn"
            style={styles.primaryBtn}
            onPress={loadDemo}
            disabled={demoLoading || uploadProgress.isUploading}
          >
            {demoLoading ? (
              <ActivityIndicator color="#FFF" size="small" />
            ) : (
              <>
                <Ionicons name="rocket-outline" size={18} color="#FFF" />
                <Text style={styles.primaryBtnText}>Load Demo Flight</Text>
              </>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            testID="upload-log-btn"
            style={styles.secondaryBtn}
            onPress={uploadLog}
            disabled={loading || uploadProgress.isUploading}
          >
            {loading ? (
              <ActivityIndicator color="#007AFF" size="small" />
            ) : (
              <>
                <Ionicons name="cloud-upload-outline" size={18} color="#007AFF" />
                <Text style={styles.secondaryBtnText}>Upload .BIN / .LOG</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Current Selection */}
        {currentLogId && (
          <View style={styles.activeCard}>
            <View style={styles.activeIndicator} />
            <View style={styles.activeInfo}>
              <Text style={styles.activeLabel}>Active Log</Text>
              <Text style={styles.activeName} numberOfLines={1}>
                {logs.find(l => l.log_id === currentLogId)?.filename || 'Selected'}
              </Text>
            </View>
            <Ionicons name="checkmark-circle" size={20} color="#00FF88" />
          </View>
        )}

        {/* Logs List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Flight Logs ({logs.length})</Text>
          {logs.length === 0 && (
            <View style={styles.emptyState}>
              <Ionicons name="airplane-outline" size={48} color="#3F3F46" />
              <Text style={styles.emptyText}>No logs loaded yet</Text>
              <Text style={styles.emptyHint}>
                Load a demo flight or upload your .BIN/.LOG file
              </Text>
            </View>
          )}
          {logs.map((log) => (
            <TouchableOpacity
              key={log.log_id}
              testID={`log-item-${log.log_id}`}
              style={[styles.logCard, currentLogId === log.log_id && styles.logCardActive]}
              onPress={() => selectLog(log)}
            >
              <View style={styles.logCardHeader}>
                <View style={styles.logIcon}>
                  <Ionicons
                    name={log.is_demo ? 'flask-outline' : 'document-outline'}
                    size={18}
                    color={currentLogId === log.log_id ? '#007AFF' : '#A1A1AA'}
                  />
                </View>
                <View style={styles.logInfo}>
                  <Text style={styles.logName} numberOfLines={1}>{log.filename}</Text>
                  <Text style={styles.logMeta}>
                    {log.vehicle_type} · {formatDuration(log.duration_sec)} · {formatSize(log.file_size)}
                  </Text>
                </View>
                <TouchableOpacity
                  testID={`delete-log-${log.log_id}`}
                  onPress={() => deleteLog(log.log_id)}
                  hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                >
                  <Ionicons name="trash-outline" size={16} color="#52525B" />
                </TouchableOpacity>
              </View>
              <View style={styles.logTags}>
                {log.message_types.slice(0, 6).map((t) => (
                  <View key={t} style={styles.tag}>
                    <Text style={styles.tagText}>{t}</Text>
                  </View>
                ))}
                {log.message_types.length > 6 && (
                  <View style={styles.tag}>
                    <Text style={styles.tagText}>+{log.message_types.length - 6}</Text>
                  </View>
                )}
              </View>
              {log.total_messages && (
                <Text style={styles.logSamples}>
                  {log.total_messages.toLocaleString()} total samples · {log.message_types.length} message types
                </Text>
              )}
            </TouchableOpacity>
          ))}
        </View>

        {/* Info Section for Beginners */}
        {mode === 'beginner' && (
          <View style={styles.infoCard}>
            <Ionicons name="information-circle-outline" size={20} color="#007AFF" />
            <View style={styles.infoContent}>
              <Text style={styles.infoTitle}>Getting Started</Text>
              <Text style={styles.infoText}>
                1. Load a demo flight or upload your .BIN log{"\n"}
                2. Go to Analysis tab to see flight data plots{"\n"}
                3. Check Health tab for automatic diagnostics{"\n"}
                4. Use FFT tab for vibration frequency analysis
              </Text>
            </View>
          </View>
        )}

        {/* Supported Formats */}
        <View style={styles.supportedFormats}>
          <Text style={styles.formatTitle}>Supported Log Formats</Text>
          <View style={styles.formatList}>
            <View style={styles.formatItem}>
              <Ionicons name="checkmark" size={12} color="#00FF88" />
              <Text style={styles.formatText}>ArduPilot .BIN / .LOG</Text>
            </View>
            <View style={styles.formatItem}>
              <Ionicons name="checkmark" size={12} color="#00FF88" />
              <Text style={styles.formatText}>DataFlash logs</Text>
            </View>
            <View style={[styles.formatItem, { opacity: 0.5 }]}>
              <Ionicons name="time-outline" size={12} color="#A1A1AA" />
              <Text style={styles.formatText}>PX4 .ulg (coming soon)</Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#050505' },
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 32 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16, marginTop: 8 },
  title: { color: '#FFFFFF', fontSize: 24, fontWeight: '700', letterSpacing: -0.5 },
  subtitle: { color: '#52525B', fontSize: 13, marginTop: 2 },
  modeBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#171717', borderWidth: 1, borderColor: '#27272A', borderRadius: 20, paddingHorizontal: 10, paddingVertical: 6, gap: 4 },
  modeBadgePro: { borderColor: 'rgba(0,255,136,0.3)', backgroundColor: 'rgba(0,255,136,0.08)' },
  modeText: { color: '#007AFF', fontSize: 10, fontWeight: '700', letterSpacing: 1 },
  modeTextPro: { color: '#00FF88' },
  
  // Analysis Toggle
  analysisToggle: { backgroundColor: '#0A0A0A', borderWidth: 1, borderColor: '#27272A', borderRadius: 12, padding: 14, marginBottom: 16 },
  analysisLabel: { color: '#A1A1AA', fontSize: 11, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 10 },
  toggleContainer: { flexDirection: 'row', gap: 8 },
  toggleBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#171717', borderWidth: 1, borderColor: '#27272A', borderRadius: 8, paddingVertical: 10, gap: 6 },
  toggleBtnActive: { backgroundColor: '#007AFF', borderColor: '#007AFF' },
  toggleText: { color: '#A1A1AA', fontSize: 13, fontWeight: '600' },
  toggleTextActive: { color: '#FFF' },
  analysisHint: { color: '#52525B', fontSize: 11, marginTop: 10, lineHeight: 16 },
  
  // Progress
  progressCard: { backgroundColor: '#0A0A0A', borderWidth: 1, borderColor: '#007AFF', borderRadius: 12, padding: 14, marginBottom: 16 },
  progressHeader: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 10 },
  progressFilename: { flex: 1, color: '#FFFFFF', fontSize: 13, fontWeight: '500' },
  progressBarBg: { height: 6, backgroundColor: '#27272A', borderRadius: 3, overflow: 'hidden' },
  progressBarFill: { height: '100%', backgroundColor: '#007AFF', borderRadius: 3 },
  progressFooter: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 },
  progressStatus: { color: '#A1A1AA', fontSize: 12 },
  progressPercent: { color: '#007AFF', fontSize: 12, fontWeight: '600' },
  
  // Success
  successCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(0,255,136,0.08)', borderWidth: 1, borderColor: 'rgba(0,255,136,0.3)', borderRadius: 10, padding: 12, marginBottom: 16, gap: 8 },
  successText: { color: '#00FF88', fontSize: 13, fontWeight: '500' },
  
  actions: { flexDirection: 'row', gap: 10, marginBottom: 16 },
  primaryBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#007AFF', borderRadius: 10, height: 48, gap: 8 },
  primaryBtnText: { color: '#FFF', fontWeight: '600', fontSize: 14 },
  secondaryBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#171717', borderRadius: 10, height: 48, gap: 8, borderWidth: 1, borderColor: '#27272A' },
  secondaryBtnText: { color: '#007AFF', fontWeight: '600', fontSize: 14 },
  activeCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(0,255,136,0.06)', borderWidth: 1, borderColor: 'rgba(0,255,136,0.2)', borderRadius: 10, padding: 12, marginBottom: 20, gap: 10 },
  activeIndicator: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#00FF88' },
  activeInfo: { flex: 1 },
  activeLabel: { color: '#00FF88', fontSize: 10, fontWeight: '700', letterSpacing: 1, textTransform: 'uppercase' },
  activeName: { color: '#FFFFFF', fontSize: 14, fontWeight: '500', marginTop: 2 },
  section: { marginBottom: 20 },
  sectionTitle: { color: '#A1A1AA', fontSize: 12, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 12 },
  emptyState: { alignItems: 'center', paddingVertical: 40, backgroundColor: '#0A0A0A', borderRadius: 12, borderWidth: 1, borderColor: '#27272A' },
  emptyText: { color: '#A1A1AA', fontSize: 16, fontWeight: '500', marginTop: 12 },
  emptyHint: { color: '#52525B', fontSize: 13, textAlign: 'center', marginTop: 4, paddingHorizontal: 40 },
  logCard: { backgroundColor: '#0A0A0A', borderWidth: 1, borderColor: '#27272A', borderRadius: 12, padding: 14, marginBottom: 10 },
  logCardActive: { borderColor: '#007AFF', backgroundColor: 'rgba(0,122,255,0.05)' },
  logCardHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  logIcon: { width: 36, height: 36, borderRadius: 8, backgroundColor: '#171717', alignItems: 'center', justifyContent: 'center' },
  logInfo: { flex: 1 },
  logName: { color: '#FFFFFF', fontSize: 14, fontWeight: '600' },
  logMeta: { color: '#52525B', fontSize: 11, marginTop: 2 },
  logTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 10 },
  tag: { backgroundColor: '#171717', borderRadius: 4, paddingHorizontal: 6, paddingVertical: 2 },
  tagText: { color: '#A1A1AA', fontSize: 10, fontWeight: '500' },
  logSamples: { color: '#3F3F46', fontSize: 10, marginTop: 8 },
  infoCard: { flexDirection: 'row', backgroundColor: 'rgba(0,122,255,0.06)', borderWidth: 1, borderColor: 'rgba(0,122,255,0.2)', borderRadius: 12, padding: 14, gap: 10, marginBottom: 16 },
  infoContent: { flex: 1 },
  infoTitle: { color: '#007AFF', fontSize: 13, fontWeight: '600', marginBottom: 4 },
  infoText: { color: '#A1A1AA', fontSize: 12, lineHeight: 20 },
  
  // Supported Formats
  supportedFormats: { backgroundColor: '#0A0A0A', borderWidth: 1, borderColor: '#27272A', borderRadius: 12, padding: 14 },
  formatTitle: { color: '#52525B', fontSize: 11, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 10 },
  formatList: { gap: 6 },
  formatItem: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  formatText: { color: '#A1A1AA', fontSize: 12 },
});
