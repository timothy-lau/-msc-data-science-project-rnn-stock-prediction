import pandas as pd
import numpy as np
import sqlalchemy as sa
import logging
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

from python.common.mysql_connector import MySqlConnector
from schema.data_model import StockPrices, Symbols, Models, StockPrediction
from config_reader import ConfigReader


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logger = logging.getLogger('job_rnn_model_predictor.py')

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

    # Retrieve all model id from database as a list
    model_list_row = con.execute(
        sa.select(Models.model_id)
    ).fetchall()
    model_list = [i[0] for i in model_list_row]
    model_list = [29,30]
    logger.info('Generating predictions for models: {}'.format(' '.join([str(model) for model in model_list])))

    # Retrieve selected model id for predict stock prices
    for model_id in model_list:
        # Retrieve the corresponding timesteps and predict_gap
        model_row = con.execute(
            sa.select(Models.timesteps, Models.predict_gap)
            .where(Models.model_id == model_id)
        ).fetchall()[0]

        timesteps, predict_gap = model_row

        logger.info('Running model %s with timesteps: %s, predict_gap: %s' % (model_id, timesteps, predict_gap))

        # Loading LSTM model for the corresponding model ID
        model = load_model('../lstm_models/model_{}'.format(model_id))

        # Shortlist list of stock to train model on
        shortlist_stock_stmt = app_config.RNN['SHORTLIST_STOCK_QUERY']

        shortlist_stock = con.execute(shortlist_stock_stmt).fetchall()
        symbol_list = [i[0] for i in shortlist_stock]

        # Predicting dataset
        sql_df = pd.read_sql(
            sa.select(
                StockPrices.stock_datetime, StockPrices.symbol, StockPrices.close, StockPrices.volume,
                Symbols.market_type,
                Symbols.sector) \
                .join(Symbols) \
                .where(StockPrices.symbol.in_([i[0] for i in shortlist_stock])), con)

        # One hot encoding
        sql_df = sql_df.join(pd.get_dummies(sql_df['sector'], prefix='sector_', drop_first=True)).drop('sector', axis=1)
        sql_df = sql_df.join(pd.get_dummies(sql_df['market_type'], prefix='market_type_', drop_first=True)).drop(
            'market_type', axis=1)

        for symbol in symbol_list:
            logger.info('Predicting symbol %s with model %s...' % (symbol, model_id))
            # Initialising scalers
            sc_close = MinMaxScaler(feature_range=(0, 1))
            sc_volume = MinMaxScaler(feature_range=(0, 1))

            # Scale numeric data with min max scaler
            scaled_close = sc_close.fit_transform(sql_df[sql_df['symbol'] == symbol]['close'].values.reshape(-1, 1))
            scaled_volume = sc_volume.fit_transform(sql_df[sql_df['symbol'] == symbol]['volume'].values.reshape(-1, 1))

            # Duplicating non numeric features by timestep and creating
            non_numeric_features = []
            for row in sql_df[sql_df['symbol'] == symbol].select_dtypes(include=['uint8']).values:
                row_l = []
                for col in row:
                    row_l.append([col] * timesteps)
                non_numeric_features.append(row_l)

            X_test = []

            # Creating a data structure with time-steps in a 3d array form
            for i in range(timesteps + predict_gap, scaled_close.shape[0]):
                X_test.append(
                    [scaled_close[i - timesteps - predict_gap:i - predict_gap, 0],
                     scaled_volume[i - timesteps - predict_gap:i - predict_gap, 0]
                     ] + non_numeric_features[i]
                )
            X_test = np.array(X_test)
            X_test = np.array(X_test).transpose(0, 2, 1)

            # Predict stock price and inverse normalisation
            pred_pre_scaled = model.predict(X_test)
            pred_stock_price = sc_close.inverse_transform(pred_pre_scaled)
            flatten_pred_stock_price = [i[0] for i in pred_stock_price]

            # Retrieve actual stock price date
            stock_datetime = sql_df[sql_df['symbol'] == symbol][timesteps + predict_gap - 1: -1]['stock_datetime']

            # Calculate prediction date
            prediction_datetime = sql_df[sql_df['symbol'] == symbol][timesteps - 1:-predict_gap - 1]['stock_datetime']

            # Zip stock datetime and predicted stock price in order to iterate
            date_price = zip(stock_datetime, prediction_datetime, flatten_pred_stock_price)

            # Insert into datebase
            for stock_dt, pred_dt, price in date_price:
                ins = sa.insert(StockPrediction).values(
                    model_id=model_id, symbol=symbol, stock_datetime=stock_dt, prediction_datetime=pred_dt, predicted_close=price
                )

                con.execute(ins)

if __name__ == "__main__":
    main()
