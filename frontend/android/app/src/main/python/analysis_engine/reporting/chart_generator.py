"""Server-side chart generation using matplotlib for reports and image export."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import io
from typing import Dict, Any, Optional, List

COLORS = ['#007AFF', '#FF3B30', '#00FF88', '#FF9500', '#BF5AF2', '#FF6B6B', '#4ECDC4', '#45B7D1']

def _setup_dark_style():
    plt.rcParams.update({
        'figure.facecolor': '#0A0A0A',
        'axes.facecolor': '#0A0A0A',
        'axes.edgecolor': '#27272A',
        'axes.labelcolor': '#A1A1AA',
        'text.color': '#A1A1AA',
        'xtick.color': '#52525B',
        'ytick.color': '#52525B',
        'grid.color': '#1A1A1A',
        'legend.facecolor': '#0A0A0A',
        'legend.edgecolor': '#27272A',
        'figure.dpi': 150,
    })


def _save_fig(fig, fmt: str = 'png') -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def generate_multi_signal_chart(
    signals_data: Dict[str, Any],
    signal_specs: List[Dict[str, str]],
    title: str = "Signal Plot",
    fmt: str = 'png',
    width: int = 12, height: int = 4,
) -> bytes:
    _setup_dark_style()
    fig, ax = plt.subplots(figsize=(width, height))

    for i, spec in enumerate(signal_specs):
        msg_type = spec.get("type", "")
        field = spec.get("field", "")
        if msg_type not in signals_data or not isinstance(signals_data[msg_type], dict):
            continue
        sig = signals_data[msg_type]
        if "TimeUS" not in sig or field not in sig:
            continue
        t = np.array(sig["TimeUS"])
        v = np.array(sig[field])
        # Downsample for chart
        if len(t) > 2000:
            step = len(t) // 2000
            t, v = t[::step], v[::step]
        ax.plot(t, v, color=COLORS[i % len(COLORS)], linewidth=0.8, label=f"{msg_type}.{field}")

    ax.set_xlabel("Time (s)", fontsize=9)
    ax.set_title(title, fontsize=11, fontweight='bold', color='#FFFFFF')
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3)
    return _save_fig(fig, fmt)


def generate_attitude_chart(signals: Dict, fmt='png') -> bytes:
    return generate_multi_signal_chart(
        signals,
        [{"type": "ATT", "field": "Roll"}, {"type": "ATT", "field": "Pitch"}, {"type": "ATT", "field": "Yaw"}],
        title="Attitude (Roll / Pitch / Yaw)", fmt=fmt,
    )


def generate_vibration_chart(signals: Dict, fmt='png') -> bytes:
    return generate_multi_signal_chart(
        signals,
        [{"type": "VIBE", "field": "VibeX"}, {"type": "VIBE", "field": "VibeY"}, {"type": "VIBE", "field": "VibeZ"}],
        title="Vibration Levels", fmt=fmt,
    )


def generate_battery_chart(signals: Dict, fmt='png') -> bytes:
    _setup_dark_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 5), sharex=True)

    if "BAT" in signals and isinstance(signals["BAT"], dict):
        bat = signals["BAT"]
        t = np.array(bat.get("TimeUS", []))
        if len(t) > 2000:
            step = len(t) // 2000
        else:
            step = 1

        if "Volt" in bat:
            ax1.plot(t[::step], np.array(bat["Volt"])[::step], color='#00FF88', linewidth=0.8, label='Voltage')
            ax1.axhline(y=14.4, color='#FF9500', linestyle='--', linewidth=0.5, alpha=0.7, label='Warning (14.4V)')
            ax1.axhline(y=13.6, color='#FF3B30', linestyle='--', linewidth=0.5, alpha=0.7, label='Critical (13.6V)')
        ax1.set_ylabel("Voltage (V)", fontsize=9)
        ax1.legend(fontsize=7)
        ax1.grid(True, alpha=0.3)
        ax1.set_title("Battery Health", fontsize=11, fontweight='bold', color='#FFFFFF')

        if "Curr" in bat:
            ax2.plot(t[::step], np.array(bat["Curr"])[::step], color='#FF9500', linewidth=0.8, label='Current')
            ax2.fill_between(t[::step], 0, np.array(bat["Curr"])[::step], alpha=0.15, color='#FF9500')
        ax2.set_xlabel("Time (s)", fontsize=9)
        ax2.set_ylabel("Current (A)", fontsize=9)
        ax2.legend(fontsize=7)
        ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return _save_fig(fig, fmt)


def generate_motor_chart(signals: Dict, fmt='png') -> bytes:
    return generate_multi_signal_chart(
        signals,
        [{"type": "RCOU", "field": "C1"}, {"type": "RCOU", "field": "C2"},
         {"type": "RCOU", "field": "C3"}, {"type": "RCOU", "field": "C4"}],
        title="Motor Outputs (PWM)", fmt=fmt,
    )


def generate_gps_chart(signals: Dict, fmt='png') -> bytes:
    _setup_dark_style()
    fig, axes = plt.subplots(2, 1, figsize=(12, 5), sharex=True)

    if "GPS" in signals and isinstance(signals["GPS"], dict):
        gps = signals["GPS"]
        t = np.array(gps.get("TimeUS", []))
        step = max(1, len(t) // 2000)

        if "Alt" in gps:
            axes[0].plot(t[::step], np.array(gps["Alt"])[::step], color='#007AFF', linewidth=0.8)
        axes[0].set_ylabel("Altitude (m)", fontsize=9)
        axes[0].set_title("GPS Data", fontsize=11, fontweight='bold', color='#FFFFFF')
        axes[0].grid(True, alpha=0.3)

        if "NSats" in gps:
            axes[1].plot(t[::step], np.array(gps["NSats"])[::step], color='#00FF88', linewidth=0.8, label='Sats')
            axes[1].axhline(y=8, color='#FF9500', linestyle='--', linewidth=0.5, alpha=0.7)
        if "HDop" in gps:
            ax2 = axes[1].twinx()
            ax2.plot(t[::step], np.array(gps["HDop"])[::step], color='#FF3B30', linewidth=0.8, label='HDop', alpha=0.7)
            ax2.set_ylabel("HDop", fontsize=8, color='#FF3B30')
            ax2.tick_params(axis='y', colors='#FF3B30')
        axes[1].set_xlabel("Time (s)", fontsize=9)
        axes[1].set_ylabel("Satellites", fontsize=9)
        axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    return _save_fig(fig, fmt)


def generate_ekf_chart(signals: Dict, fmt='png') -> bytes:
    return generate_multi_signal_chart(
        signals,
        [{"type": "EKF", "field": "VN"}, {"type": "EKF", "field": "VE"}, {"type": "EKF", "field": "VD"}],
        title="EKF Velocity Innovations", fmt=fmt,
    )


def generate_fft_chart(fft_result: Dict, signal_name: str = "", fmt='png') -> bytes:
    _setup_dark_style()
    fig, ax = plt.subplots(figsize=(12, 4))

    freqs = np.array(fft_result.get("frequencies", []))
    mag = np.array(fft_result.get("magnitude", []))

    if len(freqs) > 0:
        ax.plot(freqs, mag, color='#007AFF', linewidth=0.8)
        ax.fill_between(freqs, 0, mag, alpha=0.15, color='#007AFF')

        for peak in fft_result.get("peaks", [])[:5]:
            f = peak["frequency"]
            m = peak["magnitude"]
            color = '#FF9500' if peak.get("is_harmonic") else '#FF3B30'
            ax.axvline(x=f, color=color, linestyle='--', linewidth=0.5, alpha=0.7)
            ax.annotate(peak["label"], xy=(f, m), fontsize=7, color=color,
                       xytext=(5, 5), textcoords='offset points')

    ax.set_xlabel("Frequency (Hz)", fontsize=9)
    ax.set_ylabel("Magnitude", fontsize=9)
    title = f"FFT Spectrum: {signal_name}" if signal_name else "FFT Spectrum"
    ax.set_title(title, fontsize=11, fontweight='bold', color='#FFFFFF')
    ax.grid(True, alpha=0.3)
    return _save_fig(fig, fmt)


def generate_spectrogram_chart(spectrogram: Dict, signal_name: str = "", fmt='png') -> bytes:
    _setup_dark_style()
    fig, ax = plt.subplots(figsize=(12, 4))

    times = np.array(spectrogram.get("times", []))
    freqs = np.array(spectrogram.get("frequencies", []))
    power = np.array(spectrogram.get("power", []))

    if power.size > 0 and len(times) > 0 and len(freqs) > 0:
        im = ax.pcolormesh(times, freqs, power, shading='auto', cmap='viridis')
        fig.colorbar(im, ax=ax, label='Power (dB)', pad=0.02)

    ax.set_xlabel("Time (s)", fontsize=9)
    ax.set_ylabel("Frequency (Hz)", fontsize=9)
    title = f"Spectrogram: {signal_name}" if signal_name else "Spectrogram"
    ax.set_title(title, fontsize=11, fontweight='bold', color='#FFFFFF')
    return _save_fig(fig, fmt)


def generate_all_report_charts(signals: Dict, fft_result: Dict = None, spectrogram: Dict = None) -> Dict[str, bytes]:
    """Generate all charts for a full report. Returns dict of chart_name -> PNG bytes."""
    charts = {}
    try:
        charts['attitude'] = generate_attitude_chart(signals)
    except Exception:
        pass
    try:
        charts['vibration'] = generate_vibration_chart(signals)
    except Exception:
        pass
    try:
        charts['battery'] = generate_battery_chart(signals)
    except Exception:
        pass
    try:
        charts['motors'] = generate_motor_chart(signals)
    except Exception:
        pass
    try:
        charts['gps'] = generate_gps_chart(signals)
    except Exception:
        pass
    try:
        charts['ekf'] = generate_ekf_chart(signals)
    except Exception:
        pass
    if fft_result:
        try:
            charts['fft'] = generate_fft_chart(fft_result)
        except Exception:
            pass
    if spectrogram:
        try:
            charts['spectrogram'] = generate_spectrogram_chart(spectrogram)
        except Exception:
            pass
    return charts
