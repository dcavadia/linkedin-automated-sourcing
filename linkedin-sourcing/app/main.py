from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from app.database import get_all_interactions
from datetime import datetime
from statistics import mean  # For avg response time
from fastapi.responses import StreamingResponse
import csv
from io import StringIO




from app.nodes.message_generator import create_and_save_message, get_messages_for_candidate
from app.database import update_response

app = FastAPI(title="Message Generator API")

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class CandidateData(BaseModel):
    id: str
    name: str
    experience: str | None = None
    current_company: str | None = None

class ResponseData(BaseModel):
    msg_id: int
    response: str

@app.post("/generate")
def generate_message(candidate: CandidateData) -> Dict[str, Any]:
    try:
        result = create_and_save_message(candidate.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/track/{candidate_id}")
def get_tracking(candidate_id: str) -> list[Dict[str, Any]]:
    return get_messages_for_candidate(candidate_id)

@app.post("/update-response")
def log_response(data: ResponseData):
    update_response(data.msg_id, data.response)  # This now sets response_date and status internally
    return {"status": "updated"}

@app.get("/interactions")
def get_all_interactions_endpoint():
    interactions = get_all_interactions()
    # Convert datetimes to ISO strings for JSON (handles None safely)
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
    
    # Calculate avg response time (in days; only for replied messages with dates)
    response_times = []
    for i in interactions:
        if i['response'] and i['sent_date'] and i['response_date']:
            # Parse datetimes (SQLite returns strings or datetime objects)
            sent_dt = datetime.fromisoformat(i['sent_date']) if isinstance(i['sent_date'], str) else i['sent_date']
            resp_dt = datetime.fromisoformat(i['response_date']) if isinstance(i['response_date'], str) else i['response_date']
            delta = resp_dt - sent_dt
            days = delta.total_seconds() / (24 * 3600)  # Convert to days
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
    metrics = get_effectiveness_metrics()  # Reuse your metrics func (safe)
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header row with metrics summary (unchanged; datetime.now() is a datetime object)
    writer.writerow([
        'Report Generated:', datetime.now().isoformat(),
        'Total Sent:', metrics['total_messages_sent'],
        'Total Replies:', metrics['total_replies'],
        'Reply Rate %:', f"{metrics['reply_rate_percent']}%",
        'Avg Response Time Days:', metrics['avg_response_time_days']
    ])
    writer.writerow([])  # Empty row for spacing
    
    # Data rows: All interactions (fixed date handling)
    writer.writerow([
        'Message ID', 'Candidate ID', 'Candidate Name', 'Current Company', 
        'Message Preview', 'Sent Date', 'Response', 'Response Date', 'Status'
    ])
    for i in interactions:
        preview = (i['message'][:100] + '...') if i['message'] else 'N/A'
        
        # Fixed: Handle sent_date as string (SQLite format) or None
        sent_str = str(i['sent_date']) if i['sent_date'] else 'N/A'
        
        # Fixed: Handle response as string or None
        resp_str = i['response'] if i['response'] else 'N/A'
        
        # Fixed: Handle response_date as string or None
        resp_date_str = str(i['response_date']) if i['response_date'] else 'N/A'
        
        writer.writerow([
            i['id'], i['candidate_id'], i['candidate_name'] or 'Unknown', 
            i['current_company'] or 'Unknown', preview, sent_str, 
            resp_str, resp_date_str, i['status'] or 'N/A'
        ])
    
    output.seek(0)
    csv_content = output.getvalue()
    return StreamingResponse(
        iter([csv_content]), 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename=linkedin_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"}
    )



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
