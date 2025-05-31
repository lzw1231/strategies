from typing import Any
from vnpy.trader.constant import Interval, Offset, Direction
from vnpy_ctastrategy import CtaTemplate
from vnpy.trader.object import TickData,BarData,TradeData,OrderData
from vnpy_ctastrategy.base import StopOrder
from vnpy.trader.utility import BarGenerator,ArrayManager

class WaitMoment_02(CtaTemplate):
    author = "luozhw"

    #参数的定义
    slow_n=200
    fast_n=10
    mid_n=60
    N_parameter=10
    stop_parameter=20
    profit_parameter=100
    fix_size=1

    parameters :list=[
        'slow_n',
        'fast_n',
        'mid_n' ,
        'N_parameter',
        'stop_parameter' ,
        'profit_parameter' ,
        'fix_size',
    ]

    slow_var=0
    fast_var=0
    mid_var=0
    stop_price=0
    profit_price=0

    #定义变量
    variables :list=[
        'slow_var',
        'fast_var',
        'mid_var',
        'stop_price',
        'profit_price'
    ]

    def __init__(self, cta_engine: Any, strategy_name: str, vt_symbol: str,setting:dict)->None:
        super().__init__(cta_engine,strategy_name,vt_symbol,setting)

        #定义实例的变量
        self.bg5=BarGenerator(on_bar=self.on_bar,
                              window=5,
                              on_window_bar=self.on_5min_bar,
                              interval=Interval.MINUTE
                              )
        self.bg30=BarGenerator(on_bar=self.on_bar,
                               window=30,
                               on_window_bar=self.on_30min_bar,
                               interval=Interval.MINUTE
                               )
        self.am5=ArrayManager(50)
        self.am30=ArrayManager(300)

        self.buy_price=0
        self.sell_price = 0
        self.short_price = 0
        self.cover_price = 0

    def on_init(self) -> None:
        """"""

        self.write_log(f'{self.vt_symbol} -> 策略初始化')
        self.load_bar(50)

    def on_start(self) -> None:
        self.write_log(f'{self.vt_symbol} -> 策略启动')
        self.put_event()

    def on_stop(self):
        self.write_log('{self.vt_symbol} -> 策略停止')
        self.put_event()

    def on_tick(self, tick: TickData) -> None:
        #执行1遍on_bar
        self.bg5.update_tick(tick)

    def on_bar(self, bar: BarData) -> None:
        self.bg30.update_bar(bar)
        self.bg5.update_bar(bar)

    def on_5min_bar(self, bar: BarData) -> None:
        self.am5.update_bar(bar)

        if not self.am30.inited:
            return
        if not self.am5.inited:
            return

        #撤销所有委托，比如上一根K线有委托没成交
        self.cancel_all()

        #指标判断，是否开仓平仓
        if self.pos==0: #判断空仓，是否要开仓
            if self.fast_var>self.mid_var >self.slow_var and bar.close_price<min(self.am5.close_array[-self.N_parameter:-1]):
               self.buy_price=bar.close_price
            elif self.fast_var<self.mid_var<self.slow_var and bar.close_price>max(self.am5.close_array[-self.N_parameter:-1]):
                self.short_price=bar.close_price
        elif self.pos>0: #判断多仓，是否要平多仓
            if bar.close_price < self.mid_var or self.fast_var<self.mid_var:
               self.sell_price=bar.close_price
               #是否要做空
               if self.fast_var < self.mid_var < self.slow_var and bar.close_price > max(self.am5.close_array[-self.N_parameter: -1]):
                    self.short_price=bar.close_price
        elif self.pos<0: #判断空仓，是否要平空仓
            if bar.close_price > self.mid_var or self.fast_var > self.mid_var:
                self.cover_price=bar.close_price
                # 判断要不要开多仓
                if self.fast_var > self.mid_var > self.slow_var and bar.close_price < min(self.am5.close_array[-self.N_parameter: -1]):
                    self.buy_price=bar.close_price


        if self.stop_price and self.profit_price and self.pos!=0:
            if self.pos>0:
                self.sell(self.stop_price,self.profit_price,stop=True) #停止单止损
                self.sell(self.profit_price,self.stop_price,stop=False) #限价单止盈
            elif self.pos<0:
                self.cover(self.stop_price,self.profit_price,stop=True) #停止单止损
                self.cover(self.profit_price,self.stop_price,stop=False) #限价单止盈

        self.send_now_orders()

    def send_now_orders(self):
        """发送委托"""
        if self.buy_price and self.pos==0:
            self.buy(self.buy_price,self.fix_size)
            self.buy_price=0
        if self.short_price and self.pos==0:
            self.short(self.short_price,self.fix_size)
            self.short_price=0
        if self.sell_price and self.pos>0:
            self.sell(self.sell_price,self.fix_size,stop=True)
            self.sell_price=0
        if self.cover_price and self.pos<0:
            self.cover(self.cover_price,self.fix_size,stop=True)
            self.cover_price=0




    def on_30min_bar(self, bar: BarData) -> None:

        self.am30.update_bar(bar)
        if not self.am30.inited:return

        self.fast_var=self.am30.sma(self.fast_n)
        self.mid_var=self.am30.sma(self.mid_n)
        self.slow_var=self.am30.sma(self.slow_n)


    # 限价单有变化调用，有成交时，先调用on_order,后调用on_trade
    def on_order(self, stop_order: StopOrder) -> None:
        pass

    # 有成交时调用
    def on_trade(self, trade: TradeData) -> None:
        if trade.offset==Offset.OPEN and abs(self.pos)==self.fix_size:

            #根据方向确定乘数因子
            direction_factor =1 if trade.direction==Direction.LONG else -1

            self.stop_price=trade.price *(1000-direction_factor*self.stop_parameter)/1000
            self.profit_price=trade.price*(1000+direction_factor*self.profit_parameter)/1000


        elif trade.offset==Offset.CLOSE and self.pos==0:
            self.profit_price=0
            self.stop_price=0
            self.send_now_orders()

    def on_stop_order(self, stop_order: StopOrder) -> None:
        pass

