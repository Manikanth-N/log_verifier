from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from log_parser import LogParser, generate_demo_log
from signal_processor import SignalProcessor
from diagnostics_engine import DiagnosticsEngine
from ai_insights import AIInsights
from chart_generator import generate_multi_signal_chart, generate_all_report_charts
from report_generator import generate_pdf_report, generate_html_report, generate_markdown_report

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'ardupilot_analyzer')]


app = FastAPI(title="Vehicle Log Analyzer API")
api_router = APIRouter(prefix="/api")

# In-memory cache for parsed log data
log_data_cache: Dict[str, Dict] = {}

# Initialize engines
signal_processor = SignalProcessor()
diagnostics_engine = DiagnosticsEngine()
ai_insights = AIInsights()

UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Request Models ---
class SignalRequest(BaseModel):
    signals: List[Dict[str, str]]
    time_range: Optional[List[float]] = None
    max_points: int = 2000

class FFTRequest(BaseModel):
    signal_type: str
    signal_field: str
    window_size: int = 1024
    overlap: float = 0.5
    time_range: Optional[List[float]] = None

class AIRequest(BaseModel):
    context: Optional[str] = None


class ChartExportRequest(BaseModel):
    signals: List[Dict[str, str]]
    format: str = "png"
    title: str = "Signal Plot"


# --- Routes ---
@api_router.get("/")
async def root():
    return {"message": "Vehicle Log Analyzer API", "version": "1.0.0"}


@api_router.post("/logs/demo")
async def create_demo_log():
    log_id = str(uuid.uuid4())
    demo_data = generate_demo_log()
    log_data_cache[log_id] = demo_data

    metadata = {
        "log_id": log_id,
        "filename": "demo_flight.bin",
        "upload_date": datetime.now(timezone.utc).isoformat(),
        "file_size": 0,
        "duration_sec": demo_data["duration_sec"],
        "message_types": list(demo_data["signals"].keys()),
        "vehicle_type": demo_data.get("vehicle_type", "QuadCopter"),
        "firmware": demo_data.get("firmware", "ArduCopter V4.4.0"),
        "is_demo": True,
        "total_messages": sum(
            len(v.get("TimeUS", [])) for v in demo_data["signals"].values() if isinstance(v, dict)
        ),
    }
    await db.logs.insert_one({**metadata})
    metadata.pop("_id", None)
    return metadata


