import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  ActivityIndicator, SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAppState } from '../../components/AppContext';

const API = process.env.EXPO_PUBLIC_BACKEND_URL;

interface DiagCheck {
  name: string;
  category: string;
  status: 'good' | 'warning' | 'critical';
  severity: number;
  value: number;
  threshold: number;
  explanation: string;
  fix: string;
  beginner_text: string;
}

interface DiagResult {
  health_score: number;
  total_checks: number;
  critical: number;
  warnings: number;
  passed: number;
  checks: DiagCheck[];
}

interface AIInsight {
  insights: string;
  error?: string;
}

export default function DiagnosticsScreen() {
  const { currentLogId, mode } = useAppState();
  const [diagnostics, setDiagnostics] = useState<DiagResult | null>(null);
  const [aiInsights, setAiInsights] = useState<AIInsight | null>(null);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    if (currentLogId) loadDiagnostics();
    else { setDiagnostics(null); setAiInsights(null); }
  }, [currentLogId]);

  const loadDiagnostics = async () => {
    if (!currentLogId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/logs/${currentLogId}/diagnostics`);
      if (res.ok) {
        const data = await res.json();
        setDiagnostics(data.diagnostics);
      }
    } catch (e) {
      console.error('Diagnostics failed:', e);
    }
    setLoading(false);
  };

  const getAIInsights = async () => {
    if (!currentLogId) return;
    setAiLoading(true);
    try {
      const res = await fetch(`${API}/api/logs/${currentLogId}/ai-insights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context: null }),
      });
      if (res.ok) {
        const data = await res.json();
        setAiInsights(data.insights);
      }
    } catch (e) {
      console.error('AI insights failed:', e);
    }
    setAiLoading(false);
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case 'good': return { name: 'checkmark-circle' as const, color: '#00FF88' };
      case 'warning': return { name: 'warning' as const, color: '#FF9500' };
      case 'critical': return { name: 'alert-circle' as const, color: '#FF3B30' };
      default: return { name: 'help-circle' as const, color: '#52525B' };
    }
  };

  const scoreColor = (score: number) => {
    if (score >= 80) return '#00FF88';
    if (score >= 50) return '#FF9500';
    return '#FF3B30';
  };

  if (!currentLogId) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.emptyContainer}>
          <Ionicons name="shield-checkmark-outline" size={56} color="#3F3F46" />
          <Text style={styles.emptyTitle}>No Log Selected</Text>
          <Text style={styles.emptyHint}>Load a log to see flight health diagnostics</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.title}>
          {mode === 'beginner' ? 'Flight Health Report' : 'Flight Diagnostics'}
        </Text>

        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator color="#007AFF" size="large" />
            <Text style={styles.loadingText}>Analyzing flight data...</Text>
          </View>
        ) : diagnostics ? (
          <>
            {/* Health Score */}
            <View style={styles.scoreCard}>
              <Text style={[styles.scoreNumber, { color: scoreColor(diagnostics.health_score) }]}>
                {diagnostics.health_score}
              </Text>
              <Text style={styles.scoreLabel}>Health Score</Text>
              <View style={styles.scoreStats}>
                <View style={styles.statItem}>
                  <View style={[styles.statDot, { backgroundColor: '#FF3B30' }]} />
                  <Text style={styles.statText}>{diagnostics.critical} Critical</Text>
                </View>
                <View style={styles.statItem}>
                  <View style={[styles.statDot, { backgroundColor: '#FF9500' }]} />
                  <Text style={styles.statText}>{diagnostics.warnings} Warnings</Text>
                </View>
                <View style={styles.statItem}>
                  <View style={[styles.statDot, { backgroundColor: '#00FF88' }]} />
                  <Text style={styles.statText}>{diagnostics.passed} Passed</Text>
                </View>
              </View>
            </View>

            {/* Diagnostic Checks */}
            {diagnostics.checks.map((check, i) => {
              const icon = statusIcon(check.status);
              return (
                <View key={i} testID={`diag-check-${i}`} style={styles.checkCard}>
                  <View style={styles.checkHeader}>
                    <Ionicons name={icon.name} size={20} color={icon.color} />
                    <View style={styles.checkInfo}>
                      <Text style={styles.checkName}>{check.name}</Text>
                      <Text style={styles.checkCategory}>{check.category}</Text>
                    </View>
                    <View style={[styles.severityBadge, { backgroundColor: icon.color + '20' }]}>
                      <Text style={[styles.severityText, { color: icon.color }]}>
                        {check.severity}/10
                      </Text>
                    </View>
                  </View>
                  <Text style={styles.checkExplanation}>
                    {mode === 'beginner' ? check.beginner_text : check.explanation}
                  </Text>
                  {check.status !== 'good' && (
                    <View style={styles.fixBox}>
                      <Ionicons name="build-outline" size={12} color="#007AFF" />
                      <Text style={styles.fixText}>{check.fix}</Text>
                    </View>
                  )}
                </View>
              );
            })}

            {/* AI Insights Button */}
            <TouchableOpacity
              testID="get-ai-insights-btn"
              style={styles.aiBtn}
              onPress={getAIInsights}
              disabled={aiLoading}
            >
              {aiLoading ? (
                <ActivityIndicator color="#FFF" size="small" />
              ) : (
                <>
                  <Ionicons name="sparkles-outline" size={18} color="#FFF" />
                  <Text style={styles.aiBtnText}>Get AI Analysis (GPT-5.2)</Text>
                </>
              )}
            </TouchableOpacity>

            {/* AI Insights Display */}
            {aiInsights && (
              <View style={styles.aiCard}>
                <View style={styles.aiHeader}>
                  <Ionicons name="sparkles" size={16} color="#BF5AF2" />
                  <Text style={styles.aiTitle}>AI Flight Analysis</Text>
                </View>
                <Text style={styles.aiContent}>
                  {aiInsights.insights || aiInsights.error || 'No insights available'}
                </Text>
              </View>
            )}
          </>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#050505' },
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 32 },
  title: { color: '#FFFFFF', fontSize: 20, fontWeight: '700', marginBottom: 16, marginTop: 8 },
  loadingContainer: { alignItems: 'center', paddingVertical: 60 },
  loadingText: { color: '#A1A1AA', fontSize: 14, marginTop: 12 },
  scoreCard: { alignItems: 'center', backgroundColor: '#0A0A0A', borderWidth: 1, borderColor: '#27272A', borderRadius: 16, padding: 24, marginBottom: 20 },
  scoreNumber: { fontSize: 64, fontWeight: '800', letterSpacing: -2 },
  scoreLabel: { color: '#52525B', fontSize: 14, fontWeight: '500', marginTop: 4 },
  scoreStats: { flexDirection: 'row', gap: 16, marginTop: 16 },
  statItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  statDot: { width: 6, height: 6, borderRadius: 3 },
  statText: { color: '#A1A1AA', fontSize: 12, fontWeight: '500' },
  checkCard: { backgroundColor: '#0A0A0A', borderWidth: 1, borderColor: '#27272A', borderRadius: 12, padding: 14, marginBottom: 10 },
  checkHeader: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 },
  checkInfo: { flex: 1 },
  checkName: { color: '#FFFFFF', fontSize: 14, fontWeight: '600' },
  checkCategory: { color: '#52525B', fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 1 },
  severityBadge: { borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  severityText: { fontSize: 11, fontWeight: '700' },
  checkExplanation: { color: '#A1A1AA', fontSize: 13, lineHeight: 18 },
  fixBox: { flexDirection: 'row', alignItems: 'flex-start', gap: 6, marginTop: 8, backgroundColor: 'rgba(0,122,255,0.06)', borderRadius: 6, padding: 8 },
  fixText: { color: '#007AFF', fontSize: 12, flex: 1, lineHeight: 16 },
  aiBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#BF5AF2', borderRadius: 10, height: 48, gap: 8, marginTop: 10, marginBottom: 16 },
  aiBtnText: { color: '#FFF', fontWeight: '600', fontSize: 14 },
  aiCard: { backgroundColor: '#0A0A0A', borderWidth: 1, borderColor: 'rgba(191,90,242,0.3)', borderRadius: 12, padding: 14 },
  aiHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 10 },
  aiTitle: { color: '#BF5AF2', fontSize: 14, fontWeight: '600' },
  aiContent: { color: '#A1A1AA', fontSize: 13, lineHeight: 20 },
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyTitle: { color: '#A1A1AA', fontSize: 18, fontWeight: '600', marginTop: 16 },
  emptyHint: { color: '#52525B', fontSize: 13, textAlign: 'center', marginTop: 6 },
});
