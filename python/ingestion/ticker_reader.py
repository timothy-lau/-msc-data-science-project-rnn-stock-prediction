import pandas as pd

from python.common.common import read_latest_file


def read_stock_tickers(exchange_list):
    frames = []
    ticker_columns = ['Symbol', 'Name', 'Market Cap', 'Country', 'IPO Year', 'Sector', 'Industry']
    for exchange in exchange_list:
        # Retrieve ticker files
        nasdaq_ticker_file = read_latest_file('../data/ticker_list', exchange)

        # Read as ticker file as df
        stock_raw = pd.read_csv(nasdaq_ticker_file)[ticker_columns]
        stock_raw['Market Type'] = 'stock'
        frames.append(stock_raw)
    return pd.concat(frames)

def cleanse_tickers(raw_df):
    filtered_tickers = raw_df[
        (~raw_df['Market Cap'].isnull()) &
        (~raw_df['Name'].isnull())
        ]

    return filtered_tickers.where(filtered_tickers.notnull(), None)

def read_process_additional_tickers():
    df = pd.read_csv('../data/additional_tickers/ticker_list.csv')
    df['Market Cap'] = 0
    df['Country'] = 'N/A'
    df['IPO Year'] = 'N/A'
    df['Sector'] = 'N/A'
    df['Industry'] = 'N/A'

    return df
