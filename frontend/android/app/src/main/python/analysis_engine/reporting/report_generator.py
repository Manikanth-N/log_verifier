"""Report generation in PDF, Markdown, and HTML formats."""
import base64
import io
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fpdf import FPDF


def _b64(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode('utf-8')


# ─── HTML Report ───────────────────────────────────────────────

def generate_html_report(
    log_meta: Dict, diagnostics: Dict, charts: Dict[str, bytes],
    fft_result: Dict = None
) -> str:
    health = diagnostics.get("health_score", "N/A")
    score_color = "#00FF88" if health >= 80 else ("#FF9500" if health >= 50 else "#FF3B30")

    checks_html = ""
    for c in diagnostics.get("checks", []):
        icon = {"good": "&#10004;", "warning": "&#9888;", "critical": "&#10060;"}.get(c["status"], "?")
        color = {"good": "#00FF88", "warning": "#FF9500", "critical": "#FF3B30"}.get(c["status"], "#A1A1AA")
        checks_html += f"""
        <div style="background:#121212;border:1px solid #27272A;border-radius:8px;padding:12px;margin-bottom:8px;">
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="color:{color};font-size:18px;">{icon}</span>
            <strong style="color:#FFF;">{c['name']}</strong>
            <span style="margin-left:auto;background:{color}22;color:{color};padding:2px 8px;border-radius:4px;font-size:11px;">{c['severity']}/10</span>
          </div>
          <p style="color:#A1A1AA;font-size:13px;margin:6px 0 0;">{c['explanation']}</p>
          {"<p style='color:#007AFF;font-size:12px;margin:4px 0 0;'>Fix: " + c['fix'] + "</p>" if c['status'] != 'good' else ""}
        </div>"""

    chart_sections = ""
    chart_titles = {
        'attitude': 'Attitude (Roll / Pitch / Yaw)',
        'vibration': 'Vibration Levels',
        'battery': 'Battery Health',
        'motors': 'Motor Outputs',
        'gps': 'GPS Data',
        'ekf': 'EKF Innovations',
        'fft': 'FFT Frequency Spectrum',
        'spectrogram': 'Spectrogram',
    }
    for key, title in chart_titles.items():
        if key in charts:
            chart_sections += f"""
            <div style="margin:16px 0;">
              <h3 style="color:#A1A1AA;font-size:13px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">{title}</h3>
              <img src="data:image/png;base64,{_b64(charts[key])}" style="width:100%;border-radius:8px;border:1px solid #27272A;"/>
            </div>"""

    peaks_html = ""
    if fft_result and fft_result.get("peaks"):
        peaks_rows = ""
        for p in fft_result["peaks"][:8]:
            h_badge = '<span style="color:#FF9500;font-size:10px;"> HARMONIC</span>' if p.get("is_harmonic") else ""
            peaks_rows += f"<tr><td style='color:#FFF;padding:4px 8px;'>{p['label']}{h_badge}</td><td style='color:#A1A1AA;padding:4px 8px;'>{p['magnitude']:.4f}</td></tr>"
        peaks_html = f"""
        <div style="margin:16px 0;">
          <h3 style="color:#A1A1AA;font-size:13px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Detected Frequency Peaks</h3>
          <table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:1px solid #27272A;">
            <th style="text-align:left;padding:4px 8px;color:#52525B;">Frequency</th>
            <th style="text-align:left;padding:4px 8px;color:#52525B;">Magnitude</th>
          </tr></thead><tbody>{peaks_rows}</tbody></table>
        </div>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Vehicle Log Analysis Report</title>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#050505;color:#A1A1AA;padding:24px;max-width:900px;margin:0 auto;}}
  h1{{color:#FFF;font-size:22px;margin:0;}} h2{{color:#FFF;font-size:16px;margin:20px 0 10px;border-bottom:1px solid #27272A;padding-bottom:6px;}}
</style></head><body>
<h1>Vehicle Log Analysis Report</h1>
<p style="color:#52525B;font-size:12px;">Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>

<h2>Flight Summary</h2>
<table style="font-size:13px;">
  <tr><td style="color:#52525B;padding:3px 16px 3px 0;">File</td><td style="color:#FFF;">{log_meta.get('filename','N/A')}</td></tr>
  <tr><td style="color:#52525B;padding:3px 16px 3px 0;">Vehicle</td><td style="color:#FFF;">{log_meta.get('vehicle_type','N/A')}</td></tr>
  <tr><td style="color:#52525B;padding:3px 16px 3px 0;">Firmware</td><td style="color:#FFF;">{log_meta.get('firmware','N/A')}</td></tr>
  <tr><td style="color:#52525B;padding:3px 16px 3px 0;">Duration</td><td style="color:#FFF;">{log_meta.get('duration_sec',0):.0f} seconds</td></tr>
  <tr><td style="color:#52525B;padding:3px 16px 3px 0;">Messages</td><td style="color:#FFF;">{', '.join(log_meta.get('message_types',[]))}</td></tr>
</table>

<h2>Health Score</h2>
<div style="text-align:center;background:#0A0A0A;border:1px solid #27272A;border-radius:12px;padding:20px;">
  <div style="font-size:56px;font-weight:800;color:{score_color};">{health}</div>
  <div style="color:#52525B;font-size:13px;">/ 100</div>
  <div style="display:flex;justify-content:center;gap:16px;margin-top:10px;">
    <span style="color:#FF3B30;">{diagnostics.get('critical',0)} Critical</span>
    <span style="color:#FF9500;">{diagnostics.get('warnings',0)} Warnings</span>
    <span style="color:#00FF88;">{diagnostics.get('passed',0)} Passed</span>
  </div>
</div>

<h2>Diagnostic Results</h2>
{checks_html}

<h2>Key Plots</h2>
{chart_sections}

{peaks_html}

<div style="margin-top:24px;padding-top:12px;border-top:1px solid #27272A;color:#52525B;font-size:11px;">
  Generated by Vehicle Log Analyzer &bull; {datetime.now(timezone.utc).year}
</div>
</body></html>"""


# ─── Markdown Report ───────────────────────────────────────────

def generate_markdown_report(log_meta: Dict, diagnostics: Dict, fft_result: Dict = None) -> str:
    lines = [
        "# Vehicle Log Analysis Report",
        f"*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*\n",
        "## Flight Summary",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| File | {log_meta.get('filename','N/A')} |",
        f"| Vehicle | {log_meta.get('vehicle_type','N/A')} |",
        f"| Firmware | {log_meta.get('firmware','N/A')} |",
        f"| Duration | {log_meta.get('duration_sec',0):.0f} seconds |",
        f"| Messages | {', '.join(log_meta.get('message_types',[]))} |",
        "",
        "## Health Score",
        f"**{diagnostics.get('health_score','N/A')} / 100**\n",
        f"- Critical: {diagnostics.get('critical',0)}",
        f"- Warnings: {diagnostics.get('warnings',0)}",
        f"- Passed: {diagnostics.get('passed',0)}\n",
        "## Diagnostic Results\n",
    ]

    for c in diagnostics.get("checks", []):
        icon = {"good": "✅", "warning": "⚠️", "critical": "❌"}.get(c["status"], "❓")
        lines.append(f"### {icon} {c['name']} (Severity: {c['severity']}/10)")
        lines.append(f"{c['explanation']}\n")
        if c['status'] != 'good':
            lines.append(f"**Recommended fix:** {c['fix']}\n")

    if fft_result and fft_result.get("peaks"):
        lines.append("## Frequency Peaks\n")
        lines.append("| Frequency | Magnitude | Harmonic |")
        lines.append("|-----------|-----------|----------|")
        for p in fft_result["peaks"][:8]:
            lines.append(f"| {p['label']} | {p['magnitude']:.4f} | {'Yes' if p.get('is_harmonic') else 'No'} |")
        lines.append("")

    lines.append(f"\n---\n*Generated by Vehicle Log Analyzer*")
    return "\n".join(lines)


# ─── PDF Report ────────────────────────────────────────────────

class FlightReportPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'Vehicle Log Analysis Report', 0, 1, 'C')
        self.set_font('Helvetica', '', 9)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), 0, 1, 'C')
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, title, 0, 1)
        self.set_draw_color(39, 39, 42)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def kv_row(self, key, value):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(130, 130, 130)
        self.cell(40, 6, key, 0, 0)
        self.set_text_color(220, 220, 220)
        self.cell(0, 6, str(value), 0, 1)


