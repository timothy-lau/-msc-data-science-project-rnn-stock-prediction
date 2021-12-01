-- CREATE DIM_SYMBOLS
CREATE TABLE IF NOT EXISTS STOCK_DB.DIM_SYMBOLS (
    SYMBOL VARCHAR(20) NOT NULL PRIMARY KEY,
    NAME TEXT,
    MARKET_CAP DOUBLE,
    COUNTRY VARCHAR (50),
    IPO_YEAR VARCHAR (20),
    SECTOR TEXT,
    INDUSTRY TEXT,
    MARKET_TYPE TEXT,
    DATE_UPDATED DATETIME NOT NULL DEFAULT (NOW())
);

-- CREATE INDEX ON SYMBOL
CREATE INDEX dim_symbols_symbol_index ON STOCK_DB.DIM_SYMBOLS(symbol);
CREATE TABLE IF NOT EXISTS STOCK_DB.FACT_STOCK_PRICES (
    RECORD_ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    SYMBOL VARCHAR(20) NOT NULL,
    STOCK_DATETIME DATETIME NOT NULL,
    OPEN DOUBLE,
    HIGH DOUBLE,
    LOW DOUBLE,
    CLOSE DOUBLE,
    ADJ_CLOSE DOUBLE,
    VOLUME DOUBLE,
    FOREIGN KEY (SYMBOL) REFERENCES STOCK_DB.DIM_SYMBOLS(SYMBOL)
);

-- CREATE SYMBOL INDEX ON FACT STOCK PRICES
CREATE INDEX symbol_date_index ON STOCK_DB.FACT_STOCK_PRICES (SYMBOL, stock_datetime);

-- CREATE TABLE DIM_MODELS
CREATE TABLE IF NOT EXISTS STOCK_DB.DIM_MODELS (
    MODEL_ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    SYMBOLS_USED TEXT,
    TIMESTEPS INT,
    PREDICT_GAP INT,
    EPOCHS INT,
    DROPOUT DOUBLE,
    LAYERS INT,
    CREATED_DATE DATETIME NOT NULL DEFAULT (NOW()),
    MIN_TRAIN_DATE DATETIME,
    MAX_TRAIN_DATE DATETIME
);

-- CREATE MODEL ID INDEX FOR DIM_MODELS
CREATE INDEX model_id_index ON STOCK_DB.DIM_MODELS (MODEL_ID)
;

-- CREATE TABLE FACT_STOCK_PREDICTION
CREATE TABLE IF NOT EXISTS STOCK_DB.FACT_STOCK_PREDICTION (
    CREATED_DATE DATETIME NOT NULL DEFAULT (NOW()),
    MODEL_ID INT NOT NULL,
    SYMBOL VARCHAR(20) NOT NULL,
    PREDICTION_DATETIME DATETIME NOT NULL,
    STOCK_DATETIME DATETIME NOT NULL,
    PREDICTED_CLOSE DOUBLE,
    FOREIGN KEY (MODEL_ID) REFERENCES STOCK_DB.DIM_MODELS(MODEL_ID)
);

-- CREATE INDEX FOR FACT_STOCK_PREDICTION
CREATE INDEX symbol_model_date_index ON STOCK_DB.FACT_STOCK_PREDICTION (SYMBOL, MODEL_ID, stock_datetime);
;

-- ACTUALISE JOIN RESULLTS FOR TABLEAU OPTIMISATION
CREATE TABLE STOCK_DB.TB_STOCK_ACTUAL_PRED AS
SELECT
FACT_STOCK_PRICES.STOCK_DATETIME
, open
, high
, low
, adj_close
, volume
, CLOSE
, fact_stock_prediction.PREDICTED_CLOSE -- Close from prediction joined on the actual stock date, used for validation
, pred.predicted_close future_close -- Close from prediction joined on the date predictions were made, used for backtesting
, DIM_MODELS.*
, DIM_SYMBOLS.*
from fact_stock_prices
inner join fact_stock_prediction on fact_stock_prices.stock_datetime = fact_stock_prediction.STOCK_DATETIME
	and fact_stock_prices.symbol = fact_stock_prediction.symbol
inner join fact_stock_prediction pred on fact_stock_prediction.stock_datetime = pred.prediction_datetime
	and fact_stock_prediction.symbol = pred.symbol
    and fact_stock_prediction.MODEL_ID = pred.MODEL_ID
inner join dim_models on dim_models.model_id = fact_stock_prediction.model_id
inner join dim_symbols on dim_symbols.symbol = fact_stock_prices.SYMBOL
;
