"""
Coverage prediction API routes.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.coverage_service import coverage_service
from app.models.schemas import (
    CoveragePredictionRequest,
    CoveragePredictionResponse,
    CoveragePredictionResult
)

router = APIRouter(prefix="/api", tags=["coverage"])
logger = logging.getLogger(__name__)


@router.post("/coverage/predict", response_model=CoveragePredictionResponse)
async def predict_coverage(request: CoveragePredictionRequest):
    """Predict network coverage class using the coverage model."""
    try:
        if not coverage_service.is_loaded:
            loaded = coverage_service.load_model()
            if not loaded:
                raise HTTPException(
                    status_code=500,
                    detail="Coverage model not loaded. Verify the model path and restart the service."
                )

        features = request.model_dump()
        logger.info("Coverage request features: %s", features)
        result = coverage_service.predict(features)

        return CoveragePredictionResponse(
            success=True,
            prediction=CoveragePredictionResult(**result)
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Coverage prediction failed: {exc}")


@router.get("/coverage/health")
async def coverage_health():
    """Health endpoint for coverage model."""
    return coverage_service.get_status()
