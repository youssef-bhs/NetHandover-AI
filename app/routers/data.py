"""
Data API routes.
Serves dataset information, cell statistics, and data uploads.
"""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from typing import List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["data"])


def _resolve_dataset_path() -> Path:
    candidates = [
        settings.base_dir / "data" / "raw" / "DT2.csv",
        settings.base_dir / "DT2.csv",
        Path("DT2.csv"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


@router.get("/data/sample")
async def get_data_sample(limit: int = 100):
    """
    Get a sample of the dataset (DT2.csv).

    Args:
        limit: Number of rows to return (max 1000)

    Returns:
        JSON with data and column information
    """
    try:
        csv_path = _resolve_dataset_path()
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")

        limit = min(limit, 1000)
        df = pd.read_csv(csv_path, sep=';', nrows=limit)

        return {
            "columns": list(df.columns),
            "rows": len(df),
            "sample": df.to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")


@router.get("/data/info")
async def get_data_info():
    """
    Get dataset information: shape, column types, missing values.
    """
    try:
        csv_path = _resolve_dataset_path()
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")

        df = pd.read_csv(csv_path, sep=';')
        info = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isna().sum().to_dict(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024**2)
        }
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data info: {str(e)}")


@router.get("/cells")
async def get_cell_statistics():
    """
    Get statistics per cell (PSC).
    Returns interference and handover rates from labeled data
    (from output/cell_recommendations.csv if exists, otherwise computes on the fly).
    """
    try:
        # Try to load pre-computed cell recommendations
        rec_path = settings.output_dir / "cell_recommendations.csv"
        if rec_path.exists():
            df = pd.read_csv(rec_path)
            # Convert to list of dicts, sorted by interference rate
            data = df.sort_values('Interference_Rate', ascending=False).to_dict(orient='records')
            return {
                "source": "cached",
                "cells": data[:100]  # Top 100
            }

        # Fallback: compute from raw data
        csv_path = _resolve_dataset_path()
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Dataset not found")

        df_raw = pd.read_csv(csv_path, sep=';', dtype=str)
        df_clean = clean_data(df_raw)

        # Basic cell stats
        cell_stats = df_clean.groupby('psc').agg({
            'rscp': ['mean', 'std', 'count'],
            'ecn0': ['mean', 'std']
        }).round(3)

        # Flatten column names
        cell_stats.columns = ['_'.join(col).strip() for col in cell_stats.columns]
        cell_stats = cell_stats.reset_index()
        cell_stats.columns = ['PSC', 'rscp_mean', 'rscp_std', 'count', 'ecn0_mean', 'ecn0_std']

        # Sort by count (most samples first)
        cell_stats = cell_stats.sort_values('count', ascending=False)

        return {
            "source": "computed",
            "cells": cell_stats.head(100).to_dict(orient='records')
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cell statistics: {str(e)}")


@router.get("/plots/{plot_name}")
async def get_plot(plot_name: str):
    """
    Serve generated plots from output/plots/ directory.

    Args:
        plot_name: Filename of the plot (e.g., 'confusion_matrices.png')

    Returns:
        Image file response
    """
    try:
        plot_path = settings.output_dir / "plots" / plot_name
        if not plot_path.exists():
            raise HTTPException(status_code=404, detail="Plot not found")

        from fastapi.responses import FileResponse
        return FileResponse(
            str(plot_path),
            media_type="image/png",
            filename=plot_name
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve plot: {str(e)}")


# Import clean_data for fallback computation
from app.utils.preprocessing import clean_data
