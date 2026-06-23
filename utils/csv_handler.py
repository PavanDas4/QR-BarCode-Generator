from pathlib import Path
from typing import List, Dict


class CSVHandler:
    REQUIRED_COLUMNS = ["data", "heading", "description"]

    @staticmethod
    def load_csv(path: str) -> List[Dict[str, str]]:
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "The bulk CSV feature requires pandas. "
                "Install it with `pip install pandas` in a compatible environment."
            ) from exc

        csv_path = Path(path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        df = pd.read_csv(csv_path)
        missing = [col for col in CSVHandler.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        rows = []
        for _, row in df.iterrows():
            rows.append(
                {
                    "data": str(row["data"]).strip(),
                    "heading": str(row["heading"]).strip(),
                    "description": str(row["description"]).strip(),
                }
            )
        return rows
