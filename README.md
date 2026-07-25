# PSE Data Scraper

PSE Data Scraper pulls company lists and historical price data from PSE EDGE,
then exports them to CSV for analysis. It includes a CLI, retry logic, optional
caching, and a small Python API.

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the full pipeline:

```bash
python -m pse_data_scraper sync
```

You can also run the direct entry point (same defaults as `pse sync`):

```bash
python main.py
```

## CLI Usage

Install locally for the `pse` command:

```bash
pip install -e .
```

Examples:

```bash
pse sync
pse companies --refresh
pse prices --symbols BDO,ALI --from 2020-01-01 --to 2024-01-01
pse export --format csv
pse status
```

Common options:

- `--rate-limit` sets the delay between requests.
- `--symbols` limits downloads to specific tickers.
- `--max-companies` is useful for quick test runs.
- `--refresh` forces re-downloads even if files exist.
- `--no-cache` disables cached API responses.
- Dates accept `MM-DD-YYYY` or `YYYY-MM-DD`.

## Configuration

Generate a starter config:

```bash
pse init
```

By default, the CLI reads `pse.toml` from the current directory. You can
override it with `--config path/to/pse.toml`.

Example `pse.toml`:

```toml
[paths]
data_dir = "data"
cache_dir = ".cache"

[network]
rate_limit = 0.6

[download]
start_date = "2020-01-01"
symbols = ["BDO", "ALI"]
```

## Python API

```python
from pse_data_scraper.client import PSEClient
from pse_data_scraper.scraper import scrape_companies, save_companies_to_csv
from pse_data_scraper.downloader import download_historical_data
from pse_data_scraper.combiner import combine_csvs

client = PSEClient(rate_limit_seconds=0.6)
companies = scrape_companies(client)
save_companies_to_csv(companies, "data/companies.csv")
download_historical_data(client, companies=companies, output_dir="data/history")
combine_csvs("data/history", "data/combined.csv")
```

## Output Files

- `data/companies.csv` - company list with IDs and symbols
- `data/history/` - one CSV per company
- `data/combined.csv` - consolidated price dataset
- `.cache/` - optional cached API responses

## API Notes

The scraper uses endpoints observed from PSE EDGE. See `docs/API.md` for
payload and response details.

## Structure

```
pse-data-scraper/
├── main.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── pse_data_scraper/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── client.py
│   ├── combiner.py
│   ├── config.py
│   ├── downloader.py
│   ├── models.py
│   ├── pipeline.py
│   ├── scraper.py
│   ├── status.py
│   └── utils.py
├── tests/
│   ├── conftest.py
│   ├── test_client.py
│   ├── test_combiner.py
│   ├── test_config.py
│   ├── test_downloader.py
│   ├── test_models.py
│   ├── test_scraper.py
│   ├── test_sort.py
│   └── test_utils.py
└── docs/
    └── API.md
```

## Development

```bash
pip install -e .
pip install -r requirements-dev.txt
pytest
```

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


### Extended

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

### Sync Full Market Data (pse sync)
Scrapes all companies, downloads price history, and outputs consolidated files:

Bash
# Export as combined JSON dataset
```pse sync --format json```

# Sync specific symbols with a custom start date
```pse sync --symbols BDO,ALI,TEL --from 2026-01-01 --format json```



## License

MIT. See `LICENSE`.
