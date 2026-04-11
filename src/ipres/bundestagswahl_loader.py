"""Loader for real Bundestagswahl data from Bundeswahlleiterin.

This module provides functions to load real election results from
official Bundestagswahl CSV files and convert them into a format
suitable for simulation with ipres.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


def load_bundestagswahl_data(
    year: int,
    data_dir: Optional[Path] = None
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Load Bundestagswahl data for a specific year.

    Args:
        year: Election year (2013, 2017, 2021, 2025)
        data_dir: Directory containing BTW CSV files. If None, uses default.

    Returns:
        Tuple of (constituencies_df, vote_matrix_df, party_names):
        - constituencies_df: DataFrame with constituency info (number, name, size)
        - vote_matrix_df: DataFrame with Zweitstimmen per party per constituency
        - party_names: List of party names in order

    Raises:
        FileNotFoundError: If data file doesn't exist
        ValueError: If year is not available
    """
    if data_dir is None:
        # Default to data/bundestagswahl relative to project root
        data_dir = Path(__file__).parent.parent.parent / "data" / "bundestagswahl"

    # Try the wahlkreise specific file first (newer format with headers)
    data_file = data_dir / f"btw{year}_wahlkreise.csv"

    if not data_file.exists():
        raise FileNotFoundError(
            f"Data file not found: {data_file}\n"
            f"Download from: https://www.bundeswahlleiterin.de"
        )

    # Read CSV with proper encoding
    # This file has proper headers starting at row 10
    df = pd.read_csv(
        data_file,
        sep=';',
        encoding='utf-8-sig',
        skiprows=9  # Skip metadata rows
    )

    # Filter for constituency-level data
    constituencies_data = df[df['Gebietsart'] == 'Wahlkreis'].copy()

    # Extract constituency information
    constituencies = _extract_constituencies(constituencies_data)

    # Extract vote matrix (Zweitstimmen only)
    vote_matrix, party_names = _extract_vote_matrix(constituencies_data)

    return constituencies, vote_matrix, party_names


def _extract_constituencies(df: pd.DataFrame) -> pd.DataFrame:
    """Extract constituency information from BTW data.

    Returns DataFrame with columns:
    - constituency_number: int
    - constituency_name: str
    - constituency_size: int (Wahlberechtigte)
    """
    # Get unique constituencies - filter for "Wahlberechtigte" rows
    const_info = df[df['Gruppenart'] == 'System-Gruppe'].copy()
    const_info = const_info[const_info['Gruppenname'] == 'Wahlberechtigte'].copy()

    constituencies = pd.DataFrame({
        'constituency_number': const_info['Gebietsnummer'].astype(int),
        'constituency_name': const_info['Gebietsname'],
        'constituency_size': const_info['Anzahl'].astype(int)
    })

    # Remove duplicates and sort
    constituencies = constituencies.drop_duplicates().sort_values('constituency_number').reset_index(drop=True)

    return constituencies


def _extract_vote_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Extract vote matrix (Zweitstimmen) from BTW data.

    Returns:
        Tuple of (vote_matrix_df, party_names)
        - vote_matrix_df: Rows = constituencies, Columns = parties, Values = Zweitstimmen
        - party_names: List of party names in column order
    """
    # Filter for party results (Zweitstimmen = Stimme == 2)
    party_votes = df[
        (df['Gruppenart'] == 'Partei') &
        (df['Stimme'] == 2)  # Zweitstimmen
    ].copy()

    # Extract relevant columns
    # Note: Some entries might have NaN for Anzahl (votes), fill with 0
    result_df = pd.DataFrame({
        'constituency_number': party_votes['Gebietsnummer'].astype(int),
        'constituency_name': party_votes['Gebietsname'],
        'party_name': party_votes['Gruppenname'],
        'votes': party_votes['Anzahl'].fillna(0).astype(int)
    })

    # Pivot to create matrix: rows=constituency_names, columns=parties
    vote_matrix = result_df.pivot(
        index='constituency_name',
        columns='party_name',
        values='votes'
    ).fillna(0).astype(int)

    # Get list of party names (columns)
    party_names = vote_matrix.columns.tolist()

    # Keep constituency_name as index (don't reset it)

    return vote_matrix, party_names


def filter_major_parties(
    vote_matrix: pd.DataFrame,
    party_names: list[str],
    min_percent: float = 1.0
) -> tuple[pd.DataFrame, list[str]]:
    """Filter vote matrix to include only major parties above threshold.

    Args:
        vote_matrix: Vote matrix DataFrame (with constituency_name as index)
        party_names: List of all party names
        min_percent: Minimum percentage threshold (default 1.0%)

    Returns:
        Tuple of (filtered_vote_matrix, filtered_party_names)
    """
    # Calculate total votes per party
    total_votes = vote_matrix[party_names].sum()
    total_all_votes = total_votes.sum()

    # Calculate percentages
    percentages = (total_votes / total_all_votes * 100)

    # Filter parties above threshold
    major_parties = percentages[percentages >= min_percent].index.tolist()

    # Create filtered vote matrix (keep index)
    filtered_matrix = vote_matrix[major_parties].copy()

    return filtered_matrix, major_parties


# Example usage documentation
__doc__ += """

Example Usage
-------------

.. code-block:: python

    from ipres.bundestagswahl_loader import load_bundestagswahl_data, filter_major_parties

    # Load 2021 Bundestagswahl data
    constituencies, vote_matrix, parties = load_bundestagswahl_data(2021)

    # Filter to major parties (>1%)
    vote_matrix_filtered, major_parties = filter_major_parties(
        vote_matrix, parties, min_percent=1.0
    )

    print(f"Loaded {len(constituencies)} constituencies")
    print(f"Major parties: {major_parties}")
"""
