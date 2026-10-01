"""
QoS prediction API routes.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    QoSPredictionRequest,
    QoSPredictionResponse,
    QoSPredictionResult,
)
from app.qos_service import qos_service

router = APIRouter(prefix="/api", tags=["qos"])
logger = logging.getLogger(__name__)


@router.post("/qos/predict", response_model=QoSPredictionResponse)
async def predict_qos(request: QoSPredictionRequest):
    """Predict QoS class using the QoS model."""
    try:
        if not qos_service.is_loaded:
            loaded = qos_service.load_model()
            if not loaded:
                raise HTTPException(
                    status_code=500,
                    detail="QoS model not loaded. Verify the model path and restart the service.",
                )

        raw = request.model_dump()
        logger.info("QoS raw inputs: %s", raw)
        result = qos_service.predict(raw)

        return QoSPredictionResponse(
            success=True,
            prediction=QoSPredictionResult(**result),
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"QoS prediction failed: {exc}")


@router.get("/qos/health")
async def qos_health():
    """Health endpoint for the QoS model."""
    return qos_service.get_status()
