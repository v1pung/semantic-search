from pathlib import Path

import pandas as pd

from src.domain.entities import QAPair
from src.domain.exceptions import DataLoadError
from src.domain.interfaces.data_loader import AbstractDataLoader


class CsvDataLoader(AbstractDataLoader):
    """Loads Q&A pairs from a pipe-delimited CSV file."""

    def __init__(self, csv_path: str) -> None:
        self._csv_path = csv_path

    def load(self) -> list[QAPair]:
        path = Path(self._csv_path)
        if not path.exists():
            raise DataLoadError(f"CSV file not found: {self._csv_path}")

        try:
            df = pd.read_csv(path, sep="|")
        except Exception as exc:
            raise DataLoadError(f"Failed to read CSV file: {self._csv_path}") from exc

        required_columns = {"question", "answer"}
        missing = required_columns - set(df.columns)
        if missing:
            raise DataLoadError(f"CSV is missing required columns: {missing}")

        df = df.dropna(subset=["question", "answer"])
        df["question"] = df["question"].str.strip()
        df["answer"] = df["answer"].str.strip()
        df = df[(df["question"] != "") & (df["answer"] != "")]

        return [
            QAPair(question=str(row.question), answer=str(row.answer))
            for row in df.itertuples()
        ]