@api_router.post("/logs/upload")
async def upload_log(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.bin', '.log'):
        raise HTTPException(400, "Unsupported file type. Use .bin or .log files.")

    log_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{log_id}{ext}"
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        parser = LogParser()
        parsed_data = parser.parse_file(str(file_path))
        log_data_cache[log_id] = parsed_data
    except Exception as e:
        logger.error(f"Parse error: {e}")
        raise HTTPException(500, f"Failed to parse log: {str(e)}")

    metadata = {
        "log_id": log_id,
        "filename": file.filename,
        "upload_date": datetime.now(timezone.utc).isoformat(),
        "file_size": len(content),
        "duration_sec": parsed_data["duration_sec"],
        "message_types": list(parsed_data["signals"].keys()),
        "vehicle_type": parsed_data.get("vehicle_type", "Unknown"),
        "firmware": parsed_data.get("firmware", "Unknown"),
        "is_demo": False,
        "total_messages": sum(
            len(v.get("TimeUS", [])) for v in parsed_data["signals"].values() if isinstance(v, dict)
        ),
    }
    await db.logs.insert_one({**metadata})
    metadata.pop("_id", None)
    return metadata


@api_router.get("/logs")
async def list_logs():
    logs = await db.logs.find({}, {"_id": 0}).sort("upload_date", -1).to_list(100)
    return logs


@api_router.get("/logs/{log_id}")
async def get_log(log_id: str):
    log = await db.logs.find_one({"log_id": log_id}, {"_id": 0})
    if not log:
        raise HTTPException(404, "Log not found")
    return log


@api_router.delete("/logs/{log_id}")
async def delete_log(log_id: str):
    result = await db.logs.delete_one({"log_id": log_id})
    log_data_cache.pop(log_id, None)
    if result.deleted_count == 0:
        raise HTTPException(404, "Log not found")
    return {"message": "Log deleted"}


@api_router.get("/logs/{log_id}/signals")
async def get_signals(log_id: str):
    if log_id not in log_data_cache:
        raise HTTPException(404, "Log data not in cache. Please re-upload or load demo.")
    data = log_data_cache[log_id]
    signals = {}
    for msg_type, fields in data["signals"].items():
        if isinstance(fields, dict):
            signals[msg_type] = [k for k in fields.keys() if k != "TimeUS"]
    return {"log_id": log_id, "signals": signals}


@api_router.post("/logs/{log_id}/data")
async def get_signal_data(log_id: str, request: SignalRequest):
    if log_id not in log_data_cache:
        raise HTTPException(404, "Log data not in cache")
    data = log_data_cache[log_id]
    result = []

    for sig in request.signals:
        msg_type = sig.get("type", "")
        field = sig.get("field", "")
        if msg_type not in data["signals"]:
            continue
        sig_data = data["signals"][msg_type]
        if not isinstance(sig_data, dict) or field not in sig_data or "TimeUS" not in sig_data:
            continue

        timestamps = list(sig_data["TimeUS"])
        values = list(sig_data[field])

        # Time range filter
        if request.time_range and len(request.time_range) == 2:
            start, end = request.time_range
            filtered = [(t, v) for t, v in zip(timestamps, values) if start <= t <= end]
            if filtered:
                timestamps, values = zip(*filtered)
                timestamps, values = list(timestamps), list(values)
            else:
                timestamps, values = [], []

        # Downsample using LTTB
        if len(timestamps) > request.max_points:
            timestamps, values = signal_processor.downsample_lttb(
                timestamps, values, request.max_points
            )

        result.append({
            "type": msg_type,
            "field": field,
            "timestamps": timestamps,
            "values": values,
            "count": len(timestamps),
        })

    return {"log_id": log_id, "data": result}


@api_router.post("/logs/{log_id}/fft")
async def get_fft_analysis(log_id: str, request: FFTRequest):
    if log_id not in log_data_cache:
        raise HTTPException(404, "Log data not in cache")
    data = log_data_cache[log_id]

    if request.signal_type not in data["signals"]:
        raise HTTPException(400, f"Signal type {request.signal_type} not found")
    sig_data = data["signals"][request.signal_type]
    if not isinstance(sig_data, dict):
        raise HTTPException(400, "Invalid signal data")
    if request.signal_field not in sig_data or "TimeUS" not in sig_data:
        raise HTTPException(400, f"Field {request.signal_field} not found")

    timestamps = list(sig_data["TimeUS"])
    values = list(sig_data[request.signal_field])

    if request.time_range and len(request.time_range) == 2:
        start, end = request.time_range
        filtered = [(t, v) for t, v in zip(timestamps, values) if start <= t <= end]
        if filtered:
            timestamps, values = zip(*filtered)
            timestamps, values = list(timestamps), list(values)

    fft_result = signal_processor.compute_fft(
        timestamps, values, window_size=request.window_size, overlap=request.overlap
    )
    spectrogram = signal_processor.compute_spectrogram(
        timestamps, values, window_size=min(request.window_size, 256), overlap=request.overlap
    )

    return {
        "log_id": log_id,
        "signal": f"{request.signal_type}.{request.signal_field}",
        "fft": fft_result,
        "spectrogram": spectrogram,
    }


@api_router.get("/logs/{log_id}/diagnostics")
async def get_diagnostics(log_id: str):
    if log_id not in log_data_cache:
        raise HTTPException(404, "Log data not in cache")
    data = log_data_cache[log_id]
    results = diagnostics_engine.analyze(data)
    return {"log_id": log_id, "diagnostics": results}


@api_router.post("/logs/{log_id}/ai-insights")
async def get_ai_insights(log_id: str, request: AIRequest):
    if log_id not in log_data_cache:
        raise HTTPException(404, "Log data not in cache")
    data = log_data_cache[log_id]
    diagnostics = diagnostics_engine.analyze(data)
    insights = await ai_insights.analyze(diagnostics, request.context)
    return {"log_id": log_id, "insights": insights}


@api_router.get("/logs/{log_id}/export")
async def export_data(log_id: str, message_type: str = "ATT"):
    if log_id not in log_data_cache:
        raise HTTPException(404, "Log data not in cache")
    data = log_data_cache[log_id]
    if message_type not in data["signals"]:
        raise HTTPException(400, f"Message type {message_type} not found")
    sig_data = data["signals"][message_type]
    if not isinstance(sig_data, dict):
        raise HTTPException(400, "Invalid signal data")
    csv_content = signal_processor.to_csv(sig_data)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={message_type}_export.csv"},
    )


@api_router.get("/logs/{log_id}/report")
async def generate_report(log_id: str, format: str = Query("pdf", enum=["pdf", "html", "md"])):
    """Generate a comprehensive flight analysis report."""
    if log_id not in log_data_cache:
        raise HTTPException(404, "Log data not in cache")
    
    data = log_data_cache[log_id]
    log_meta = await db.logs.find_one({"log_id": log_id}, {"_id": 0})
    if not log_meta:
        raise HTTPException(404, "Log metadata not found")
    
    # Run diagnostics
    diagnostics = diagnostics_engine.analyze(data)
    
    # Generate charts for PDF/HTML
    charts = {}
    if format in ("pdf", "html"):
        try:
            charts = generate_all_report_charts(data["signals"])
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
    
    # Generate the report
    if format == "pdf":
        content = generate_pdf_report(log_meta, diagnostics, charts)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=flight_report.pdf"},
        )
    elif format == "html":
        content = generate_html_report(log_meta, diagnostics, charts)
        return Response(
            content=content.encode('utf-8'),
            media_type="text/html",
            headers={"Content-Disposition": "attachment; filename=flight_report.html"},
        )
    else:  # markdown
        content = generate_markdown_report(log_meta, diagnostics)
        return Response(
            content=content.encode('utf-8'),
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=flight_report.md"},
        )


@api_router.post("/logs/{log_id}/export-chart")
async def export_chart(log_id: str, request: ChartExportRequest):
    """Export a chart as PNG or SVG image."""
    if log_id not in log_data_cache:
        raise HTTPException(404, "Log data not in cache")
    
    data = log_data_cache[log_id]
    signals = data["signals"]
    
    fmt = request.format.lower()
    if fmt not in ("png", "svg"):
        raise HTTPException(400, "Format must be 'png' or 'svg'")
    
    try:
        chart_bytes = generate_multi_signal_chart(
            signals,
            request.signals,
            title=request.title,
            fmt=fmt,
        )
    except Exception as e:
        logger.error(f"Chart export failed: {e}")
        raise HTTPException(500, f"Chart generation failed: {str(e)}")
    
    content_type = "image/png" if fmt == "png" else "image/svg+xml"
    return Response(
        content=chart_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename=chart.{fmt}"},
    )


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
