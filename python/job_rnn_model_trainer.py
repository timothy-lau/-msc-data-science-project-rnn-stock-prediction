import pandas as pd
from datetime import datetime
import numpy as np
import logging

import sqlalchemy as sa
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
from sklearn.preprocessing import MinMaxScaler

from python.common.mysql_connector import MySqlConnector
from schema.data_model import StockPrices, Symbols, Models
from config_reader import ConfigReader


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logger = logging.getLogger('job_rnn_model_trainer.py')
    logger.info('Starting Job RNN Model Trainer...')

    # Initalise config reader
    app_config = ConfigReader('../configurations/run_config.json')

    logger.info('Connecting to database...')
    # Initialise database connection
    engine = MySqlConnector(
        host='localhost',
        user='root',
        password='db_user',
        database='stock_db'
    )

    con = engine.con

    # Shortlist list of stock to train model on
    shortlist_stock_stmt = app_config.RNN['SHORTLIST_STOCK_QUERY']

    shortlist_stock = con.execute(shortlist_stock_stmt).fetchall()
    symbol_list = [i[0] for i in shortlist_stock]
    logger.info('Training model on: {}'.format(' '.join(symbol_list)))

    if app_config.RNN['TRAIN_MODEL_MAX_DATE']:
        max_date = app_config.RNN['TRAIN_MODEL_MAX_DATE']
    else:
        max_date = datetime.now()

    # Read from database filter on shortlist tickers
    sql_df = pd.read_sql(
        sa.select(
            StockPrices.stock_datetime, StockPrices.symbol, StockPrices.close, StockPrices.volume, Symbols.market_type,
            Symbols.sector) \
            .join(Symbols) \
            .where(StockPrices.symbol.in_([i[0] for i in shortlist_stock])) \
            .where(StockPrices.stock_datetime <= max_date), con)

    min_date = str(min(sql_df['stock_datetime']))

    logger.info('Dataset size is {} rows'.format(len(sql_df)))

    # One hot encoding
    sql_df = sql_df.join(pd.get_dummies(sql_df['sector'], prefix='sector_', drop_first=True)).drop('sector', axis=1)
    sql_df = sql_df.join(pd.get_dummies(sql_df['market_type'], prefix='market_type_', drop_first=True)).drop(
        'market_type', axis=1)

    symbols_used = ' '.join(symbol_list)

    # Params Format: timesteps, predict_gap, epochs, dropout, layers, batch_size
    # Control parameters are (60, 1, 50, 0.2, 4, 32),
    param_list = app_config.RNN['MODEL_PARAMS']

    for timesteps, predict_gap, epochs, dropout, layers, batch_size in param_list:
        logger.info('Training model on timesteps: %s, predict_gap: %s, epochs: %s, dropout: %s, layers: %s, batch_size: %s' % (
            timesteps, predict_gap, epochs, dropout, layers, batch_size
        ))
        # Feature Scaling
        sc_close = MinMaxScaler(feature_range=(0, 1))
        sc_volume = MinMaxScaler(feature_range=(0, 1))
        symbol_list = sql_df['symbol'].unique()

        X_train_list = []
        y_train_list = []

        # Iterate each stock and create steps individually
        for symbol in symbol_list:
            X_train = []
            y_train = []

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

            # Creating a data structure with time-steps in a 3d array form
            for i in range(timesteps + predict_gap, scaled_close.shape[0]):
                X_train.append(
                    [scaled_close[i - timesteps - predict_gap:i - predict_gap, 0],
                     scaled_volume[i - timesteps - predict_gap:i - predict_gap, 0]
                     ] + non_numeric_features[i]
                )
                y_train.append(scaled_close[i, 0])

            X_train, y_train = np.array(X_train), np.array(y_train)
            X_train = np.array(X_train).transpose((0, 2, 1))
            X_train_list.append(X_train)
            y_train_list.append(y_train)

        combined_X_train = np.concatenate(X_train_list)
        combined_y_train = np.concatenate(y_train_list)


        model = Sequential()

        # 1st layer
        model.add(LSTM(units=50, return_sequences=True, input_shape=(combined_X_train.shape[1], combined_X_train.shape[2])))
        model.add(Dropout(dropout))

        if layers == 4:
            # 2nd layer
            model.add(LSTM(units=50, return_sequences=True))
            model.add(Dropout(dropout))

            # 3rd layer
            model.add(LSTM(units=50, return_sequences=True))
            model.add(Dropout(dropout))

        # 4th layer
        model.add(LSTM(units=50))
        model.add(Dropout(dropout))

        # Adding the output layer
        model.add(Dense(units=1))

        # Compiling the RNN
        model.compile(optimizer='adam', loss='mean_squared_error')

        # Fitting the RNN to the Training set
        model.fit(combined_X_train, combined_y_train, epochs=epochs, batch_size=batch_size)

        ins = sa.insert(Models).values(
            symbols_used=symbols_used, timesteps=timesteps, predict_gap=predict_gap, epochs=epochs, dropout=dropout, layers=layers, batch_size=batch_size, min_train_date=min_date, max_train_date=max_date
        )

        con.execute(ins)

        latest_model_id = con.execute(
            sa.select(sa.func.max(Models.model_id))
                .limit(1)
        ).fetchall()

        if latest_model_id:
            model_id = latest_model_id[0][0]

        # Saving model
        dir = '../lstm_models/model_{}'.format(str(model_id))
        model.save(dir)
        logger.info('Saved model {} to location {}'.format(str(model_id), dir))

if __name__ == "__main__":
    main()
