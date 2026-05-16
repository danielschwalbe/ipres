"""Party configuration, loading, and interactive selection for election simulations."""

from __future__ import annotations
from dataclasses import dataclass, field
import os
from pathlib import Path
import pandas as pd
from ipres.utils.paths import find_project_root
import numpy as np
from ipywidgets import widgets
from IPython.display import display

# Optional GUI file dialog support
try:
    import tkinter as _tk
    from tkinter import filedialog as _filedialog
except Exception:  # pragma: no cover
    _tk = None  # pragma: no mutate
    _filedialog = None  # pragma: no mutate


@dataclass
class Parties:
    parties: pd.DataFrame = field(default_factory=pd.DataFrame)

    # -------- factory methods --------
    @classmethod
    def from_random(cls, N: int) -> "Parties":
        df = cls._from_random(N)
        return cls(parties=df)

    def fill_random(self, N: int):
        self.parties = self._from_random(N)

    @classmethod
    def from_dataframe(cls, parties: pd.DataFrame) -> "Parties":
        return cls(parties=cls._validate_df(parties))

    def set_dataframe(self, parties: pd.DataFrame):
        self.parties = self._validate_df(parties)

    @classmethod
    def from_parquet(cls, path: str) -> "Parties":
        return cls(parties=cls._validate_df(pd.read_parquet(path)))

    def set_parquet(self, path: str):
        self.parties = self._validate_df(pd.read_parquet(path))

    @classmethod
    def from_csv(cls, path: str) -> "Parties":
        return cls(parties=cls._validate_df(pd.read_csv(path)))

    def set_csv(self, path: str):
        self.parties = self._validate_df(pd.read_csv(path))

    def getSelectedParties(self, selected_parties: list[str]) -> Parties:
        """Return a new Parties instance containing only the specified parties.

        Args:
            selected_parties: Names of the parties to retain.

        Returns:
            A new :class:`Parties` with the filtered DataFrame.
        """
        return Parties(self.parties[self.parties['party_name'].isin(selected_parties)])

    # -------- Internal helpers --------
    @staticmethod
    def _from_random(N: int) -> pd.DataFrame:
        """Generate N unique party names of the form "Partei A", "Partei B", …, "Partei AA", …

        Name generation is deterministic and guaranteed to produce no duplicates.
        """
        # Deterministic RNG kept (not used) in case we later extend generation to use randomness
        _ = np.random.default_rng(0)

        # Generate labels "Partei A", "Partei B", ..., "Partei Z", "Partei AA", etc.
        def _letters(idx: int) -> str:
            s = ""
            idx += 1  # make 1-based
            while idx > 0:
                idx, rem = divmod(idx - 1, 26)
                s = chr(ord('A') + rem) + s
            return s

        N = int(N)
        names = [f"Partei {_letters(i)}" for i in range(N)]
        # Defensive uniqueness assertion
        if len(set(names)) != N:
            raise ValueError("Random party name generation produced duplicates, which should be impossible.")
        df = pd.DataFrame({'party_name': names})
        return df

    @staticmethod
    def _validate_df(df: pd.DataFrame) -> pd.DataFrame:
        """Validate and normalise a parties DataFrame.

        Ensures the required ``party_name`` column exists, strips whitespace,
        and checks for empty or duplicate party names.

        Args:
            df: Raw parties DataFrame to validate.

        Returns:
            Validated DataFrame containing only the required columns.

        Raises:
            ValueError: If required columns are missing, names are empty, or duplicates exist.
        """
        required = ['party_name']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column '{col}' in parties file.")
        # Coerce types and clean up
        df = df.copy()
        df['party_name'] = df['party_name'].astype(str)
        # Normalize whitespace
        df['party_name'] = df['party_name'].str.strip()
        # Validate non-empty names
        if (df['party_name'] == '').any():
            bad_idx = df.index[df['party_name'] == ''].tolist()
            raise ValueError(f"Empty party names found at rows: {bad_idx}")
        # Validate uniqueness
        dup_mask = df['party_name'].duplicated(keep=False)
        if dup_mask.any():
            dups = sorted(df.loc[dup_mask, 'party_name'].unique().tolist())
            raise ValueError(f"Duplicate party names found: {dups}")
        return df[required]

    # -------- Accessors --------
    def getParties(self) -> pd.DataFrame:
        """Return the underlying parties DataFrame."""
        return self.parties

    def getPartyNames(self) -> list[str]:
        """Return the list of party names."""
        return self.parties['party_name'].tolist();

    def getN(self) -> int:
        """Return the number of parties."""
        return int(self.parties.shape[0])

    def setup(self: Parties):
        # Widgets
        lbl_title = widgets.HTML("""
            <h3>Parteien konfigurieren</h3>
            <p>Wie sollen die Parteien bereitgestellt werden?</p>
        """)

        rb_source = widgets.RadioButtons(
            options=[
                ("Zufällig erzeugen", "random"),
                ("Aus Datei laden (Parquet/CSV)", "file"),  # pragma: no mutate
            ],
            value="file",
            description="Quelle:",
            disabled=False,
            layout=widgets.Layout(width="auto")
        )

        # Dateipfad-Eingabe und Datei-Upload (Alternative)
        txt_path = widgets.Text(
            value="data/examples/de_parties.parquet",
            description="Pfad:",
            placeholder="Pfad zu .parquet oder .csv",
            layout=widgets.Layout(width="100%")
        )

        file_upload = widgets.FileUpload(
            accept=".parquet,.csv",
            multiple=False,
            description="Datei hochladen"
        )

        # Parameter für Zufallserzeugung
        spn_N = widgets.IntText(value=6, description="Anzahl (N):")

        box_file = widgets.VBox([
            widgets.HTML("<b>Datei-Quelle</b>"),
            txt_path,
            widgets.HTML("<span style='color:gray'>Oder unten direkt eine Datei hochladen:</span>"),
            file_upload,
        ])

        box_random = widgets.VBox([
            widgets.HTML("<b>Zufallserzeugung</b>"),
            spn_N
        ])

        # Sichtbarkeit steuern
        def _toggle_boxes(change=None):
            """Toggle visibility of file vs. random-generation UI elements."""
            use_file = (rb_source.value == "file")
            box_file.layout.display = "block" if use_file else "none"
            box_random.layout.display = "none" if use_file else "block"  # pragma: no mutate

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
            """Load or generate parties from file or random generation based on UI state."""
            with out:
                out.clear_output()
                try:
                    if rb_source.value == "random":  # pragma: no mutate
                        self.fill_random(int(spn_N.value))
                    else:
                        # 1) Wenn via Upload
                        if file_upload.value:
                            filename = file_upload.value[0].name
                            content = file_upload.value[0].content
                            import io
                            if filename.endswith(".parquet"):
                                df = pd.read_parquet(io.BytesIO(content))
                                self.set_dataframe(df)
                            elif filename.endswith(".csv"):
                                df = pd.read_csv(io.BytesIO(content))
                                self.set_dataframe(df)
                            else:
                                raise ValueError("Nur .parquet oder .csv werden unterstützt.")  # pragma: no mutate
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

                    display(widgets.HTML("<div style='color:green'>Parteien wurden erfolgreich geladen/erzeugt.</div>"))  # pragma: no mutate

                    _N = int(self.getN())
                    display(widgets.HTML(f'<h3>Parteien (Vorschau – erste {_N} von {_N} Parteien)</h3>'))
                    display(self.getParties())
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

    # -------- Persistence --------
    def save(self, path: str | None = None) -> str:
        """
        Save the parties DataFrame to CSV or Parquet.
        - If path is provided, use it.
        - If path is None, open a file save dialog to let the user choose the file.
        The file format is determined by the filename suffix (.csv or .parquet).
        Returns the final path used.
        """
        df = self.parties
        if df is None:
            raise ValueError("No parties data to save.")

        # Ask for path if not provided
        if path is None:
            if _filedialog is None or _tk is None:
                raise RuntimeError("No GUI available to choose a file path. Please provide 'path'.")
            try:
                root = _tk.Tk()
                root.withdraw()
                # Suggest default filename
                default_name = "parties.parquet"
                path = _filedialog.asksaveasfilename(
                    defaultextension=".parquet",
                    initialfile=default_name,
                    filetypes=[
                        ("Parquet files", "*.parquet"),  # pragma: no mutate
                        ("CSV files", "*.csv"),
                        ("All files", "*.*"),
                    ],
                    title="Save parties to file"
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
        return path
