import numpy as np
from typing import Dict, Any, List
import struct
import os


def generate_demo_log() -> Dict[str, Any]:
    """Generate a realistic ArduPilot flight log with intentional anomalies for diagnostics."""
    duration = 120.0
    np.random.seed(42)

    # Time arrays at different rates
    t_fast = np.linspace(0, duration, int(duration * 100))    # 100Hz
    t_med = np.linspace(0, duration, int(duration * 50))      # 50Hz
    t_slow = np.linspace(0, duration, int(duration * 25))     # 25Hz
    t_gps = np.linspace(0, duration, int(duration * 5))       # 5Hz
    t_bat = np.linspace(0, duration, int(duration * 10))      # 10Hz

    # --- Flight Profile ---
    def altitude_profile(t):
        a = np.zeros_like(t)
        # Takeoff 0-15s
        mask = t < 15
        a[mask] = (t[mask] / 15.0) * 30.0
        # Hover 15-40s
        mask = (t >= 15) & (t < 40)
        a[mask] = 30.0 + np.random.normal(0, 0.3, mask.sum())
        # Forward 40-60s
        mask = (t >= 40) & (t < 60)
        prog = (t[mask] - 40) / 20.0
        a[mask] = 30.0 + 5 * np.sin(prog * np.pi)
        # Maneuvers 60-80s
        mask = (t >= 60) & (t < 80)
        prog = (t[mask] - 60) / 20.0
        a[mask] = 35.0 + 10 * np.sin(prog * 4 * np.pi)
        # Return 80-100s
        mask = (t >= 80) & (t < 100)
        prog = (t[mask] - 80) / 20.0
        a[mask] = 35.0 - 5 * prog
        # Land 100-120s
        mask = t >= 100
        prog = (t[mask] - 100) / 20.0
        a[mask] = 30.0 * np.maximum(0, 1 - prog)
        return a

    def throttle_profile(t):
        thr = np.ones_like(t) * 1500
        thr[t < 15] = 1200 + (t[t < 15] / 15.0) * 400
        thr[(t >= 15) & (t < 40)] = 1520 + np.random.normal(0, 10, ((t >= 15) & (t < 40)).sum())
        thr[(t >= 40) & (t < 60)] = 1580 + np.random.normal(0, 15, ((t >= 40) & (t < 60)).sum())
        thr[(t >= 60) & (t < 80)] = 1600 + np.random.normal(0, 30, ((t >= 60) & (t < 80)).sum())
        thr[(t >= 80) & (t < 100)] = 1500 + np.random.normal(0, 10, ((t >= 80) & (t < 100)).sum())
        mask = t >= 100
        prog = (t[mask] - 100) / 20.0
        thr[mask] = 1500 - prog * 400
        return np.clip(thr, 1000, 2000)

    alt = altitude_profile(t_fast)
    thr_fast = throttle_profile(t_fast)
    thr_med = throttle_profile(t_med)

    # --- ATT ---
    roll = np.random.normal(0, 0.8, len(t_fast))
    roll[(t_fast >= 40) & (t_fast < 60)] += np.random.normal(0, 2, ((t_fast >= 40) & (t_fast < 60)).sum())
    maneuver_mask = (t_fast >= 60) & (t_fast < 80)
    prog_m = (t_fast[maneuver_mask] - 60) / 20.0
    roll[maneuver_mask] = 15 * np.sin(prog_m * 6 * np.pi) + np.random.normal(0, 2, maneuver_mask.sum())

    pitch = np.random.normal(0, 0.5, len(t_fast))
    pitch[(t_fast >= 40) & (t_fast < 60)] += -8 + np.random.normal(0, 1, ((t_fast >= 40) & (t_fast < 60)).sum())
    pitch[maneuver_mask] = 10 * np.cos(prog_m * 4 * np.pi) + np.random.normal(0, 1.5, maneuver_mask.sum())

    yaw = np.cumsum(np.random.normal(0, 0.1, len(t_fast)))
    yaw[maneuver_mask] += np.linspace(0, 270, maneuver_mask.sum())
    yaw = yaw % 360

    att = {
        "TimeUS": t_fast.tolist(),
        "Roll": roll.tolist(),
        "DesRoll": (roll + np.random.normal(0, 0.3, len(t_fast))).tolist(),
        "Pitch": pitch.tolist(),
        "DesPitch": (pitch + np.random.normal(0, 0.3, len(t_fast))).tolist(),
        "Yaw": yaw.tolist(),
        "DesYaw": ((yaw + np.random.normal(0, 0.5, len(t_fast))) % 360).tolist(),
        "ErrRP": np.abs(np.random.normal(0, 0.3, len(t_fast))).tolist(),
        "ErrYaw": np.abs(np.random.normal(0, 0.5, len(t_fast))).tolist(),
    }

    # --- IMU ---
    gyr_x = np.gradient(np.radians(roll)) * 100 + np.random.normal(0, 0.01, len(t_fast))
    gyr_y = np.gradient(np.radians(pitch)) * 100 + np.random.normal(0, 0.01, len(t_fast))
    gyr_z = np.gradient(np.radians(yaw)) * 100 + np.random.normal(0, 0.005, len(t_fast))
    acc_x = np.random.normal(0, 0.3, len(t_fast))
    acc_y = np.random.normal(0, 0.3, len(t_fast))
    acc_z = -9.81 + np.random.normal(0, 0.2, len(t_fast))
    # Add motor vibration noise (realistic multi-frequency)
    motor_freq = 120  # Hz - typical motor frequency
    vib_signal = 0.5 * np.sin(2 * np.pi * motor_freq * t_fast) + 0.3 * np.sin(2 * np.pi * 2 * motor_freq * t_fast)
    acc_z += vib_signal * (thr_fast - 1000) / 1000.0

    imu = {
        "TimeUS": t_fast.tolist(),
        "GyrX": gyr_x.tolist(),
        "GyrY": gyr_y.tolist(),
        "GyrZ": gyr_z.tolist(),
        "AccX": acc_x.tolist(),
        "AccY": acc_y.tolist(),
        "AccZ": acc_z.tolist(),
    }

    # --- VIBE ---
    vibe_x = np.abs(np.random.normal(8, 2, len(t_med)))
    vibe_y = np.abs(np.random.normal(8, 2, len(t_med)))
    vibe_z = np.abs(np.random.normal(12, 3, len(t_med)))
    # Intentional vibration spike at 42-48s (prop issue)
    spike_mask = (t_med >= 42) & (t_med <= 48)
    vibe_z[spike_mask] += 25 + np.random.normal(0, 5, spike_mask.sum())
    vibe_x[spike_mask] += 15 + np.random.normal(0, 3, spike_mask.sum())
    clip0 = np.zeros(len(t_med))
    clip1 = np.zeros(len(t_med))
    clip2 = np.zeros(len(t_med))
    clip0[spike_mask] = np.random.randint(0, 3, spike_mask.sum())

    vibe = {
        "TimeUS": t_med.tolist(),
        "VibeX": vibe_x.tolist(),
        "VibeY": vibe_y.tolist(),
        "VibeZ": vibe_z.tolist(),
        "Clip0": clip0.tolist(),
        "Clip1": clip1.tolist(),
        "Clip2": clip2.tolist(),
    }

    # --- GPS ---
    base_lat, base_lng = 47.3977, 8.5456  # Zurich
    lat = base_lat + np.cumsum(np.random.normal(0, 0.00001, len(t_gps)))
    lng = base_lng + np.cumsum(np.random.normal(0, 0.00001, len(t_gps)))
    # Forward flight adds movement
    fwd_mask = (t_gps >= 40) & (t_gps < 60)
    lat[fwd_mask] += np.linspace(0, 0.002, fwd_mask.sum())
    lng[fwd_mask] += np.linspace(0, 0.001, fwd_mask.sum())
    gps_alt = altitude_profile(t_gps) + np.random.normal(0, 0.5, len(t_gps))
    gps_spd = np.abs(np.gradient(lat) * 111000 * 5)  # rough m/s
    nsats = np.random.randint(10, 16, len(t_gps))
    hdop = 0.8 + np.random.exponential(0.2, len(t_gps))
    # GPS glitch at ~70s
    glitch_mask = (t_gps >= 69) & (t_gps <= 72)
    hdop[glitch_mask] = 4.0 + np.random.normal(0, 1, glitch_mask.sum())
    nsats[glitch_mask] = np.random.randint(4, 7, glitch_mask.sum())
    lat[glitch_mask] += 0.005

    gps = {
        "TimeUS": t_gps.tolist(),
        "Status": (np.ones(len(t_gps)) * 3).astype(int).tolist(),
        "NSats": nsats.tolist(),
        "HDop": np.round(hdop, 2).tolist(),
        "Lat": lat.tolist(),
        "Lng": lng.tolist(),
        "Alt": gps_alt.tolist(),
        "Spd": np.round(gps_spd, 2).tolist(),
    }

    # --- BAT ---
    volt = 16.8 - (t_bat / duration) * 2.0 + np.random.normal(0, 0.05, len(t_bat))
    curr = (thr_fast[::int(len(t_fast)/len(t_bat))][:len(t_bat)] - 1000) / 1000.0 * 25 + np.random.normal(0, 0.5, len(t_bat))
    curr = np.clip(curr, 0, 35)
    bat = {
        "TimeUS": t_bat.tolist(),
        "Volt": np.round(volt, 2).tolist(),
        "VoltR": np.round(volt - 0.3, 2).tolist(),
        "Curr": np.round(curr, 2).tolist(),
        "CurrTot": np.round(np.cumsum(curr * 0.1 / 3600) * 1000, 1).tolist(),
        "Temp": (25 + t_bat * 0.05 + np.random.normal(0, 0.5, len(t_bat))).tolist(),
    }

    # --- RCIN ---
    rc_roll = 1500 + (np.interp(t_med, t_fast, roll) * 5).astype(int)
    rc_pitch = 1500 + (np.interp(t_med, t_fast, pitch) * 5).astype(int)
    rc_thr = thr_med.astype(int)
    rc_yaw = 1500 + np.random.randint(-20, 20, len(t_med))
    rcin = {
        "TimeUS": t_med.tolist(),
        "C1": np.clip(rc_roll, 1000, 2000).tolist(),
        "C2": np.clip(rc_pitch, 1000, 2000).tolist(),
        "C3": np.clip(rc_thr, 1000, 2000).tolist(),
        "C4": np.clip(rc_yaw, 1000, 2000).tolist(),
    }

    # --- RCOU (Motor outputs) ---
    base_out = thr_med
    m1 = base_out + np.random.normal(0, 15, len(t_med))
    m2 = base_out + np.random.normal(0, 15, len(t_med))
    m3 = base_out + np.random.normal(0, 15, len(t_med)) + 30  # Motor 3 imbalance
    m4 = base_out + np.random.normal(0, 15, len(t_med))
    rcou = {
        "TimeUS": t_med.tolist(),
        "C1": np.clip(m1, 1000, 2000).astype(int).tolist(),
        "C2": np.clip(m2, 1000, 2000).astype(int).tolist(),
        "C3": np.clip(m3, 1000, 2000).astype(int).tolist(),
        "C4": np.clip(m4, 1000, 2000).astype(int).tolist(),
    }

    # --- BARO ---
    baro_alt = altitude_profile(t_slow) + np.random.normal(0, 0.15, len(t_slow))
    baro = {
        "TimeUS": t_slow.tolist(),
        "Alt": baro_alt.tolist(),
        "Press": (101325 - baro_alt * 12 + np.random.normal(0, 5, len(t_slow))).tolist(),
        "Temp": (25 + np.random.normal(0, 0.3, len(t_slow))).tolist(),
        "CRt": np.gradient(baro_alt).tolist(),
    }

    # --- MAG ---
    mag_x = 200 + np.random.normal(0, 5, len(t_med))
    mag_y = -50 + np.random.normal(0, 5, len(t_med))
    mag_z = 400 + np.random.normal(0, 5, len(t_med))
    mag = {
        "TimeUS": t_med.tolist(),
        "MagX": mag_x.tolist(),
        "MagY": mag_y.tolist(),
        "MagZ": mag_z.tolist(),
        "OfsX": np.random.normal(-10, 1, len(t_med)).tolist(),
        "OfsY": np.random.normal(5, 1, len(t_med)).tolist(),
        "OfsZ": np.random.normal(-20, 1, len(t_med)).tolist(),
    }

    # --- EKF ---
    ekf_roll = roll[::4][:len(t_slow)] if len(t_slow) <= len(roll[::4]) else np.interp(t_slow, t_fast, roll)
    ekf_pitch = pitch[::4][:len(t_slow)] if len(t_slow) <= len(pitch[::4]) else np.interp(t_slow, t_fast, pitch)
    innov_vn = np.random.normal(0, 0.3, len(t_slow))
    innov_ve = np.random.normal(0, 0.3, len(t_slow))
    innov_vd = np.random.normal(0, 0.2, len(t_slow))
    # EKF divergence around GPS glitch
    ekf_glitch = (t_slow >= 69) & (t_slow <= 73)
    innov_vn[ekf_glitch] += np.random.normal(2, 0.5, ekf_glitch.sum())
    innov_ve[ekf_glitch] += np.random.normal(1.5, 0.5, ekf_glitch.sum())

    ekf = {
        "TimeUS": t_slow.tolist(),
        "Roll": (ekf_roll if isinstance(ekf_roll, list) else ekf_roll.tolist()),
        "Pitch": (ekf_pitch if isinstance(ekf_pitch, list) else ekf_pitch.tolist()),
        "VN": innov_vn.tolist(),
        "VE": innov_ve.tolist(),
        "VD": innov_vd.tolist(),
    }

    # --- MODE ---
    modes = {
        "TimeUS": [0, 5, 15, 40, 80, 100],
        "Mode": ["Stabilize", "AltHold", "Loiter", "Auto", "RTL", "Land"],
        "ModeNum": [0, 2, 5, 3, 6, 9],
    }

    signals = {
        "ATT": att,
        "IMU": imu,
        "VIBE": vibe,
        "GPS": gps,
        "BAT": bat,
        "RCIN": rcin,
        "RCOU": rcou,
        "BARO": baro,
        "MAG": mag,
        "EKF": ekf,
        "MODE": modes,
    }

    return {
        "duration_sec": duration,
        "signals": signals,
        "vehicle_type": "QuadCopter",
        "firmware": "ArduCopter V4.4.0",
    }


