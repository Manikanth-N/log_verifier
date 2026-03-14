"""
FFT Analysis tests: frequency analysis, spectrogram, peak detection
"""
import pytest


class TestFFTAnalysis:
    """Test FFT endpoint with various configurations"""

    def test_fft_basic(self, base_url, api_client, demo_log_id):
        """Test basic FFT computation"""
        payload = {
            "signal_type": "IMU",
            "signal_field": "GyrZ",
            "window_size": 1024,
            "overlap": 0.5
        }
        response = api_client.post(
            f"{base_url}/api/logs/{demo_log_id}/fft",
            json=payload
        )
        assert response.status_code == 200, f"FFT failed: {response.text}"
        
        data = response.json()
        assert "log_id" in data, "Missing log_id"
        assert "signal" in data, "Missing signal"
        assert "fft" in data, "Missing fft results"
        assert "spectrogram" in data, "Missing spectrogram"
        
        # Verify FFT structure
        fft = data["fft"]
        assert "frequencies" in fft, "Missing frequencies"
        assert "magnitude" in fft, "Missing magnitude"
        assert "psd" in fft, "Missing PSD"
        assert "peaks" in fft, "Missing peaks"
        assert "sample_rate" in fft, "Missing sample_rate"
        assert "nyquist" in fft, "Missing nyquist"
        
        # Verify arrays have data
        assert len(fft["frequencies"]) > 0, "Frequencies array empty"
        assert len(fft["magnitude"]) > 0, "Magnitude array empty"
        assert len(fft["frequencies"]) == len(fft["magnitude"]), "Frequency/magnitude length mismatch"
        
        print(f"✓ FFT: {len(fft['frequencies'])} frequency bins, {len(fft['peaks'])} peaks detected")

    def test_fft_peak_detection(self, base_url, api_client, demo_log_id):
        """Test FFT peak detection returns valid peaks"""
        payload = {
            "signal_type": "IMU",
            "signal_field": "AccZ",
            "window_size": 2048,
            "overlap": 0.5
        }
        response = api_client.post(
            f"{base_url}/api/logs/{demo_log_id}/fft",
            json=payload
        )
        assert response.status_code == 200, f"FFT peak detection failed: {response.text}"
        
        data = response.json()
        peaks = data["fft"]["peaks"]
        
        # Verify peaks structure
        if len(peaks) > 0:
            peak = peaks[0]
            assert "frequency" in peak, "Peak missing frequency"
            assert "magnitude" in peak, "Peak missing magnitude"
            assert "label" in peak, "Peak missing label"
            assert "is_harmonic" in peak, "Peak missing is_harmonic"
            
            # Verify frequency is positive and reasonable
            assert peak["frequency"] > 0, "Peak frequency should be positive"
            assert peak["magnitude"] > 0, "Peak magnitude should be positive"
        
        print(f"✓ FFT peaks: {len(peaks)} peaks detected")

    def test_fft_spectrogram(self, base_url, api_client, demo_log_id):
        """Test spectrogram computation"""
        payload = {
            "signal_type": "VIBE",
            "signal_field": "VibeZ",
            "window_size": 512,
            "overlap": 0.5
        }
        response = api_client.post(
            f"{base_url}/api/logs/{demo_log_id}/fft",
            json=payload
        )
        assert response.status_code == 200, f"Spectrogram failed: {response.text}"
        
        data = response.json()
        spec = data["spectrogram"]
        
        assert "times" in spec, "Spectrogram missing times"
        assert "frequencies" in spec, "Spectrogram missing frequencies"
        assert "power" in spec, "Spectrogram missing power"
        
        # Verify 2D power array
        assert len(spec["power"]) > 0, "Power array should not be empty"
        if len(spec["power"]) > 0:
            assert len(spec["power"][0]) > 0, "Power array should be 2D"
        
        print(f"✓ Spectrogram: {len(spec['frequencies'])} freq bins × {len(spec['times'])} time bins")

    def test_fft_different_signals(self, base_url, api_client, demo_log_id):
        """Test FFT on different signal types"""
        test_signals = [
            ("IMU", "GyrX"),
            ("IMU", "GyrY"),
            ("VIBE", "VibeX"),
        ]
        
        for signal_type, signal_field in test_signals:
            payload = {
                "signal_type": signal_type,
                "signal_field": signal_field,
                "window_size": 1024,
                "overlap": 0.5
            }
            response = api_client.post(
                f"{base_url}/api/logs/{demo_log_id}/fft",
                json=payload
            )
            assert response.status_code == 200, f"FFT failed for {signal_type}.{signal_field}: {response.text}"
            data = response.json()
            assert len(data["fft"]["frequencies"]) > 0, f"No FFT data for {signal_type}.{signal_field}"
        
        print(f"✓ FFT tested on {len(test_signals)} different signals")

    def test_fft_invalid_signal(self, base_url, api_client, demo_log_id):
        """Test FFT with invalid signal type"""
        payload = {
            "signal_type": "NONEXISTENT",
            "signal_field": "Fake",
            "window_size": 1024
        }
        response = api_client.post(
            f"{base_url}/api/logs/{demo_log_id}/fft",
            json=payload
        )
        assert response.status_code == 400, "Should return 400 for invalid signal"
        print("✓ FFT rejects invalid signal types")

    def test_fft_nonexistent_log(self, base_url, api_client):
        """Test FFT on non-existent log"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {
            "signal_type": "IMU",
            "signal_field": "GyrZ",
            "window_size": 1024
        }
        response = api_client.post(f"{base_url}/api/logs/{fake_id}/fft", json=payload)
        assert response.status_code == 404, "Should return 404 for non-existent log"
        print("✓ FFT returns 404 for non-existent log")
