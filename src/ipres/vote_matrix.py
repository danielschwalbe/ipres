"""Vote data container and probabilistic vote-matrix generation engine."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Optional, Union
from collections.abc import Mapping as MappingABC, Sequence as SequenceABC
import pandas as pd
import numpy as np

from ipres.constituencies_config import ConstituenciesConfig
from ipres.contestant import Contestant
from ipres.election_config import Language
from ipres.strings import t, format_number
from ipres.plotting import plotSharePie

@dataclass
class VoteMatrix:
    """Vote data produced by a simulated or real ballot.

    Holds the raw vote counts and the contestant registry for one election round.
    Instances are created via :meth:`generate` or directly by passing
    ``votes`` and ``contestants`` to the constructor.

    Attributes:
        _votes: DataFrame of vote counts with constituencies as the index and
            contestant names as columns.
        _contestants: Dict mapping each contestant name to its
            :class:`~ipres.contestant.Contestant` instance.
    """
    _votes: pd.DataFrame
    _contestants: dict[str, Contestant]

    # ---- Factory ----

    @classmethod
    def generate(
        cls,
        constituencies_config: ConstituenciesConfig,
        contestants: list[Contestant],
        probabilities: Optional[Union[Mapping[str, float], SequenceABC[float]]] = None,
        rng: Optional[np.random.Generator] = None,
        turnout: Optional[Union[Mapping[str, float], SequenceABC[float], float]] = None,
        vote_matrix: Optional[pd.DataFrame] = None,
    ) -> VoteMatrix:
        """Generate vote data for a ballot round and return it as a :class:`VoteMatrix`.

        Args:
            constituencies_config: Configuration defining constituencies and
                their sizes.
            contestants: The contestants competing in the ballot.
            probabilities: Vote-share probabilities for each contestant, either
                as a mapping of contestant name to percentage or as a sequence
                of percentages in the same order as ``contestants``. Values must
                be in percent [0, 100] and are normalised to 100 if needed.
                If ``None``, shares are drawn uniformly at random.
            rng: NumPy random generator. If ``None``, a fresh default generator
                is created.
            turnout: Voter turnout for each constituency, either as a mapping
                of constituency name to percentage, as a sequence of percentages
                (same order as constituencies), or as a single float used as the
                mean for a Beta-distributed draw. Values must be in percent
                [0, 100]. If ``None``, turnout is drawn from a Beta(2, 2)
                distribution.
            vote_matrix: Optional pre-computed vote matrix. When provided,
                random vote generation is skipped and this matrix is validated
                and aligned instead.
                Format: ``index=constituency_names``, ``columns=contestant_names``,
                ``values=vote_counts``.

        Returns:
            A new :class:`VoteMatrix` with ``_votes`` and ``_contestants`` populated.
        """
        df = cls._run(constituencies_config, contestants, probabilities, rng, turnout, vote_matrix)
        dict_contestants = { c.name : c for c in contestants}
        return cls(_votes=df, _contestants=dict_contestants)

    # ---- Accessors ----

    def getContestants(self) -> dict[str, Contestant]:
        """Return the contestants dict mapping each name to its Contestant."""
        return self._contestants

    def getVotes(self) -> pd.DataFrame:
        """Return the raw vote-count DataFrame (index=constituencies, columns=contestants)."""
        return self._votes

    # ---- Analysis ----

    def getContestantsByPercentDesc(self, decimals: int = 2) -> pd.Series:  # pragma: no mutate
        """Return all contestants with their total vote-share percentages in descending order.

        Args:
            decimals: Number of decimal places to round the percentages to.

        Returns:
            A pandas Series with contestant names as the index and rounded
            percentages (float) as values, sorted descending. The sort is
            stable — ties preserve the original contestant order.

        Raises:
            ValueError: If no votes are available.
        """
        if self._votes is None or self._votes.empty:
            raise ValueError("No votes available. Call generate() first.")
        # Total votes per contestant across all constituencies
        contestant_totals = self._votes.sum(axis=0).astype(float)
        total = float(contestant_totals.sum())
        if total <= 0.0:
            # No votes cast at all -> 0% for every contestant
            pct = pd.Series(0.0, index=self._votes.columns, dtype=float)
        else:
            pct = (contestant_totals / total) * 100.0
        if decimals is not None:
            pct = pct.round(decimals)
        # Stable descending sort (ties preserve original contestant order)
        pct = pct.sort_values(ascending=False, kind="mergesort")
        return pct

    def getContestantsByPercentThreshold(self, threshold: float, decimals: int = 2) -> pd.Series:  # pragma: no mutate
        """Return the leading contestants whose cumulative share reaches a given threshold.

        Builds on :meth:`getContestantsByPercentDesc` and returns the shortest
        prefix whose cumulative percentage is ``>= threshold``. If rounding
        prevents the threshold from being reached, the full list is returned.

        Args:
            threshold: Cumulative percentage threshold in [0, 100].
            decimals: Number of decimal places passed to
                :meth:`getContestantsByPercentDesc`.

        Returns:
            A pandas Series as described in :meth:`getContestantsByPercentDesc`,
            truncated at the first position where the cumulative sum reaches
            ``threshold``.

        Raises:
            ValueError: If ``threshold`` is outside [0, 100].
        """
        if threshold < 0 or threshold > 100:
            raise ValueError("threshold must be between 0 and 100 (in %).")

        pct = self.getContestantsByPercentDesc(decimals=decimals)
        if pct.empty:
            return pct

        # Build cumulative sum and find the first position that meets the threshold
        csum = pct.cumsum()
        mask = csum >= threshold
        if mask.any():
            # Index of the first True
            cut_pos = int(np.argmax(mask.to_numpy()))
            return pct.iloc[: cut_pos + 1]
        # Threshold never reached (e.g. due to rounding) -> return everything
        return pct

    # ---- Display ----

    def plot_vote_share_pie(self, title: Optional[str] = None, min_percent: float = 1.0, language: Language = Language.DE):
        """Visualise the overall vote distribution as a pie chart.

        Args:
            title: Optional custom chart title. Defaults to a German-language
                summary showing the total vote count.
            min_percent: Minimum share threshold in percent. Contestants below
                this are grouped as "Sonstige" (default: 1.0%).

        Returns:
            matplotlib.figure.Figure

        Raises:
            ValueError: If no votes are available.
        """
        if self._votes is None or self._votes.empty:
            raise ValueError("No votes available. Call generate() first.")

        # Total votes per contestant
        contestant_totals = self._votes.sum(axis=0)
        total_votes = contestant_totals.sum()

        # Calculate percentages
        percentages = (contestant_totals / total_votes * 100.0)

        # Sort by vote count (descending)
        sorted_indices = contestant_totals.sort_values(ascending=False).index

        # Separate major contestants (>= min_percent) from small ones
        major_parties = []
        major_votes = []
        small_votes_total = 0

        for party in sorted_indices:
            pct = percentages[party]  # pragma: no mutate
            votes = contestant_totals[party]

            if pct >= min_percent:
                major_parties.append(party)
                major_votes.append(votes)
            else:
                small_votes_total += votes

        # Add "other" group if there are small parties
        if small_votes_total > 0:
            major_parties.append(t("label_other", language))
            major_votes.append(small_votes_total)

        if title is None:  # pragma: no mutate
            title = t("title_vote_dist_simple", language, total=format_number(int(total_votes), language))  # pragma: no mutate

        fig = plotSharePie(np.array(major_votes), major_parties, title)
        return fig

    def show_votes_table(self, styler: bool = False, print_table: bool = False, language: Language = Language.DE):
        """Return the raw vote-count matrix as a DataFrame or styled table.

        Args:
            styler: If ``True``, return a pandas Styler with thousands
                separators and a caption, suitable for Jupyter/HTML output.
                If ``False`` (default), return the plain DataFrame.
            print_table: If ``True``, also print the table to stdout via
                ``print()``. Only effective when ``styler=False``.

        Returns:
            pandas.DataFrame or pandas.io.formats.style.Styler depending on
            ``styler``.

        Raises:
            ValueError: If no votes are available.
        """
        if self._votes is None or self._votes.empty:
            raise ValueError("No votes available. Call generate() first.")
        if styler:
            return (self._votes.style
                    .format(thousands=".", formatter={c: "{:,.0f}".format for c in self._votes.columns})
                    .set_caption(t("caption_votes_per_constituency", language)))

        if print_table:  # pragma: no mutate
            # Fallback: plain console output
            with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # pragma: no mutate
                print(self._votes.to_string())
        return self._votes

    def show_votes_table_percent(self, styler: bool = False, decimals: int = 2):
        """Return the vote-count matrix as row-wise percentages.

        Each row is normalised to 100% so the values represent each contestant's
        share within a single constituency.

        Args:
            styler: If ``True``, return a pandas Styler with percentage
                formatting and a caption. If ``False`` (default), return the
                plain DataFrame of float percentages.
            decimals: Number of decimal places for rounding and display
                formatting.

        Returns:
            pandas.DataFrame or pandas.io.formats.style.Styler depending on
            ``styler``.

        Raises:
            ValueError: If no votes are available.
        """
        if self._votes is None or self._votes.empty:
            raise ValueError("No votes available. Call generate() first.")

        # Row sums (total votes per constituency). Avoid division by zero for empty rows.
        row_sums = self._votes.sum(axis=1)
        denom = row_sums.replace(0, np.nan)
        pct = self._votes.div(denom, axis=0) * 100.0
        # Constituencies with zero total votes get 0% across all columns
        pct = pct.fillna(0.0)
        pct = pct.round(decimals)

        if styler:
            fmt = f"{{:.{decimals}f}}%"  # pragma: no mutate
            return (pct.style
                    .format(fmt)
                    .set_caption("Stimmenanteile je Wahlkreis und Partei (% je Zeile)"))

        return pct

    # ---- Internal ----

    @staticmethod
    def _generateVotes(sizes: np.ndarray, N: int, rng: np.random.Generator, probs: np.ndarray) -> np.ndarray:
        """Generate the vote matrix by sampling from a multinomial distribution.

        For each constituency ``i`` with ``sizes[i]`` voters, one draw from
        Multinomial(sizes[i], probs) is taken. Individual cells may be zero;
        only the row sum is guaranteed to equal ``sizes[i]``.

        Args:
            sizes: Integer array of shape ``(M,)`` with the number of votes to
                cast per constituency.
            N: Number of contestants (columns).
            rng: NumPy random generator.
            probs: Probability vector of shape ``(N,)`` summing to 1.

        Returns:
            Integer ndarray of shape ``(M, N)`` with vote counts.

        Raises:
            ValueError: If any entry in ``sizes`` is negative.
        """
        sizes = np.asarray(sizes, dtype=int)
        M = sizes.shape[0]
        S = np.zeros((M, int(N)), dtype=int)
        for i in range(M):
            total = int(sizes[i])
            if total < 0:
                raise ValueError("Constituency sizes must be non-negative.")
            if total == 0:
                # No votes cast in this constituency
                continue
            S[i, :] = rng.multinomial(total, probs)
        return S

    @classmethod
    def _process_turnout_rates(cls, M: int, constituency_names: list[str],
                               rng: np.random.Generator | None,
                               turnout: Mapping[str, float] | SequenceABC[float] | float | None) -> np.ndarray:
        """Convert the ``turnout`` argument to a per-constituency rate array in [0, 1].

        Args:
            M: Number of constituencies.
            constituency_names: Ordered list of constituency names.
            rng: NumPy random generator used when drawing stochastic turnout.
            turnout: See :meth:`generate` for the full specification.

        Returns:
            A float ndarray of shape ``(M,)`` with values clipped to [0, 1].

        Raises:
            ValueError: If turnout values are out of range or the sequence
                length does not match ``M``.
        """
        if isinstance(turnout, MappingABC):
            try:
                turnout_vals_pct = np.array([float(turnout[name]) for name in constituency_names], dtype=float)
            except KeyError as e:
                raise ValueError(f"Missing turnout for constituency: {e.args[0]}") from None
            if np.any((turnout_vals_pct < 0.0) | (turnout_vals_pct > 100.0)):
                raise ValueError("Turnout mapping values must be in percent [0, 100].")
            turnout_rates = turnout_vals_pct / 100.0
        elif isinstance(turnout, SequenceABC) and not isinstance(turnout, (str, bytes)):
            turnout_vals_pct = np.array(list(turnout), dtype=float)
            if len(turnout_vals_pct) != M:
                raise ValueError(
                    "When turnout is passed as a list/sequence, its length must match the number of constituencies."
                )
            if np.any((turnout_vals_pct < 0.0) | (turnout_vals_pct > 100.0)):
                raise ValueError("Turnout sequence values must be in percent [0, 100].")
            turnout_rates = turnout_vals_pct / 100.0
        elif isinstance(turnout, (float, int)):
            m_pct = float(turnout)
            if not (0.0 <= m_pct <= 100.0):
                raise ValueError("When turnout is a single number, it must be in percent [0, 100].")
            m = m_pct / 100.0
            # Draw random values around the mean m using a Beta distribution.
            # Concentration parameter k controls spread (higher = less spread).
            k = 20.0  # pragma: no mutate
            alpha = max(m * k, 1e-6)  # pragma: no mutate
            beta = max((1.0 - m) * k, 1e-6)  # pragma: no mutate
            turnout_rates = np.random.default_rng().beta(alpha, beta, size=M) if rng is None else rng.beta(alpha, beta,
                                                                                                           size=M)
        else:
            # None or not provided: draw randomly with moderate spread around 0.5
            a, b = 2.0, 2.0  # pragma: no mutate
            turnout_rates = np.random.default_rng().beta(a, b, size=M) if rng is None else rng.beta(a, b, size=M)

        # Clip to [0, 1] and return
        turnout_rates = np.clip(turnout_rates, 0.0, 1.0)  # pragma: no mutate
        return turnout_rates

    @staticmethod
    def _randomContestantPreferences(N: int, rng: np.random.Generator) -> np.ndarray:
        """Draw a random probability vector over ``N`` contestants.

        Uses a Dirichlet(1, …, 1) distribution, which is uniform over the
        probability simplex.

        Args:
            N: Number of contestants.
            rng: NumPy random generator.

        Returns:
            A float ndarray of shape ``(N,)`` summing to 1.
        """
        return rng.dirichlet(alpha=np.ones(int(N)))

    @classmethod
    def _resolve_contestant_shares(cls, N: int, contestant_names: list[str],
                              probabilities: Mapping[str, float] | SequenceABC[float] | None,
                              rng: np.random.Generator | None) -> np.ndarray:
        """Resolve the ``probabilities`` argument to a normalised probability vector.

        Args:
            N: Number of contestants.
            contestant_names: Ordered list of contestant names.
            probabilities: See :meth:`generate` for the full specification.
            rng: NumPy random generator used when drawing random shares.

        Returns:
            A float ndarray of shape ``(N,)`` with values in [0, 1] summing to 1.

        Raises:
            ValueError: If probabilities are negative, out of range, or cannot
                be normalised.
        """
        if probabilities is None:
            p = cls._randomContestantPreferences(N, rng)
        elif isinstance(probabilities, MappingABC):
            try:
                p = np.array([probabilities[name] for name in contestant_names], dtype=float)
            except KeyError as e:
                raise ValueError(f"Missing probability for party: {e.args[0]}") from None
        elif isinstance(probabilities, SequenceABC) and not isinstance(probabilities, (str, bytes)):  # pragma: no mutate
            # Sequence in the same order as contestants
            p = np.array(list(probabilities), dtype=float)
            if len(p) != N:
                raise ValueError(
                    "When probabilities is passed as a list/sequence, its length must match the number of contestants."
                )
        else:
            raise ValueError(
                "probabilities must be a Mapping[str, float], a sequence of probabilities, or None."
            )

        # Validation and normalisation
        if probabilities is None:
            # Random shares (already in [0, 1])
            if np.any(p < 0):  # pragma: no mutate
                raise ValueError("Probabilities must be non-negative.")  # pragma: no mutate
            s = float(p.sum())
            if s <= 0.0:  # pragma: no mutate
                raise ValueError("Probabilities must sum to a positive value.")  # pragma: no mutate
            if not np.isclose(s, 1.0):
                # Should not happen with _randomContestantPreferences, but normalise as a safeguard
                import warnings
                warnings.warn(
                    f"Probabilities (random shares) sum to {s} instead of 1.0. Auto-normalizing."
                )
                p = p / s
        else:
            # Input is interpreted as percent [0, 100]
            if np.any(p < 0):
                raise ValueError("Probabilities must be non-negative.")
            if np.any(p > 100.0):
                raise ValueError("Probabilities must be in percent [0, 100].")
            sum_pct = float(p.sum())
            if sum_pct <= 0.0:
                raise ValueError("Probabilities must sum to a positive value (in percent).")
            if np.isclose(sum_pct, 100.0):
                # Exact percentages -> convert to fractions
                p = p / 100.0
            else:
                # Normalise to 100% with a warning, then convert to fractions
                import warnings
                warnings.warn(
                    f"Probabilities (in percent) sum to {sum_pct} instead of 100. Auto-normalizing to 100%."
                )
                p = p / sum_pct
        return p

    @classmethod
    def _run(
        cls,
        constituencies_config: ConstituenciesConfig,
        contestants: list[Contestant],
        probabilities: Optional[Union[Mapping[str, float], SequenceABC[float]]] = None,
        rng: Optional[np.random.Generator] = None,
        turnout: Optional[Union[Mapping[str, float], SequenceABC[float], float]] = None,
        vote_matrix: Optional[pd.DataFrame] = None)  -> pd.DataFrame:
        """Internal implementation of :meth:`generate`. Returns the raw vote DataFrame.

        Args:
            constituencies_config: Constituency configuration.
            contestants: The list of contestants.
            probabilities: See :meth:`generate`.
            rng: NumPy random generator.
            turnout: See :meth:`generate`.
            vote_matrix: Optional pre-computed vote matrix; skips generation when provided.

        Returns:
            DataFrame with constituency names as index and contestant names as columns.
        """
        # Prepare RNG
        if rng is None:
            rng = np.random.default_rng()

        contestant_names = cls._validate_contestant_names(contestants)

        constituency_names = list(constituencies_config.getConstituencyNames())

        # If vote_matrix is provided, validate and use it directly
        if vote_matrix is not None:
            # Validate that vote_matrix covers all required constituencies and contestants
            if not set(constituency_names).issubset(set(vote_matrix.index)):
                missing = set(constituency_names) - set(vote_matrix.index)
                raise ValueError(f"vote_matrix missing constituencies: {missing}")
            if not set(contestant_names).issubset(set(vote_matrix.columns)):
                missing = set(contestant_names) - set(vote_matrix.columns)
                raise ValueError(f"vote_matrix missing contestants: {missing}")

            # Align to expected order and return
            return vote_matrix.loc[constituency_names, contestant_names].fillna(0).astype(int)

        const_df = constituencies_config.getConstituencies()

        # Base sizes per constituency (registered/eligible voters). 'votes_cast' is intentionally ignored.
        base_sizes = const_df['constituency_size'].to_numpy(dtype=int)

        # Process turnout (input in percent [0, 100], used internally as rate [0, 1]):
        M = len(constituency_names)
        turnout_rates = cls._process_turnout_rates(M, constituency_names, rng, turnout)

        sizes = np.round(base_sizes * turnout_rates).astype(int)
        sizes = np.maximum(sizes, 0)

        N = len(contestant_names)

        # Map probabilities to contestant order, or draw randomly
        p = cls._resolve_contestant_shares(N, contestant_names, probabilities, rng)

        # Generate vote matrix (M x N)
        S = cls._generateVotes(sizes=sizes, N=N, rng=rng, probs=p)

        # Build DataFrame: rows = constituencies, columns = contestants
        df = pd.DataFrame(S, index=constituency_names, columns=contestant_names)
        return df

    @classmethod
    def _validate_contestant_names(cls, contestants: list[Contestant]) -> list[str]:
        """Validate and return the list of contestant names.

        Args:
            contestants: The contestants to validate.

        Returns:
            A list of contestant names in the same order as ``contestants``.

        Raises:
            ValueError: If ``contestants`` is not a list, any name is empty, or
                names are not unique.
        """
        if not isinstance(contestants, list):
            raise ValueError("contestants must be of type list[Contestant].")
        contestant_names = [x.name for x in contestants]
        # Validate: no empty names, no duplicates
        if any((p is None) or (str(p).strip() == "") for p in contestant_names):
            raise ValueError("Contestant names must not be empty.")
        if len(set(contestant_names)) != len(contestant_names):
            raise ValueError("Contestant names must be unique (no duplicates).")
        return contestant_names