def generate_pdf_report(
    log_meta: Dict, diagnostics: Dict, charts: Dict[str, bytes], fft_result: Dict = None
) -> bytes:
    pdf = FlightReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_fill_color(5, 5, 5)
    pdf.rect(0, 0, 210, 297, 'F')

    # Flight Summary
    pdf.section_title("Flight Summary")
    pdf.kv_row("File:", log_meta.get('filename', 'N/A'))
    pdf.kv_row("Vehicle:", log_meta.get('vehicle_type', 'N/A'))
    pdf.kv_row("Firmware:", log_meta.get('firmware', 'N/A'))
    pdf.kv_row("Duration:", f"{log_meta.get('duration_sec', 0):.0f} seconds")
    pdf.kv_row("Messages:", ', '.join(log_meta.get('message_types', [])))
    pdf.ln(4)

    # Health Score
    pdf.section_title("Health Score")
    score = diagnostics.get("health_score", 0)
    if score >= 80:
        pdf.set_text_color(0, 255, 136)
    elif score >= 50:
        pdf.set_text_color(255, 149, 0)
    else:
        pdf.set_text_color(255, 59, 48)
    pdf.set_font('Helvetica', 'B', 36)
    pdf.cell(30, 20, str(score), 0, 0)
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 20, f" / 100    ({diagnostics.get('critical',0)} critical, {diagnostics.get('warnings',0)} warnings, {diagnostics.get('passed',0)} passed)", 0, 1)
    pdf.ln(4)

    # Diagnostic Checks
    pdf.section_title("Diagnostic Results")
    for c in diagnostics.get("checks", []):
        color_map = {"good": (0, 255, 136), "warning": (255, 149, 0), "critical": (255, 59, 48)}
        r, g, b = color_map.get(c["status"], (160, 160, 160))
        status_icon = {"good": "[OK]", "warning": "[WARN]", "critical": "[CRIT]"}.get(c["status"], "[?]")

        pdf.set_text_color(r, g, b)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, f"{status_icon} {c['name']} (Severity: {c['severity']}/10)", 0, 1)
        pdf.set_text_color(160, 160, 160)
        pdf.set_font('Helvetica', '', 8)  # Smaller font
        # Clean and truncate text to prevent layout issues
        explanation = c['explanation'].encode('ascii', errors='ignore').decode('ascii')
        explanation = explanation[:400] + "..." if len(explanation) > 400 else explanation
        try:
            pdf.multi_cell(0, 4, explanation, 0, 'L')
        except:
            # Fallback to simple cell if multi_cell fails
            pdf.cell(0, 6, explanation[:100] + "...", 0, 1)
        
        if c['status'] != 'good':
            pdf.set_text_color(0, 122, 255)
            pdf.set_font('Helvetica', 'I', 8)  # Smaller font
            fix_text = c['fix'].encode('ascii', errors='ignore').decode('ascii')
            fix_text = fix_text[:250] + "..." if len(fix_text) > 250 else fix_text
            try:
                pdf.multi_cell(0, 4, f"Fix: {fix_text}", 0, 'L')
            except:
                # Fallback to simple cell if multi_cell fails
                pdf.cell(0, 6, f"Fix: {fix_text[:80]}...", 0, 1)
        pdf.ln(2)

    # Charts
    chart_titles = {
        'attitude': 'Attitude', 'vibration': 'Vibration', 'battery': 'Battery',
        'motors': 'Motor Outputs', 'gps': 'GPS', 'ekf': 'EKF Innovations',
        'fft': 'FFT Spectrum', 'spectrogram': 'Spectrogram',
    }
    for key, title in chart_titles.items():
        if key not in charts:
            continue
        pdf.add_page()
        pdf.set_fill_color(5, 5, 5)
        pdf.rect(0, 0, 210, 297, 'F')
        pdf.section_title(title)
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(charts[key])
            tmp_path = tmp.name
        try:
            pdf.image(tmp_path, x=10, w=190)
        except Exception:
            pass
        finally:
            os.unlink(tmp_path)

    # Peaks table
    if fft_result and fft_result.get("peaks"):
        pdf.ln(8)
        pdf.section_title("Detected Frequency Peaks")
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(60, 6, "Frequency", 0, 0)
        pdf.cell(40, 6, "Magnitude", 0, 0)
        pdf.cell(0, 6, "Harmonic", 0, 1)
        pdf.set_font('Helvetica', '', 9)
        for p in fft_result["peaks"][:8]:
            pdf.set_text_color(220, 220, 220)
            pdf.cell(60, 5, p['label'], 0, 0)
            pdf.cell(40, 5, f"{p['magnitude']:.4f}", 0, 0)
            if p.get('is_harmonic'):
                pdf.set_text_color(255, 149, 0)
                pdf.cell(0, 5, "Yes", 0, 1)
            else:
                pdf.set_text_color(160, 160, 160)
                pdf.cell(0, 5, "No", 0, 1)

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.read()
