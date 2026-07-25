import logging
import os
from pathlib import Path
import pandas as pd
from pse_data_scraper.pipeline import export_prices


def export_dataset(
    history_dir: str, combined_path: str, export_format: str = "csv"
) -> None:
    """
    Combines price history CSVs and exports the final dataset to CSV or JSON format.
    """
    combined_csv = Path(combined_path)

    # 1. Combine individual ticker CSVs in history_dir into the target combined CSV
    logging.info("Combining historical CSVs from %s...", history_dir)
    export_prices(history_dir, str(combined_csv))

    if not combined_csv.exists():
        logging.error("Failed to generate combined dataset at %s", combined_csv)
        return

    # 2. Export to requested format
    fmt = export_format.lower()

    if fmt == "json":
        json_path = combined_csv.with_suffix(".json")
        df = pd.read_csv(combined_csv)

        # Output as clean JSON array: [{"Date": "2026-07-24", "Close": 142.5}, ...]
        df.to_json(json_path, orient="records", indent=2, date_format="iso")
        print(f"Successfully exported JSON to: {json_path}")

    elif fmt == "csv":
        print(f"Successfully exported CSV to: {combined_csv}")

    else:
        logging.error("Unsupported export format: %s", fmt)