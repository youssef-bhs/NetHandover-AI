"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from typing import Dict, List, Optional, Any


class CoveragePredictionRequest(BaseModel):
    """Request for coverage model prediction."""

    model_config = ConfigDict(extra="forbid")

    RSRP: float = Field(..., description="Reference Signal Received Power (dBm)")
    RSRQ: float = Field(..., description="Reference Signal Received Quality (dB)")
    RLC_DL: float = Field(..., description="Downlink throughput indicator")
    PCI: float = Field(..., description="Physical Cell Identity")
    Band_enc: float = Field(..., description="Encoded band index")
    hour: float = Field(..., description="Hour of day")
    minute: float = Field(..., description="Minute of hour")
    second: float = Field(..., description="Second of minute")
    RSRP_lag1: float = Field(..., description="RSRP lag 1")
    RSRP_lag2: float = Field(..., description="RSRP lag 2")
    RSRP_roll3: float = Field(..., description="RSRP rolling mean (3)")
    RSRP_roll5: float = Field(..., description="RSRP rolling mean (5)")
    RSRQ_lag1: float = Field(..., description="RSRQ lag 1")
    RSRQ_lag2: float = Field(..., description="RSRQ lag 2")
    RSRQ_roll3: float = Field(..., description="RSRQ rolling mean (3)")
    RSRQ_roll5: float = Field(..., description="RSRQ rolling mean (5)")
    RLC_DL_lag1: float = Field(..., description="RLC DL lag 1")
    RLC_DL_lag2: float = Field(..., description="RLC DL lag 2")
    RLC_DL_roll3: float = Field(..., description="RLC DL rolling mean (3)")
    RLC_DL_roll5: float = Field(..., description="RLC DL rolling mean (5)")


class CoveragePredictionResult(BaseModel):
    """Coverage prediction result."""

    predicted_class: str
    confidence: float = Field(..., ge=0, le=100)
    probabilities: Dict[str, float]


class CoveragePredictionResponse(BaseModel):
    """Response for coverage prediction endpoint."""

    success: bool
    prediction: CoveragePredictionResult
    message: Optional[str] = None


class QoSPredictionRequest(BaseModel):
    """Request for QoS model prediction."""

    model_config = ConfigDict(extra="forbid")

    rsrp: float = Field(..., description="Reference Signal Received Power (dBm)")
    rsrq: float = Field(..., description="Reference Signal Received Quality (dB)")
    rlc_downlink_throughput: float = Field(
        ..., description="Downlink throughput indicator"
    )
    band: float = Field(..., description="Frequency band")
    physical_cell_identity: float = Field(..., description="Physical Cell ID")


class QoSPredictionResult(BaseModel):
    """QoS prediction result."""

    predicted_class: str
    confidence: Optional[float] = Field(None, ge=0, le=100)
    probabilities: Dict[str, float] = Field(default_factory=dict)


class QoSPredictionResponse(BaseModel):
    """Response for QoS prediction endpoint."""

    success: bool
    prediction: QoSPredictionResult
    message: Optional[str] = None


class ChatRequest(BaseModel):
    """Request for chat/analysis."""

    message: str = Field(..., min_length=1, description="User's question")
    features: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional: feature values for prediction context"
    )
    prediction_id: Optional[str] = Field(None, description="Optional: reference to past prediction")
    model: Optional[str] = Field(
        None,
        description="Gemini model name (e.g., gemini-1.5-flash)"
    )


class ChatResponse(BaseModel):
    """Response for chat endpoint."""

    success: bool
    answer: str
    sources: List[str] = Field(default_factory=list)
    prediction_used: Optional[CoveragePredictionResult] = None
    model_used: str
    tokens_used: Optional[Dict[str, Optional[int]]] = None


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None
