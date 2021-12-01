import pandas as pd


def transform_yf_data(data):
    cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    # Process yf data into appropriate format
    stock_data_l = []
    for ticker in data[cols[0]]:
        d = {}
        for col in cols:
            d[col] = data[col][ticker]
        df = pd.DataFrame(d)
        df['Symbol'] = ticker
        stock_data_l.append(df)

    join_df = pd.concat(stock_data_l).dropna()

    return join_df


def join_yf_nasdaq(yf_df, nasdaq_df):
    # Join with df from nasdaq.com to retrieve other attributes
    yf_df['copy_index'] = yf_df.index
    return yf_df.merge(nasdaq_df, how='left', on='Symbol').rename(columns={'copy_index':'Date'}).set_index('Date')