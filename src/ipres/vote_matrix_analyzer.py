from __future__ import annotations
from typing import Optional
import pandas as pd
import numpy as np

from ipres.election_config import Language
from ipres.strings import t

class VoteMatrixAnalyzer:
    """Analyzer for vote matrices, computing relative votes and constituency importance."""

    def __init__(self, votes: pd.DataFrame):
        """Initialize VoteMatrixAnalyzer with a vote matrix.

        Args:
            votes: DataFrame with constituencies as rows and parties as columns.
                   Each element contains the absolute vote count.
        """
        self.votes = votes

    def getRelativeVoteMatrix(self) -> pd.DataFrame:
        """Returns the relative vote matrix where each entry r_ij contains the proportion
        of votes that party j received in constituency i.

        Each row (constituency) sums to 1.0, representing the distribution of votes
        within that constituency across all parties.

        Returns:
            pd.DataFrame: Matrix with constituencies as rows and parties as columns.
                         Each element r_ij = votes_ij / total_votes_in_constituency_i
        """
        votes = self.votes
        if votes is None or votes.empty:
            raise ValueError("No votes available. Please run the ballot first.")

        # Calculate row sums (total votes per constituency)
        row_sums = votes.sum(axis=1)

        # Avoid division by zero: replace 0 with NaN for division
        denom = row_sums.replace(0, np.nan)

        # Calculate relative shares (each row sums to 1.0 or 100%)
        relative_matrix = votes.div(denom, axis=0)

        # Constituencies with 0 total votes get 0.0 for all parties
        relative_matrix = relative_matrix.fillna(0.0)

        return relative_matrix

    def getConstituencyImportanceMatrix(self) -> pd.DataFrame:
        """Returns the constituency importance matrix where each entry w_ij represents
        the relative importance of constituency i for party j.

        The importance is calculated as:
        w_ij = (M - 1) * r_ij / sum(r_kj for all k != i)

        Where:
        - r_ij is the proportion of votes party j received in constituency i
        - M is the total number of constituencies

        The (M-1) normalization factor ensures that:
        - w_ij = 1.0 for constituencies with average importance (uniform distribution)
        - w_ij > 1.0 for constituencies with above-average importance
        - w_ij < 1.0 for constituencies with below-average importance

        Returns:
            pd.DataFrame: Matrix with constituencies as rows and parties as columns.
                         Each element w_ij represents how important constituency i
                         is for party j relative to all other constituencies.
                         Values around 1.0 indicate average importance.

        """
        relative_votes = self.getRelativeVoteMatrix()
        return self._getConstituencyImportanceMatrix_impl(relative_votes, self.votes)

    def show_relative_vote_matrix(self, styler: bool = False, decimals: int = 4, max_rows: Optional[int] = None, language: Language = Language.DE):  # pragma: no mutate
        """Display the relative vote matrix as a formatted table.

        Each element r_ij shows the proportion of votes that party j received in
        constituency i (relative to the total votes in that constituency). Each row
        sums to 1.0.

        Args:
            styler: If ``True``, return a pandas Styler (HTML-formatted, for notebooks).
                If ``False``, return a plain DataFrame with interactive display.
            decimals: Number of decimal places for display.
            max_rows: Maximum number of rows shown in the Styler. ``None`` shows all rows.
                Only respected when ``styler=True``.

        Returns:
            :class:`pandas.DataFrame` or :class:`pandas.io.formats.style.Styler`

        Note:
            Without a Styler (``styler=False``), the DataFrame retains the interactive
            Jupyter display with scroll options. With ``styler=True``, a formatted HTML
            table is returned.
        """
        relative_matrix = self.getRelativeVoteMatrix()

        if styler:
            fmt = f"{{:.{decimals}f}}"  # pragma: no mutate
            styled = (relative_matrix.style
                    .format(fmt)
                    .set_caption(t("caption_relative_vote_matrix", language))  # pragma: no mutate
                    .set_table_styles([
                        {'selector': 'caption', 'props': [('font-size', '14px'), ('font-weight', 'bold')]}  # pragma: no mutate
                    ]))

            # Set max_rows for display if specified
            if max_rows is not None:  # pragma: no mutate
                with pd.option_context('display.max_rows', max_rows):  # pragma: no mutate
                    return styled
            return styled

        return relative_matrix.round(decimals)

    def show_constituency_importance_matrix(self, styler: bool = False, decimals: int = 4, max_rows: Optional[int] = None, language: Language = Language.DE):  # pragma: no mutate
        """Display the constituency importance matrix as a formatted table.

        Each element w_ij shows the relative importance of constituency i for party j.
        Importance is calculated as: w_ij = r_ij / Σ(r_kj for all k ≠ i).

        Args:
            styler: If ``True``, return a pandas Styler (HTML-formatted, for notebooks).
                If ``False``, return a plain DataFrame with interactive display.
            decimals: Number of decimal places for display.
            max_rows: Maximum number of rows shown in the Styler. ``None`` shows all rows.
                Only respected when ``styler=True``.

        Returns:
            :class:`pandas.DataFrame` or :class:`pandas.io.formats.style.Styler`

        Note:
            Without a Styler (``styler=False``), the DataFrame retains the interactive
            Jupyter display with scroll options. With ``styler=True``, a formatted HTML
            table is returned.
        """
        importance_matrix = self.getConstituencyImportanceMatrix()

        if styler:
            fmt = f"{{:.{decimals}f}}"  # pragma: no mutate
            styled = (importance_matrix.style
                    .format(fmt)
                    .set_caption(t("caption_constituency_importance", language))  # pragma: no mutate
                    .set_table_styles([
                        {'selector': 'caption', 'props': [('font-size', '14px'), ('font-weight', 'bold')]}  # pragma: no mutate
                    ]))

            # Set max_rows for display if specified
            if max_rows is not None:  # pragma: no mutate
                with pd.option_context('display.max_rows', max_rows):  # pragma: no mutate
                    return styled
            return styled

        return importance_matrix.round(decimals)

    @staticmethod
    def _getConstituencyImportanceMatrix_impl(relative_votes: pd.DataFrame, votes: pd.DataFrame) -> pd.DataFrame:
        """Implementation of constituency importance matrix calculation.

        Returns the constituency importance matrix where each entry w_ij represents
        the relative importance of constituency i for party j.

        The importance is calculated as:
        w_ij = (M - 1) * r_ij / sum(r_kj for all k != i)

        Where:
        - r_ij is the proportion of votes party j received in constituency i
        - M is the total number of constituencies

        The (M-1) normalization factor ensures that:
        - w_ij = 1.0 for constituencies with average importance (uniform distribution)
        - w_ij > 1.0 for constituencies with above-average importance
        - w_ij < 1.0 for constituencies with below-average importance

        Args:
            relative_votes: DataFrame with constituencies as rows and parties as columns.
                           Each element r_ij = votes_ij / total_votes_in_constituency_i
                           (rows should sum to 1.0)
            votes: Absolute votes DataFrame for handling edge cases

        Returns:
            pd.DataFrame: Matrix with constituencies as rows and parties as columns.
                         Each element w_ij represents how important constituency i
                         is for party j relative to all other constituencies.
                         Values around 1.0 indicate average importance.

        Example:
            >>> import pandas as pd
            >>> relative_votes = pd.DataFrame({
            ...     'Party A': [0.5, 0.3, 0.2],
            ...     'Party B': [0.3, 0.4, 0.3],
            ...     'Party C': [0.2, 0.3, 0.5]
            ... }, index=['District 1', 'District 2', 'District 3'])
            >>> votes = pd.DataFrame({
            ...     'Party A': [500, 300, 200],
            ...     'Party B': [300, 400, 300],
            ...     'Party C': [200, 300, 500]
            ... }, index=['District 1', 'District 2', 'District 3'])
            >>> importance = VoteMatrixAnalyzer._getConstituencyImportanceMatrix_impl(relative_votes, votes)
            >>> # For uniform distribution, all values would be 1.0
        """
        # Calculate column sums (sum of r_ij over all constituencies for each party)
        column_sums = relative_votes.sum(axis=0)

        # For each constituency, calculate w_ij = r_ij / (sum_k r_kj - r_ij)
        # This is equivalent to: w_ij = r_ij / (total_j - r_ij)
        importance_matrix = pd.DataFrame(
            index=relative_votes.index,
            columns=relative_votes.columns,
            dtype=float
        )

        for party in relative_votes.columns:
            total_party_share = column_sums[party]
            for constituency in relative_votes.index:
                r_ij = relative_votes.loc[constituency, party]
                # Sum of all other constituencies for this party
                denominator = total_party_share - r_ij

                M = relative_votes.shape[0] # Number of constituencies

                if denominator > 0:
                    importance_matrix.loc[constituency, party] = (M - 1) * r_ij / denominator
                else:
                    # Party has votes ONLY in this constituency (or nowhere)
                    # Use offset = total_votes_in_system to ensure these values are larger than
                    # any normal importance value, with ties broken by absolute vote count
                    total_votes_in_system = votes.sum().sum()
                    importance_matrix.loc[constituency, party] = total_votes_in_system + votes.loc[constituency, party]

        return importance_matrix


