from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
from app.database import (
    get_all_interactions, init_db, get_candidates, save_candidates,
    update_message_status, get_messages_for_candidate, update_response
)
from datetime import datetime
from statistics import mean
from fastapi.responses import StreamingResponse
import csv
from io import StringIO, BytesIO
import os
from dotenv import load_dotenv
from app.nodes.search import search_linkedin
from app.nodes.message_generator import create_and_save_message

load_dotenv()

app = FastAPI(title="Message Generator API")

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

init_db()

class CandidateData(BaseModel):
    id: str
    name: str
    experience: str | None = None
    current_company: str | None = None
    role_desc: str | None = None
    cta: str | None = None

class ResponseData(BaseModel):
    msg_id: int
    response: str

class SearchConfig(BaseModel):
    keywords: List[str] = ["AI Engineer"]
    location: str = ""
    company: str = ""
    min_exp: int = 0
    max_results: int = 10

@app.post("/generate")
async def generate_message(data: dict):
    try:
        result = create_and_save_message(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/accept-message/{msg_id}")
async def accept_message(msg_id: int):
    try:
        updated = update_message_status(msg_id, 'sent')
        if not updated:
            raise HTTPException(status_code=404, detail="Message not found")
        return {"updated": True, "msg_id": msg_id, "status": "sent"}
    except Exception as e:
        print(f"Accept error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/track/{candidate_id}")
def get_tracking(candidate_id: str) -> list[Dict[str, Any]]:
    messages = get_messages_for_candidate(candidate_id)
    if not messages:
        print(f"No messages for candidate_id: {candidate_id}")
    for m in messages:
        if m['sent_date']:
            m['sent_date'] = m['sent_date'].isoformat() if hasattr(m['sent_date'], 'isoformat') else str(m['sent_date'])
        if m['response_date']:
            m['response_date'] = m['response_date'].isoformat() if hasattr(m['response_date'], 'isoformat') else str(m['response_date'])
    return messages

@app.post("/update-response")
def log_response(data: ResponseData):
    update_response(data.msg_id, data.response)
    return {"status": "updated"}

@app.get("/interactions")
def get_all_interactions_endpoint():
    interactions = get_all_interactions()
    for i in interactions:
        if i['sent_date']:
            i['sent_date'] = i['sent_date'].isoformat() if hasattr(i['sent_date'], 'isoformat') else str(i['sent_date'])
        if i['response_date']:
            i['response_date'] = i['response_date'].isoformat() if hasattr(i['response_date'], 'isoformat') else str(i['response_date'])
    return interactions

@app.get("/metrics")
def get_effectiveness_metrics():
    interactions = get_all_interactions()
    total_sent = len(interactions)
    total_replies = sum(1 for i in interactions if i['response'] is not None)
    reply_rate = (total_replies / total_sent * 100) if total_sent > 0 else 0
    response_times = []
    for i in interactions:
        if i['response'] and i['sent_date'] and i['response_date']:
            sent_dt = datetime.fromisoformat(i['sent_date']) if isinstance(i['sent_date'], str) else i['sent_date']
            resp_dt = datetime.fromisoformat(i['response_date']) if isinstance(i['response_date'], str) else i['response_date']
            delta = resp_dt - sent_dt
            days = delta.total_seconds() / (24 * 3600)
            response_times.append(days)
    avg_response_time = mean(response_times) if response_times else 0
    return {
        "total_messages_sent": total_sent,
        "total_replies": total_replies,
        "reply_rate_percent": round(reply_rate, 1),
        "avg_response_time_days": round(avg_response_time, 1)
    }

@app.get("/export-report")
def export_report():
    interactions = get_all_interactions()
    metrics = get_effectiveness_metrics()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Report Generated:', datetime.now().isoformat(),
        'Total Sent:', metrics['total_messages_sent'],
        'Total Replies:', metrics['total_replies'],
        'Reply Rate %:', f"{metrics['reply_rate_percent']}%",
        'Avg Response Time Days:', f"{metrics['avg_response_time_days']:.1f}"
    ])
    writer.writerow([])
    writer.writerow([
        'Message ID', 'Candidate ID', 'Candidate Name',
        'Message Preview', 'Sent Date', 'Response', 'Response Date', 'Status'
    ])
    for i in interactions:
        preview = (i['message'][:100] + '...') if i['message'] and len(i['message']) > 100 else (i['message'] or 'N/A')
        sent_str = str(i['sent_date']) if i['sent_date'] else 'N/A'
        resp_str = i['response'] if i['response'] else 'N/A'
        resp_date_str = str(i['response_date']) if i['response_date'] else 'N/A'
        writer.writerow([
            i['id'], i['candidate_id'], i['candidate_name'] or 'Unknown',
            preview, sent_str, resp_str, resp_date_str, i['status'] or 'N/A'
        ])
    output.seek(0)
    csv_content = output.getvalue()
    return StreamingResponse(
        BytesIO(csv_content.encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=candidate-report-{datetime.now().strftime('%Y-%m-%d')}.csv"}
    )

@app.post("/search")
def perform_search(config: SearchConfig):
    try:
        config_dict = config.dict()
        if config.max_results:
            config_dict['max_results'] = config.max_results
        profiles = search_linkedin(config_dict)
        saved_count = save_candidates(profiles)
        all_candidates = get_candidates()
        return {
            "profiles_found": profiles,
            "saved_to_db": saved_count,
            "total_candidates": len(all_candidates),
            "candidates": all_candidates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}. Check .env creds, CAPTCHA, or LinkedIn access.")

@app.get("/candidates")
def list_candidates():
    return get_candidates()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
