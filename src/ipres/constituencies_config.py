"""Constituency configuration, loading, and interactive selection for election simulations."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
import numpy as np
from ipywidgets import widgets
from IPython.display import display
import os
from ipres.utils.paths import find_project_root

# Optional GUI file dialog support
try:
    import tkinter as _tk
    from tkinter import filedialog as _filedialog
except Exception:  # pragma: no cover
    _tk = None
    _filedialog = None

@dataclass
class ConstituenciesConfig:
    constituencies: pd.DataFrame = field(default_factory=pd.DataFrame)

    @classmethod
    def from_random(cls, M: int, Smin: int, Smax: int, average_turnout_percent: float = 75.0) -> "ConstituenciesConfig":
        df = cls._from_random(M, Smin, Smax, average_turnout_percent)
        return cls(constituencies = df)

    def fill_random(self, M: int, Smin: int, Smax : int, average_turnout_percent: float = 75.0 ):
        self.constituencies = self._from_random(M, Smin , Smax, average_turnout_percent)

    @classmethod
    def from_dataframe(cls, constituencies: pd.DataFrame) -> "ConstituenciesConfig":
        return cls(constituencies = cls._validate_df(constituencies))

    def set_dataframe(self, constituencies: pd.DataFrame):
        self.constituencies = self._validate_df(constituencies)

    @classmethod
    def from_parquet(cls, path: str) -> "ConstituenciesConfig":
        return cls(constituencies = cls._validate_df(pd.read_parquet(path)))

    def set_parquet(self, path: str):
        self.constituencies = self._validate_df(pd.read_parquet(path))

    @classmethod
    def from_csv(cls, path: str) -> "ConstituenciesConfig":
        return cls(constituencies = cls._validate_df(pd.read_csv(path)))

    def set_csv(self, path: str):
        self.constituencies = self._validate_df(pd.read_csv(path))

     # -------- Internal helpers --------
    @staticmethod
    def _from_random(M: int, Smin: int, Smax: int, average_turnout_percent: float = 75.0) -> pd.DataFrame:
        rng = np.random.default_rng(0)
        sizes = rng.integers(low=Smin, high=Smax + 1, size=M)

        # Generate per-constituency turnout in percent with exact specified average
        avg = float(average_turnout_percent)
        if not np.isfinite(avg):
            raise ValueError("average_turnout_percent must be a finite number.")
        if M <= 0:
            raise ValueError("M must be positive.")
        # Clamp average to [0, 100]
        avg = max(0.0, min(100.0, avg))

        # Create zero-mean random deviations and scale to stay within [0, 100]
        z: np.ndarray = rng.standard_normal(M)  # NumPy array of shape (M,)
        z = z - z.mean()
        max_abs: float = np.max(np.abs(z)) if np.any(z != 0) else 1.0
        z = z / max_abs  # now in [-1, 1]
        # choose an amplitude so values stay within bounds; use 60% of the max possible span
        amplitude_max: float = min(avg, 100.0 - avg)
        amplitude: float = 0.6 * amplitude_max
        turnout: np.ndarray = avg + amplitude * z  # NumPy array of per-constituency turnout (%)
        # Ensure numeric stability
        turnout = turnout.astype(float)

        df = pd.DataFrame({
            'constituency_name': [f"Constituency_{i+1}" for i in range(M)],
            'constituency_size': sizes.astype(int),
        })
        # Store turnout as percent (float)
        df['turnout_percent'] = np.round(turnout, 2)
        # Votes cast = size * turnout_percent / 100, rounded to nearest integer
        df['votes_cast'] = np.rint(df['constituency_size'].to_numpy() * df['turnout_percent'].to_numpy() / 100.0).astype(int)
        return df
    @staticmethod
    def _validate_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate a constituencies DataFrame:
        - Ensure required columns exist and have correct dtypes
        - Preserve optional turnout-related columns if present
        - Derive missing counterpart between turnout_percent and votes_cast when possible
        - Return the full DataFrame (do not drop extra user-provided columns)
        """
        required = ['constituency_name', 'constituency_size']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column '{col}' in constituencies file.")
        # Work on a copy
        df = df.copy()
        # Coerce required types
        df['constituency_name'] = df['constituency_name'].astype(str)
        df['constituency_size'] = df['constituency_size'].astype(int)

        # Optional columns handling
        has_turnout = 'turnout_percent' in df.columns
        has_votes_cast = 'votes_cast' in df.columns

        if has_turnout:
            # Coerce and sanitize turnout
            df['turnout_percent'] = pd.to_numeric(df['turnout_percent'], errors='coerce').fillna(0.0).astype(float)
            # Keep within [0, 100]
            df['turnout_percent'] = df['turnout_percent'].clip(lower=0.0, upper=100.0)
            # Round to 2 decimals for display consistency
            df['turnout_percent'] = df['turnout_percent'].round(2)

        if has_votes_cast:
            df['votes_cast'] = pd.to_numeric(df['votes_cast'], errors='coerce').fillna(0).astype(int)
            # Negative votes make no sense
            df.loc[df['votes_cast'] < 0, 'votes_cast'] = 0

        # Derivations if one of the two is missing
        if has_turnout and not has_votes_cast:
            df['votes_cast'] = np.rint(df['constituency_size'].to_numpy() * df['turnout_percent'].to_numpy() / 100.0).astype(int)
            has_votes_cast = True
        elif has_votes_cast and not has_turnout:
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                turnout = (df['votes_cast'].to_numpy() / np.where(df['constituency_size'].to_numpy() == 0, 1, df['constituency_size'].to_numpy())) * 100.0
            turnout = np.where(df['constituency_size'].to_numpy() == 0, 0.0, turnout)
            df['turnout_percent'] = np.round(turnout, 2)
            has_turnout = True

        # Ensure integer dtype for votes_cast if it exists
        if 'votes_cast' in df.columns:
            df['votes_cast'] = df['votes_cast'].astype(int)

        return df

    def getConstituencies(self) -> pd.DataFrame:
        return self.constituencies

    def getConstituencyNames(self) -> list[str]:
        return self.constituencies['constituency_name'].tolist();

    def getConstituencySizes(self) -> list[int]:
        return self.constituencies['constituency_size'].tolist();

    def getTurnoutPercentages(self) -> list[float]:
        return self.constituencies['turnout_percent'].tolist();

    def getVotesCast(self) -> list[int]:
        return self.constituencies['votes_cast'].tolist();

    def getM(self) -> int:
        return self.getConstituencies().shape[0]

    def getNumberOfConstituencies(self) -> int:
        return self.getConstituencies().shape[0]

    def setup(self : ConstituenciesConfig):
        # Widgets
        lbl_title = widgets.HTML("""
            <h3>Wahlkreise konfigurieren</h3>
            <p>Wie sollen die Wahlkreise bereitgestellt werden?</p>
        """)

        rb_source = widgets.RadioButtons(
            options=[
                ("Zufällig erzeugen", "random"),
                ("Aus Datei laden (Parquet/CSV)", "file"),
            ],
            value="file",
            description="Quelle:",
            disabled=False,
            layout=widgets.Layout(width="auto")
        )

        # Dateipfad-Eingabe und Datei-Upload (Alternative)
        txt_path = widgets.Text(
            value="data/examples/de_bundestag_constituencies.parquet",
            description="Pfad:",
            placeholder="Pfad zu .parquet oder .csv",
            layout=widgets.Layout(width="100%")
        )

        file_upload = widgets.FileUpload(
            accept=".parquet,.csv",
            multiple=False,
            description="Datei hochladen"
        )

        # Parameter für Zufallserzeugung (optional anpassbar)
        spn_M = widgets.IntText(value=299, description="Anzahl (M):")
        spn_Smin = widgets.IntText(value=100_000, description="Smin:")
        spn_Smax = widgets.IntText(value=300_000, description="Smax:")
        spn_avg_turnout = widgets.FloatText(value=75.0, description="Ø Wahlbeteiligung (%):")

        box_file = widgets.VBox([
            widgets.HTML("<b>Datei-Quelle</b>"),
            txt_path,
            widgets.HTML("<span style='color:gray'>Oder unten direkt eine Datei hochladen:</span>"),
            file_upload,
        ])

        box_random = widgets.VBox([
            widgets.HTML("<b>Zufallserzeugung</b>"),
            widgets.HBox([spn_M, spn_Smin, spn_Smax, spn_avg_turnout])
        ])

        # Sichtbarkeit steuern
        def _toggle_boxes(change=None):
            """Toggle visibility of file vs. random-generation UI elements."""
            use_file = (rb_source.value == "file")
            box_file.layout.display = "block" if use_file else "none"
            box_random.layout.display = "none" if use_file else "block"

        rb_source.observe(_toggle_boxes, names="value")

        _toggle_boxes()

        btn_ok = widgets.Button(description="OK", button_style="primary")
        btn_cancel = widgets.Button(description="Abbrechen")
        out = widgets.Output()

        dialog = widgets.VBox([
            lbl_title,
            rb_source,
            box_file,
            box_random,
            widgets.HBox([btn_ok, btn_cancel]),
            out
        ])

        def handle_ok(_):
            """Load or generate constituencies from file or random generation based on UI state."""
            with out:
                out.clear_output()
                try:
                    if rb_source.value == "random":
                        self.fill_random(int(spn_M.value), int(spn_Smin.value), int(spn_Smax.value), float(spn_avg_turnout.value))
                    else:
                        # 1) Wenn via Upload
                        if file_upload.value:
                            # Upload-Inhalt in einen DataFrame einlesen
                            # Dateiname und Inhalt
                            filename = file_upload.value[0].name
                            content = file_upload.value[0].content
                            if filename.endswith(".parquet"):
                                import io
                                df = pd.read_parquet(io.BytesIO(content))
                                self.set_dataframe(df)
                            elif filename.endswith(".csv"):
                                import io
                                df = pd.read_csv(io.BytesIO(content))
                                self.set_dataframe(df)
                            else:
                                raise ValueError("Nur .parquet oder .csv werden unterstützt.")
                        else:
                            # 2) Pfad verwenden
                            path = txt_path.value.strip()
                            if not path:
                                raise ValueError("Bitte einen Dateipfad angeben oder eine Datei hochladen.")
                            if not Path(path).is_absolute():
                                path = str(find_project_root() / path)
                            if path.endswith(".parquet"):
                                self.set_parquet(path)
                            elif path.endswith(".csv"):
                                self.set_csv(path)
                            else:
                                raise ValueError("Bitte .parquet oder .csv angeben.")
                    display(
                        widgets.HTML("<div style='color:green'>Wahlkreise wurden erfolgreich geladen/erzeugt.</div>"))

                    display(widgets.HTML(f'<h3>Wahlkreise (Vorschau – erste 10 von {self.getM()} Wahlkreisen)</h3>'))
                    display(self.getConstituencies().head(10))

                except Exception as e:
                    display(widgets.HTML(f"<div style='color:#b00020'>Fehler: {e}</div>"))

        def handle_cancel(_):
            """Clear output and display cancellation message."""
            with out:
                out.clear_output()
                display(widgets.HTML("<div>Abgebrochen.</div>"))

        btn_ok.on_click(handle_ok)
        btn_cancel.on_click(handle_cancel)
        file_upload.observe(handle_ok, names="value")
        display(dialog)

    def save(self, path: str | None = None) -> str:
        """
        Save the constituencies DataFrame to CSV or Parquet.
        - If path is provided, use it.
        - If path is None in a Jupyter environment, provide a simple input widget.
        - If path is None in a GUI environment, open a file save dialog.
        The file format is determined by the filename suffix (.csv or .parquet).
        Returns the final path used.
        """
        df = self.constituencies
        if df is None:
            raise ValueError("No constituencies data to save.")

        # Ask for path if not provided
        if path is None:
            # Try to detect if we're in a Jupyter/IPython environment
            try:
                from IPython import get_ipython
                if get_ipython() is not None:
                    # We're in Jupyter/IPython - use widget-based input
                    print("Please provide a file path to save the constituencies.")
                    print("Example: 'data/my_constituencies.parquet' or 'data/my_constituencies.csv'")
                    path = input("Enter file path: ").strip()
                    if not path:
                        raise RuntimeError("Save cancelled: no path provided.")
                else:
                    raise RuntimeError("Not in IPython environment")
            except (ImportError, RuntimeError):
                # Fallback to tkinter GUI dialog
                if _filedialog is None or _tk is None:
                    raise RuntimeError(
                        "No GUI available to choose a file path. "
                        "Please provide 'path' argument directly: "
                        "constituencies_config.save('data/my_file.parquet')"
                    )
                try:
                    root = _tk.Tk()
                    root.withdraw()
                    # Suggest default filename
                    default_name = "constituencies.parquet"
                    path = _filedialog.asksaveasfilename(
                        defaultextension=".parquet",
                        initialfile=default_name,
                        filetypes=[
                            ("Parquet files", "*.parquet"),
                            ("CSV files", "*.csv"),
                            ("All files", "*.*"),
                        ],
                        title="Save constituencies to file"
                    )
                finally:
                    try:
                        root.destroy()
                    except Exception:
                        pass
                if not path:
                    raise RuntimeError("Save cancelled by user.")

        if not Path(path).is_absolute():
            path = str(find_project_root() / path)
        suffix = os.path.splitext(path)[1].lower()
        if suffix == ".csv":
            df.to_csv(path, index=False)
        elif suffix == ".parquet":
            df.to_parquet(path, index=False)
        else:
            raise ValueError("Unsupported file type. Please use a path ending with .csv or .parquet")

        print(f"Successfully saved constituencies to: {path}")
        return path
