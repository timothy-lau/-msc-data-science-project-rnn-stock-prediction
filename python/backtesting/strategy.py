import backtrader as bt
from .indicator import MyIndicator


class commonStrategy():
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        portfolio = self.broker.get_value()
        cash = self.broker.cash
        equity = portfolio - cash
        cashflow = cash / portfolio
        print('%s, PF %.0f, Cash %.0f, Equity %i, CF %s Units %i' % (
            dt.isoformat(), portfolio, cash, equity, '{:.0%}'.format(cashflow), self.units), txt)

    def perc_cash_to_units(self, cash, close, perc):
        return int(cash * perc / close)

    def perc_equity_to_units(self, equity, perc):
        return int(equity * perc)

    def buy_by_perc(self, cash, close, buy_perc):
        n_units = self.perc_cash_to_units(cash, close, buy_perc)
        value = n_units * close
        if cash >= value:
            self.order = self.buy(size=n_units)
            self.units += n_units
            self.log('BUY CREATE, Price %.2f, Units %i, Value %.2f' %
                     (close, n_units, value))

    def sell_by_perc(self, close, sell_perc):
        if self.units:
            n_units = self.perc_equity_to_units(self.units, sell_perc)
            value = n_units * close
            if self.units >= n_units:
                self.order = self.sell(size=n_units)
                self.units -= n_units
                self.log('SELL CREATE, Close %.2f, Units %i, Value %.2f' %
                         (close, n_units, value))

class FollowTheTrendBollinger(bt.Strategy, commonStrategy):
    def __init__(self, params_dict):
        # Set params
        self.params.maperiod = params_dict['maperiod']
        self.params.buy_perc = params_dict['buy_perc']
        self.params.sell_perc = params_dict['sell_perc']
        self.params.stdev = params_dict['stdev']

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.data.close
        self.future_close = self.data.future_close
        self.portfolio = 0
        self.cash = 0

        # Keep track of order and equity
        self.order = None
        self.units = 0

        # Add a MovingAverageSimple indicator
        self.bband = bt.indicators.BollingerBands(period=self.params.maperiod, devfactor=self.params.stdev)
        # self.future_close_ind = MyIndicator(self.data)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %(order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' % (order.executed.price, order.executed.value, order.executed.comm))
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None


    def next(self):
        # Simply log the closing price of the series from the reference
        self.portfolio = self.broker.get_value()
        self.cash = self.broker.cash
        self.log('Close %.2f,' % (self.dataclose[0]))

        # Buy section
        if self.dataclose[0] >= self.bband.lines.top[0]:
            self.buy_by_perc(self.cash, self.dataclose[0], self.params.buy_perc)

        # Sell section
        if self.dataclose[0] <= self.bband.lines.bot[0]:
            self.sell_by_perc(self.dataclose[0], self.params.sell_perc)


########################################################################################################################
class FollowTheTrendMA(bt.Strategy, commonStrategy):
    def __init__(self, params_dict):
        # Set params
        self.params.maperiod = params_dict['maperiod']
        self.params.maperiod2 = params_dict['maperiod2']
        self.params.buy_perc = params_dict['buy_perc']
        self.params.sell_perc = params_dict['sell_perc']
        self.params.stdev = params_dict['stdev']

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.data.close
        self.future_close = self.data.future_close
        self.portfolio = 0
        self.cash = 0

        # Keep track of order and equity
        self.order = None
        self.units = 0

        # Add a MovingAverageSimple indicator
        # self.bband = bt.indicators.BollingerBands(period=self.params.maperiod, devfactor=self.params.stdev)
        self.sma1 = bt.ind.SMA(period=self.params.maperiod)
        self.sma2 = bt.ind.SMA(period=self.params.maperiod2)
        self.sma_crossover = bt.ind.CrossOver(self.sma1, self.sma2, subplot=False)
        self.close_ma_crossover = bt.ind.CrossOver(self.dataclose, self.sma1, subplot=False)
        # self.future_close_ind = MyIndicator(self.data)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %(order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' % (order.executed.price, order.executed.value, order.executed.comm))
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.portfolio = self.broker.get_value()
        self.cash = self.broker.cash
        self.log('Close %.2f,' % (self.dataclose[0]))

        # Buy section
        if self.sma_crossover > 0:
            self.buy_by_perc(self.cash, self.dataclose[0], self.params.buy_perc)

        if self.sma1 > self.sma2:
            if self.close_ma_crossover > 0:
                self.buy_by_perc(self.cash, self.dataclose[0], self.params.buy_perc)

        # Sell section
        if self.sma_crossover < 0:
            self.sell_by_perc(self.dataclose[0], self.params.sell_perc)

        if self.sma1 < self.sma2:
            if self.close_ma_crossover < 0:
                self.sell_by_perc(self.dataclose[0], self.params.sell_perc)
                

