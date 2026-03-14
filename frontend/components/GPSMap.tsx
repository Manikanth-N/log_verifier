import React from 'react';
import { View, StyleSheet, Dimensions, Platform } from 'react-native';
import { WebView } from 'react-native-webview';

interface GPSPoint {
  lat: number;
  lng: number;
  alt?: number;
  time?: number;
}

interface GPSMapProps {
  points: GPSPoint[];
  height?: number;
  showPath?: boolean;
  showMarkers?: boolean;
}

export default function GPSMap({ points, height = 400, showPath = true, showMarkers = true }: GPSMapProps) {
  if (points.length === 0) {
    return <View style={[styles.container, { height }]} />;
  }

  // Calculate center
  const centerLat = points.reduce((sum, p) => sum + p.lat, 0) / points.length;
  const centerLng = points.reduce((sum, p) => sum + p.lng, 0) / points.length;

  // Generate HTML with Leaflet
  const mapHTML = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <style>
        body { margin: 0; padding: 0; }
        #map { width: 100%; height: 100vh; background: #0A0A0A; }
        .leaflet-container { background: #0A0A0A !important; }
        .leaflet-tile { filter: brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.3) brightness(0.7); }
      </style>
    </head>
    <body>
      <div id="map"></div>
      <script>
        const points = ${JSON.stringify(points)};
        const map = L.map('map').setView([${centerLat}, ${centerLng}], 16);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap'
        }).addTo(map);

        // Draw path
        ${showPath ? `
        const pathCoords = points.map(p => [p.lat, p.lng]);
        L.polyline(pathCoords, {
          color: '#007AFF',
          weight: 3,
          opacity: 0.8
        }).addTo(map);
        ` : ''}

        // Add markers
        ${showMarkers ? `
        if (points.length > 0) {
          // Start marker
          L.circleMarker([points[0].lat, points[0].lng], {
            radius: 8,
            color: '#00FF88',
            fillColor: '#00FF88',
            fillOpacity: 0.8,
            weight: 2
          }).addTo(map).bindPopup('Start');
          
          // End marker
          if (points.length > 1) {
            const last = points[points.length - 1];
            L.circleMarker([last.lat, last.lng], {
              radius: 8,
              color: '#FF3B30',
              fillColor: '#FF3B30',
              fillOpacity: 0.8,
              weight: 2
            }).addTo(map).bindPopup('End');
          }
        }
        ` : ''}

        // Fit bounds
        if (points.length > 1) {
          const bounds = L.latLngBounds(points.map(p => [p.lat, p.lng]));
          map.fitBounds(bounds, { padding: [20, 20] });
        }
      </script>
    </body>
    </html>
  `;

  return (
    <View style={[styles.container, { height }]}>
      <WebView
        source={{ html: mapHTML }}
        style={styles.webview}
        javaScriptEnabled
        domStorageEnabled
        scrollEnabled={false}
        scalesPageToFit
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#0A0A0A',
    borderWidth: 1,
    borderColor: '#27272A',
  },
  webview: {
    flex: 1,
    backgroundColor: 'transparent',
  },
});
