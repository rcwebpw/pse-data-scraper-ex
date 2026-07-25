# PSE EDGE API Notes

This project uses the same endpoints that the PSE EDGE website calls from the browser.
These endpoints are undocumented and may change without notice.

## Company Directory

Endpoint:

- `GET https://edge.pse.com.ph/companyDirectory/search.ax?pageNo={page}`

Notes:

- The response is HTML.
- Company rows are in `table.list tbody tr`.
- The company and security IDs are embedded in the `onclick` handler:
  - `cmDetail('COMPANY_ID','SECURITY_ID')`

## Historical Stock Data

Endpoint:

- `POST https://edge.pse.com.ph/common/DisclosureCht.ax`

Headers:

- `Referer: https://edge.pse.com.ph/companyPage/stockData.do`
- `X-Requested-With: XMLHttpRequest`

JSON payload:

```json
{
  "cmpy_id": "123",
  "security_id": "456",
  "startDate": "01-01-1900",
  "endDate": "08-30-2024"
}
```

Response (JSON):

- `chartData`: list of daily records

Record fields used:

- `CHART_DATE` (example: `Aug 30, 2024 00:00:00`)
- `VALUE`
- `OPEN`
- `CLOSE`
- `HIGH`
- `LOW`

## Rate Limiting

The scraper enforces a configurable delay between requests (`--rate-limit`) and retries
transient failures (HTTP 429/5xx) with exponential backoff.

# API & CLI Reference

## Dataset Exporter (`pse_data_scraper.exporter`)

The `exporter` module handles consolidation of individual ticker CSVs in the history directory and outputs structured market datasets in either CSV or JSON formats.

### `export_dataset()`

```python
from pse_data_scraper.exporter import export_dataset

export_dataset(
    history_dir: str, 
    combined_path: str, 
    export_format: str = "csv"
) -> None
```

### Parameters
history_dir (str): Path to the directory containing individual ticker CSV files (e.g., "data/history").

combined_path (str): Destination file path for the combined output file (e.g., "data/combined.csv").

export_format (str, optional): Desired output file format. Accepted values are "csv" or "json". Defaults to "csv".

### Output Behavior
- CSV: Combines all individual stock data into combined_path (e.g., data/combined.csv).

- JSON: Generates the base dataset first, then creates a matching JSON array file using the .json extension (e.g., data/combined.json).

CLI Command Reference
```pse export```
Consolidates all downloaded stock price files into a single, unified dataset file.

### Usage Examples
Export as consolidated CSV:

```pse export --format csv```

Export as structured JSON array:

```pse export --format json```

### JSON Output Schema
When exporting using --format json, the resulting combined.json contains an array of normalized daily trading objects:

```
[
  {
    "Symbol": "BDO",
    "Company": "Banco de Oro Unibank, Inc.",
    "Date": "2026-07-24",
    "Open": 141.00,
    "High": 143.20,
    "Low": 140.50,
    "Close": 142.50,
    "Volume": 2154300,
    "Value": 306232150.00
  },
  {
    "Symbol": "ALI",
    "Company": "Ayala Land, Inc.",
    "Date": "2026-07-24",
    "Open": 29.50,
    "High": 30.10,
    "Low": 29.20,
    "Close": 29.80,
    "Volume": 5421000,
    "Value": 161245800.00
  }
]
```