import { Stack } from 'expo-router';
import { AppProvider } from '../components/AppContext';
import { StatusBar } from 'expo-status-bar';
import { View, StyleSheet } from 'react-native';

export default function RootLayout() {
  return (
    <AppProvider>
      <View style={styles.root}>
        <StatusBar style="light" />
        <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: '#050505' } }}>
          <Stack.Screen name="(tabs)" />
        </Stack>
      </View>
    </AppProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#050505' },
});
