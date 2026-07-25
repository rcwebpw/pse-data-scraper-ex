"""
Download historical stock data from PSE EDGE.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import requests

from pse_data_scraper.client import PSEClient
from pse_data_scraper.models import Company, HistoricalPrice
from pse_data_scraper.utils import ensure_payload_date, format_output_date, sanitize_filename
from pse_data_scraper.scraper import load_companies_from_csv

logger = logging.getLogger(__name__)

HISTORICAL_DATA_URL = "https://edge.pse.com.ph/common/DisclosureCht.ax"
HISTORICAL_DATA_REFERER = "https://edge.pse.com.ph/companyPage/stockData.do"


def _build_history_payload(
    company: Company,
    start_date: str,
    end_date: str,
) -> dict:
    return {
        "cmpy_id": company.company_id,
        "security_id": company.security_id,
        "startDate": start_date,
        "endDate": end_date,
    }


def _cache_key(company: Company, start_date: str, end_date: str) -> str:
    return f"{company.company_id}_{company.security_id}_{start_date}_{end_date}.json"


def _load_cached_json(cache_path: Path) -> Optional[dict]:
    if not cache_path.exists():
        return None
    try:
        with cache_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def _save_cached_json(cache_path: Path, payload: dict) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle)
    except OSError:
        logger.warning("Failed to write cache file: %s", cache_path)


def fetch_historical_data(
    client: PSEClient,
    company: Company,
    start_date: str,
    end_date: str,
    cache_dir: Optional[Path] = None,
    refresh: bool = False,
) -> List[HistoricalPrice]:
    cache_payload: Optional[dict] = None
    cache_path: Optional[Path] = None

    if cache_dir is not None:
        cache_path = cache_dir / _cache_key(company, start_date, end_date)
        if not refresh:
            cache_payload = _load_cached_json(cache_path)

    if cache_payload is None:
        payload = _build_history_payload(company, start_date, end_date)
        response = client.post(
            HISTORICAL_DATA_URL,
            json=payload,
            headers={
                "Referer": HISTORICAL_DATA_REFERER,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        response.raise_for_status()
        cache_payload = response.json()
        if cache_path is not None and cache_payload.get("chartData"):
            _save_cached_json(cache_path, cache_payload)

    chart_data = cache_payload.get("chartData", [])
    results: List[HistoricalPrice] = []
    for item in chart_data:
        parsed = HistoricalPrice.from_api(item, company.stock_symbol)
        if parsed is not None:
            results.append(parsed)
    results.sort(key=lambda r: r.date)
    return results


def write_company_history(
    output_path: Path,
    company: Company,
    rows: Iterable[HistoricalPrice],
    output_format: str = "csv",
) -> Path:
    """
    Saves company price history to CSV or JSON format.
    """
    fmt = output_format.lower()
    target_path = output_path.with_suffix(f".{fmt}")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "json":
        records = []
        for item in rows:
            records.append({
                "Symbol": item.symbol,
                "Company": company.company_name,
                "Date": format_output_date(item.date),
                "Value": float(item.value) if item.value is not None else 0.0,
                "Open": float(item.open) if item.open is not None else 0.0,
                "Close": float(item.close) if item.close is not None else 0.0,
                "High": float(item.high) if item.high is not None else 0.0,
                "Low": float(item.low) if item.low is not None else 0.0,
            })
            
        with target_path.open("w", encoding="utf-8") as json_file:
            json.dump(records, json_file, indent=2)

    else:  # Default CSV
        with target_path.open("w", newline="", encoding="utf-8") as company_file:
            writer = csv.writer(company_file)
            writer.writerow(["Symbol", "Company", "Date", "Value", "Open", "Close", "High", "Low"])
            for item in rows:
                writer.writerow(
                    [
                        item.symbol,
                        company.company_name,
                        format_output_date(item.date),
                        item.value,
                        item.open,
                        item.close,
                        item.high,
                        item.low,
                    ]
                )

    return target_path


def download_historical_data(
    client: PSEClient,
    companies: Optional[Sequence[Company]] = None,
    input_csv: Optional[str] = None,
    output_dir: str = "data/history",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    symbols: Optional[Sequence[str]] = None,
    max_companies: Optional[int] = None,
    cache_dir: Optional[str] = ".cache",
    refresh: bool = False,
    output_format: str = "csv",
) -> List[Path]:
    if companies is None and input_csv is None:
        raise ValueError("Either 'companies' or 'input_csv' must be provided")
    if companies is None:
        companies = load_companies_from_csv(input_csv)

    symbol_set = {symbol.strip().upper() for symbol in symbols} if symbols else None
    output_root = Path(output_dir)
    cache_root = Path(cache_dir) if cache_dir else None

    start_payload = ensure_payload_date(start_date or "01-01-1900")
    end_payload = ensure_payload_date(end_date or date.today())

    saved_paths: List[Path] = []
    processed = 0

    for company in companies:
        if symbol_set and company.stock_symbol.upper() not in symbol_set:
            continue

        if max_companies is not None and processed >= max_companies:
            break

        processed += 1
        safe_name = sanitize_filename(company.company_name)
        
        # Base file path; format extension is set dynamically in write_company_history
        base_filename = f"{company.stock_symbol}_{safe_name}"
        expected_path = output_root / f"{base_filename}.{output_format.lower()}"

        if expected_path.exists() and not refresh:
            logger.info("Skipping %s (already exists)", expected_path)
            saved_paths.append(expected_path)
            continue

        logger.info("[%s] %s %s %s", processed, company.stock_symbol, company.company_id, company.company_name)

        try:
            rows = fetch_historical_data(
                client=client,
                company=company,
                start_date=start_payload,
                end_date=end_payload,
                cache_dir=cache_root,
                refresh=refresh,
            )
            if not rows:
                logger.info("No data for %s", company.company_name)
                continue
            
            saved_path = write_company_history(
                output_path=output_root / base_filename,
                company=company,
                rows=rows,
                output_format=output_format,
            )
            saved_paths.append(saved_path)
            logger.info("Saved: %s", saved_path)
        except requests.RequestException as exc:
            logger.warning("Request failed for %s: %s", company.company_name, exc)
        except (ValueError, KeyError) as exc:
            logger.warning("Unexpected payload for %s: %s", company.company_name, exc)

    return saved_paths