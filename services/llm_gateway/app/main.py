from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import LLMGenerateRequest, LLMGenerateResponse
from app.providers.deepseek import DeepSeekProvider
from app.rate_limit import check_rate_limit
from app.cost_control import record_audit_log
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_gateway")

# Base.metadata.create_all(bind=engine) # Tabelas já devem vir do migration central ou create_compliance_tables

app = FastAPI(title="Aracannabis LLM Gateway", version="1.0.0")

# Provider Factory
def get_provider(name: str):
    if name == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise HTTPException(500, "DeepSeek API Key not configured")
        return DeepSeekProvider(api_key=api_key)
    
    if name == "zhipu":
        api_key = os.getenv("ZHIPU_API_KEY")
        if not api_key:
            raise HTTPException(500, "Zhipu API Key not configured")
        return ZhipuProvider(api_key=api_key)

    if name == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(500, "Google API Key not configured")
        return GoogleProvider(api_key=api_key)

    raise HTTPException(400, f"Provider {name} not supported")

@app.post("/generate", response_model=LLMGenerateResponse)
async def generate_response(
    request: LLMGenerateRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    # 1. Rate Limiting (Multi-tenant)
    if not check_rate_limit(request.tenant_id):
        raise HTTPException(429, "Rate limit exceeded for tenant")

    # 2. Select Provider
    provider = get_provider(request.provider)
    
    try:
        # 3. Call External LLM (Network Egress allowed here)
        result = await provider.generate_completion(
            anonymized_text=request.anonymized_text,
            task=request.task
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 4. Audit Log (Async via BackgroundTasks ou depois do await)
        # Vamos fazer síncrono para garantir persistência antes de responder
        metrics = {
            "tokens_input": result["tokens_input"],
            "tokens_output": result["tokens_output"],
            "duration": duration_ms
        }
        
        record_audit_log(
            session=db,
            request_data=request.dict(),
            metrics=metrics,
            status="success"
        )
        
        return LLMGenerateResponse(
            output=result["output"],
            tokens_used=result["tokens_input"] + result["tokens_output"],
            provider=request.provider,
            processing_time_ms=duration_ms,
            status="success"
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"LLM Generation Error: {e}")
        
        # Log failure
        record_audit_log(
            session=db,
            request_data=request.dict(),
            metrics={"duration": duration_ms},
            status="error",
            error=str(e)
        )
        
        raise HTTPException(502, "Failed to generate LLM response")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "llm_gateway"}
