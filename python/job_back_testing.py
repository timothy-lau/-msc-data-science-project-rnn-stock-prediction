from datetime import datetime as dt
import logging

import pandas as pd
import sqlalchemy as sa
from backtesting.custom_datafeed import PandasData
from backtesting.strategy import *
import backtrader as bt

from config_reader import ConfigReader
from common.mysql_connector import MySqlConnector
from schema.data_model import ActualisedTable


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logger = logging.getLogger('job_back_testing.py')
    logger.info('Starting Job Back Testing...')

    # Initialise config reader
    app_config = ConfigReader('../configurations/run_config.json')
    now = dt.now()

    # Initialise database connection
    engine = MySqlConnector(
            host=app_config.DATABASE['HOST'],
            user=app_config.DATABASE['USER'],
            password=app_config.DATABASE['PASSWORD'],
            database=app_config.DATABASE['DATABASE']
        )

    con = engine.con

    symbol = app_config.BACK_TESTING['SYMBOL']
    model = app_config.BACK_TESTING['MODEL']

    logger.info('Using Symbol:{} , Model:{}.'.format(symbol, str(model)))

    # Read stock price data from database
    sql_df = pd.read_sql(
        sa.select(ActualisedTable.stock_datetime, ActualisedTable.symbol, ActualisedTable.open, ActualisedTable.high, ActualisedTable.low,
                  ActualisedTable.close, ActualisedTable.adj_close, ActualisedTable.volume, ActualisedTable.future_close) \
            .where(ActualisedTable.symbol == symbol) \
            .where(ActualisedTable.model_id == model), con)

    opening_stock = sql_df['close'].head(1).values[0]
    closing_stock = sql_df['close'].tail(1).values[0]
    original_return = (closing_stock - opening_stock)/opening_stock

    # Transform stock data into backtrader format
    data = PandasData(dataname=sql_df)

    # initialise cerebro
    cerebro = bt.Cerebro()

    logger.info('Using strategy: {}'.format(app_config.BACK_TESTING['STRATEGY']))

    # add strategy
    if app_config.BACK_TESTING['STRATEGY'] == 'FollowTheTrendMA':
        cerebro.addstrategy(FollowTheTrendMA, app_config.BACK_TESTING['PARAMS']['FollowTheTrendMA'])
    elif app_config.BACK_TESTING['STRATEGY'] == 'FollowTheTrendBollinger':
        cerebro.addstrategy(FollowTheTrendBollinger, app_config.BACK_TESTING['PARAMS']['FollowTheTrendBollinger'])
    elif app_config.BACK_TESTING['STRATEGY'] == 'MeanReversionMinMax':
        cerebro.addstrategy(MeanReversionMinMax, app_config.BACK_TESTING['PARAMS']['MeanReversionMinMax'])
    elif app_config.BACK_TESTING['STRATEGY'] == 'MeanReversionBollinger':
        cerebro.addstrategy(MeanReversionBollinger, app_config.BACK_TESTING['PARAMS']['MeanReversionBollinger'])


    # add data to cerebro
    cerebro.adddata(data)

    # set configurations
    cerebro.broker.setcash(app_config.BACK_TESTING['INITIAL_CASH'])
    cerebro.broker.setcommission(app_config.BACK_TESTING['COMMISSION'])
    cerebro.broker.set_coc(True)

    start_portfolio = cerebro.broker.getvalue()
    logger.info('Starting Portfolio Value: %.2f' % start_portfolio)

    cerebro.run()

    end_portfolio = cerebro.broker.getvalue()
    logger.info('Final Portfolio Value: %.2f' % end_portfolio)
    logger.info('Portfolio %.2f -> %.2f, Perc change %.2f' % (start_portfolio, end_portfolio, (end_portfolio-start_portfolio)/start_portfolio*100)+'%')
    logger.info('Symbol %s  %.2f -> %.2f, Perc change %.2f' % (symbol, opening_stock, closing_stock, original_return*100)+'%')

    cerebro.plot(figsize=(16,14), dpi=100)

if __name__ == "__main__":
    main()