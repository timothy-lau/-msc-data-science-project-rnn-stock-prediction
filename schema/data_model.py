from sqlalchemy import Column, Integer, Text, VARCHAR, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

import datetime

Base = declarative_base()


class Symbols(Base):
    __tablename__ = 'dim_symbols'
    symbol = Column('symbol', VARCHAR(length=20), nullable=False, primary_key=True)
    name = Column('name', Text)
    market_cap = Column('market_cap', Float)
    country = Column('country', VARCHAR(length=50))
    ipo_year = Column('ipo_year', VARCHAR(length=20))
    sector = Column('sector', Text)
    industry = Column('industry', Text)
    market_type = Column('market_type', Text)
    date_updated = Column('date_updated', DateTime, nullable=False, default=datetime.datetime.utcnow())


class StockPrices(Base):
    __tablename__ = 'fact_stock_prices'
    record_id = Column('record_id', Integer, nullable=False, primary_key=True, autoincrement=True)
    symbol = Column('symbol', VARCHAR(length=20), ForeignKey('dim_symbols.symbol'), nullable=False)
    stock_datetime = Column('stock_datetime', DateTime, nullable=False)
    open = Column('open', Float)
    high = Column('high', Float)
    low = Column('low', Float)
    close = Column('close', Float)
    adj_close = Column('adj_close', Float)
    volume = Column('volume', Float)


class Models(Base):
    __tablename__ = 'dim_models'
    model_id = Column('model_id', Integer, nullable=False, primary_key=True, autoincrement=True)
    symbols_used = Column('symbols_used', Text)
    timesteps = Column('timesteps', Integer)
    predict_gap = Column('predict_gap', Integer)
    epochs = Column('epochs', Integer)
    dropout = Column('dropout', Float)
    layers = Column('layers', Integer)
    batch_size = Column('batch_size', Integer)
    created_date = Column('created_date', DateTime, nullable=False, default=datetime.datetime.utcnow())
    min_train_date = Column('min_train_date', DateTime)
    max_train_date = Column('max_train_date', DateTime)

class StockPrediction(Base):
    __tablename__ = 'fact_stock_prediction'
    dummy_id = Column('dummy_id', Integer, primary_key=True)
    created_date = Column('created_date', DateTime, nullable=False, default=datetime.datetime.utcnow())
    model_id = Column('model_id', Integer, ForeignKey('dim_models.model_id'), nullable=False)
    symbol = Column('symbol', VARCHAR(length=20), ForeignKey('dim_symbols.symbol'), nullable=False)
    prediction_datetime = Column('prediction_datetime', DateTime, nullable=False)
    stock_datetime = Column('stock_datetime', DateTime, nullable=False)
    predicted_close = Column('predicted_close', Float)

class ActualisedTable(Base):
    __tablename__ = 'tb_stock_actual_pred'
    dummy_id = Column('dummy_id', Integer, primary_key=True)
    stock_datetime = Column('stock_datetime')
    open = Column('open')
    high = Column('high')
    low = Column('low')
    adj_close = Column('adj_close')
    volume = Column('volume')
    predicted_close = Column('predicted_close')
    close = Column('close')
    batch_size = Column('batch_size')
    future_close = Column('future_close')
    model_id = Column('model_id')
    symbols_used = Column('symbols_used')
    timesteps = Column('timesteps')
    predict_gap = Column('predict_gap')
    epochs = Column('epochs')
    dropout = Column('dropout')
    layers = Column('layers')
    created_date = Column('created_date')
    min_train_date = Column('min_train_date')
    max_train_date = Column('max_train_date')
    symbol = Column('symbol')
    name = Column('name')
    market_cap = Column('market_cap')
    country = Column('country')
    ipo_year = Column('ipo_year')
    sector = Column('sector')
    industry = Column('industry')
    market_type = Column('market_type')
    date_updated = Column('date_updated')
