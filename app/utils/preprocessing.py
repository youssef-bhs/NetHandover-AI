"""
Preprocessing utilities for UMTS interference and handover prediction.
Reused from training notebooks.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw UMTS data.

    Steps:
    - Rename columns to short names
    - Remove empty rows
    - Handle comma-separated multi-values (take first)
    - Convert numeric columns
    - Parse timestamps
    - Drop rows with missing critical values
    - Remove duplicates
    - Clip to realistic ranges
    """
    df = df.copy()

    # Rename columns
    cols = {
        'Time': 'time',
        'Band (active)': 'band',
        'Channel number (active)': 'uarfcn',
        'Scrambling code (active)': 'psc',
        'RSCP (active)': 'rscp',
        'Ec/N0 (active)': 'ecn0',
        'RSCP (detected)': 'rscp_det',
        'Scrambling code (detected)': 'psc_det'
    }
    df = df.rename(columns=cols)

    # Remove rows where ALL columns are empty/whitespace
    em = df.apply(lambda r: r.astype(str).str.strip().eq('').all(), axis=1)
    df = df[~em].copy()

    # Handle comma-separated values: take first (primary serving cell)
    for c in ['band', 'uarfcn', 'psc', 'rscp', 'ecn0', 'psc_det', 'rscp_det']:
        df[c] = df[c].apply(
            lambda x: str(x).split(',')[0].strip()
            if pd.notna(x) and ',' in str(x) else x
        )

    # Convert numeric columns
    for c in ['uarfcn', 'psc', 'rscp', 'ecn0', 'rscp_det', 'psc_det']:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    # Parse time
    df['time'] = pd.to_datetime(
        df['time'], format='%H:%M:%S.%f', exact=False, errors='coerce'
    )

    # Drop rows missing critical data
    before = len(df)
    df = df.dropna(subset=['time', 'psc', 'rscp', 'ecn0'])
    df = df.reset_index(drop=True)

    # Drop duplicates
    before = len(df)
    df = df.drop_duplicates()
    df = df.reset_index(drop=True)

    # Clip to realistic ranges
    df['rscp'] = df['rscp'].clip(-120, -25)
    df['ecn0'] = df['ecn0'].clip(-30, 5)

    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer features for ML models.

    Features:
    - delta_rscp: RSCP(active) - RSCP(detected)
    - has_neighbor: indicator if neighbor detected
    - Rolling means (5, 10) for RSCP and Ec/N0 by cell
    - Rolling std for Ec/N0
    - Differentials (first difference)
    - Cell-level aggregates (mean, min, max, std)
    - Relative to cell mean
    """
    df = df.copy().sort_values(['psc', 'time']).reset_index(drop=True)

    # Base signal gap
    df['delta_rscp'] = df['rscp'] - df['rscp_det']
    df['delta_rscp'] = df['delta_rscp'].fillna(0)
    df['has_neighbor'] = df['rscp_det'].notna().astype(int)

    # Cell averages
    df['psc_rscp_mean'] = df.groupby('psc')['rscp'].transform('mean')
    df['psc_ecn0_mean'] = df.groupby('psc')['ecn0'].transform('mean')
    df['rscp_vs_mean'] = df['rscp'] - df['psc_rscp_mean']
    df['ecn0_vs_mean'] = df['ecn0'] - df['psc_ecn0_mean']

    # Rolling means
    for w in [5, 10]:
        df[f'rscp_rmean_{w}'] = df.groupby('psc')['rscp'].transform(
            lambda x: x.rolling(w, min_periods=1).mean())
        df[f'ecn0_rmean_{w}'] = df.groupby('psc')['ecn0'].transform(
            lambda x: x.rolling(w, min_periods=1).mean())

    # Quality volatility
    df['ecn0_rstd_5'] = df.groupby('psc')['ecn0'].transform(
        lambda x: x.rolling(5, min_periods=1).std()
    ).fillna(0)

    # Differentials
    df['rscp_diff'] = df.groupby('psc')['rscp'].diff().fillna(0)
    df['ecn0_diff'] = df.groupby('psc')['ecn0'].diff().fillna(0)

    return df


def create_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create target labels for interference and handover_needed.

    Label 1: interference
    - Ec/N0 < -10 dB persistent (>= 3 of last 5 consecutive)

    Label 2: handover_needed
    - delta_rscp < 5 + neighbor detected + EcN0 < -10
    - Persistent (>= 2 of 4 consecutive)
    """
    df = df.copy().sort_values(['psc', 'time']).reset_index(drop=True)

    # Label 1: interference
    base_int = (df['ecn0'] < -10).astype(int)

    def roll_int(g):
        ind = base_int.loc[g.index]
        rs = ind.rolling(window=5, min_periods=1).sum()
        return (rs >= 3).astype(int)

    df['interference'] = df.groupby('psc', group_keys=False).apply(roll_int)

    # Label 2: handover_needed
    base_ho = (
        (df['delta_rscp'] < 5) &
        (df['has_neighbor'] == 1) &
        (df['ecn0'] < -10)
    ).astype(int)

    def roll_ho(g):
        ind = base_ho.loc[g.index]
        rs = ind.rolling(window=4, min_periods=1).sum()
        return (rs >= 2).astype(int)

    df['handover_needed'] = df.groupby('psc', group_keys=False).apply(roll_ho)

    return df


def prepare_training_data(
    df_labeled: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
):
    """
    Prepare features and labels for training.

    Returns:
        X_train, X_test, y_train_int, y_test_int, y_train_ho, y_test_ho,
        feature_cols, scaler_int, scaler_ho
    """
    # Exclude non-feature columns
    exclude = ['time', 'band', 'uarfcn', 'psc', 'psc_det', 'rscp_det',
               'interference', 'handover_needed']
    feature_cols = [c for c in df_labeled.columns if c not in exclude]

    df_model = df_labeled[feature_cols].copy()
    df_model = df_model.apply(pd.to_numeric, errors='coerce').fillna(0)

    # Tasks
    y_int = df_labeled['interference'].values
    y_ho = df_labeled['handover_needed'].values
    X = df_model.values

    # Train/test split
    X_train, X_test, y_train_int, y_test_int = train_test_split(
        X, y_int, test_size=test_size, random_state=random_state, stratify=y_int
    )
    # For handover, split with same indices
    _, _, y_train_ho, y_test_ho = train_test_split(
        X, y_ho, test_size=test_size, random_state=random_state, stratify=y_ho
    )

    # Scale features
    scaler_int = StandardScaler()
    X_train_int_scaled = scaler_int.fit_transform(X_train)
    X_test_int_scaled = scaler_int.transform(X_test)

    scaler_ho = StandardScaler()
    X_train_ho_scaled = scaler_ho.fit_transform(X_train)
    X_test_ho_scaled = scaler_ho.transform(X_test)

    return (
        X_train_int_scaled, X_test_int_scaled,
        y_train_int, y_test_int,
        y_train_ho, y_test_ho,
        feature_cols, scaler_int, scaler_ho
    )
