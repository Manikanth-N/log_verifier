import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  ActivityIndicator, SafeAreaView, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAppState, VerificationMode } from '../../components/AppContext';
import * as DocumentPicker from 'expo-document-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NativeAnalysis from '../../modules/NativeAnalysis';

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
    verificationMode, setVerificationMode,
    verificationStatus, setVerificationStatus,
    publicKeyPath, setPublicKeyPath,
    publicKeyName, setPublicKeyName,
    uploadProgress, setUploadProgress,
  } = useAppState();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

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

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  // Reset verification status when mode changes
  useEffect(() => {
    setVerificationStatus({ status: 'none' });
  }, [verificationMode, setVerificationStatus]);

  const loadDemo = async () => {
    setDemoLoading(true);
    setUploadProgress({ isUploading: true, progress: 0, status: 'Generating demo flight data...' });
    try {
      setUploadProgress({ isUploading: true, progress: 30, status: 'Processing signals...' });
      const logData = await NativeAnalysis.generateDemoLog(120);
      setUploadProgress({ isUploading: true, progress: 80, status: 'Finalizing...' });
      
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
    } catch (e: any) {
      Alert.alert('Error', `Failed to generate demo log: ${e.message}`);
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
        status: 'Parsing log file...',
        filename: file.name,
      });

      // Use native module to parse log locally
      setUploadProgress({ isUploading: true, progress: 30, status: 'Parsing log structure...', filename: file.name });
      
      try {
        const logData = await NativeAnalysis.parseLog(file.uri);
        setUploadProgress({ isUploading: true, progress: 70, status: 'Processing signals...', filename: file.name });
        
        await AsyncStorage.setItem(`log_${logData.log_id}`, JSON.stringify({
          log_id: logData.log_id,
          filename: file.name,
          upload_date: new Date().toISOString(),
          duration_sec: logData.duration_sec,
          message_types: logData.message_types,
          file_size: file.size || 0,
          is_demo: false,
          signals: logData.signals,
        }));
        
        setCurrentLogId(logData.log_id);
        setCurrentLogName(file.name);
        
        // Run verification if in Certified mode with public key
        if (verificationMode === 'certified' && publicKeyPath) {
          setUploadProgress({ isUploading: true, progress: 85, status: 'Verifying cryptographic signature...', filename: file.name });
          try {
            const verifyResult = await NativeAnalysis.verifyLog(file.uri, publicKeyPath, 'certified');
            setVerificationStatus({
              status: verifyResult.status as 'pass' | 'fail',
              message: verifyResult.error_message || undefined,
              hashChainValid: verifyResult.hash_chain_valid,
              signatureValid: verifyResult.signature_valid,
              algorithm: verifyResult.algorithm || undefined,
              chunksVerified: verifyResult.chunks_verified,
              totalChunks: verifyResult.total_chunks,
            });
          } catch (verifyErr: any) {
            setVerificationStatus({
              status: 'fail',
              message: verifyErr.message || 'Verification failed',
            });
          }
        }
        
        await fetchLogs();
        setUploadProgress({ isUploading: false, progress: 100, status: 'Log loaded successfully!' });
      } catch (parseErr: any) {
        Alert.alert('Parse Error', parseErr.message || 'Failed to parse log file');
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
    // Reset verification when selecting a different log
    setVerificationStatus({ status: 'none' });
  };

  const deleteLog = async (logId: string) => {
    try {
      await AsyncStorage.removeItem(`log_${logId}`);
      if (currentLogId === logId) {
        setCurrentLogId(null);
        setCurrentLogName('');
        setVerificationStatus({ status: 'none' });
      }
      await fetchLogs();
    } catch (e) {
      console.error('Failed to delete log:', e);
    }
  };

  const pickPublicKey = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: '*/*',
        copyToCacheDirectory: true,
      });
      if (result.canceled || !result.assets?.[0]) return;
      
      const file = result.assets[0];
      setPublicKeyPath(file.uri);
      setPublicKeyName(file.name);
      Alert.alert('Public Key Selected', file.name);
    } catch (e: any) {
      Alert.alert('Error', 'Failed to select public key');
    }
  };

  const runVerification = async () => {
    if (!currentLogId || verificationMode !== 'certified') return;
    
    const log = logs.find(l => l.log_id === currentLogId);
    if (!log) return;
    
    setVerificationStatus({ status: 'pending' });
    
    try {
      // Get the log file path from AsyncStorage
      const logDataStr = await AsyncStorage.getItem(`log_${currentLogId}`);
      if (!logDataStr) {
        throw new Error('Log data not found');
      }
      
      // For now, we'll show a message that verification requires the original file
      // In a full implementation, we'd store the file path or re-pick it
      const verifyResult = await NativeAnalysis.verifyLog(
        log.filename, // This would need to be the actual file URI
        publicKeyPath,
        'certified'
      );
      
      setVerificationStatus({
        status: verifyResult.status as 'pass' | 'fail',
        message: verifyResult.error_message || undefined,
        hashChainValid: verifyResult.hash_chain_valid,
        signatureValid: verifyResult.signature_valid,
        algorithm: verifyResult.algorithm || undefined,
        chunksVerified: verifyResult.chunks_verified,
        totalChunks: verifyResult.total_chunks,
      });
    } catch (e: any) {
      setVerificationStatus({
        status: 'fail',
        message: e.message || 'Verification failed',
      });
    }
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

  const getModeDescription = (mode: VerificationMode): string => {
    switch (mode) {
      case 'beginner':
        return 'Basic plots & diagnostics only';
      case 'pro':
        return 'Full analysis with FFT, motor harmonics & correlations';
      case 'certified':
        return 'DGCA CS-UAS Clause 7.1 · Ed25519 + Blake2b verification';
    }
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
          <View style={[
            styles.modeBadge,
            verificationMode === 'pro' && styles.modeBadgePro,
            verificationMode === 'certified' && styles.modeBadgeCertified,
          ]}>
            <Ionicons
              name={verificationMode === 'beginner' ? 'school-outline' : verificationMode === 'pro' ? 'construct-outline' : 'shield-checkmark'}
              size={12}
              color={verificationMode === 'certified' ? '#000' : verificationMode === 'pro' ? '#00FF88' : '#007AFF'}
            />
            <Text style={[
              styles.modeText,
              verificationMode === 'pro' && styles.modeTextPro,
              verificationMode === 'certified' && styles.modeTextCertified,
            ]}>
              {verificationMode.toUpperCase()}
            </Text>
          </View>
        </View>

        {/* Verification Status Banner - Only in Certified mode */}
        {verificationMode === 'certified' && verificationStatus.status !== 'none' && (
          <View style={[
            styles.verificationBanner,
            verificationStatus.status === 'pass' && styles.verificationBannerPass,
            verificationStatus.status === 'fail' && styles.verificationBannerFail,
            verificationStatus.status === 'pending' && styles.verificationBannerPending,
          ]}>
            {verificationStatus.status === 'pending' ? (
              <ActivityIndicator color="#FFD700" size="small" />
            ) : (
              <Ionicons
                name={verificationStatus.status === 'pass' ? 'shield-checkmark' : 'warning'}
                size={20}
                color={verificationStatus.status === 'pass' ? '#00FF88' : '#FF3B30'}
              />
            )}
            <View style={styles.verificationBannerContent}>
              <Text style={[
                styles.verificationBannerTitle,
                verificationStatus.status === 'pass' && styles.verificationBannerTitlePass,
                verificationStatus.status === 'fail' && styles.verificationBannerTitleFail,
              ]}>
                {verificationStatus.status === 'pending' ? 'Verifying...' :
                 verificationStatus.status === 'pass' ? 'SIGNATURE VERIFIED' : 'VERIFICATION FAILED'}
              </Text>
              {verificationStatus.message && (
                <Text style={styles.verificationBannerMessage}>{verificationStatus.message}</Text>
              )}
              {verificationStatus.status === 'pass' && (
                <Text style={styles.verificationBannerDetails}>
                  {verificationStatus.algorithm} · {verificationStatus.chunksVerified}/{verificationStatus.totalChunks} chunks
                </Text>
              )}
            </View>
          </View>
        )}

        {/* Verification Mode Selector */}
        <View style={styles.verificationCard}>
          <Text style={styles.sectionLabel}>Verification Level</Text>
          <View style={styles.segmentedControl}>
            <TouchableOpacity
              testID="beginner-mode-btn"
              style={[
                styles.segmentBtn,
                styles.segmentBtnLeft,
                verificationMode === 'beginner' && styles.segmentBtnActive,
              ]}
              onPress={() => setVerificationMode('beginner')}
            >
              <Ionicons
                name="school-outline"
                size={14}
                color={verificationMode === 'beginner' ? '#FFF' : '#A1A1AA'}
              />
              <Text style={[
                styles.segmentText,
                verificationMode === 'beginner' && styles.segmentTextActive,
              ]}>Beginner</Text>
            </TouchableOpacity>
            <TouchableOpacity
              testID="pro-mode-btn"
              style={[
                styles.segmentBtn,
                verificationMode === 'pro' && styles.segmentBtnActive,
              ]}
              onPress={() => setVerificationMode('pro')}
            >
              <Ionicons
                name="construct-outline"
                size={14}
                color={verificationMode === 'pro' ? '#FFF' : '#A1A1AA'}
              />
              <Text style={[
                styles.segmentText,
                verificationMode === 'pro' && styles.segmentTextActive,
              ]}>Pro</Text>
            </TouchableOpacity>
            <TouchableOpacity
              testID="certified-mode-btn"
              style={[
                styles.segmentBtn,
                styles.segmentBtnRight,
                verificationMode === 'certified' && styles.segmentBtnCertified,
              ]}
              onPress={() => setVerificationMode('certified')}
            >
              <Ionicons
                name="shield-checkmark-outline"
                size={14}
                color={verificationMode === 'certified' ? '#000' : '#FFD700'}
              />
              <Text style={[
                styles.segmentText,
                verificationMode === 'certified' && styles.segmentTextCertified,
              ]}>Certified</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.verificationHint}>
            {getModeDescription(verificationMode)}
          </Text>

          {/* Public Key Picker - Only shown in Certified mode */}
          {verificationMode === 'certified' && (
            <View style={styles.publicKeySection}>
              <TouchableOpacity
                testID="pick-pubkey-btn"
                style={styles.pubkeyBtn}
                onPress={pickPublicKey}
              >
                <Ionicons name="key-outline" size={16} color="#FFD700" />
                <Text style={styles.pubkeyBtnText}>
                  {publicKeyPath ? 'Change Public Key' : 'Select Public Key (.dat)'}
                </Text>
              </TouchableOpacity>
              {publicKeyPath && (
                <View style={styles.pubkeySelected}>
                  <Ionicons name="checkmark-circle" size={14} color="#00FF88" />
                  <Text style={styles.pubkeyFileName} numberOfLines={1}>
                    {publicKeyName}
                  </Text>
                </View>
              )}
              {!publicKeyPath && (
                <Text style={styles.pubkeyWarning}>
                  ⚠️ Public key required for certified verification
                </Text>
              )}
            </View>
          )}
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
                    {log.vehicle_type || 'Unknown'} · {formatDuration(log.duration_sec)} · {formatSize(log.file_size)}
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
                {log.message_types?.slice(0, 6).map((t) => (
                  <View key={t} style={styles.tag}>
                    <Text style={styles.tagText}>{t}</Text>
                  </View>
                ))}
                {log.message_types?.length > 6 && (
                  <View style={styles.tag}>
                    <Text style={styles.tagText}>+{log.message_types.length - 6}</Text>
                  </View>
                )}
              </View>
              {log.total_messages && (
                <Text style={styles.logSamples}>
                  {log.total_messages.toLocaleString()} total samples · {log.message_types?.length || 0} message types
                </Text>
              )}
            </TouchableOpacity>
          ))}
        </View>

        {/* Info Section for Beginners */}
        {verificationMode === 'beginner' && (
          <View style={styles.infoCard}>
            <Ionicons name="information-circle-outline" size={20} color="#007AFF" />
            <View style={styles.infoContent}>
              <Text style={styles.infoTitle}>Getting Started</Text>
              <Text style={styles.infoText}>
                1. Load a demo flight or upload your .BIN log{"\n"}
                2. Go to Analysis tab to see flight data plots{"\n"}
                3. Check Health tab for automatic diagnostics{"\n"}
                4. Switch to Pro mode to unlock FFT & Advanced analysis
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
  modeBadgeCertified: { borderColor: 'rgba(255,215,0,0.5)', backgroundColor: '#FFD700' },
  modeText: { color: '#007AFF', fontSize: 10, fontWeight: '700', letterSpacing: 1 },
  modeTextPro: { color: '#00FF88' },
  modeTextCertified: { color: '#000' },
  
  // Verification Banner
  verificationBanner: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#0A0A0A', borderWidth: 1, borderColor: '#27272A', borderRadius: 12, padding: 14, marginBottom: 16, gap: 12 },
  verificationBannerPass: { borderColor: 'rgba(0,255,136,0.4)', backgroundColor: 'rgba(0,255,136,0.08)' },
  verificationBannerFail: { borderColor: 'rgba(255,59,48,0.4)', backgroundColor: 'rgba(255,59,48,0.08)' },
  verificationBannerPending: { borderColor: 'rgba(255,215,0,0.4)', backgroundColor: 'rgba(255,215,0,0.08)' },
  verificationBannerContent: { flex: 1 },
  verificationBannerTitle: { color: '#A1A1AA', fontSize: 12, fontWeight: '700', letterSpacing: 1 },
  verificationBannerTitlePass: { color: '#00FF88' },
  verificationBannerTitleFail: { color: '#FF3B30' },
  verificationBannerMessage: { color: '#A1A1AA', fontSize: 11, marginTop: 4 },
  verificationBannerDetails: { color: '#52525B', fontSize: 10, marginTop: 2 },
  
  // Verification Mode
  verificationCard: { backgroundColor: '#0A0A0A', borderWidth: 1, borderColor: '#27272A', borderRadius: 12, padding: 14, marginBottom: 16 },
  sectionLabel: { color: '#A1A1AA', fontSize: 11, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 10 },
  segmentedControl: { flexDirection: 'row', borderRadius: 8, overflow: 'hidden' },
  segmentBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#171717', borderWidth: 1, borderColor: '#27272A', paddingVertical: 10, gap: 4 },
  segmentBtnLeft: { borderTopLeftRadius: 8, borderBottomLeftRadius: 8 },
  segmentBtnRight: { borderTopRightRadius: 8, borderBottomRightRadius: 8 },
  segmentBtnActive: { backgroundColor: '#007AFF', borderColor: '#007AFF' },
  segmentBtnCertified: { backgroundColor: '#FFD700', borderColor: '#FFD700' },
  segmentText: { color: '#A1A1AA', fontSize: 11, fontWeight: '600' },
  segmentTextActive: { color: '#FFF' },
  segmentTextCertified: { color: '#000', fontWeight: '700' },
  verificationHint: { color: '#52525B', fontSize: 11, marginTop: 10, lineHeight: 16 },
  publicKeySection: { marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#27272A' },
  pubkeyBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,215,0,0.1)', borderWidth: 1, borderColor: 'rgba(255,215,0,0.3)', borderRadius: 8, paddingVertical: 10, gap: 8 },
  pubkeyBtnText: { color: '#FFD700', fontSize: 13, fontWeight: '600' },
  pubkeySelected: { flexDirection: 'row', alignItems: 'center', marginTop: 8, gap: 6 },
  pubkeyFileName: { color: '#00FF88', fontSize: 12, flex: 1 },
  pubkeyWarning: { color: '#FF6B6B', fontSize: 11, marginTop: 8 },
  
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
