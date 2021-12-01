import backtrader as bt


class PandasData(bt.feeds.PandasData):
    '''
    Uses a Pandas DataFrame as the feed source, using indices into column
    names (which can be "numeric")

    This means that all parameters related to lines must have numeric
    values as indices into the tuples

    Params:

      - ``nocase`` (default *True*) case insensitive match of column names

    Note:

      - The ``dataname`` parameter is a Pandas DataFrame

      - Values possible for datetime

        - None: the index contains the datetime
        - -1: no index, autodetect column
        - >= 0 or string: specific colum identifier

      - For other lines parameters

        - None: column not present
        - -1: autodetect
        - >= 0 or string: specific colum identifier
    '''
    lines = ('future_close',)
    params = (
        # Possible values for datetime (must always be present)
        #  None : datetime is the "index" in the Pandas Dataframe
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('datetime', 'stock_datetime'),

        # Possible values below:
        #  None : column not present
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('adj_close', -1),

        # custom columns
        ('symbol', 'symbol'),
        ('future_close', -1)
    )