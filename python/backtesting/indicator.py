import backtrader as bt

class MyIndicator(bt.Indicator):
    lines = ('future_close',)
    plotinfo = dict(subplot=False, plotname='future_close')

    def __init__(self):
        self.lines.future_close = self.data.future_close