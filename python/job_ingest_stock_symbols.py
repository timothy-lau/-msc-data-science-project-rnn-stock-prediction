from datetime import datetime as dt
from sqlalchemy.dialects.mysql import insert
import pandas as pd
import logging

from config_reader import ConfigReader
from schema.data_model import Symbols
from common.mysql_connector import MySqlConnector
from python.ingestion.ticker_reader import read_stock_tickers, cleanse_tickers, read_process_additional_tickers


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

    # Read latest ticker files and process them into a dataframe
    stock_ticker_raw = read_stock_tickers(exchange_list=['nasdaq', 'nyse', 'amex'])

    # Cleanse stock tickers
    stock_ticker_cleansed = cleanse_tickers(stock_ticker_raw)

    # Read and process additional tickers
    additional_tickers_df = read_process_additional_tickers()

    combined_df = pd.concat([stock_ticker_cleansed, additional_tickers_df])

    # Write to db
    for index, row in combined_df.iterrows():
        ins = insert(Symbols).values(
            symbol=row.Symbol, name=row.Name, market_cap=row['Market Cap'], country=row.Country, ipo_year=row['IPO Year'],
            sector=row.Sector, industry=row.Industry, market_type=row['Market Type']
        )
        on_duplicate_ins = ins.on_duplicate_key_update(
            symbol=row.Symbol, name=row.Name, market_cap=row['Market Cap'], country=row.Country, ipo_year=row['IPO Year'],
            sector=row.Sector, industry=row.Industry, market_type=row['Market Type'], date_updated=dt.utcnow()
        )

        con.execute(on_duplicate_ins)
    con.close()

if __name__ == "__main__":
    main()