# Keep standalone function for backward compatibility with existing code
def getConstituencyImportanceMatrix(relative_votes: pd.DataFrame, votes: pd.DataFrame) -> pd.DataFrame:
    """Standalone function for backward compatibility.

    Returns the constituency importance matrix where each entry w_ij represents
    the relative importance of constituency i for party j.

    The importance is calculated as:
    w_ij = (M - 1) * r_ij / sum(r_kj for all k != i)

    Where:
    - r_ij is the proportion of votes party j received in constituency i
    - M is the total number of constituencies

    The (M-1) normalization factor ensures that:
    - w_ij = 1.0 for constituencies with average importance (uniform distribution)
    - w_ij > 1.0 for constituencies with above-average importance
    - w_ij < 1.0 for constituencies with below-average importance

    Args:
        relative_votes: DataFrame with constituencies as rows and parties as columns.
                       Each element r_ij = votes_ij / total_votes_in_constituency_i
                       (rows should sum to 1.0)
        votes: Absolute votes DataFrame for handling edge cases

    Returns:
        pd.DataFrame: Matrix with constituencies as rows and parties as columns.
                     Each element w_ij represents how important constituency i
                     is for party j relative to all other constituencies.
                     Values around 1.0 indicate average importance.

    Example:
        >>> import pandas as pd
        >>> relative_votes = pd.DataFrame({
        ...     'Party A': [0.5, 0.3, 0.2],
        ...     'Party B': [0.3, 0.4, 0.3],
        ...     'Party C': [0.2, 0.3, 0.5]
        ... }, index=['District 1', 'District 2', 'District 3'])
        >>> votes = pd.DataFrame({
        ...     'Party A': [500, 300, 200],
        ...     'Party B': [300, 400, 300],
        ...     'Party C': [200, 300, 500]
        ... }, index=['District 1', 'District 2', 'District 3'])
        >>> importance = getConstituencyImportanceMatrix(relative_votes, votes)
        >>> # For uniform distribution, all values would be 1.0
    """
    return VoteMatrixAnalyzer._getConstituencyImportanceMatrix_impl(relative_votes, votes)
