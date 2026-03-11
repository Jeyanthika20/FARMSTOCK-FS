from fastapi import APIRouter, Request
from app.models.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health(request: Request):
    svc  = request.app.state.model_service
    meta = svc.model_info if svc._loaded else {}
    return HealthResponse(
        status       = "healthy" if svc._loaded else "model_not_loaded",
        model_loaded = svc._loaded,
        model_name   = meta.get('best_model', 'N/A'),
        version      = "2.0.0",
    )

@router.get("/crops")
def get_crops(request: Request):
    svc = request.app.state.model_service
    return {"crops": svc.crops, "total": len(svc.crops)}

@router.get("/markets")
def get_markets(request: Request):
    svc = request.app.state.model_service
    return {"markets": svc.markets, "total": len(svc.markets)}

@router.get("/model/info")
def model_info(request: Request):
    return request.app.state.model_service.model_info
