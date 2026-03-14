import React, { useRef, useEffect, useState } from 'react';
import { View, StyleSheet, ActivityIndicator, Text, Platform } from 'react-native';
import { WebView } from 'react-native-webview';

interface PlotlyTrace {
  x: number[];
  y: number[];
  name?: string;
  type?: string;
  mode?: string;
  line?: { color?: string; width?: number };
  marker?: { color?: string; size?: number };
  [key: string]: any;
}

interface PlotlyLayout {
  title?: string;
  xaxis?: any;
  yaxis?: any;
  [key: string]: any;
}

interface PlotlyChartProps {
  traces: PlotlyTrace[];
  layout?: PlotlyLayout;
  height?: number;
  testID?: string;
}

const CHART_COLORS = ['#007AFF', '#FF3B30', '#00FF88', '#FF9500', '#BF5AF2', '#FF6B6B', '#4ECDC4', '#45B7D1'];

const DEFAULT_LAYOUT: PlotlyLayout = {
  paper_bgcolor: '#0A0A0A',
  plot_bgcolor: '#0A0A0A',
  font: { color: '#A1A1AA', size: 11 },
  margin: { l: 50, r: 20, t: 30, b: 40 },
  xaxis: {
    gridcolor: '#27272A',
    zerolinecolor: '#3F3F46',
    title: { text: 'Time (s)', font: { size: 11 } },
  },
  yaxis: {
    gridcolor: '#27272A',
    zerolinecolor: '#3F3F46',
  },
  legend: {
    bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#A1A1AA', size: 10 },
    orientation: 'h',
    y: 1.12,
  },
  hovermode: 'x unified',
  dragmode: 'zoom',
};

export default function PlotlyChart({ traces, layout, height = 300, testID }: PlotlyChartProps) {
  const [loading, setLoading] = useState(true);

  // Apply default colors to traces
  const coloredTraces = traces.map((trace, i) => ({
    ...trace,
    line: { color: CHART_COLORS[i % CHART_COLORS.length], width: 1.5, ...(trace.line || {}) },
  }));

  const mergedLayout = { ...DEFAULT_LAYOUT, ...layout, height: height - 10 };

  const html = `<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0">
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0A0A0A;overflow:hidden}#chart{width:100vw;height:${height - 10}px}</style>
</head><body>
<div id="chart"></div>
<script>
try {
  var traces=${JSON.stringify(coloredTraces)};
  var layout=${JSON.stringify(mergedLayout)};
  Plotly.newPlot('chart',traces,layout,{responsive:true,scrollZoom:true,displayModeBar:true,modeBarButtonsToRemove:['lasso2d','select2d','toImage'],displaylogo:false});
  window.ReactNativeWebView&&window.ReactNativeWebView.postMessage(JSON.stringify({type:'ready'}));
} catch(e) {
  document.body.innerHTML='<p style="color:#FF3B30;padding:20px">Chart error: '+e.message+'</p>';
}
</script>
</body></html>`;

  if (Platform.OS === 'web') {
    return (
      <View style={[styles.container, { height }]} testID={testID}>
        <iframe
          srcDoc={html}
          style={{ width: '100%', height: '100%', border: 'none', backgroundColor: '#0A0A0A' }}
          sandbox="allow-scripts"
        />
      </View>
    );
  }

  return (
    <View style={[styles.container, { height }]} testID={testID}>
      {loading && (
        <View style={styles.loading}>
          <ActivityIndicator color="#007AFF" />
          <Text style={styles.loadingText}>Loading chart...</Text>
        </View>
      )}
      <WebView
        source={{ html }}
        style={{ flex: 1, backgroundColor: '#0A0A0A', opacity: loading ? 0 : 1 }}
        javaScriptEnabled
        domStorageEnabled
        originWhitelist={['*']}
        onMessage={(event) => {
          try {
            const msg = JSON.parse(event.nativeEvent.data);
            if (msg.type === 'ready') setLoading(false);
          } catch {}
        }}
        onLoadEnd={() => setTimeout(() => setLoading(false), 2000)}
        scrollEnabled={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { backgroundColor: '#0A0A0A', borderRadius: 8, overflow: 'hidden', borderWidth: 1, borderColor: '#27272A' },
  loading: { ...StyleSheet.absoluteFillObject, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0A0A0A', zIndex: 10 },
  loadingText: { color: '#A1A1AA', fontSize: 12, marginTop: 8 },
});
