# About the project
The main deliverables of the project is to develop an application ecosystem that utilises artificial intelligence, such as the recurrent neural network in attempt to predict the trend of the stock market, and using the competitive advantage that the prediction gives, to allow the user to explore basic trading strategies and be able to evaluate their performance of these strategies through historical data. The application is built to be flexible and delivered through a configuration driven approach, allowing the user to modify any parameters, which stock to predict, or even add in any custom strategy to test out.

# Getting Started

## Prerequisites
- Setup Python environment and installed required libraries.
```bash
# Create virtual environment for ingestion 3.7
virtualenv venv --python=python3.7

# Use the virtual env
source venv/bin/activate # Mac
.\venv\Scripts\activate # Windows

# Install dependencies for local development
pip install -r requirements.txt
```

- Make sure you have installed MySql server
- Setup database and run `/sql/create_tables.sql` to setup the tables required

## Downloading Data

Nasdaq, NTSE, AMEX can be retrieved from: 
https://www.nasdaq.com/market-activity/stocks/screener

Use the stock screener and save csv under: /data/ticker_list/*.csv

# Setting up configurations
Configure initial configurations from `configurations/run_config.json`

Enter required values for the database 
```bash
  "DATABASE":
  {
    "HOST": "",
    "USER": "",
    "PASSWORD": "",
    "DATABASE": ""
  }
```

Setup parameters to run ingestion of stock data. For the first time running, set `INITIAL_RUN` to `True` and enter the date to download data from in the field `STOCK_START_DATE`
```bash
  "DATA_INGESTION":
  {
    "INITIAL_RUN" : false,
    "STOCK_START_DATE" : "2019-01-01",
    "DOWNLOAD_PREVIOUS_HISTORICAL_DATA" : false
  }
```

# Running The Application
After the configuration file is set up, run the individual jobs in the order of:
- `job_ingest_stock_symbols.py`
- `job_ingest_stock_prices.py`
- `job_rnn_model_trainer.py`
- `job_rnn_model_predicter.py`
- `job_back_testing.py`

# Interactive Dashboard
Dashboard can be found under the Tableau file `stock_prediction_dashboard.twb`
It requires database connection and data loaded in order to run.

A snippet of how the dashboard looks like can be found in `Dashboard_Sample.pdf`