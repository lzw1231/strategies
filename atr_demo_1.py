from vnpy_ctastrategy.template import CtaTemplate


class AtrTreeDemo(CtaTemplate):
    author = "luozhw"

    # 参数
    atr_multiple: int = 5
    atr_parameter: int = 20

    fixed_profit_target: int = 100
    fixed_stop_target: int = 15

    count_control: int = 1