class LogParser:
    """Parse ArduPilot .BIN and .LOG files."""

    # DataFlash message format definitions
    FORMAT_HEADER = struct.Struct('<BBB')
    MSG_HEADER = struct.Struct('<BB')

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ('.bin',):
            return self._parse_bin(filepath)
        elif ext in ('.log',):
            return self._parse_log_text(filepath)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _parse_bin(self, filepath: str) -> Dict[str, Any]:
        """Parse binary DataFlash .BIN log file."""
        signals: Dict[str, Dict[str, list]] = {}
        formats: Dict[int, Dict] = {}

        with open(filepath, 'rb') as f:
            data = f.read()

        pos = 0
        total = len(data)

        while pos < total - 3:
            # Look for message header: 0xA3, 0x95
            if data[pos] != 0xA3 or data[pos + 1] != 0x95:
                pos += 1
                continue

            msg_type = data[pos + 2]
            pos += 3

            if msg_type == 128:  # FMT message
                if pos + 86 > total:
                    break
                fmt_type = data[pos]
                fmt_len = data[pos + 1]
                fmt_name = data[pos + 2:pos + 6].decode('ascii', errors='ignore').rstrip('\x00')
                fmt_format = data[pos + 6:pos + 22].decode('ascii', errors='ignore').rstrip('\x00')
                fmt_labels = data[pos + 22:pos + 86].decode('ascii', errors='ignore').rstrip('\x00')
                formats[fmt_type] = {
                    'name': fmt_name,
                    'len': fmt_len,
                    'format': fmt_format,
                    'labels': fmt_labels.split(','),
                }
                pos += 86
            elif msg_type in formats:
                fmt = formats[msg_type]
                msg_len = fmt['len'] - 3
                if pos + msg_len > total:
                    break
                try:
                    values = self._decode_message(data[pos:pos + msg_len], fmt['format'])
                    name = fmt['name']
                    if name not in signals:
                        signals[name] = {label: [] for label in fmt['labels']}
                    for label, value in zip(fmt['labels'], values):
                        if label in signals[name]:
                            signals[name][label].append(value)
                except Exception:
                    pass
                pos += msg_len
            else:
                pos += 1

        # Convert TimeUS to seconds
        for msg_type in signals:
            if 'TimeUS' in signals[msg_type] and signals[msg_type]['TimeUS']:
                t0 = signals[msg_type]['TimeUS'][0]
                signals[msg_type]['TimeUS'] = [
                    (t - t0) / 1e6 for t in signals[msg_type]['TimeUS']
                ]

        duration = 0
        for msg_type in signals:
            if 'TimeUS' in signals[msg_type] and signals[msg_type]['TimeUS']:
                duration = max(duration, signals[msg_type]['TimeUS'][-1])

        return {
            "duration_sec": duration,
            "signals": signals,
            "vehicle_type": "Unknown",
            "firmware": "Unknown",
        }

    def _decode_message(self, data: bytes, fmt: str) -> list:
        """Decode a binary message using format string."""
        FORMAT_MAP = {
            'b': ('b', 1), 'B': ('B', 1), 'h': ('h', 2), 'H': ('H', 2),
            'i': ('i', 4), 'I': ('I', 4), 'f': ('f', 4), 'd': ('d', 8),
            'Q': ('Q', 8), 'q': ('q', 8), 'n': ('4s', 4), 'N': ('16s', 16),
            'Z': ('64s', 64), 'c': ('h', 2), 'C': ('H', 2), 'e': ('i', 4),
            'E': ('I', 4), 'L': ('i', 4), 'M': ('B', 1), 'a': ('64s', 64),
        }
        SCALE = {'c': 0.01, 'C': 0.01, 'e': 0.01, 'E': 0.01, 'L': 1e-7}

        values = []
        offset = 0
        for ch in fmt:
            if ch not in FORMAT_MAP:
                continue
            struct_fmt, size = FORMAT_MAP[ch]
            if offset + size > len(data):
                break
            val = struct.unpack_from(f'<{struct_fmt}', data, offset)[0]
            if isinstance(val, bytes):
                val = val.decode('ascii', errors='ignore').rstrip('\x00')
            elif ch in SCALE:
                val = val * SCALE[ch]
            values.append(val)
            offset += size
        return values

    def _parse_log_text(self, filepath: str) -> Dict[str, Any]:
        """Parse text-format .LOG file."""
        signals: Dict[str, Dict[str, list]] = {}

        with open(filepath, 'r', errors='ignore') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) < 2:
                    continue
                msg_type = parts[0].strip()
                if msg_type not in signals:
                    signals[msg_type] = {}

                for i, part in enumerate(parts[1:], 1):
                    kv = part.strip().split(':')
                    if len(kv) == 2:
                        field = kv[0].strip()
                        try:
                            value = float(kv[1].strip())
                        except ValueError:
                            value = kv[1].strip()
                        if field not in signals[msg_type]:
                            signals[msg_type][field] = []
                        signals[msg_type][field].append(value)

        # Convert TimeUS
        for msg_type in signals:
            if 'TimeUS' in signals[msg_type] and signals[msg_type]['TimeUS']:
                t0 = signals[msg_type]['TimeUS'][0]
                signals[msg_type]['TimeUS'] = [(t - t0) / 1e6 for t in signals[msg_type]['TimeUS']]

        duration = 0
        for msg_type in signals:
            if 'TimeUS' in signals[msg_type] and signals[msg_type]['TimeUS']:
                duration = max(duration, signals[msg_type]['TimeUS'][-1])

        return {
            "duration_sec": duration,
            "signals": signals,
            "vehicle_type": "Unknown",
            "firmware": "Unknown",
        }
