import datetime
import pandas as pd
import backtrader as bt
import matplotlib.pyplot as plt
import tushare as ts

plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置画图时的中文显示
plt.rcParams["axes.unicode_minus"] = False  # 设置画图时的负号显示


# 1.数据加载
def get_data(code, start_time, end_time):
    df = ts.get_k_data(code, start=start_time, end=end_time)
    df.index = pd.to_datetime(df.date)
    df['openinterest'] = 0
    # 对df的数据列进行一个整合
    df = df[['open', 'high', 'low', 'close', 'volume', 'openinterest']]
    return df


# 2.构建策略
class MyStrategy(bt.Strategy):
    params = (
        ('size', 100),
        ('bolling_period', 50),
        ('trend_period', 20),
        ('dev_factor', 1.25),
    )

    variables = {
        'long_buy_count': 0,
        'short_buy_count': 0,
        'position_size': 0,
        'adaptive_sma_period': 50,
        'adaptive_sma': 0.0,
    }

    def __init__(self):
        # 交易订单状态初始化
        self.order = None

        # 计算布林线
        # 使用自带的indicators中自带的函数计算出支撑线和压力线，period设置周期，默认是20
        self.lines.top = bt.indicators.BollingerBands(self.datas[0], period=self.p.bolling_period, devfactor=self.p.dev_factor).top
        self.lines.mid = bt.indicators.BollingerBands(self.datas[0], period=self.p.bolling_period, devfactor=self.p.dev_factor).mid
        self.lines.bot = bt.indicators.BollingerBands(self.datas[0], period=self.p.bolling_period, devfactor=self.p.dev_factor).bot
        self.sma = bt.indicators.SMA(self.datas[0], period=self.variables['adaptive_sma_period'])

    # 每个bar都会执行一次, 回测的每个日期都会执行一次
    def next(self):
        if self.datas[0].datetime.date(0) > self.datas[0].datetime.date(-self.p.trend_period):
            trend = int(self.datas[0].close[0] - self.datas[0].close[-self.p.trend_period])

            # 加仓
            if self.variables['position_size'] == 0:
                if trend > 0 and self.datas[0].close[0] >= self.lines.top[0]:
                    self.order = self.buy(size=self.p.size)
                    self.variables['position_size'] += self.p.size
                    self.variables['long_buy_count'] += 1
                    print("======================")
                    print(f"{self.datas[0].datetime.date(0)}收盘价突破上轨，做多价格为{self.datas[0].close[0]}")
                # elif trend < 0 and self.datas[0].close[0] <= self.lines.bot[0]:
                #     self.order = self.sell(size=self.p.size)
                #     self.variables['position_size'] -= self.p.size
                #     self.variables['short_buy_count'] += 1
                #     print("======================")
                #     print(f"{self.datas[0].datetime.date(0)}收盘价跌破下轨，做空价格为{self.datas[0].close[0]}")

            # 自适应调节均线周期
            if self.variables['position_size'] == 0:
                self.variables['adaptive_sma_period'] = 50
            else:
                self.variables['adaptive_sma_period'] -= 2
                self.variables['adaptive_sma_period'] = max(self.variables['adaptive_sma_period'], 10)

            if self.datas[0].datetime.date(0) > self.datas[0].datetime.date(-self.variables['adaptive_sma_period']):
                close_sum = 0
                for i in range(0, self.variables['adaptive_sma_period']):
                    close_sum += self.datas[0].close[-i]
                self.variables['adaptive_sma'] = close_sum / self.variables['adaptive_sma_period']

            # 平仓
            if self.variables['position_size'] > 0 and self.datas[0].low[0] <= self.variables['adaptive_sma'] and self.variables['adaptive_sma'] < self.lines.top[0]:
                self.order = self.sell(size=self.variables['position_size'])
                self.variables['position_size'] -= self.variables['position_size']
                print("======================")
                print(f"{self.datas[0].datetime.date(0)}最低价跌破自适应均线且自适应均线突破布林带上轨，平多价格为{self.datas[0].close[0]}")
            # if self.variables['position_size'] < 0 and self.datas[0].high[0] >= self.variables['adaptive_sma'] and self.variables['adaptive_sma'] > self.lines.bot[0]:
            #     self.order = self.buy(size=self.variables['position_size'])
            #     self.variables['position_size'] -= self.variables['position_size']
            #     print("======================")
            #     print(f"{self.datas[0].datetime.date(0)}最高价突破自适应均线且自适应均线跌破布林带下轨，平空价格为{self.datas[0].close[0]}")

        # if self.datas[0].close <= self.lines.bot[0]:
        #     self.order = self.buy(size=self.p.size)
        #     self.variables['position_size'] += self.p.size
        #     print("======================")
        #     print(f"{self.datas[0].datetime.date(0)}收盘价跌破下轨，买入价格为{self.datas[0].close[0]}")
        #
        # if self.datas[0].close >= self.lines.top[0]:
        #     self.order = self.sell(size=self.p.size)
        #     self.variables['position_size'] -= self.p.size
        #     print("======================")
        #     print(f"{self.datas[0].datetime.date(0)}收盘价超过上轨，卖出价格为{self.datas[0].close[0]}")


if __name__ == '__main__':
    # 3.策略设置
    # 创建大脑
    cerebro = bt.Cerebro()

    # 绘图显示的参数
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(bt.observers.Value)

    # 加载并读取数据源
    start_cash = 200000
    start_date_time = datetime.datetime(2020, 1, 1)
    start_ymd_time = start_date_time.strftime("%Y-%m-%d")
    end_date_time = datetime.datetime(2022, 11, 1)
    end_ymd_time = end_date_time.strftime("%Y-%m-%d")
    stock_code = '600519'
    data = get_data(stock_code, start_ymd_time, end_ymd_time)
    call_data = bt.feeds.PandasData(dataname=data, fromdate=start_date_time, todate=end_date_time)

    # 将数据加入回测系统
    cerebro.adddata(call_data)
    # 加入自己的策略
    cerebro.addstrategy(MyStrategy)
    # 经纪人
    cerebro.broker.setcash(start_cash)
    # 设置手续费
    cerebro.broker.setcommission(0.0002)
    # 设置滑点
    cerebro.broker.set_slippage_perc(perc=0.0001)

    # 4.执行回测
    result = cerebro.run()
    print(f'初始化资金: {start_cash}, 回测时间: {start_ymd_time}：{end_ymd_time}')
    profit = int(cerebro.broker.getvalue()) - start_cash
    print('投资收益: %.2f' % profit)
    profit_ratio = profit / start_cash * 100
    print('投资收益率: %.2f%%' % profit_ratio)
    print('做多次数：%s, 做空次数：%s' % (MyStrategy.variables['long_buy_count'], MyStrategy.variables['short_buy_count']))
    # Plot the result
    cerebro.plot(style='candlestick')
