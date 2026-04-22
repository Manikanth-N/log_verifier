/**
 * Analysis Templates
 * 
 * Pre-built graph configurations similar to review.px4.io
 * Templates define which signals to display and how to lay them out.
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export interface SignalConfig {
  type: string;
  field: string;
  label: string;
  color: string;
  unit?: string;
  yAxisId?: string;
}

export interface PlotConfig {
  title: string;
  signals: SignalConfig[];
  height?: number;
  showLegend?: boolean;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'flight' | 'sensors' | 'motors' | 'ekf' | 'power' | 'custom';
  plots: PlotConfig[];
  requiredSignals: string[];
}

// ==================== Pre-built Templates ====================

export const TEMPLATES: Template[] = [
  // Attitude Template
  {
    id: 'attitude',
    name: 'Attitude',
    description: 'Roll, Pitch, Yaw and desired vs actual',
    icon: 'compass-outline',
    category: 'flight',
    requiredSignals: ['ATT'],
    plots: [
      {
        title: 'Roll',
        signals: [
          { type: 'ATT', field: 'Roll', label: 'Actual Roll', color: '#007AFF', unit: '°' },
          { type: 'ATT', field: 'DesRoll', label: 'Desired Roll', color: '#FF9500', unit: '°' },
        ],
      },
      {
        title: 'Pitch',
        signals: [
          { type: 'ATT', field: 'Pitch', label: 'Actual Pitch', color: '#007AFF', unit: '°' },
          { type: 'ATT', field: 'DesPitch', label: 'Desired Pitch', color: '#FF9500', unit: '°' },
        ],
      },
      {
        title: 'Yaw',
        signals: [
          { type: 'ATT', field: 'Yaw', label: 'Actual Yaw', color: '#007AFF', unit: '°' },
          { type: 'ATT', field: 'DesYaw', label: 'Desired Yaw', color: '#FF9500', unit: '°' },
        ],
      },
    ],
  },

  // Vibration Template
  {
    id: 'vibration',
    name: 'Vibration',
    description: 'IMU vibration levels and clipping',
    icon: 'pulse-outline',
    category: 'sensors',
    requiredSignals: ['VIBE', 'IMU'],
    plots: [
      {
        title: 'Vibration Levels',
        signals: [
          { type: 'VIBE', field: 'VibeX', label: 'Vibe X', color: '#FF3B30', unit: 'm/s²' },
          { type: 'VIBE', field: 'VibeY', label: 'Vibe Y', color: '#34C759', unit: 'm/s²' },
          { type: 'VIBE', field: 'VibeZ', label: 'Vibe Z', color: '#007AFF', unit: 'm/s²' },
        ],
      },
      {
        title: 'Accelerometer (Raw)',
        signals: [
          { type: 'IMU', field: 'AccX', label: 'Accel X', color: '#FF3B30', unit: 'm/s²' },
          { type: 'IMU', field: 'AccY', label: 'Accel Y', color: '#34C759', unit: 'm/s²' },
          { type: 'IMU', field: 'AccZ', label: 'Accel Z', color: '#007AFF', unit: 'm/s²' },
        ],
      },
      {
        title: 'Clipping Events',
        signals: [
          { type: 'VIBE', field: 'Clip0', label: 'IMU0 Clips', color: '#FF9500', unit: 'count' },
          { type: 'VIBE', field: 'Clip1', label: 'IMU1 Clips', color: '#5856D6', unit: 'count' },
          { type: 'VIBE', field: 'Clip2', label: 'IMU2 Clips', color: '#FF2D55', unit: 'count' },
        ],
      },
    ],
  },

  // Motors Template
  {
    id: 'motors',
    name: 'Motors',
    description: 'Motor outputs and PWM values',
    icon: 'cog-outline',
    category: 'motors',
    requiredSignals: ['RCOU'],
    plots: [
      {
        title: 'Motor Outputs (PWM)',
        signals: [
          { type: 'RCOU', field: 'C1', label: 'Motor 1', color: '#FF3B30', unit: 'µs' },
          { type: 'RCOU', field: 'C2', label: 'Motor 2', color: '#34C759', unit: 'µs' },
          { type: 'RCOU', field: 'C3', label: 'Motor 3', color: '#007AFF', unit: 'µs' },
          { type: 'RCOU', field: 'C4', label: 'Motor 4', color: '#FF9500', unit: 'µs' },
        ],
      },
      {
        title: 'Motors 5-8 (if present)',
        signals: [
          { type: 'RCOU', field: 'C5', label: 'Motor 5', color: '#5856D6', unit: 'µs' },
          { type: 'RCOU', field: 'C6', label: 'Motor 6', color: '#FF2D55', unit: 'µs' },
          { type: 'RCOU', field: 'C7', label: 'Motor 7', color: '#AF52DE', unit: 'µs' },
          { type: 'RCOU', field: 'C8', label: 'Motor 8', color: '#00C7BE', unit: 'µs' },
        ],
      },
    ],
  },

  // GPS Template
  {
    id: 'gps',
    name: 'GPS',
    description: 'GPS position, speed, and accuracy',
    icon: 'navigate-outline',
    category: 'flight',
    requiredSignals: ['GPS'],
    plots: [
      {
        title: 'Altitude',
        signals: [
          { type: 'GPS', field: 'Alt', label: 'GPS Altitude', color: '#007AFF', unit: 'm' },
          { type: 'GPS', field: 'RAlt', label: 'Rel Altitude', color: '#34C759', unit: 'm' },
        ],
      },
      {
        title: 'Speed',
        signals: [
          { type: 'GPS', field: 'Spd', label: 'Ground Speed', color: '#FF9500', unit: 'm/s' },
        ],
      },
      {
        title: 'GPS Quality',
        signals: [
          { type: 'GPS', field: 'NSats', label: 'Satellites', color: '#007AFF', unit: '' },
          { type: 'GPS', field: 'HDop', label: 'HDOP', color: '#FF3B30', unit: '' },
        ],
      },
    ],
  },

  // Battery Template
  {
    id: 'battery',
    name: 'Battery',
    description: 'Voltage, current, and power consumption',
    icon: 'battery-half-outline',
    category: 'power',
    requiredSignals: ['BAT', 'CURR'],
    plots: [
      {
        title: 'Battery Voltage',
        signals: [
          { type: 'BAT', field: 'Volt', label: 'Voltage', color: '#34C759', unit: 'V' },
          { type: 'BAT', field: 'VoltR', label: 'Resting Volt', color: '#007AFF', unit: 'V' },
        ],
      },
      {
        title: 'Current Draw',
        signals: [
          { type: 'BAT', field: 'Curr', label: 'Current', color: '#FF9500', unit: 'A' },
        ],
      },
      {
        title: 'Power & Consumed',
        signals: [
          { type: 'BAT', field: 'CurrTot', label: 'mAh Used', color: '#FF3B30', unit: 'mAh' },
        ],
      },
    ],
  },

  // EKF Template
  {
    id: 'ekf',
    name: 'EKF',
    description: 'Extended Kalman Filter health and innovations',
    icon: 'analytics-outline',
    category: 'ekf',
    requiredSignals: ['EKF', 'NKF'],
    plots: [
      {
        title: 'Velocity Innovations',
        signals: [
          { type: 'NKF4', field: 'SV', label: 'Vel Innov', color: '#007AFF', unit: 'm/s' },
          { type: 'NKF4', field: 'SP', label: 'Pos Innov', color: '#FF9500', unit: 'm' },
        ],
      },
      {
        title: 'Compass Variance',
        signals: [
          { type: 'NKF4', field: 'SMX', label: 'Mag X Innov', color: '#FF3B30', unit: '' },
          { type: 'NKF4', field: 'SMY', label: 'Mag Y Innov', color: '#34C759', unit: '' },
          { type: 'NKF4', field: 'SMZ', label: 'Mag Z Innov', color: '#007AFF', unit: '' },
        ],
      },
      {
        title: 'EKF Flags',
        signals: [
          { type: 'NKF4', field: 'PI', label: 'Pos Innov', color: '#5856D6', unit: '' },
        ],
      },
    ],
  },

  // RC Input Template
  {
    id: 'rc_input',
    name: 'RC Input',
    description: 'Radio control stick inputs',
    icon: 'game-controller-outline',
    category: 'flight',
    requiredSignals: ['RCIN'],
    plots: [
      {
        title: 'Stick Inputs',
        signals: [
          { type: 'RCIN', field: 'C1', label: 'Roll', color: '#FF3B30', unit: 'µs' },
          { type: 'RCIN', field: 'C2', label: 'Pitch', color: '#34C759', unit: 'µs' },
          { type: 'RCIN', field: 'C3', label: 'Throttle', color: '#007AFF', unit: 'µs' },
          { type: 'RCIN', field: 'C4', label: 'Yaw', color: '#FF9500', unit: 'µs' },
        ],
      },
      {
        title: 'Aux Channels',
        signals: [
          { type: 'RCIN', field: 'C5', label: 'Ch 5', color: '#5856D6', unit: 'µs' },
          { type: 'RCIN', field: 'C6', label: 'Ch 6', color: '#FF2D55', unit: 'µs' },
          { type: 'RCIN', field: 'C7', label: 'Ch 7', color: '#AF52DE', unit: 'µs' },
          { type: 'RCIN', field: 'C8', label: 'Ch 8', color: '#00C7BE', unit: 'µs' },
        ],
      },
    ],
  },

  // Gyroscope Template
  {
    id: 'gyro',
    name: 'Gyroscope',
    description: 'Angular rates from IMU gyroscopes',
    icon: 'sync-outline',
    category: 'sensors',
    requiredSignals: ['IMU'],
    plots: [
      {
        title: 'Angular Rates',
        signals: [
          { type: 'IMU', field: 'GyrX', label: 'Gyro X (Roll)', color: '#FF3B30', unit: 'rad/s' },
          { type: 'IMU', field: 'GyrY', label: 'Gyro Y (Pitch)', color: '#34C759', unit: 'rad/s' },
          { type: 'IMU', field: 'GyrZ', label: 'Gyro Z (Yaw)', color: '#007AFF', unit: 'rad/s' },
        ],
      },
    ],
  },
];

// ==================== Template Selector Component ====================

interface TemplateSelectorProps {
  selectedTemplate: Template | null;
  onSelectTemplate: (template: Template) => void;
  availableSignals?: string[];
}

export function TemplateSelector({ 
  selectedTemplate, 
  onSelectTemplate,
  availableSignals = [],
}: TemplateSelectorProps) {
  const categories = [
    { id: 'flight', label: 'Flight', icon: 'airplane-outline' },
    { id: 'sensors', label: 'Sensors', icon: 'speedometer-outline' },
    { id: 'motors', label: 'Motors', icon: 'cog-outline' },
    { id: 'power', label: 'Power', icon: 'battery-half-outline' },
    { id: 'ekf', label: 'EKF', icon: 'analytics-outline' },
  ];

  const isTemplateAvailable = (template: Template): boolean => {
    if (availableSignals.length === 0) return true;
    return template.requiredSignals.some(sig => 
      availableSignals.some(avail => avail.startsWith(sig))
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Analysis Templates</Text>
      <Text style={styles.subtitle}>Quick views for common analysis tasks</Text>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryRow}>
        {categories.map(cat => (
          <View key={cat.id} style={styles.categoryChip}>
            <Ionicons name={cat.icon as any} size={12} color="#A1A1AA" />
            <Text style={styles.categoryText}>{cat.label}</Text>
          </View>
        ))}
      </ScrollView>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.templateScroll}>
        {TEMPLATES.map(template => {
          const available = isTemplateAvailable(template);
          const isSelected = selectedTemplate?.id === template.id;
          
          return (
            <TouchableOpacity
              key={template.id}
              testID={`template-${template.id}`}
              style={[
                styles.templateCard,
                isSelected && styles.templateCardSelected,
                !available && styles.templateCardDisabled,
              ]}
              onPress={() => available && onSelectTemplate(template)}
              disabled={!available}
            >
              <View style={[
                styles.templateIcon,
                isSelected && styles.templateIconSelected,
                !available && styles.templateIconDisabled,
              ]}>
                <Ionicons
                  name={template.icon as any}
                  size={20}
                  color={isSelected ? '#007AFF' : available ? '#A1A1AA' : '#3F3F46'}
                />
              </View>
              <Text style={[
                styles.templateName,
                isSelected && styles.templateNameSelected,
                !available && styles.templateNameDisabled,
              ]}>
                {template.name}
              </Text>
              <Text style={[
                styles.templateDesc,
                !available && styles.templateDescDisabled,
              ]} numberOfLines={2}>
                {template.description}
              </Text>
              {!available && (
                <View style={styles.unavailableBadge}>
                  <Text style={styles.unavailableText}>N/A</Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {selectedTemplate && (
        <View style={styles.selectedInfo}>
          <Ionicons name="checkmark-circle" size={14} color="#007AFF" />
          <Text style={styles.selectedText}>
            {selectedTemplate.name}: {selectedTemplate.plots.length} plots
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  subtitle: {
    color: '#52525B',
    fontSize: 12,
    marginBottom: 12,
  },
  categoryRow: {
    marginBottom: 12,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#171717',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginRight: 6,
    gap: 4,
  },
  categoryText: {
    color: '#A1A1AA',
    fontSize: 10,
    fontWeight: '600',
  },
  templateScroll: {
    marginBottom: 8,
  },
  templateCard: {
    backgroundColor: '#0A0A0A',
    borderWidth: 1,
    borderColor: '#27272A',
    borderRadius: 12,
    padding: 12,
    width: 120,
    marginRight: 10,
  },
  templateCardSelected: {
    borderColor: '#007AFF',
    backgroundColor: 'rgba(0,122,255,0.08)',
  },
  templateCardDisabled: {
    opacity: 0.5,
  },
  templateIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#171717',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  templateIconSelected: {
    backgroundColor: 'rgba(0,122,255,0.15)',
  },
  templateIconDisabled: {
    backgroundColor: '#0F0F0F',
  },
  templateName: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
  },
  templateNameSelected: {
    color: '#007AFF',
  },
  templateNameDisabled: {
    color: '#52525B',
  },
  templateDesc: {
    color: '#52525B',
    fontSize: 10,
    lineHeight: 14,
  },
  templateDescDisabled: {
    color: '#3F3F46',
  },
  unavailableBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#27272A',
    borderRadius: 4,
    paddingHorizontal: 4,
    paddingVertical: 2,
  },
  unavailableText: {
    color: '#52525B',
    fontSize: 8,
    fontWeight: '700',
  },
  selectedInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  selectedText: {
    color: '#007AFF',
    fontSize: 12,
    fontWeight: '500',
  },
});

export default TemplateSelector;
