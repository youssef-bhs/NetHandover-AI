"""
Chat API routes.
Handles RAG-enhanced conversations with LLM, integrated with predictions.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
import google.generativeai as genai

from app.config import settings
from app.coverage_service import coverage_service
from app.qos_service import qos_service
RAG_IMPORT_ERROR = None
try:
    from app.rag_service import rag_service
except Exception as exc:
    rag_service = None
    RAG_IMPORT_ERROR = str(exc)
from app.models.schemas import ChatRequest, ChatResponse, CoveragePredictionResult

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)


def _normalize_model_name(model_name: Optional[str]) -> Optional[str]:
    if not model_name:
        return model_name
    return model_name if model_name.startswith("models/") else f"models/{model_name}"


def _llm_only_answer(
    message: str,
    prediction: Optional[Dict[str, Any]],
    model: Optional[str],
    rag_error: Optional[str] = None
) -> Dict[str, Any]:
    """Fallback chat response without RAG retrieval."""
    model_to_use = _normalize_model_name(model or settings.gemini_model)
    genai.configure(api_key=settings.gemini_api_key)

    system_prompt = (
        "You are a senior network engineer specializing in coverage and QoS "
        "assessment. Provide concise, technical, actionable answers based on "
        "RSRP, RSRQ, throughput, band, PCI, and temporal patterns."
    )

    context_lines = []
    if prediction:
        context_lines.append("Prediction context:")
        prediction_type = prediction.get('prediction_type')
        predicted_class = prediction.get('predicted_class')
        confidence = prediction.get('confidence')
        probabilities = prediction.get('probabilities', {})
        if prediction_type:
            context_lines.append(f"- Type: {prediction_type}")
        if predicted_class:
            context_lines.append(f"- Predicted Class: {predicted_class}")
        if confidence is not None:
            context_lines.append(f"- Confidence: {confidence:.2f}%")
        if probabilities:
            prob_text = ", ".join(
                f"{label}: {float(value) * 100:.2f}%" for label, value in probabilities.items()
            )
            context_lines.append(f"- Probabilities: {prob_text}")

    if rag_error:
        context_lines.append("Note: RAG knowledge base is unavailable.")

    user_prompt = "\n".join(context_lines + ["", f"User question: {message}"])

    model_client = genai.GenerativeModel(
        model_name=model_to_use,
        system_instruction=system_prompt
    )

    try:
        response = model_client.generate_content(
            user_prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 1200
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM request failed: {exc}")

    answer = getattr(response, "text", None) or ""
    if not answer and getattr(response, "candidates", None):
        parts = response.candidates[0].content.parts if response.candidates[0].content else []
        answer = "".join([getattr(part, "text", "") for part in parts]).strip()

    if not answer:
        raise HTTPException(status_code=500, detail="LLM request failed: empty response")

    usage = getattr(response, "usage_metadata", None)
    if isinstance(usage, dict):
        prompt_tokens = usage.get("prompt_token_count")
        completion_tokens = usage.get("candidates_token_count")
    else:
        prompt_tokens = getattr(usage, "prompt_token_count", None) if usage else None
        completion_tokens = getattr(usage, "candidates_token_count", None) if usage else None

    return {
        "answer": answer,
        "model_used": model_to_use,
        "sources": [],
        "tokens_used": {
            "prompt": prompt_tokens,
            "completion": completion_tokens
        }
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with telecom specialist AI.

    This endpoint combines:
    1. Optional coverage prediction (if features provided)
    2. RAG retrieval from knowledge base
    3. Gemini LLM analysis

    You can provide:
    - Just a question (pure RAG Q&A)
    - Features dictionary → will predict first, then analyze with prediction context
    - prediction_id to reference a past prediction
    """
    try:
        rag_error = RAG_IMPORT_ERROR
        if rag_service:
            try:
                if not rag_service.is_initialized:
                    initialized = rag_service.initialize()
                    if not initialized:
                        rag_error = "RAG initialization failed. Check server logs."
            except Exception as exc:
                rag_error = str(exc)

        # Step 1: Get prediction if features provided
        prediction_result = None
        if request.features:
            feature_keys = set(request.features.keys())
            qos_keys = {
                'rsrp',
                'rsrq',
                'rlc_downlink_throughput',
                'band',
                'physical_cell_identity',
            }
            if qos_keys.issubset(feature_keys):
                if not qos_service.is_loaded:
                    success = qos_service.load_model()
                    if not success:
                        raise HTTPException(
                            status_code=500,
                            detail="QoS model not available. Check the model path."
                        )
                pred_results = qos_service.predict(request.features)
                prediction_result = {
                    'prediction_type': 'qos',
                    'predicted_class': pred_results.get('predicted_class'),
                    'confidence': pred_results.get('confidence'),
                    'probabilities': pred_results.get('probabilities')
                }
            else:
                if not coverage_service.is_loaded:
                    success = coverage_service.load_model()
                    if not success:
                        raise HTTPException(
                            status_code=500,
                            detail="Coverage model not available. Check the model path."
                        )

                pred_results = coverage_service.predict(request.features)
                prediction_result = {
                    'prediction_type': 'coverage',
                    'predicted_class': pred_results.get('predicted_class'),
                    'confidence': pred_results.get('confidence'),
                    'probabilities': pred_results.get('probabilities')
                }

        # Step 2: Analyze with LLM using RAG, or fallback to LLM-only
        if rag_service and rag_service.is_initialized:
            analysis = rag_service.analyze(
                question=request.message,
                prediction=prediction_result,
                model=_normalize_model_name(request.model)
            )
        else:
            analysis = _llm_only_answer(
                request.message,
                prediction_result,
                _normalize_model_name(request.model),
                rag_error
            )

        if analysis.get('error'):
            raise HTTPException(status_code=500, detail=analysis['answer'])

        return ChatResponse(
            success=True,
            answer=analysis['answer'],
            sources=analysis.get('sources', []),
            prediction_used=CoveragePredictionResult(**prediction_result) if prediction_result else None,
            model_used=analysis.get('model_used', settings.gemini_model),
            tokens_used=analysis.get('tokens_used')
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/chat/status")
async def chat_status():
    """Get RAG and LLM status."""
    if rag_service:
        status = rag_service.get_status()
    else:
        status = {
            "initialized": False,
            "document_count": 0,
            "llm_model": settings.gemini_model,
            "embedding_model": None,
            "error": RAG_IMPORT_ERROR
        }
    return {
        "rag_initialized": status.get('initialized', False),
        "document_count": status.get('document_count', 0),
        "llm_model": status.get('llm_model'),
        "embedding_model": status.get('embedding_model'),
        "rag_error": status.get('error')
    }
