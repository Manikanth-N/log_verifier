import numpy as np
from typing import Dict, Any, List


class DiagnosticsEngine:
    """Automated flight diagnostics for ArduPilot logs."""

    # Thresholds
    VIBE_WARN = 30.0
    VIBE_CRIT = 60.0
    CLIP_WARN = 5
    GPS_HDOP_WARN = 2.0
    GPS_SATS_WARN = 8
    EKF_INNOV_WARN = 0.8
    EKF_INNOV_CRIT = 1.5
    BAT_VOLT_WARN = 14.4  # per cell * 4
    BAT_VOLT_CRIT = 13.6
    MOTOR_IMBALANCE_WARN = 50  # PWM difference threshold

    # Parameter limits for limit checking
    PARAMETER_LIMITS = {
        "VIBE_MAX": {"min": 0, "max": 30.0, "unit": "m/s²", "desc": "Maximum acceptable vibration level"},
        "BAT_MIN_VOLT": {"min": 13.0, "max": 16.8, "unit": "V", "desc": "Battery voltage range (4S LiPo)"},
        "GPS_HDOP": {"min": 0, "max": 2.0, "unit": "", "desc": "GPS horizontal dilution of precision"},
        "GPS_MIN_SATS": {"min": 8, "max": 30, "unit": "sats", "desc": "Minimum satellite count for navigation"},
        "EKF_INNOV": {"min": 0, "max": 0.8, "unit": "", "desc": "EKF innovation threshold"},
        "MOTOR_PWM_DIFF": {"min": 0, "max": 50, "unit": "PWM", "desc": "Maximum motor output imbalance"},
        "ATT_ERR_MAX": {"min": 0, "max": 5.0, "unit": "°", "desc": "Maximum attitude error"},
        "CURR_MAX": {"min": 0, "max": 50.0, "unit": "A", "desc": "Maximum current draw"},
    }

    def analyze(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run all diagnostics and return results."""
        signals = log_data.get("signals", {})
        results = []

        if "VIBE" in signals:
            results.extend(self._check_vibration(signals["VIBE"]))
        if "GPS" in signals:
            results.extend(self._check_gps(signals["GPS"]))
        if "EKF" in signals:
            results.extend(self._check_ekf(signals["EKF"]))
        if "BAT" in signals:
            results.extend(self._check_battery(signals["BAT"]))
        if "RCOU" in signals:
            results.extend(self._check_motors(signals["RCOU"]))
        if "IMU" in signals:
            results.extend(self._check_imu(signals["IMU"]))
        if "ATT" in signals:
            results.extend(self._check_attitude(signals["ATT"]))

        # Calculate overall health score
        if results:
            max_severity = max(r["severity"] for r in results)
            avg_severity = np.mean([r["severity"] for r in results])
            health_score = max(0, 100 - int(max_severity * 6 + avg_severity * 4))
        else:
            health_score = 100

        # Sort by severity (highest first)
        results.sort(key=lambda x: x["severity"], reverse=True)

        # Get parameter limits
        parameter_limits = self._check_parameter_limits(signals)

        return {
            "health_score": health_score,
            "total_checks": len(results),
            "critical": sum(1 for r in results if r["status"] == "critical"),
            "warnings": sum(1 for r in results if r["status"] == "warning"),
            "passed": sum(1 for r in results if r["status"] == "good"),
            "checks": results,
            "parameter_limits": parameter_limits,
        }

    def _check_parameter_limits(self, signals: Dict) -> List[Dict]:
        """Check various parameters against recommended limits."""
        limits = []

        # Vibration limits
        if "VIBE" in signals:
            vibe = signals["VIBE"]
            for axis in ["VibeX", "VibeY", "VibeZ"]:
                if axis in vibe:
                    max_val = float(np.max(vibe[axis]))
                    status = "within" if max_val <= self.VIBE_WARN else ("warning" if max_val <= self.VIBE_CRIT else "exceeded")
                    limits.append({
                        "name": f"Vibration {axis[-1]}-axis (max)",
                        "value": round(max_val, 2),
                        "min_limit": 0,
                        "max_limit": self.VIBE_WARN,
                        "status": status,
                        "unit": "m/s²",
                        "description": f"Peak vibration on {axis[-1]}-axis"
                    })

        # Battery voltage limits
        if "BAT" in signals and "Volt" in signals["BAT"]:
            min_volt = float(np.min(signals["BAT"]["Volt"]))
            status = "within" if min_volt >= self.BAT_VOLT_WARN else ("warning" if min_volt >= self.BAT_VOLT_CRIT else "exceeded")
            limits.append({
                "name": "Battery Voltage (min)",
                "value": round(min_volt, 2),
                "min_limit": self.BAT_VOLT_CRIT,
                "max_limit": 16.8,
                "status": status,
                "unit": "V",
                "description": "Minimum battery voltage during flight"
            })

        # GPS HDop limits
        if "GPS" in signals and "HDop" in signals["GPS"]:
            max_hdop = float(np.max(signals["GPS"]["HDop"]))
            status = "within" if max_hdop <= self.GPS_HDOP_WARN else ("warning" if max_hdop <= self.GPS_HDOP_WARN * 2 else "exceeded")
            limits.append({
                "name": "GPS HDop (max)",
                "value": round(max_hdop, 2),
                "min_limit": 0,
                "max_limit": self.GPS_HDOP_WARN,
                "status": status,
                "unit": "",
                "description": "Maximum GPS horizontal dilution of precision"
            })

        # GPS satellite count
        if "GPS" in signals and "NSats" in signals["GPS"]:
            min_sats = int(np.min(signals["GPS"]["NSats"]))
            status = "within" if min_sats >= self.GPS_SATS_WARN else "warning"
            limits.append({
                "name": "GPS Satellites (min)",
                "value": min_sats,
                "min_limit": self.GPS_SATS_WARN,
                "max_limit": 30,
                "status": status,
                "unit": "sats",
                "description": "Minimum satellite count during flight"
            })

        # EKF innovation limits
        if "EKF" in signals:
            for field in ["VN", "VE", "VD"]:
                if field in signals["EKF"]:
                    max_innov = float(np.max(np.abs(signals["EKF"][field])))
                    status = "within" if max_innov <= self.EKF_INNOV_WARN else ("warning" if max_innov <= self.EKF_INNOV_CRIT else "exceeded")
                    axis_name = {"VN": "North", "VE": "East", "VD": "Down"}[field]
                    limits.append({
                        "name": f"EKF Innovation {axis_name}",
                        "value": round(max_innov, 3),
                        "min_limit": 0,
                        "max_limit": self.EKF_INNOV_WARN,
                        "status": status,
                        "unit": "",
                        "description": f"Maximum EKF velocity innovation ({axis_name})"
                    })

        # Motor balance
        if "RCOU" in signals:
            motor_fields = [f for f in ["C1", "C2", "C3", "C4"] if f in signals["RCOU"]]
            if len(motor_fields) >= 2:
                motor_avgs = {mf: np.mean(signals["RCOU"][mf]) for mf in motor_fields}
                overall_avg = np.mean(list(motor_avgs.values()))
                max_diff = max(abs(v - overall_avg) for v in motor_avgs.values())
                status = "within" if max_diff <= self.MOTOR_IMBALANCE_WARN else "warning"
                limits.append({
                    "name": "Motor Balance (diff)",
                    "value": round(max_diff, 1),
                    "min_limit": 0,
                    "max_limit": self.MOTOR_IMBALANCE_WARN,
                    "status": status,
                    "unit": "PWM",
                    "description": "Maximum motor output deviation from average"
                })

        # Current draw
        if "BAT" in signals and "Curr" in signals["BAT"]:
            max_curr = float(np.max(signals["BAT"]["Curr"]))
            status = "within" if max_curr <= 40 else ("warning" if max_curr <= 60 else "exceeded")
            limits.append({
                "name": "Current Draw (max)",
                "value": round(max_curr, 1),
                "min_limit": 0,
                "max_limit": 50.0,
                "status": status,
                "unit": "A",
                "description": "Peak current draw during flight"
            })

        return limits

    def _check_vibration(self, vibe: Dict) -> List[Dict]:
        results = []
        for axis in ["VibeX", "VibeY", "VibeZ"]:
            if axis not in vibe:
                continue
            vals = np.array(vibe[axis])
            max_val = np.max(vals)
            avg_val = np.mean(vals)
            p95 = np.percentile(vals, 95)

            if max_val > self.VIBE_CRIT:
                status, severity = "critical", 9
                explanation = f"Extreme vibration on {axis[-1]}-axis (peak: {max_val:.1f} m/s²). This can cause sensor aliasing, EKF issues, and poor flight performance."
                fix = "Check propeller balance, tighten all frame bolts, inspect motor mounts, add vibration dampening."
            elif max_val > self.VIBE_WARN or p95 > self.VIBE_WARN * 0.7:
                status, severity = "warning", 5
                explanation = f"Elevated vibration on {axis[-1]}-axis (peak: {max_val:.1f}, avg: {avg_val:.1f} m/s²). May affect flight stability."
                fix = "Balance propellers, check for loose components, verify motor mount integrity."
            else:
                status, severity = "good", 0
                explanation = f"{axis[-1]}-axis vibration within normal range (peak: {max_val:.1f}, avg: {avg_val:.1f} m/s²)."
                fix = "No action needed."

            results.append({
                "name": f"Vibration {axis[-1]}-axis",
                "category": "vibration",
                "status": status,
                "severity": severity,
                "value": round(float(max_val), 2),
                "threshold": self.VIBE_WARN,
                "explanation": explanation,
                "fix": fix,
                "beginner_text": self._beginner_vibe(axis[-1], status, max_val),
            })

        # Check clipping
        for clip_field in ["Clip0", "Clip1", "Clip2"]:
            if clip_field not in vibe:
                continue
            total_clips = sum(1 for v in vibe[clip_field] if v > 0)
            if total_clips > self.CLIP_WARN:
                results.append({
                    "name": f"Sensor Clipping ({clip_field})",
                    "category": "vibration",
                    "status": "critical" if total_clips > 50 else "warning",
                    "severity": 8 if total_clips > 50 else 4,
                    "value": total_clips,
                    "threshold": self.CLIP_WARN,
                    "explanation": f"Accelerometer clipping detected ({total_clips} events). Sensor readings are being saturated.",
                    "fix": "Reduce vibration immediately. Add soft-mount for flight controller. Balance propellers.",
                    "beginner_text": f"Your drone's motion sensor is hitting its limits {total_clips} times. This means vibrations are too strong. Try balancing your propellers.",
                })

        return results

    def _check_gps(self, gps: Dict) -> List[Dict]:
        results = []
        if "HDop" in gps:
            hdop = np.array(gps["HDop"])
            max_hdop = np.max(hdop)
            avg_hdop = np.mean(hdop)

            if max_hdop > self.GPS_HDOP_WARN * 2:
                status, severity = "critical", 7
                explanation = f"GPS accuracy severely degraded (HDop peak: {max_hdop:.1f}). Position estimates are unreliable."
                fix = "Check GPS antenna placement, ensure clear sky view, check for RF interference."
            elif max_hdop > self.GPS_HDOP_WARN:
                status, severity = "warning", 4
                explanation = f"GPS accuracy reduced (HDop peak: {max_hdop:.1f}, avg: {avg_hdop:.1f}). Position may drift."
                fix = "Improve GPS antenna position, avoid flying near buildings or trees."
            else:
                status, severity = "good", 0
                explanation = f"GPS accuracy good (HDop avg: {avg_hdop:.1f})."
                fix = "No action needed."

            results.append({
                "name": "GPS Accuracy",
                "category": "gps",
                "status": status,
                "severity": severity,
                "value": round(float(max_hdop), 2),
                "threshold": self.GPS_HDOP_WARN,
                "explanation": explanation,
                "fix": fix,
                "beginner_text": f"GPS signal quality: {'Poor - your drone may not know exactly where it is' if status != 'good' else 'Good - your drone knows its position well'}.",
            })

        if "NSats" in gps:
            nsats = np.array(gps["NSats"])
            min_sats = int(np.min(nsats))
            if min_sats < self.GPS_SATS_WARN:
                results.append({
                    "name": "GPS Satellites",
                    "category": "gps",
                    "status": "warning",
                    "severity": 5,
                    "value": min_sats,
                    "threshold": self.GPS_SATS_WARN,
                    "explanation": f"Low satellite count detected (minimum: {min_sats}). Need at least {self.GPS_SATS_WARN} for reliable navigation.",
                    "fix": "Wait longer for GPS lock before takeoff. Ensure clear sky view.",
                    "beginner_text": f"At one point, your drone could only see {min_sats} GPS satellites. It needs at least {self.GPS_SATS_WARN} for safe flight.",
                })

        return results

    def _check_ekf(self, ekf: Dict) -> List[Dict]:
        results = []
        for field in ["VN", "VE", "VD"]:
            if field not in ekf:
                continue
            vals = np.array(ekf[field])
            max_innov = np.max(np.abs(vals))
            rms = np.sqrt(np.mean(vals ** 2))

            axis_name = {"VN": "North", "VE": "East", "VD": "Down"}[field]

            if max_innov > self.EKF_INNOV_CRIT:
                status, severity = "critical", 8
                explanation = f"EKF velocity innovation {axis_name} is diverging (peak: {max_innov:.2f}). Navigation solution may be unreliable."
                fix = "Check sensor calibration, GPS health, and compass interference. May need to recalibrate IMU and compass."
            elif max_innov > self.EKF_INNOV_WARN:
                status, severity = "warning", 4
                explanation = f"EKF velocity innovation {axis_name} elevated (peak: {max_innov:.2f}, RMS: {rms:.2f})."
                fix = "Monitor in future flights. Consider recalibrating sensors."
            else:
                status, severity = "good", 0
                explanation = f"EKF {axis_name} velocity innovation normal (RMS: {rms:.2f})."
                fix = "No action needed."

            results.append({
                "name": f"EKF Innovation {axis_name}",
                "category": "ekf",
                "status": status,
                "severity": severity,
                "value": round(float(max_innov), 3),
                "threshold": self.EKF_INNOV_WARN,
                "explanation": explanation,
                "fix": fix,
                "beginner_text": f"Navigation filter {'is having trouble estimating position' if status != 'good' else 'is working well'} in the {axis_name.lower()} direction.",
            })

        return results

    def _check_battery(self, bat: Dict) -> List[Dict]:
        results = []
        if "Volt" in bat:
            volts = np.array(bat["Volt"])
            min_volt = np.min(volts)
            avg_volt = np.mean(volts)

            if min_volt < self.BAT_VOLT_CRIT:
                status, severity = "critical", 9
                explanation = f"Battery voltage critically low (min: {min_volt:.1f}V). Risk of battery damage and mid-air power loss."
                fix = "Land immediately when voltage drops below {:.1f}V. Check battery health and capacity.".format(self.BAT_VOLT_CRIT)
            elif min_volt < self.BAT_VOLT_WARN:
                status, severity = "warning", 5
                explanation = f"Battery voltage low (min: {min_volt:.1f}V, avg: {avg_volt:.1f}V). Battery may be aging."
                fix = "Set voltage failsafe. Consider replacing battery if capacity has degraded."
            else:
                status, severity = "good", 0
                explanation = f"Battery voltage healthy (min: {min_volt:.1f}V, avg: {avg_volt:.1f}V)."
                fix = "No action needed."

            results.append({
                "name": "Battery Voltage",
                "category": "power",
                "status": status,
                "severity": severity,
                "value": round(float(min_volt), 2),
                "threshold": self.BAT_VOLT_WARN,
                "explanation": explanation,
                "fix": fix,
                "beginner_text": f"Battery {'is running low - charge or replace soon' if status != 'good' else 'level looks healthy'}.",
            })

            # Voltage sag detection
            if len(volts) > 20:
                window = max(10, len(volts) // 20)
                rolling_diff = np.array([volts[i] - volts[i + window] for i in range(len(volts) - window)])
                max_sag = float(np.max(rolling_diff)) if len(rolling_diff) > 0 else 0
                if max_sag > 1.0:
                    results.append({
                        "name": "Voltage Sag",
                        "category": "power",
                        "status": "critical" if max_sag > 2.0 else "warning",
                        "severity": 7 if max_sag > 2.0 else 4,
                        "value": round(max_sag, 2),
                        "threshold": 1.0,
                        "explanation": f"Voltage sag of {max_sag:.1f}V detected during high-current draw. Battery internal resistance may be high.",
                        "fix": "Replace battery if internal resistance is too high. Reduce current draw or use higher C-rating battery.",
                        "beginner_text": f"Your battery voltage dropped by {max_sag:.1f}V suddenly. The battery might be old or too small for your drone.",
                    })

        return results

    def _check_motors(self, rcou: Dict) -> List[Dict]:
        results = []
        motor_fields = [f for f in ["C1", "C2", "C3", "C4"] if f in rcou]
        if len(motor_fields) < 2:
            return results

        motor_avgs = {}
        motor_maxs = {}
        for mf in motor_fields:
            vals = np.array(rcou[mf])
            motor_avgs[mf] = np.mean(vals)
            motor_maxs[mf] = np.max(vals)

        overall_avg = np.mean(list(motor_avgs.values()))
        max_diff = max(abs(v - overall_avg) for v in motor_avgs.values())
        imbalanced_motor = max(motor_avgs, key=lambda k: abs(motor_avgs[k] - overall_avg))

        if max_diff > self.MOTOR_IMBALANCE_WARN:
            motor_num = int(imbalanced_motor[1])
            direction = "higher" if motor_avgs[imbalanced_motor] > overall_avg else "lower"
            results.append({
                "name": "Motor Balance",
                "category": "motors",
                "status": "warning",
                "severity": 5,
                "value": round(float(max_diff), 1),
                "threshold": self.MOTOR_IMBALANCE_WARN,
                "explanation": f"Motor {motor_num} output is {direction} than average by {max_diff:.0f} PWM. This indicates mechanical imbalance.",
                "fix": f"Check motor {motor_num}: propeller condition, motor mount, ESC calibration. Verify CG (center of gravity).",
                "beginner_text": f"Motor {motor_num} is working {'harder' if direction == 'higher' else 'less'} than the others. Check if the propeller is damaged or the drone is tilted.",
            })
        else:
            results.append({
                "name": "Motor Balance",
                "category": "motors",
                "status": "good",
                "severity": 0,
                "value": round(float(max_diff), 1),
                "threshold": self.MOTOR_IMBALANCE_WARN,
                "explanation": f"Motor outputs are well balanced (max difference: {max_diff:.0f} PWM).",
                "fix": "No action needed.",
                "beginner_text": "All motors are working evenly. Good!",
            })

        # Motor saturation detection
        SATURATION_THRESHOLD = 1950
        for mf in motor_fields:
            vals = np.array(rcou[mf])
            sat_count = int(np.sum(vals >= SATURATION_THRESHOLD))
            sat_pct = sat_count / len(vals) * 100
            if sat_pct > 5:
                motor_num = int(mf[1])
                results.append({
                    "name": f"Motor {motor_num} Saturation",
                    "category": "motors",
                    "status": "critical" if sat_pct > 20 else "warning",
                    "severity": 8 if sat_pct > 20 else 5,
                    "value": round(sat_pct, 1),
                    "threshold": 5.0,
                    "explanation": f"Motor {motor_num} reached saturation ({sat_pct:.1f}% of flight time at >{SATURATION_THRESHOLD} PWM). No headroom for stabilization.",
                    "fix": f"Reduce weight, use larger propellers, or more powerful motors. Motor {motor_num} cannot provide more thrust.",
                    "beginner_text": f"Motor {motor_num} was running at maximum power {sat_pct:.0f}% of the time. Your drone may be too heavy.",
                })

        return results

    def _check_imu(self, imu: Dict) -> List[Dict]:
        results = []
        for axis in ["AccX", "AccY", "AccZ"]:
            if axis not in imu:
                continue
            vals = np.array(imu[axis])
            std = np.std(vals)
            if axis == "AccZ":
                # Z-axis has gravity, so check deviation from -9.81
                mean_dev = abs(np.mean(vals) - (-9.81))
                if mean_dev > 1.0:
                    results.append({
                        "name": f"IMU Calibration ({axis})",
                        "category": "sensors",
                        "status": "warning",
                        "severity": 3,
                        "value": round(float(mean_dev), 2),
                        "threshold": 1.0,
                        "explanation": f"Accelerometer Z-axis mean deviates from gravity by {mean_dev:.2f} m/s². May indicate calibration issue.",
                        "fix": "Recalibrate accelerometer on a level surface.",
                        "beginner_text": "The motion sensor might need recalibrating. Place your drone on a flat surface and run calibration.",
                    })
        return results

    def _check_attitude(self, att: Dict) -> List[Dict]:
        results = []
        if "ErrRP" in att:
            err = np.array(att["ErrRP"])
            max_err = np.max(err)
            avg_err = np.mean(err)
            if max_err > 5:
                results.append({
                    "name": "Attitude Control",
                    "category": "control",
                    "status": "warning" if max_err < 10 else "critical",
                    "severity": 4 if max_err < 10 else 7,
                    "value": round(float(max_err), 2),
                    "threshold": 5.0,
                    "explanation": f"Attitude error (Roll/Pitch) peaked at {max_err:.1f}°. The flight controller struggled to maintain desired attitude.",
                    "fix": "Check PID tuning parameters. Reduce aggressiveness or run Autotune.",
                    "beginner_text": f"Your drone had trouble staying level at times (error up to {max_err:.1f}°). This could mean the flight settings need adjusting.",
                })
        return results

    def _beginner_vibe(self, axis: str, status: str, value: float) -> str:
        axis_names = {"X": "side-to-side", "Y": "front-to-back", "Z": "up-and-down"}
        direction = axis_names.get(axis, axis)
        if status == "critical":
            return f"Your drone is shaking a lot in the {direction} direction ({value:.0f} m/s²). This is dangerous! Check your propellers and frame for loose parts."
        elif status == "warning":
            return f"There's some extra shaking in the {direction} direction ({value:.0f} m/s²). Consider checking propeller balance."
        return f"Vibration in the {direction} direction is normal ({value:.0f} m/s²). Good!"
