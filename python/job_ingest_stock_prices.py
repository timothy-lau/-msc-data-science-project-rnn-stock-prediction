from datetime import datetime as dt
import yfinance as yf
import sqlalchemy as sa
from sqlalchemy.sql.expression import func
import logging

from python.ingestion.stock_data_transformer import transform_yf_data
from config_reader import ConfigReader
from schema.data_model import StockPrices, Symbols
from common.mysql_connector import MySqlConnector

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logger = logging.getLogger('job_ingest_stock_prices.py')
    logger.info('Starting Job Ingest Stock Prices...')
    now = dt.now()

    # Initalise config reader
    app_config = ConfigReader('../configurations/run_config.json')

    logger.info('Connecting to database...')
    # Initialise database connection
    engine = MySqlConnector(
        host=app_config.DATABASE['HOST'],
        user=app_config.DATABASE['USER'],
        password=app_config.DATABASE['PASSWORD'],
        database=app_config.DATABASE['DATABASE']
    )

    con = engine.con

    ticker_results = con.execute(sa.select(Symbols.symbol).distinct()).fetchall()
    # flatten the sql results
    ticker_list = [ticker[0] for ticker in ticker_results]
    logger.info('Total number of tickers to download: %s' % (len(ticker_list)))

    # Check if configuration for initial run and adhoc load data is set to True, if so error
    if (app_config.DATA_INGESTION['INITIAL_RUN']) and (app_config.DATA_INGESTION['DOWNLOAD_PREVIOUS_HISTORICAL_DATA']):
        raise Exception('Config for Initial Run and Download previous historical data cannot be both set to True')

    # Set start date to stock start date if it is initial run or downloading more historical data
    if (app_config.DATA_INGESTION['INITIAL_RUN']) or (app_config.DATA_INGESTION['DOWNLOAD_PREVIOUS_HISTORICAL_DATA']):
        start_date = app_config.DATA_INGESTION['STOCK_START_DATE']
    else:
        start_date = con.execute(sa.select(func.max(StockPrices.stock_datetime))).fetchone()[0]  # query mysql for latest date +1

    # Delete any data after start date (due to time zone difference some records might need to be removed)
    logger.info('Emptying out stock data from table from {}'.format(str(start_date)))
    con.execute(
        sa.delete(StockPrices).where(StockPrices.stock_datetime >= start_date)
    )

    logger.info('Downloading stock data from {}'.format(str(start_date)))

    # If adhoc run for downloading more historical data, set end date to earliest record in database
    if app_config.DATA_INGESTION['DOWNLOAD_PREVIOUS_HISTORICAL_DATA']:
        end_date = con.execute(sa.select(func.min(StockPrices.stock_datetime))).fetchone()[0]
        data = yf.download(ticker_list, start=start_date, end=end_date)
    else:
        data = yf.download(ticker_list, start=start_date)

    logger.info('Shape of data is {}, {}'.format(str(data.shape[0]), str(data.shape[1])))

    # Transform yf data to appropriate format
    logger.info('Transforming YF data to appropriate format...')
    transformed_df = transform_yf_data(data)

    logger.info('Writing data to database...')
    row_count = 0

    # Write to db
    for index, row in transformed_df.iterrows():
        ins = sa.insert(StockPrices).values(
            symbol=row.Symbol, stock_datetime=index, open=row.Open, high=row.High, low=row.Low, close=row.Close,
            adj_close=row['Adj Close'], volume=row.Volume
        )
        con.execute(ins)
        row_count += 1
        logger.info('Inserted {} rows into stock_prices table.'.format(str(row_count)))
    con.close()

if __name__ == "__main__":
    main()