########################################################################################################################
class MeanReversionMinMax(bt.Strategy, commonStrategy):
    def __init__(self, params_dict):
        # Set params
        self.params.maperiod = params_dict['maperiod']
        self.params.buy_perc = params_dict['buy_perc']
        self.params.sell_perc = params_dict['sell_perc']
        self.params.stdev = params_dict['stdev']

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.data.close
        self.future_close = self.data.future_close
        self.portfolio = 0
        self.cash = 0

        # Keep track of order and equity
        self.order = None
        self.units = 0

        # Add a MovingAverageSimple indicator
        self.max = bt.ind.MaxN(self.dataclose, period=self.params.maperiod, subplot=False)
        self.min = bt.ind.MinN(self.dataclose, period=self.params.maperiod, subplot=False)

        self.crossoverbot = bt.ind.CrossOver(self.dataclose, self.min)
        self.crossovertop = bt.ind.CrossOver(self.dataclose, self.max)
        # self.future_close_ind = MyIndicator(self.data)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %(order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' % (order.executed.price, order.executed.value, order.executed.comm))
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.portfolio = self.broker.get_value()
        self.cash = self.broker.cash
        self.log('Close %.2f,' % (self.dataclose[0]))

        # Buy section
        # if self.datas[0].close <= self.bband.lines.bot[0]:
        if self.dataclose == self.min:
            self.buy_by_perc(self.cash, self.dataclose[0], self.params.buy_perc)

        # Sell section
        # if self.datas[0].close >= self.bband.lines.top[0]:
        if self.dataclose == self.max:
            self.sell_by_perc(self.dataclose[0], self.params.sell_perc)

########################################################################################################################
class MeanReversionBollinger(bt.Strategy, commonStrategy):
    def __init__(self, params_dict):
        # Set params
        self.params.maperiod = params_dict['maperiod']
        self.params.buy_perc = params_dict['buy_perc']
        self.params.sell_perc = params_dict['sell_perc']
        self.params.stdev = params_dict['stdev']

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.data.close
        self.future_close = self.data.future_close
        self.portfolio = 0
        self.cash = 0

        # Keep track of order and equity
        self.order = None
        self.units = 0

        # Add a MovingAverageSimple indicator
        self.bband = bt.indicators.BollingerBands(period=self.params.maperiod, devfactor=self.params.stdev)
        self.crossoverbot = bt.ind.CrossOver(self.dataclose, self.bband.lines.bot)
        self.crossovertop = bt.ind.CrossOver(self.dataclose, self.bband.lines.top)
        # self.future_close_ind = MyIndicator(self.data)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %(order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' % (order.executed.price, order.executed.value, order.executed.comm))
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.portfolio = self.broker.get_value()
        self.cash = self.broker.cash
        self.log('Close %.2f,' % (self.dataclose[0]))

        # Buy section
        # if self.datas[0].close <= self.bband.lines.bot[0]:
        if self.crossoverbot < 0:
            self.buy_by_perc(self.cash, self.dataclose[0], self.params.buy_perc)

        # Sell section
        # if self.datas[0].close >= self.bband.lines.top[0]:
        if self.crossovertop > 0:
            self.sell_by_perc(self.dataclose[0], self.params.sell_perc)
