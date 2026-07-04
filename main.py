import time
import uuid
from typing import List
from fastapi import FastAPI, Query, Request, Response, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# --- ASSIGNED CONFIGURATION VALUES ---
ASSIGNED_ORIGIN = "https://dash-cv7skh.example.com"
MY_EMAIL = "24f2006763@ds.study.iitm.ac.in"  # <-- CHANGE THIS to your actual logged-in email address

# --- MIDDLEWARE FOR PROCESS TIME, REQUEST ID, AND STRICT CORS ---
@app.middleware("http")
async def process_and_cors_middleware(request: Request, call_next):
    start_time = time.time()
    
    # 1. Generate or grab Request ID
    request_id = str(uuid.uuid4())
    
    # Handle preflight OPTIONS requests manually to guarantee strict origin isolation
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin")
        response = Response(status_code=200)
        
        if origin == ASSIGNED_ORIGIN:
            response.headers["Access-Control-Allow-Origin"] = ASSIGNED_ORIGIN
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "X-Request-ID, Content-Type"
        # If origin doesn't match, we return 200 without adding any ACAO headers (browser blocks it)
        
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.6f}"
        return response

    # Execute downstream request pipeline handlers
    try:
        response = await call_next(request)
    except Exception as e:
        response = JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    # 2. Append standard process profiling headers
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    
    # 3. Apply Strict Origin CORS Enforcement on normal responses
    origin = request.headers.get("Origin")
    if origin == ASSIGNED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = ASSIGNED_ORIGIN
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"

    return response

# --- STATS CALCULATION ENDPOINT ---
@app.get("/stats")
async def get_stats(values: str = Query(..., description="Comma-separated list of integers")):
    if not values.strip():
        raise HTTPException(status_code=400, detail="Values parameter cannot be empty")
        
    try:
        # Parse out raw string input stream into functional array integers
        parsed_numbers: List[int] = [int(v.strip()) for v in values.split(",") if v.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid character input detected. All values must be integers.")

    if not parsed_numbers:
        raise HTTPException(status_code=400, detail="No valid numbers found to aggregate")

    # Compute descriptive parameters safely
    n_count = len(parsed_numbers)
    s_sum = sum(parsed_numbers)
    m_min = min(parsed_numbers)
    x_max = max(parsed_numbers)
    f_mean = float(s_sum) / n_count

    return {
        "email": MY_EMAIL,
        "count": n_count,
        "sum": s_sum,
        "min": m_min,
        "max": x_max,
        "mean": round(f_mean, 4)
    }