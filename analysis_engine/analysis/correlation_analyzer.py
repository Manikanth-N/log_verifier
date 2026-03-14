"""Correlation analysis module for flight data."""
import numpy as np
from typing import Dict, List, Any, Optional
from scipy import stats


class CorrelationAnalyzer:
    """Analyze correlations between different flight parameters."""

    def analyze_vibration_throttle_correlation(self, signals: Dict) -> Dict[str, Any]:
        """Analyze correlation between vibration and throttle."""
        if 'VIBE' not in signals or 'RCIN' not in signals:
            return {"status": "insufficient_data", "correlations": []}

        vibe = signals['VIBE']
        rcin = signals['RCIN']

        if 'TimeUS' not in vibe or 'TimeUS' not in rcin or 'C3' not in rcin:
            return {"status": "missing_fields", "correlations": []}

        # Interpolate throttle to vibe timestamps
        vibe_times = np.array(vibe['TimeUS'])
        rcin_times = np.array(rcin['TimeUS'])
        throttle = np.array(rcin['C3'])
        throttle_interp = np.interp(vibe_times, rcin_times, throttle)

        correlations = []

        for axis in ['VibeX', 'VibeY', 'VibeZ']:
            if axis not in vibe:
                continue

            vibe_vals = np.array(vibe[axis])
            if len(vibe_vals) != len(throttle_interp):
                continue

            # Compute Pearson correlation
            corr_coef, p_value = stats.pearsonr(throttle_interp, vibe_vals)

            # Compute Spearman rank correlation (for non-linear relationships)
            spearman_coef, spearman_p = stats.spearmanr(throttle_interp, vibe_vals)

            # Bin analysis (vibration at different throttle ranges)
            throttle_ranges = [
                (1000, 1200, 'idle'),
                (1200, 1400, 'low'),
                (1400, 1600, 'mid'),
                (1600, 1800, 'high'),
                (1800, 2000, 'max')
            ]

            vibe_by_throttle = []
            for tmin, tmax, label in throttle_ranges:
                mask = (throttle_interp >= tmin) & (throttle_interp < tmax)
                if np.sum(mask) > 10:
                    avg_vibe = float(np.mean(vibe_vals[mask]))
                    max_vibe = float(np.max(vibe_vals[mask]))
                    vibe_by_throttle.append({
                        "throttle_range": label,
                        "throttle_min": tmin,
                        "throttle_max": tmax,
                        "avg_vibration": round(avg_vibe, 2),
                        "max_vibration": round(max_vibe, 2),
                        "sample_count": int(np.sum(mask)),
                    })

            # Determine correlation strength
            abs_corr = abs(corr_coef)
            if abs_corr < 0.3:
                strength = "weak"
            elif abs_corr < 0.6:
                strength = "moderate"
            else:
                strength = "strong"

            correlations.append({
                "axis": axis,
                "pearson_correlation": round(float(corr_coef), 3),
                "pearson_p_value": round(float(p_value), 4),
                "spearman_correlation": round(float(spearman_coef), 3),
                "spearman_p_value": round(float(spearman_p), 4),
                "correlation_strength": strength,
                "is_significant": bool(p_value < 0.05),
                "vibration_by_throttle": vibe_by_throttle,
            })

        # Overall assessment
        avg_correlation = np.mean([c['pearson_correlation'] for c in correlations]) if correlations else 0
        significant_count = sum(1 for c in correlations if c['is_significant'])

        return {
            "status": "success",
            "correlations": correlations,
            "summary": {
                "average_correlation": round(float(avg_correlation), 3),
                "significant_axes": significant_count,
                "interpretation": self._interpret_vibe_throttle_correlation(avg_correlation),
            }
        }

    def _interpret_vibe_throttle_correlation(self, avg_corr: float) -> str:
        """Provide human-readable interpretation."""
        abs_corr = abs(avg_corr)
        if abs_corr < 0.3:
            return "Vibration appears independent of throttle. Check for mechanical issues."
        elif abs_corr < 0.6:
            return "Moderate correlation detected. Vibration increases with throttle, which is normal."
        else:
            return "Strong correlation detected. Vibration is highly dependent on throttle. Check propeller balance and motor mounts."

    def analyze_battery_load_correlation(self, signals: Dict) -> Dict[str, Any]:
        """Analyze correlation between battery voltage sag and current draw."""
        if 'BAT' not in signals:
            return {"status": "no_battery_data"}

        bat = signals['BAT']
        if 'Volt' not in bat or 'Curr' not in bat or 'TimeUS' not in bat:
            return {"status": "missing_fields"}

        volts = np.array(bat['Volt'])
        current = np.array(bat['Curr'])
        times = np.array(bat['TimeUS'])

        if len(volts) < 20:
            return {"status": "insufficient_data"}

        # Compute voltage delta (detect sag)
        voltage_delta = np.diff(volts)
        sag_indices = np.where(voltage_delta < -0.1)[0]  # Significant drops

        sag_events = []
        for idx in sag_indices[:10]:  # Limit to 10 events
            if idx + 1 < len(current):
                sag_events.append({
                    "time": round(float(times[idx]), 2),
                    "voltage_drop": round(float(abs(voltage_delta[idx])), 3),
                    "current_at_sag": round(float(current[idx]), 2),
                })

        # Overall correlation
        corr_coef, p_value = stats.pearsonr(current, volts)

        return {
            "status": "success",
            "correlation": round(float(corr_coef), 3),
            "p_value": round(float(p_value), 4),
            "sag_events": sag_events,
            "interpretation": "High current draw causes voltage sag" if corr_coef < -0.5 else "Battery voltage is stable under load",
        }
