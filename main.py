from datetime import datetime
import pandas as pd
import backtrader as bt
import matplotlib.pyplot as plt
import tushare as ts

plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置画图时的中文显示
plt.rcParams["axes.unicode_minus"] = False  # 设置画图时的负号显示


# 1.数据加载
def get_data(code='600519', start_time='2017-01-01', end_time='2022-01-01'):
    df = ts.get_k_data(code, start=start_time, end=end_time)
    df.index = pd.to_datetime(df.date)
    df['openinterest'] = 0
    # 对df的数据列进行一个整合
    df = df[['open', 'high', 'low', 'close', 'volume', 'openinterest']]
    return df


stock_df = get_data()
fromdate = datetime(2017, 1, 1)
todate = datetime(2022, 1, 1)
startcash = 100000
# 加载并读取数据源 dataname 数据来源 fromdate todate date格式
data = bt.feeds.PandasData(dataname=stock_df, fromdate=fromdate, todate=todate)


# 2.构建策略
# 上穿20日线买入，跌穿20日均线就卖出
class MyStrategy(bt.Strategy):
    params = (
        ('period_20', 20),
        ('period_15', 15),
    )

    def __init__(self):
        self.order = None
        self.ma20 = bt.indicators.SMA(self.datas[0], period=self.p.period_20)
        self.ma15 = bt.indicators.SMA(self.datas[0], period=self.p.period_15)
        # 15日均线和20日均线的差值
        self.ma_15_20 = self.ma15 - self.ma20

    # 每个bar都会执行一次, 回测的每个日期都会执行一次
    def next(self):
        # 空仓
        if not self.position:
            if self.datas[0].close[0] > self.ma[0]:
                self.order = self.buy(size=200)
                print("买入：")
                print(self.order)
        else:
            if self.datas[0].close[0] < self.ma[0]:
                self.order = self.sell(size=200)
                print("卖出：")
                print(self.order)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datatime.date(0)
        print('%s,%s' % (dt.isoformat(), txt))


# 3.策略设置
# 创建大脑
cerebro = bt.Cerebro()
# 将数据加入回测系统
cerebro.adddata(data)
# 加入自己的策略
cerebro.addstrategy(MyStrategy)
# 经纪人
cerebro.broker.setcash(startcash)
# 设置手续费
cerebro.broker.setcommission(0.0002)
# 设置滑点
cerebro.broker.set_slippage_perc(perc=0.0001)

# 4.执行回测
s = fromdate.strftime("%Y-%m-%d")
t = todate.strftime("%Y-%m-%d")
print(f"初始资金: {startcash}\n回测时间: {s}至{t}")
cerebro.run()

portval = cerebro.broker.getvalue()
print(f"剩余资金: {portval}\n回测时间: {s}至{t}")
