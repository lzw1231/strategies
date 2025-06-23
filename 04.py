from vnpy_ctastrategy import CtaTemplate
from vnpy.trader.object import BarData, TickData, TradeData, OrderData
from vnpy_ctastrategy.base import StopOrder
from vnpy.trader.utility import BarGenerator, ArrayManager
from typing import Any
from vnpy.trader.constant import Interval


class WaitMoment(CtaTemplate):
    author = 'luozhw'
    parameters: list = []
    variables: list = []

    def __init__(self, cta_engine: Any, strategy_name: str, vt_symbol: str, setting: dict) -> None:
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg5 = BarGenerator(on_bar=self.on_bar, window=5, on_window_bar=self.on_5min_bar, interval=Interval.MINUTE)
        self.bg30 = BarGenerator(on_bar=self.on_bar, window=30, on_window_bar=self.on_30min_bar, interval=Interval.MINUTE)

        self.am5 = ArrayManager(50)
        self.am30 = ArrayManager(260)

    def on_init(self):
        self.write_log(f"策略初始化")
        self.load_bar(40)

    def on_start(self):
        self.write_log(f"策略启动")
        self.put_event()

    def on_stop(self):
        self.write_log(f"策略停止")
        self.put_event()

    def on_tick(self, tick: TickData):
        self.bg5.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.bg30.update_bar(bar)
        self.bg5.update_bar(bar)

    def on_5min_bar(self, bar: BarData) -> None:
        pass

    def on_30min_bar(self, bar: BarData) -> None:
        self.am30.update_bar(bar)

    def on_order(self, order: OrderData) -> None:
        pass

    def on_trade(self, trade: TradeData) -> None:
        pass

    def on_stop_order(self, order: StopOrder) -> None:
        pass
