import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { View, StyleSheet } from 'react-native';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

function TabIcon({ name, color }: { name: IconName; color: string }) {
  return <Ionicons name={name} size={22} color={color} />;
}

export default function TabLayout() {
  return (
    <View style={styles.container}>
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: '#0A0A0A',
            borderTopColor: '#27272A',
            borderTopWidth: 1,
            height: 60,
            paddingBottom: 8,
            paddingTop: 4,
          },
          tabBarActiveTintColor: '#007AFF',
          tabBarInactiveTintColor: '#52525B',
          tabBarLabelStyle: { fontSize: 10, fontWeight: '600' },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: 'Dashboard',
            tabBarIcon: ({ color }) => <TabIcon name="grid-outline" color={color} />,
          }}
        />
        <Tabs.Screen
          name="analysis"
          options={{
            title: 'Analysis',
            tabBarIcon: ({ color }) => <TabIcon name="analytics-outline" color={color} />,
          }}
        />
        <Tabs.Screen
          name="fft"
          options={{
            title: 'FFT',
            tabBarIcon: ({ color }) => <TabIcon name="bar-chart-outline" color={color} />,
          }}
        />
        <Tabs.Screen
          name="diagnostics"
          options={{
            title: 'Health',
            tabBarIcon: ({ color }) => <TabIcon name="shield-checkmark-outline" color={color} />,
          }}
        />
        <Tabs.Screen
          name="data"
          options={{
            title: 'Data',
            tabBarIcon: ({ color }) => <TabIcon name="document-text-outline" color={color} />,
          }}
        />
        <Tabs.Screen
          name="advanced"
          options={{
            title: 'Advanced',
            tabBarIcon: ({ color }) => <TabIcon name="speedometer-outline" color={color} />,
          }}
        />
      </Tabs>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#050505' },
});
