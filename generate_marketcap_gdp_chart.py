import csv
import html as html_module
import json
import math
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "marketcap_gdp_raw.json"
CSV_PATH = ROOT / "a_share_marketcap_gdp_match.csv"
SVG_PATH = ROOT / "a_share_marketcap_gdp_match.svg"
HTML_PATH = ROOT / "a_share_marketcap_gdp_match.html"

COLORS = {
    "surface": "#FAFAFB",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E4E7EF",
    "axis": "#CDD3E1",
    "blue": "#4569B7",
    "blue_dark": "#27457E",
    "orange": "#C8754A",
    "gold": "#D64545",
    "green": "#2C8C67",
    "fed": "#168A5B",
}

FED_RATE_AXIS_MAX = 6.0
# 分母 = 上年GDP × 80%（巴菲特指标常用的 80% 门槛线，100% 即市值达到上年GDP的 80%）
GDP_BENCHMARK_FACTOR = 0.80

# 画布与绘图区几何：Python 端的 SVG 与 HTML 里的缩放/悬停脚本共用同一组数值，
# 改布局只需改这里，避免两边坐标漂移。
CHART_WIDTH = 1440
CHART_HEIGHT = 720
CHART_ML = 88
CHART_MR = 56
PLOT_Y0 = 250
PLOT_Y1 = 550

FED_RATE_STEPS = [
    ("2005-03-22", 2.75),
    ("2005-05-03", 3.00),
    ("2005-06-30", 3.25),
    ("2005-08-09", 3.50),
    ("2005-09-20", 3.75),
    ("2005-11-01", 4.00),
    ("2005-12-13", 4.25),
    ("2006-01-31", 4.50),
    ("2006-03-28", 4.75),
    ("2006-05-10", 5.00),
    ("2006-06-29", 5.25),
    ("2007-09-18", 4.75),
    ("2007-10-31", 4.50),
    ("2007-12-11", 4.25),
    ("2008-01-22", 3.50),
    ("2008-01-30", 3.00),
    ("2008-03-18", 2.25),
    ("2008-04-30", 2.00),
    ("2008-10-08", 1.50),
    ("2008-10-29", 1.00),
    ("2008-12-16", 0.25),
    ("2015-12-16", 0.50),
    ("2016-12-14", 0.75),
    ("2017-03-15", 1.00),
    ("2017-06-14", 1.25),
    ("2017-12-13", 1.50),
    ("2018-03-21", 1.75),
    ("2018-06-13", 2.00),
    ("2018-09-26", 2.25),
    ("2018-12-19", 2.50),
    ("2019-07-31", 2.25),
    ("2019-09-18", 2.00),
    ("2019-10-30", 1.75),
    ("2020-03-03", 1.25),
    ("2020-03-15", 0.25),
    ("2022-03-16", 0.50),
    ("2022-05-04", 1.00),
    ("2022-06-15", 1.75),
    ("2022-07-27", 2.50),
    ("2022-09-21", 3.25),
    ("2022-11-02", 4.00),
    ("2022-12-14", 4.50),
    ("2023-02-01", 4.75),
    ("2023-03-22", 5.00),
    ("2023-05-03", 5.25),
    ("2023-07-26", 5.50),
    ("2024-09-18", 5.00),
    ("2024-11-07", 4.75),
    ("2024-12-18", 4.50),
    ("2025-09-17", 4.25),
    ("2025-10-29", 4.00),
    ("2025-12-10", 3.75),
]

# Concise summaries of the policy background stated in the corresponding FOMC
# post-meeting statements. These are shown only when the user hovers a rate-change node.
FED_RATE_REASONS = {
    "2005-03-22": "经济扩张稳健；核心通胀仍受抑，但资源利用率和能源价格带来上行风险",
    "2005-05-03": "经济继续稳健扩张；能源价格和资源利用率可能推高通胀压力",
    "2005-06-30": "经济增长反弹；能源及其他商品价格、资源利用率增加通胀风险",
    "2005-08-09": "经济保持良好增长；继续撤除宽松以平衡增长与价格稳定风险",
    "2005-09-20": "经济活动持续扩张；能源价格和资源利用率上升带来通胀风险",
    "2005-11-01": "经济扩张仍稳健；能源价格上升可能增加通胀压力",
    "2005-12-13": "经济继续扩张；资源利用率提高和能源价格上升需要防范通胀",
    "2006-01-31": "经济增长稳健；核心通胀受控，但资源利用率和能源价格构成风险",
    "2006-03-28": "经济增长反弹且资源利用率上升；能源和商品价格可能推高通胀",
    "2006-05-10": "经济增长强劲、就业稳健；资源利用率和能源价格带来通胀压力",
    "2006-06-29": "经济仍在扩张；能源和商品价格、资源利用率使通胀风险上升",
    "2007-09-18": "住房调整和金融市场动荡加剧；增长下行风险明显上升",
    "2007-10-31": "住房市场收缩、金融条件收紧；需要降低经济增长的下行风险",
    "2007-12-11": "经济增长放缓，住房和金融市场承压；增长下行风险超过通胀风险",
    "2008-01-22": "住房与金融市场恶化，增长下行风险显著上升；采取紧急降息",
    "2008-01-30": "住房部门持续收缩、信贷条件收紧；支持经济增长并缓解下行风险",
    "2008-03-18": "住房和金融市场压力加剧，金融条件急剧收紧；防止金融压力反馈至实体经济",
    "2008-04-30": "经济活动疲弱、房市调整和金融市场承压；为增长提供支持并兼顾通胀",
    "2008-10-08": "全球金融危机急剧恶化；与主要央行协调降息以缓解金融压力",
    "2008-10-29": "金融市场持续紧张，住房、消费和投资走弱；防止经济进一步恶化",
    "2008-12-16": "经济活动和就业继续恶化，通胀压力消退；将利率降至接近零支持经济",
    "2015-12-16": "就业持续改善，通胀预计回升；经济已具备承受渐进加息的条件",
    "2016-12-14": "就业继续增强、经济温和扩张，通胀接近2%；继续撤除宽松",
    "2017-03-15": "劳动力市场持续改善，经济温和扩张，通胀较前期回升",
    "2017-06-14": "就业增长稳健、经济温和扩张；通胀虽低于2%但预计回升",
    "2017-12-13": "经济稳健扩张、就业持续改善，通胀逐步接近2%",
    "2018-03-21": "经济活动稳健、就业持续增强，通胀接近2%；渐进撤除宽松",
    "2018-06-13": "经济活动强劲、就业持续改善，通胀接近2%；继续逐步正常化",
    "2018-09-26": "经济活动强劲、就业增长稳健，通胀接近2%；继续撤除宽松",
    "2018-12-19": "经济和就业保持扩张，通胀接近2%；继续加息但政策路径趋于渐进",
    "2019-07-31": "全球增长放缓、贸易政策不确定性和通胀偏低；采取预防性降息",
    "2019-09-18": "全球增长放缓和贸易不确定性持续，通胀低于目标；进一步提供支持",
    "2019-10-30": "全球增长和商业投资偏弱、贸易不确定性仍在；通胀偏低，需要支持扩张",
    "2020-03-03": "新冠疫情对经济活动构成不断演变的风险；紧急降息支持经济",
    "2020-03-15": "疫情扩散冲击经济和金融市场；紧急降至接近零并维护信贷流动",
    "2022-03-16": "通胀显著高于2%，劳动力市场强劲；结束疫情时期宽松并启动加息",
    "2022-05-04": "通胀高企且广泛，劳动力市场紧张；加快收紧并启动缩表",
    "2022-06-15": "通胀持续高于目标，能源和供应链压力仍在；加快加息压低通胀",
    "2022-07-27": "通胀仍高但经济活动放缓；就业强劲，继续收紧以恢复价格稳定",
    "2022-09-21": "通胀居高不下、预期风险上升，劳动力市场紧；大幅加息",
    "2022-11-02": "通胀持续高企，供需失衡和劳动力市场紧张；继续大幅收紧",
    "2022-12-14": "通胀仍明显高于2%，就业强劲；继续加息形成足够限制性立场",
    "2023-02-01": "通胀有所缓解但仍高，劳动力市场强劲；继续适度收紧",
    "2023-03-22": "通胀仍高，同时银行体系压力可能收紧信贷；在金融稳定与通胀控制间权衡",
    "2023-05-03": "通胀仍高于目标，银行信贷收紧风险增加；继续加息并接近终点",
    "2023-07-26": "通胀仍高，经济活动和就业保持韧性；进一步提高限制性程度",
    "2024-09-18": "通胀向2%持续回落、就业市场降温；防止就业风险继续上升",
    "2024-11-07": "通胀继续向2%靠近，就业市场从过热转向平衡；继续校准政策",
    "2024-12-18": "通胀仍略高于2%，就业市场放缓；继续降息以平衡双重使命风险",
    "2025-09-17": "就业增长放缓、失业率上行，通胀仍略高；就业下行风险上升",
    "2025-10-29": "就业增长放缓、失业率上升风险加大；继续降息支持最大就业",
    "2025-12-10": "就业增长低迷、失业率上行风险上升，通胀仍偏高；继续平衡双重使命",
}

BULL_MARKET_STAGES = [
    ("2005-06-06", "2007-11-06", "2006-07 牛市", "金融地产 / 资源周期", "orange", 1),
    ("2008-11-05", "2009-08-04", "2008-09 反弹", "四万亿: 基建地产 / 有色煤炭", "blue", 2),
    ("2014-07-01", "2015-06-15", "2014-15 牛市", "券商 / 互联网+ / TMT", "orange", 0),
    ("2019-01-04", "2021-12-31", "2019-21 结构牛", "消费医药 / 新能源 / 半导体", "green", 0),
    ("2024-09-24", "2024-12-31", "2024 924行情", "宏观政策推动", "orange", 1),
    ("2025-04-01", "2026-07-10", "2025-26 科技修复", "AI算力 / 半导体", "blue", 0),
]

PHASE_MARKER_WINDOWS = [
    ("2009-01-01", "2009-04-30", "min", "blue", 14, 34),
    ("2015-04-01", "2015-07-31", "max", "orange", 14, -24),
    ("2018-10-01", "2019-02-28", "min", "blue", -14, 34),
    ("2024-09-01", "2025-02-28", "min", "blue", 14, 34),
]

DOWNTURN_ANNOTATIONS = [
    ("2020-03-23", "2020.3 下跌原因", "新冠疫情扩散 / 全球流动性冲击", "blue", -18, -58),
    ("2022-04-26", "2022.4 下跌原因", "国内疫情扰动 / Fed加息 / 俄乌冲突", "blue", 18, -58),
    ("2025-04-07", "2025.4 中美贸易战", "美对等关税落地 / 出口链与风险偏好受冲击", "blue", -18, 55),
    ("2026-06-26", "2026.6 TRS一刀切", "监管叫停跨境TRS新增 / 跨境配置通道收紧", "blue", -60, -93),
]


def parse_date(value):
    year, month, day = [int(part) for part in value.split("-")]
    return date(year, month, day)


def yyyymm(dt):
    return f"{dt.year}{dt.month:02d}"


def fmt_num(value, digits=2):
    if value is None:
        return ""
    return f"{value:,.{digits}f}"


def fmt_pct(value, digits=1):
    if value is None:
        return ""
    return f"{value * 100:.{digits}f}%"


def fmt_pct_value(value, digits=1):
    if value is None:
        return ""
    return f"{value:.{digits}f}%"


def fmt_rate_value(value, digits=2):
    if value is None:
        return ""
    quantum = Decimal("1").scaleb(-digits)
    rounded = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    return f"{rounded:.{digits}f}%"


def scale(domain_min, domain_max, range_min, range_max):
    if math.isclose(domain_max, domain_min):
        return lambda _: (range_min + range_max) / 2
    return lambda value: range_min + (value - domain_min) / (domain_max - domain_min) * (range_max - range_min)


def nice_ticks(max_value, target=7):
    if max_value <= 0:
        return [0]
    raw_step = max_value / target
    mag = 10 ** math.floor(math.log10(raw_step))
    for mult in (1, 2, 2.5, 5, 10):
        step = mult * mag
        if raw_step <= step:
            break
    top = math.ceil(max_value / step) * step
    count = int(round(top / step))
    return [i * step for i in range(count + 1)]


def line_path(points):
    if not points:
        return ""
    first, *rest = points
    chunks = [f"M {first[0]:.2f} {first[1]:.2f}"]
    chunks.extend(f"L {x:.2f} {y:.2f}" for x, y in rest)
    return " ".join(chunks)


def step_path(points):
    if not points:
        return ""
    first, *rest = points
    chunks = [f"M {first[0]:.2f} {first[1]:.2f}"]
    last_y = first[1]
    for x_pos, y_pos in rest:
        chunks.append(f"L {x_pos:.2f} {last_y:.2f}")
        chunks.append(f"L {x_pos:.2f} {y_pos:.2f}")
        last_y = y_pos
    return " ".join(chunks)


def svg_text(xp, yp, content, size=14, color="ink", weight="400", anchor="start", extra=""):
    return (
        f'<text x="{xp:.1f}" y="{yp:.1f}" font-size="{size}" '
        f'font-weight="{weight}" fill="{COLORS[color]}" text-anchor="{anchor}" {extra}>'
        f"{html_module.escape(str(content))}</text>"
    )


def svg_card(x, y, width, height, title, value, subtitle, value_color="ink"):
    elems = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="8" fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>',
        svg_text(x + 18, y + 28, title, 13, "muted"),
        svg_text(x + 18, y + 62, value, 24, value_color, "700", extra='class="mono"'),
    ]
    # 副标题为空时整行不输出（如「上年GDP」卡片只留标题与数值）。
    if subtitle:
        elems.append(svg_text(x + 18, y + 89, subtitle, 13, "muted"))
    return "\n".join(elems)


def svg_extrema_marker(row, x_pos, y_pos, color, x0, x1, y0, y1, dx, dy):
    anchor = "start" if dx >= 0 else "end"
    text_x = x_pos + dx
    text_y = max(y0 + 14, min(y1 - 8, y_pos + dy))
    if text_x < x0 + 10:
        anchor = "start"
        text_x = x_pos + abs(dx)
    elif text_x > x1 - 10:
        anchor = "end"
        text_x = x_pos - abs(dx)
    leader_x = text_x - 4 if anchor == "start" else text_x + 4
    leader_y = text_y - 4
    text_style = 'class="mono" style="paint-order:stroke;stroke:#FFFFFF;stroke-width:4px;stroke-linejoin:round"'
    return "\n".join(
        [
            f'<line x1="{x_pos:.1f}" y1="{y_pos:.1f}" x2="{leader_x:.1f}" y2="{leader_y:.1f}" stroke="{COLORS[color]}" stroke-width="1.2" stroke-opacity="0.65"/>',
            f'<circle cx="{x_pos:.1f}" cy="{y_pos:.1f}" r="4.8" fill="{COLORS["panel"]}" stroke="{COLORS[color]}" stroke-width="2"/>',
            svg_text(
                text_x,
                text_y,
                fmt_pct_value(row["market_cap_to_gdp_pct"], 2),
                12,
                color,
                "700",
                anchor,
                text_style,
            ),
        ]
    )


def build_phase_markers(rows):
    markers = []
    seen_indices = set()
    for start, end, kind, color, dx, dy in PHASE_MARKER_WINDOWS:
        window_rows = [row for row in rows if start <= row["trading_date"] <= end]
        if not window_rows:
            continue
        selector = max if kind == "max" else min
        row = selector(window_rows, key=lambda item: item["market_cap_to_gdp_pct"])
        if row["trading_day_index"] in seen_indices:
            continue
        seen_indices.add(row["trading_day_index"])
        markers.append({"row": row, "color": color, "dx": dx, "dy": dy})
    return markers


def first_index_on_or_after(rows, date_value):
    for row in rows:
        if row["trading_date"] >= date_value:
            return row["trading_day_index"]
    return rows[-1]["trading_day_index"]


def last_index_on_or_before(rows, date_value):
    for row in reversed(rows):
        if row["trading_date"] <= date_value:
            return row["trading_day_index"]
    return rows[0]["trading_day_index"]


def build_bull_market_stages(rows):
    stages = []
    for start, end, title, drivers, color, level in BULL_MARKET_STAGES:
        start_index = first_index_on_or_after(rows, start)
        end_index = last_index_on_or_before(rows, end)
        if start_index > end_index:
            continue
        stages.append(
            {
                "start_index": start_index,
                "end_index": end_index,
                "title": title,
                "drivers": drivers,
                "color": color,
                "level": level,
            }
        )
    return stages


def row_on_or_after(rows, date_value):
    for row in rows:
        if row["trading_date"] >= date_value:
            return row
    return rows[-1]


def build_downturn_annotations(rows):
    annotations = []
    for date_value, title, reason, color, dx, dy in DOWNTURN_ANNOTATIONS:
        row = row_on_or_after(rows, date_value)
        annotations.append({"row": row, "title": title, "reason": reason, "color": color, "dx": dx, "dy": dy})
    return annotations


def fed_lower_rate(upper_rate, event_date):
    if event_date < parse_date("2008-12-16"):
        return upper_rate
    return max(0.0, upper_rate - 0.25)


def fed_target_text(lower_rate, upper_rate):
    if math.isclose(lower_rate, upper_rate):
        return f"{upper_rate:.2f}%"
    return f"{lower_rate:.2f}-{upper_rate:.2f}%"


def build_fed_events(rows):
    events = []
    previous_upper = None
    first_date = rows[0]["date_obj"]
    for date_value, upper_rate in FED_RATE_STEPS:
        event_date = parse_date(date_value)
        if previous_upper is None:
            previous_upper = upper_rate
            continue
        change_bp = round((upper_rate - previous_upper) * 100)
        if event_date >= first_date and change_bp:
            lower_rate = fed_lower_rate(upper_rate, event_date)
            row = row_on_or_after(rows, date_value)
            events.append(
                {
                    "date": date_value,
                    "row": row,
                    "action": "加息" if change_bp > 0 else "降息",
                    "change_bp": change_bp,
                    "upper_rate": upper_rate,
                    "lower_rate": lower_rate,
                    "mid_rate": (upper_rate + lower_rate) / 2,
                    "target": fed_target_text(lower_rate, upper_rate),
                    "reason": FED_RATE_REASONS[date_value],
                }
            )
        previous_upper = upper_rate
    return events


def svg_fed_event_markers(events, x_scale, y_scale):
    elems = ['<g id="fedEventLayer" pointer-events="none">']
    for event in events:
        x_pos = x_scale(event["row"]["trading_day_index"])
        y_pos = y_scale(event["mid_rate"])
        label = f'{event["date"]} {event["action"]} {event["change_bp"]:+d}bp；目标区间 {event["target"]}；原因：{event["reason"]}'
        elems.append(
            f'<circle cx="{x_pos:.1f}" cy="{y_pos:.1f}" r="3.5" fill="{COLORS["panel"]}" stroke="{COLORS["fed"]}" stroke-width="1.5" data-event-index="{event["row"]["trading_day_index"]}"><title>{html_module.escape(label)}</title></circle>'
        )
    elems.append("</g>")
    return "\n".join(elems)


def svg_bull_stage_bands(stages, x_scale, x0, x1, y0, y1):
    elems = ['<g id="stageBandLayer" pointer-events="none">']
    for stage in stages:
        left = max(x0, x_scale(stage["start_index"]))
        right = min(x1, x_scale(stage["end_index"]))
        width = max(1, right - left)
        color = COLORS[stage["color"]]
        elems.append(f'<rect x="{left:.1f}" y="{y0:.1f}" width="{width:.1f}" height="{y1-y0:.1f}" fill="{color}" opacity="0.055"/>')
        elems.append(f'<line x1="{left:.1f}" y1="{y0:.1f}" x2="{left:.1f}" y2="{y1:.1f}" stroke="{color}" stroke-width="1" stroke-dasharray="4 5" opacity="0.32"/>')
        elems.append(f'<line x1="{right:.1f}" y1="{y0:.1f}" x2="{right:.1f}" y2="{y1:.1f}" stroke="{color}" stroke-width="1" stroke-dasharray="4 5" opacity="0.22"/>')
    elems.append("</g>")
    return "\n".join(elems)


def svg_downturn_annotation(annotation, x_scale, y_scale, x0, x1, y0, y1):
    row = annotation["row"]
    x_pos = x_scale(row["trading_day_index"])
    y_pos = y_scale(row["market_cap_to_gdp_pct"])
    dx = annotation["dx"]
    dy = annotation["dy"]
    anchor = "start" if dx >= 0 else "end"
    text_x = x_pos + dx
    text_y = max(y0 + 44, min(y1 - 26, y_pos + dy))
    if text_x < x0 + 10:
        anchor = "start"
        text_x = x_pos + abs(dx)
    elif text_x > x1 - 10:
        anchor = "end"
        text_x = x_pos - abs(dx)
    leader_x = text_x - 5 if anchor == "start" else text_x + 5
    leader_y = text_y + 3
    color = COLORS[annotation["color"]]
    text_style = 'style="paint-order:stroke;stroke:#FFFFFF;stroke-width:4px;stroke-linejoin:round"'
    return "\n".join(
        [
            f'<line x1="{x_pos:.1f}" y1="{y_pos:.1f}" x2="{leader_x:.1f}" y2="{leader_y:.1f}" stroke="{color}" stroke-width="1.2" stroke-opacity="0.65"/>',
            f'<circle cx="{x_pos:.1f}" cy="{y_pos:.1f}" r="4.6" fill="{COLORS["panel"]}" stroke="{color}" stroke-width="2"/>',
            f'<text x="{text_x:.1f}" y="{text_y:.1f}" font-size="11" font-weight="700" fill="{color}" text-anchor="{anchor}" {text_style}>{html_module.escape(annotation["title"])}</text>',
            f'<text x="{text_x:.1f}" y="{text_y + 15:.1f}" font-size="10.5" font-weight="600" fill="{color}" text-anchor="{anchor}" {text_style}>{html_module.escape(annotation["reason"])}</text>',
        ]
    )


def svg_downturn_annotations(annotations, x_scale, y_scale, x0, x1, y0, y1):
    elems = ['<g id="downturnLayer" pointer-events="none">']
    for annotation in annotations:
        elems.append(svg_downturn_annotation(annotation, x_scale, y_scale, x0, x1, y0, y1))
    elems.append("</g>")
    return "\n".join(elems)


def svg_bull_stage_labels(stages, x_scale, x0, x1, y0):
    elems = ['<g id="stageLabelLayer" pointer-events="none">']
    text_style = 'style="paint-order:stroke;stroke:#FFFFFF;stroke-width:4px;stroke-linejoin:round"'
    for stage in stages:
        left = max(x0, x_scale(stage["start_index"]))
        right = min(x1, x_scale(stage["end_index"]))
        center = max(x0 + 46, min(x1 - 46, (left + right) / 2))
        y = y0 + 18 + stage["level"] * 34
        color = COLORS[stage["color"]]
        elems.append(
            f'<text x="{center:.1f}" y="{y:.1f}" font-size="11" font-weight="700" fill="{color}" text-anchor="middle" {text_style}>{html_module.escape(stage["title"])}</text>'
        )
        elems.append(
            f'<text x="{center:.1f}" y="{y+15:.1f}" font-size="10.5" font-weight="600" fill="{color}" text-anchor="middle" {text_style}>{html_module.escape(stage["drivers"])}</text>'
        )
    elems.append("</g>")
    return "\n".join(elems)


def attach_fed_rates(rows):
    steps = [(parse_date(date_value), rate) for date_value, rate in FED_RATE_STEPS]
    steps.sort(key=lambda item: item[0])
    step_index = 0
    for row in rows:
        while step_index + 1 < len(steps) and row["date_obj"] >= steps[step_index + 1][0]:
            step_index += 1
        upper_rate = steps[step_index][1]
        lower_rate = fed_lower_rate(upper_rate, row["date_obj"])
        row["fed_funds_target_upper_pct"] = upper_rate
        row["fed_funds_target_lower_pct"] = lower_rate
        row["fed_funds_target_mid_pct"] = (upper_rate + lower_rate) / 2


def fed_step_points(rows, field_name, x_scale, y_scale):
    points = []
    last_rate = None
    for row in rows:
        rate = row[field_name]
        if last_rate is None or not math.isclose(rate, last_rate):
            points.append((x_scale(row["trading_day_index"]), y_scale(rate)))
            last_rate = rate
    points.append((x_scale(rows[-1]["trading_day_index"]), y_scale(rows[-1][field_name])))
    return points


def load_trading_day_rows():
    payload = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    rows = []

    for source_row in payload["data"]:
        dt = parse_date(source_row["date"])
        market_cap = float(source_row["marketCap"])
        source_gdp = float(source_row["gdp"])
        gdp = source_gdp
        gdp_benchmark = gdp * GDP_BENCHMARK_FACTOR
        ratio = market_cap / gdp_benchmark if gdp_benchmark else None
        close = float(source_row["close"])

        rows.append(
            {
                "trading_date": source_row["date"],
                "date_obj": dt,
                "x_month": yyyymm(dt),
                "market_cap_100m_cny": market_cap,
                "market_cap_trn_cny": market_cap / 10000,
                "gdp_100m_cny": gdp,
                "gdp_trn_cny": gdp / 10000,
                "gdp_benchmark_100m_cny": gdp_benchmark,
                "gdp_benchmark_trn_cny": gdp_benchmark / 10000,
                "market_cap_to_gdp": ratio,
                "market_cap_to_gdp_pct": ratio * 100 if ratio is not None else None,
                "close": close,
                "market_cap_source": source_row.get("market_cap_source", "legulegu"),
            }
        )

    rows.sort(key=lambda row: row["date_obj"])
    for index, row in enumerate(rows):
        row["trading_day_index"] = index
    attach_fed_rates(rows)
    return rows


def write_csv(rows):
    fieldnames = [
        "trading_date",
        "x_month",
        "trading_day_index",
        "market_cap_100m_cny",
        "market_cap_trn_cny",
        "gdp_100m_cny",
        "gdp_trn_cny",
        "gdp_benchmark_100m_cny",
        "gdp_benchmark_trn_cny",
        "market_cap_to_gdp",
        "market_cap_to_gdp_pct",
        "fed_funds_target_mid_pct",
        "close",
        "market_cap_source",
    ]

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            cleaned = {key: row.get(key) for key in fieldnames}
            cleaned["trading_day_index"] = row["trading_day_index"] + 1
            for key, value in list(cleaned.items()):
                if isinstance(value, float):
                    cleaned[key] = f"{value:.10g}"
                elif value is None:
                    cleaned[key] = ""
            writer.writerow(cleaned)


def build_axis_ticks(rows):
    first = rows[0]
    latest = rows[-1]
    ticks = []
    seen_months = set()

    def add(row):
        month = row["x_month"]
        if month not in seen_months:
            ticks.append(row)
            seen_months.add(month)

    add(first)

    seen_years = set()
    for row in rows:
        dt = row["date_obj"]
        if dt.year in seen_years or dt.month != 1:
            continue
        seen_years.add(dt.year)
        add(row)

    add(latest)
    return sorted(ticks, key=lambda row: row["trading_day_index"])


def add_y_grid(elems, x0, x1, y0, y1, ticks, y_scale, label_func):
    for tick in ticks:
        yy = y_scale(tick)
        if y0 <= yy <= y1:
            dash = "" if math.isclose(tick, 0) else ' stroke-dasharray="3 5"'
            elems.append(f'<line x1="{x0}" y1="{yy:.1f}" x2="{x1}" y2="{yy:.1f}" stroke="{COLORS["grid"]}"{dash}/>')
            elems.append(svg_text(x0 - 14, yy + 4, label_func(tick), 12, "muted", anchor="end", extra='class="mono"'))


def add_x_axis(elems, rows, x_scale, x0, x1, y_axis, label_y, y_grid_top=None, y_grid_bottom=None):
    ticks = build_axis_ticks(rows)
    forced_levels = {}
    tick_boxes = []
    for row in ticks:
        xp = x_scale(row["trading_day_index"])
        anchor = "middle"
        if xp < x0 + 30:
            anchor = "start"
        elif xp > x1 - 30:
            anchor = "end"
        label = row["x_month"]
        label_width = len(label) * 7.2
        if anchor == "end":
            left, right = xp - label_width, xp
        elif anchor == "middle":
            left, right = xp - label_width / 2, xp + label_width / 2
        else:
            left, right = xp, xp + label_width
        tick_boxes.append((left, right))
    if len(tick_boxes) > 1:
        if min(tick_boxes[0][1], tick_boxes[1][1]) - max(tick_boxes[0][0], tick_boxes[1][0]) > -2:
            forced_levels[0] = 1
            forced_levels[1] = 0
        if min(tick_boxes[-2][1], tick_boxes[-1][1]) - max(tick_boxes[-2][0], tick_boxes[-1][0]) > -2:
            forced_levels[len(ticks) - 2] = 0
            forced_levels[len(ticks) - 1] = 1

    label_boxes = []
    for tick_index, row in enumerate(ticks):
        xp = x_scale(row["trading_day_index"])
        if y_grid_top is not None and y_grid_bottom is not None:
            elems.append(
                f'<line x1="{xp:.1f}" y1="{y_grid_top}" x2="{xp:.1f}" y2="{y_grid_bottom}" '
                f'stroke="{COLORS["grid"]}" stroke-dasharray="2 7"/>'
            )
        elems.append(f'<line x1="{xp:.1f}" y1="{y_axis}" x2="{xp:.1f}" y2="{y_axis+7}" stroke="{COLORS["axis"]}"/>')
        anchor = "middle"
        if xp < x0 + 30:
            anchor = "start"
        elif xp > x1 - 30:
            anchor = "end"
        label = row["x_month"]
        label_width = len(label) * 7.2
        if anchor == "end":
            left, right = xp - label_width, xp
        elif anchor == "middle":
            left, right = xp - label_width / 2, xp + label_width / 2
        else:
            left, right = xp, xp + label_width
        preferred_levels = [forced_levels[tick_index]] if tick_index in forced_levels else [0, 1]
        label_yp = label_y + preferred_levels[-1] * 16
        for level in preferred_levels:
            candidate_y = label_y + level * 16
            has_overlap = False
            for existing_left, existing_right, existing_y in label_boxes:
                overlaps_x = min(right, existing_right) - max(left, existing_left) > -2
                overlaps_y = abs(candidate_y - existing_y) < 13
                if overlaps_x and overlaps_y:
                    has_overlap = True
                    break
            if not has_overlap:
                label_yp = candidate_y
                break
        label_boxes.append((left, right, label_yp))
        elems.append(svg_text(xp, label_yp, label, 12, "muted", anchor=anchor, extra='class="mono"'))


def make_svg(rows):
    if not rows:
        raise ValueError("No trading-day rows are available.")

    width, height = CHART_WIDTH, CHART_HEIGHT
    ml, mr = CHART_ML, CHART_MR
    x0, x1 = ml, width - mr
    ratio_y0, ratio_y1 = PLOT_Y0, PLOT_Y1

    first = rows[0]
    latest = rows[-1]
    previous = rows[-2] if len(rows) >= 2 else None
    domain_start = 0
    domain_end = len(rows) - 1
    x = scale(domain_start, domain_end, x0, x1)

    max_pct = max(row["market_cap_to_gdp_pct"] for row in rows if row["market_cap_to_gdp_pct"] is not None)
    ratio_ticks = nice_ticks(max_pct * 1.03, target=7)
    ratio_max = max(ratio_ticks[-1], 100)
    y_scale_ratio = scale(0, ratio_max, ratio_y1, ratio_y0)
    fed_axis_max = max(FED_RATE_AXIS_MAX, math.ceil(max(row["fed_funds_target_mid_pct"] for row in rows) * 2) / 2)
    y_scale_fed = scale(0, fed_axis_max, ratio_y1, ratio_y0)

    ratio_points = [(x(row["trading_day_index"]), y_scale_ratio(row["market_cap_to_gdp_pct"])) for row in rows]
    fed_mid_step_points = fed_step_points(rows, "fed_funds_target_mid_pct", x, y_scale_fed)
    fed_events = build_fed_events(rows)

    latest_x = x(latest["trading_day_index"])
    latest_ratio_y = y_scale_ratio(latest["market_cap_to_gdp_pct"])
    latest_fed_y = y_scale_fed(latest["fed_funds_target_mid_pct"])
    fed_tick_label_ys = [y_scale_fed(tick) + 4 for tick in (0, 2, 4, 6) if tick <= fed_axis_max]

    def fed_label_y(y_pos, occupied):
        label_y = y_pos + 4
        if any(abs(label_y - tick_y) < 14 for tick_y in occupied):
            label_y = y_pos + 18
        return max(ratio_y0 + 12, min(ratio_y1 - 8, label_y))

    latest_fed_label_y = fed_label_y(latest_fed_y, fed_tick_label_ys)

    day_change = None
    if previous:
        day_change = latest["market_cap_to_gdp"] / previous["market_cap_to_gdp"] - 1

    elems = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        "<style>",
        "text{font-family:'Microsoft YaHei','Segoe UI',Arial,sans-serif;} .mono{font-family:Consolas,'SF Mono',monospace;}",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="{COLORS["surface"]}"/>',
        svg_text(ml, 58, "A股总市值880001/（上年GDP×80%）（日度交易日）", 31, "ink", "700"),
    ]

    card_y = 86
    card_h = 96
    gap = 18
    benchmark_trn = latest["gdp_benchmark_trn_cny"]
    cards = [
        (
            "交易日范围",
            f"{first['x_month']}-{latest['x_month']}",
            f"{first['trading_date']} 至 {latest['trading_date']}，共 {len(rows)} 个交易日",
            "ink",
        ),
        (
            "最新A股总市值",
            f"{fmt_num(latest['market_cap_trn_cny'], 2)}万亿元",
            latest["trading_date"],
            "blue",
        ),
        (
            "总市值参考下限",
            f"{fmt_num(benchmark_trn * 0.95, 2)}万亿元",
            "上年GDP×80%×(1-5%)",
            "blue_dark",
        ),
        (
            "总市值参考上限",
            f"{fmt_num(benchmark_trn * 1.05, 2)}万亿元",
            "上年GDP×80%×(1+5%)",
            "blue_dark",
        ),
        (
            "市值/（上年GDP×80%）",
            fmt_pct(latest["market_cap_to_gdp"], 2),
            f"较前一交易日 {fmt_pct(day_change, 2) if day_change is not None else 'n/a'}",
            "gold",
        ),
    ]
    # 单排 5 张：首张「交易日范围」副标题较长，单独放宽，其余均分剩余宽度。
    range_card_w = 320
    other_card_w = (x1 - x0 - gap * (len(cards) - 1) - range_card_w) / (len(cards) - 1)
    card_x = x0
    for index, card in enumerate(cards):
        card_w = range_card_w if index == 0 else other_card_w
        elems.append(svg_card(card_x, card_y, card_w, card_h, *card))
        card_x += card_w + gap

    # Single panel: market-cap-to-GDP ratio.
    ratio_legend_y = ratio_y0 - 32
    elems.append(f'<line x1="{x1-640}" y1="{ratio_legend_y-5}" x2="{x1-600}" y2="{ratio_legend_y-5}" stroke="{COLORS["gold"]}" stroke-width="3"/>')
    elems.append(svg_text(x1 - 590, ratio_legend_y, "市值/（上年GDP×80%）", 13, "ink"))
    elems.append(f'<line x1="{x1-400}" y1="{ratio_legend_y-5}" x2="{x1-360}" y2="{ratio_legend_y-5}" stroke="{COLORS["green"]}" stroke-width="2" stroke-dasharray="6 6"/>')
    elems.append(svg_text(x1 - 350, ratio_legend_y, "100%参考线", 13, "ink"))
    elems.append(f'<line x1="{x1-180}" y1="{ratio_legend_y-5}" x2="{x1-140}" y2="{ratio_legend_y-5}" stroke="{COLORS["fed"]}" stroke-width="2"/>')
    elems.append(svg_text(x1 - 130, ratio_legend_y, "Fed均值", 13, "ink"))
    elems.append(f'<rect x="{x0}" y="{ratio_y0}" width="{x1-x0}" height="{ratio_y1-ratio_y0}" fill="{COLORS["panel"]}" stroke="{COLORS["grid"]}"/>')
    add_y_grid(elems, x0, x1, ratio_y0, ratio_y1, ratio_ticks, y_scale_ratio, lambda tick: f"{tick:g}%")
    for tick in (0, 2, 4, 6):
        if tick <= fed_axis_max:
            tick_y = y_scale_fed(tick)
            elems.append(f'<line x1="{x1}" y1="{tick_y:.1f}" x2="{x1+6}" y2="{tick_y:.1f}" stroke="{COLORS["fed"]}" stroke-width="1" opacity="0.5"/>')
            elems.append(svg_text(x1 + 10, tick_y + 4, f"{tick:g}%", 11, "fed", anchor="start", extra='class="mono"'))
    hundred_y = y_scale_ratio(100)
    latest_ratio_label_y = latest_ratio_y - 11
    if abs(latest_ratio_label_y - (hundred_y - 8)) < 24:
        latest_ratio_label_y = latest_ratio_y + 22
    elems.append(f'<line x1="{x0}" y1="{hundred_y:.1f}" x2="{x1}" y2="{hundred_y:.1f}" stroke="{COLORS["green"]}" stroke-width="1.4" stroke-dasharray="6 6"/>')
    bull_stages = build_bull_market_stages(rows)
    downturn_annotations = build_downturn_annotations(rows)
    elems.append(svg_bull_stage_bands(bull_stages, x, x0, x1, ratio_y0, ratio_y1))
    x_axis_elems = []
    add_x_axis(x_axis_elems, rows, x, x0, x1, ratio_y1, ratio_y1 + 32, ratio_y0, ratio_y1)
    elems.append('<g id="xAxisLayer">')
    elems.extend(x_axis_elems)
    elems.append("</g>")
    elems.append(f'<path id="fedRatePath" d="{step_path(fed_mid_step_points)}" fill="none" stroke="{COLORS["fed"]}" stroke-width="2" opacity="0.86"/>')
    elems.append(svg_fed_event_markers(fed_events, x, y_scale_fed))
    elems.append(f'<path id="ratioPath" d="{line_path(ratio_points)}" fill="none" stroke="{COLORS["gold"]}" stroke-width="2.6"/>')
    elems.append(svg_bull_stage_labels(bull_stages, x, x0, x1, ratio_y0))
    elems.append(svg_downturn_annotations(downturn_annotations, x, y_scale_ratio, x0, x1, ratio_y0, ratio_y1))
    high_row = max(rows, key=lambda row: row["market_cap_to_gdp_pct"])
    low_row = min(rows, key=lambda row: row["market_cap_to_gdp_pct"])
    phase_markers = build_phase_markers(rows)
    elems.append('<g id="extremaLayer" pointer-events="none">')
    elems.append(
        svg_extrema_marker(
            high_row,
            x(high_row["trading_day_index"]),
            y_scale_ratio(high_row["market_cap_to_gdp_pct"]),
            "orange",
            x0,
            x1,
            ratio_y0,
            ratio_y1,
            14,
            -18,
        )
    )
    if high_row is not low_row:
        elems.append(
            svg_extrema_marker(
                low_row,
                x(low_row["trading_day_index"]),
                y_scale_ratio(low_row["market_cap_to_gdp_pct"]),
                "blue",
                x0,
                x1,
                ratio_y0,
                ratio_y1,
                14,
                30,
            )
        )
    for marker in phase_markers:
        row = marker["row"]
        elems.append(
            svg_extrema_marker(
                row,
                x(row["trading_day_index"]),
                y_scale_ratio(row["market_cap_to_gdp_pct"]),
                marker["color"],
                x0,
                x1,
                ratio_y0,
                ratio_y1,
                marker["dx"],
                marker["dy"],
            )
        )
    elems.append("</g>")
    elems.append(f'<circle id="latestPoint" cx="{latest_x:.1f}" cy="{latest_ratio_y:.1f}" r="5.2" fill="{COLORS["panel"]}" stroke="{COLORS["gold"]}" stroke-width="2"/>')
    # 白描边与其余标注一致，避免最新值压在本就密集的比值曲线上看不清。
    elems.append(svg_text(x1 - 8, latest_ratio_label_y, fmt_pct(latest["market_cap_to_gdp"], 2), 14, "gold", "700", "end", 'id="latestLabel" class="mono" style="paint-order:stroke;stroke:#FFFFFF;stroke-width:4px;stroke-linejoin:round"'))
    elems.append(f'<circle id="latestFedPoint" cx="{latest_x:.1f}" cy="{latest_fed_y:.1f}" r="3.8" fill="{COLORS["panel"]}" stroke="{COLORS["fed"]}" stroke-width="1.8"/>')
    elems.append(svg_text(x1 + 10, latest_fed_label_y, fmt_rate_value(latest["fed_funds_target_mid_pct"], 2), 11, "fed", "700", "start", 'id="latestFedLabel" class="mono"'))

    source_lines = [
        "数据来源：A股总市值 2011-10-19 起取通达信880001指数（1点=100亿元），此前为乐咕乐股原序列；GDP取年度国内生产总值。",
        "GDP 一律取上年数（如2026年用2025年GDP 140.19万亿元），不做当年增速外推；比值分母为上年GDP×80%，100%即市值达到上年GDP的80%。",
        "Fed利率为FOMC目标区间上下限平均值；利率变动原因按相应FOMC会后声明简要归纳。",
    ]
    for offset, line in enumerate(source_lines):
        elems.append(svg_text(ml, height - 70 + offset * 19, line, 13, "muted"))
    elems.append("</svg>")
    return "\n".join(elems)


def write_html(svg, rows):
    latest = rows[-1]
    ratio_scale_max = max(nice_ticks(max(row["market_cap_to_gdp_pct"] for row in rows) * 1.03, target=7)[-1], 100)
    fed_scale_max = max(FED_RATE_AXIS_MAX, math.ceil(max(row["fed_funds_target_mid_pct"] for row in rows) * 2) / 2)
    tooltip_rows = json.dumps(
        [
            {
                "date": row["trading_date"],
                "month": row["x_month"],
                "close": row["close"],
                "ratioPct": row["market_cap_to_gdp_pct"],
                "fedRate": row["fed_funds_target_mid_pct"],
            }
            for row in rows
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    phase_marker_rows = json.dumps(
        [
            {
                "index": marker["row"]["trading_day_index"],
                "color": COLORS[marker["color"]],
                "dx": marker["dx"],
                "dy": marker["dy"],
            }
            for marker in build_phase_markers(rows)
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    bull_stage_rows = json.dumps(
        [
            {
                "startIndex": stage["start_index"],
                "endIndex": stage["end_index"],
                "title": stage["title"],
                "drivers": stage["drivers"],
                "color": COLORS[stage["color"]],
                "level": stage["level"],
            }
            for stage in build_bull_market_stages(rows)
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    downturn_annotation_rows = json.dumps(
        [
            {
                "index": annotation["row"]["trading_day_index"],
                "title": annotation["title"],
                "reason": annotation["reason"],
                "color": COLORS[annotation["color"]],
                "dx": annotation["dx"],
                "dy": annotation["dy"],
            }
            for annotation in build_downturn_annotations(rows)
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    fed_event_rows = json.dumps(
        [
            {
                "index": event["row"]["trading_day_index"],
                "date": event["date"],
                "action": event["action"],
                "changeBp": event["change_bp"],
                "target": event["target"],
                "midRate": event["mid_rate"],
                "reason": event["reason"],
                "color": COLORS["fed"],
            }
            for event in build_fed_events(rows)
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    table_rows = "\n".join(
        "<tr>"
        f"<td>{row['trading_date']}</td>"
        f"<td>{row['x_month']}</td>"
        f"<td>{row['trading_day_index'] + 1}</td>"
        f"<td>{fmt_pct(row['market_cap_to_gdp'], 2)}</td>"
        f"<td>{fmt_num(row['market_cap_trn_cny'], 2)}</td>"
        f"<td>{fmt_num(row['gdp_trn_cny'], 2)}</td>"
        f"<td>{fmt_rate_value(row['fed_funds_target_mid_pct'], 2)}</td>"
        "</tr>"
        for row in rows
    )
    html_doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A股总市值880001/（上年GDP×80%）（日度交易日）</title>
  <style>
    body {{ margin: 0; background: #FAFAFB; color: #1F2430; font-family: 'Microsoft YaHei','Segoe UI',Arial,sans-serif; }}
    main {{ max-width: 1440px; margin: 0 auto; padding: 12px; box-sizing: border-box; }}
    .zoom-tools {{ display: flex; align-items: center; gap: 10px; margin: 0 0 10px; color: #6F768A; font-size: 13px; flex-wrap: wrap; }}
    .zoom-tools button {{ border: 1px solid #CDD3E1; background: #FFFFFF; color: #1F2430; border-radius: 7px; padding: 6px 10px; cursor: pointer; font: inherit; }}
    .zoom-tools button:hover {{ border-color: #A98B14; color: #A98B14; }}
    .zoom-status {{ font-family: Consolas,'SF Mono',monospace; color: #1F2430; }}
    .chart {{ position: relative; overflow: hidden; background: white; border: 1px solid #E4E7EF; border-radius: 8px; cursor: crosshair; touch-action: none; }}
    .chart svg {{ display: block; width: 100%; height: auto; }}
    .hover-tooltip {{ position: fixed; display: none; pointer-events: none; z-index: 5; min-width: 148px; max-width: min(360px, calc(100vw - 24px)); padding: 8px 10px; border-radius: 7px; background: rgba(31,36,48,0.94); color: #fff; font-size: 13px; line-height: 1.45; box-shadow: 0 8px 24px rgba(31,36,48,0.18); overflow-wrap: anywhere; }}
    .hover-tooltip .date {{ font-family: Consolas,'SF Mono',monospace; font-weight: 700; }}
    .hover-tooltip .close {{ color: #F4D46B; font-family: Consolas,'SF Mono',monospace; font-weight: 700; }}
    .hover-tooltip .fed-rate {{ color: {COLORS["fed"]}; font-family: Consolas,'SF Mono',monospace; font-weight: 700; }}
    .hover-tooltip .fed-event {{ margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.24); }}
    .hover-tooltip .fed-action {{ color: #9BE4B7; font-weight: 700; }}
    .hover-tooltip .fed-reason {{ margin-top: 2px; color: #E7EBF2; font-size: 12px; line-height: 1.5; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; background: white; }}
    th, td {{ border: 1px solid #E4E7EF; padding: 8px 10px; text-align: right; white-space: nowrap; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) {{ text-align: left; }}
    th {{ background: #F0F2F6; position: sticky; top: 0; z-index: 1; }}
    .note {{ color: #6F768A; font-size: 13px; line-height: 1.6; }}
    .table-wrap {{ max-height: 540px; overflow: auto; border: 1px solid #E4E7EF; border-radius: 8px; }}
  </style>
</head>
<body>
<main>
  <div class="zoom-tools" aria-label="图表缩放控制">
    <button type="button" id="zoomIn">放大</button>
    <button type="button" id="zoomOut">缩小</button>
    <button type="button" id="zoomReset">重置</button>
    <span>滚轮缩放，拖动平移</span>
    <span>绿色节点为FOMC加/降息，悬停查看原因</span>
    <span id="zoomStatus" class="zoom-status"></span>
  </div>
  <div class="chart" id="chart">{svg}<div class="hover-tooltip" id="hoverTooltip"></div></div>
  <div class="table-wrap">
    <table>
      <thead><tr><th>交易日</th><th>横轴YYYYMM</th><th>交易日序号</th><th>市值/（上年GDP×80%）</th><th>A股总市值（万亿元）</th><th>上年GDP（万亿元）</th><th>Fed均值</th></tr></thead>
      <tbody>{table_rows}</tbody>
    </table>
  </div>
</main>
<script>
(() => {{
  const data = {tooltip_rows};
  const phaseMarkers = {phase_marker_rows};
  const bullStages = {bull_stage_rows};
  const downturnAnnotations = {downturn_annotation_rows};
  const fedEvents = {fed_event_rows};
  const fedEventByIndex = new Map(fedEvents.map((event) => [event.index, event]));
  const chart = document.getElementById('chart');
  const tooltip = document.getElementById('hoverTooltip');
  const svg = chart.querySelector('svg');
  const zoomStatus = document.getElementById('zoomStatus');
  const ratioPath = document.getElementById('ratioPath');
  const fedRatePath = document.getElementById('fedRatePath');
  const stageBandLayer = document.getElementById('stageBandLayer');
  const stageLabelLayer = document.getElementById('stageLabelLayer');
  const downturnLayer = document.getElementById('downturnLayer');
  const fedEventLayer = document.getElementById('fedEventLayer');
  const xAxisLayer = document.getElementById('xAxisLayer');
  const extremaLayer = document.getElementById('extremaLayer');
  const latestPoint = document.getElementById('latestPoint');
  const latestLabel = document.getElementById('latestLabel');
  const latestFedPoint = document.getElementById('latestFedPoint');
  const latestFedLabel = document.getElementById('latestFedLabel');
  const svgNS = 'http://www.w3.org/2000/svg';
  const viewBox = {{ width: {CHART_WIDTH}, height: {CHART_HEIGHT} }};
  const plot = {{ x0: {CHART_ML}, x1: {CHART_WIDTH - CHART_MR}, y0: {PLOT_Y0}, y1: {PLOT_Y1} }};
  const yScale = {{ min: 0, max: {ratio_scale_max:g} }};
  const fedScale = {{ min: 0, max: {fed_scale_max:g} }};
  const minWindow = 20;
  const panSpeed = 3;
  let viewStart = 0;
  let viewEnd = data.length - 1;
  let dragging = null;

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const yOf = (ratioPct) => {{
    const normalized = (ratioPct - yScale.min) / (yScale.max - yScale.min);
    return plot.y1 - normalized * (plot.y1 - plot.y0);
  }};
  const yFedOf = (ratePct) => {{
    const normalized = (ratePct - fedScale.min) / (fedScale.max - fedScale.min);
    return plot.y1 - normalized * (plot.y1 - plot.y0);
  }};
  const xOf = (index) => {{
    const span = Math.max(1, viewEnd - viewStart);
    return plot.x0 + (index - viewStart) / span * (plot.x1 - plot.x0);
  }};
  const indexBounds = () => {{
    const start = clamp(Math.ceil(viewStart), 0, data.length - 1);
    const end = clamp(Math.floor(viewEnd), 0, data.length - 1);
    return {{ start, end }};
  }};
  const createSvg = (name, attrs = {{}}) => {{
    const element = document.createElementNS(svgNS, name);
    Object.entries(attrs).forEach(([key, value]) => {{
      if (value !== null && value !== undefined) {{
        element.setAttribute(key, value);
      }}
    }});
    return element;
  }};
  const svgPointFromEvent = (event) => {{
    const svgRect = svg.getBoundingClientRect();
    return {{
      x: (event.clientX - svgRect.left) * viewBox.width / svgRect.width,
      y: (event.clientY - svgRect.top) * viewBox.height / svgRect.height,
      rect: svgRect,
    }};
  }};
  const inPlot = (point) => point.x >= plot.x0 && point.x <= plot.x1 && point.y >= plot.y0 && point.y <= plot.y1;
  const formatPct = (value) => `${{Number(value).toFixed(2)}}%`;

  const hoverLine = document.createElementNS(svgNS, 'line');
  hoverLine.setAttribute('y1', plot.y0);
  hoverLine.setAttribute('y2', plot.y1);
  hoverLine.setAttribute('stroke', '#1F2430');
  hoverLine.setAttribute('stroke-width', '1.2');
  hoverLine.setAttribute('stroke-dasharray', '4 5');
  hoverLine.setAttribute('opacity', '0');
  hoverLine.setAttribute('pointer-events', 'none');
  svg.appendChild(hoverLine);

  const hide = () => {{
    tooltip.style.display = 'none';
    hoverLine.setAttribute('opacity', '0');
  }};

  const pathForView = () => {{
    const {{ start, end }} = indexBounds();
    const parts = [];
    for (let index = start; index <= end; index += 1) {{
      const row = data[index];
      const prefix = parts.length ? 'L' : 'M';
      parts.push(`${{prefix}}${{xOf(index).toFixed(1)}} ${{yOf(row.ratioPct).toFixed(1)}}`);
    }}
    return parts.join(' ');
  }};

  const fedPathForView = () => {{
    const {{ start, end }} = indexBounds();
    const parts = [];
    let lastY = null;
    for (let index = start; index <= end; index += 1) {{
      const x = xOf(index).toFixed(1);
      const y = yFedOf(data[index].fedRate);
      if (!parts.length) {{
        parts.push(`M${{x}} ${{y.toFixed(1)}}`);
      }} else {{
        parts.push(`L${{x}} ${{lastY.toFixed(1)}}`);
        if (!Object.is(y, lastY)) {{
          parts.push(`L${{x}} ${{y.toFixed(1)}}`);
        }}
      }}
      lastY = y;
    }}
    return parts.join(' ');
  }};

  const addTick = (tickMap, index, label) => {{
    const safeIndex = clamp(index, 0, data.length - 1);
    tickMap.set(safeIndex, {{ index: safeIndex, label }});
  }};

  const renderStages = () => {{
    while (stageBandLayer.firstChild) {{
      stageBandLayer.removeChild(stageBandLayer.firstChild);
    }}
    while (stageLabelLayer.firstChild) {{
      stageLabelLayer.removeChild(stageLabelLayer.firstChild);
    }}

    const {{ start, end }} = indexBounds();
    bullStages.forEach((stage) => {{
      const visibleStart = Math.max(stage.startIndex, start);
      const visibleEnd = Math.min(stage.endIndex, end);
      if (visibleStart > visibleEnd) {{
        return;
      }}

      const left = Math.max(plot.x0, xOf(visibleStart));
      const right = Math.min(plot.x1, xOf(visibleEnd));
      const width = Math.max(1, right - left);
      stageBandLayer.appendChild(createSvg('rect', {{
        x: left.toFixed(1),
        y: plot.y0.toFixed(1),
        width: width.toFixed(1),
        height: (plot.y1 - plot.y0).toFixed(1),
        fill: stage.color,
        opacity: '0.055',
      }}));
      stageBandLayer.appendChild(createSvg('line', {{
        x1: left.toFixed(1),
        y1: plot.y0.toFixed(1),
        x2: left.toFixed(1),
        y2: plot.y1.toFixed(1),
        stroke: stage.color,
        'stroke-width': '1',
        'stroke-dasharray': '4 5',
        opacity: '0.32',
      }}));
      stageBandLayer.appendChild(createSvg('line', {{
        x1: right.toFixed(1),
        y1: plot.y0.toFixed(1),
        x2: right.toFixed(1),
        y2: plot.y1.toFixed(1),
        stroke: stage.color,
        'stroke-width': '1',
        'stroke-dasharray': '4 5',
        opacity: '0.22',
      }}));

      const center = clamp((left + right) / 2, plot.x0 + 46, plot.x1 - 46);
      const labelY = plot.y0 + 18 + stage.level * 34;
      const title = createSvg('text', {{
        x: center.toFixed(1),
        y: labelY.toFixed(1),
        fill: stage.color,
        'font-size': '11',
        'font-weight': '700',
        'text-anchor': 'middle',
        style: 'paint-order:stroke;stroke:#FFFFFF;stroke-width:4px;stroke-linejoin:round',
      }});
      title.textContent = stage.title;
      stageLabelLayer.appendChild(title);

      const drivers = createSvg('text', {{
        x: center.toFixed(1),
        y: (labelY + 15).toFixed(1),
        fill: stage.color,
        'font-size': '10.5',
        'font-weight': '600',
        'text-anchor': 'middle',
        style: 'paint-order:stroke;stroke:#FFFFFF;stroke-width:4px;stroke-linejoin:round',
      }});
      drivers.textContent = stage.drivers;
      stageLabelLayer.appendChild(drivers);
    }});
  }};

  const renderDownturnAnnotations = () => {{
    while (downturnLayer.firstChild) {{
      downturnLayer.removeChild(downturnLayer.firstChild);
    }}

    const {{ start, end }} = indexBounds();
    downturnAnnotations.forEach((annotation) => {{
      if (annotation.index < start || annotation.index > end) {{
        return;
      }}
      const point = data[annotation.index];
      const x = xOf(annotation.index);
      const y = yOf(point.ratioPct);
      let anchor = annotation.dx >= 0 ? 'start' : 'end';
      let textX = x + annotation.dx;
      const textY = clamp(y + annotation.dy, plot.y0 + 44, plot.y1 - 26);
      if (textX < plot.x0 + 10) {{
        anchor = 'start';
        textX = x + Math.abs(annotation.dx);
      }} else if (textX > plot.x1 - 10) {{
        anchor = 'end';
        textX = x - Math.abs(annotation.dx);
      }}
      const leaderX = anchor === 'start' ? textX - 5 : textX + 5;
      const leaderY = textY + 3;
      downturnLayer.appendChild(createSvg('line', {{
        x1: x.toFixed(1),
        y1: y.toFixed(1),
        x2: leaderX.toFixed(1),
        y2: leaderY.toFixed(1),
        stroke: annotation.color,
        'stroke-width': '1.2',
        'stroke-opacity': '0.65',
      }}));
      downturnLayer.appendChild(createSvg('circle', {{
        cx: x.toFixed(1),
        cy: y.toFixed(1),
        r: '4.6',
        fill: '#FFFFFF',
        stroke: annotation.color,
        'stroke-width': '2',
      }}));

      const title = createSvg('text', {{
        x: textX.toFixed(1),
        y: textY.toFixed(1),
        fill: annotation.color,
        'font-size': '11',
        'font-weight': '700',
        'text-anchor': anchor,
        style: 'paint-order:stroke;stroke:#FFFFFF;stroke-width:4px;stroke-linejoin:round',
      }});
      title.textContent = annotation.title;
      downturnLayer.appendChild(title);

      const reason = createSvg('text', {{
        x: textX.toFixed(1),
        y: (textY + 15).toFixed(1),
        fill: annotation.color,
        'font-size': '10.5',
        'font-weight': '600',
        'text-anchor': anchor,
        style: 'paint-order:stroke;stroke:#FFFFFF;stroke-width:4px;stroke-linejoin:round',
      }});
      reason.textContent = annotation.reason;
      downturnLayer.appendChild(reason);
    }});
  }};

  const renderFedEvents = () => {{
    while (fedEventLayer.firstChild) {{
      fedEventLayer.removeChild(fedEventLayer.firstChild);
    }}

    const {{ start, end }} = indexBounds();
    fedEvents.forEach((event) => {{
      if (event.index < start || event.index > end) {{
        return;
      }}
      const x = xOf(event.index);
      const y = yFedOf(event.midRate);
      const marker = createSvg('circle', {{
        cx: x.toFixed(1),
        cy: y.toFixed(1),
        r: '3.5',
        fill: '#FFFFFF',
        stroke: event.color,
        'stroke-width': '1.5',
        'data-event-index': event.index,
      }});
      const title = createSvg('title');
      const delta = `${{event.changeBp > 0 ? '+' : ''}}${{event.changeBp}}bp`;
      title.textContent = `${{event.date}} ${{event.action}} ${{delta}}；目标区间 ${{event.target}}；原因：${{event.reason}}`;
      marker.appendChild(title);
      fedEventLayer.appendChild(marker);
    }});
  }};

  const renderXAxis = () => {{
    while (xAxisLayer.firstChild) {{
      xAxisLayer.removeChild(xAxisLayer.firstChild);
    }}

    const {{ start, end }} = indexBounds();
    const windowSize = Math.max(1, end - start + 1);
    const tickMap = new Map();
    const compactDate = (row) => row.date.replace(/-/g, '');
    addTick(tickMap, start, windowSize <= 80 ? compactDate(data[start]) : data[start].month);

    if (windowSize > 1200) {{
      let lastMonth = '';
      for (let index = start; index <= end; index += 1) {{
        const row = data[index];
        if (row.month !== lastMonth) {{
          if (row.month.endsWith('01')) {{
            addTick(tickMap, index, row.month);
          }}
          lastMonth = row.month;
        }}
      }}
    }} else if (windowSize > 260) {{
      let lastMonth = '';
      const quarterMonths = new Set([1, 4, 7, 10]);
      for (let index = start; index <= end; index += 1) {{
        const row = data[index];
        if (row.month !== lastMonth) {{
          const monthNumber = Number(row.month.slice(4));
          if (quarterMonths.has(monthNumber)) {{
            addTick(tickMap, index, row.month);
          }}
          lastMonth = row.month;
        }}
      }}
    }} else if (windowSize > 80) {{
      let lastMonth = '';
      for (let index = start; index <= end; index += 1) {{
        const row = data[index];
        if (row.month !== lastMonth) {{
          addTick(tickMap, index, row.month);
          lastMonth = row.month;
        }}
      }}
    }} else {{
      const step = Math.max(1, Math.ceil(windowSize / 8));
      for (let index = start; index <= end; index += step) {{
        addTick(tickMap, index, compactDate(data[index]));
      }}
    }}

    addTick(tickMap, end, windowSize <= 80 ? compactDate(data[end]) : data[end].month);

    const ticks = Array.from(tickMap.values()).sort((left, right) => left.index - right.index);
    const tickViews = ticks.map((tick, position) => {{
      const x = xOf(tick.index);
      const anchor = x < plot.x0 + 44 ? 'start' : (x > plot.x1 - 44 ? 'end' : 'middle');
      const approxWidth = tick.label.length * 7.3;
      let left = x - approxWidth / 2;
      let right = x + approxWidth / 2;
      if (anchor === 'start') {{
        left = x;
        right = x + approxWidth;
      }} else if (anchor === 'end') {{
        left = x - approxWidth;
        right = x;
      }}
      return {{ ...tick, position, x, anchor, approxWidth, left, right }};
    }});
    const overlaps = (left, right) => Math.min(left.right, right.right) - Math.max(left.left, right.left) > -2;
    const forcedLevels = new Map();
    if (tickViews.length > 1) {{
      if (overlaps(tickViews[0], tickViews[1])) {{
        forcedLevels.set(0, 1);
        forcedLevels.set(1, 0);
      }}
      if (overlaps(tickViews[tickViews.length - 2], tickViews[tickViews.length - 1])) {{
        forcedLevels.set(tickViews.length - 2, 0);
        forcedLevels.set(tickViews.length - 1, 1);
      }}
    }}

    const labelBoxes = [];
    tickViews.forEach((tick) => {{
      const x = tick.x;
      xAxisLayer.appendChild(createSvg('line', {{
        x1: x.toFixed(1),
        y1: plot.y0,
        x2: x.toFixed(1),
        y2: plot.y1,
        stroke: '#E4E7EF',
        'stroke-width': '1',
        'stroke-dasharray': '2 7',
      }}));
      xAxisLayer.appendChild(createSvg('line', {{
        x1: x.toFixed(1),
        y1: plot.y1,
        x2: x.toFixed(1),
        y2: plot.y1 + 7,
        stroke: '#CDD3E1',
      }}));

      const preferredLevels = forcedLevels.has(tick.position) ? [forcedLevels.get(tick.position)] : [0, 1];
      let labelLevel = preferredLevels[preferredLevels.length - 1];
      for (const level of preferredLevels) {{
        const hasOverlap = labelBoxes.some((existing) => (
          existing.level === level
          && Math.min(tick.right, existing.right) - Math.max(tick.left, existing.left) > -2
        ));
        if (!hasOverlap) {{
          labelLevel = level;
          break;
        }}
      }}
      const text = createSvg('text', {{
        x: x.toFixed(1),
        y: plot.y1 + 32 + labelLevel * 17,
        fill: '#6F768A',
        'font-size': '12',
        'font-family': "Consolas,'SF Mono',monospace",
        'text-anchor': tick.anchor,
      }});
      text.textContent = tick.label;
      xAxisLayer.appendChild(text);
      labelBoxes.push({{ left: tick.left, right: tick.right, level: labelLevel }});
    }});
  }};

  const renderEndpoint = () => {{
    const endpointIndex = clamp(Math.floor(viewEnd), 0, data.length - 1);
    const point = data[endpointIndex];
    const x = xOf(endpointIndex);
    const y = yOf(point.ratioPct);
    latestPoint.setAttribute('cx', x.toFixed(1));
    latestPoint.setAttribute('cy', y.toFixed(1));
    latestPoint.setAttribute('opacity', '1');
    latestLabel.setAttribute('x', Math.min(plot.x1 - 8, Math.max(plot.x0 + 64, x - 8)).toFixed(1));
    latestLabel.setAttribute('y', (y - 11 < plot.y0 + 8 ? y + 22 : y - 11).toFixed(1));
    latestLabel.textContent = formatPct(point.ratioPct);
    const fedTickLabelYs = [0, 2, 4, 6]
      .filter((tick) => tick <= fedScale.max)
      .map((tick) => yFedOf(tick) + 4);
    const labelX = Math.min(plot.x1 + 10, Math.max(plot.x0 + 64, x + 8)).toFixed(1);
    const fedY = yFedOf(point.fedRate);
    latestFedPoint.setAttribute('cx', x.toFixed(1));
    latestFedPoint.setAttribute('cy', fedY.toFixed(1));
    latestFedPoint.setAttribute('opacity', '1');
    latestFedLabel.setAttribute('x', labelX);
    let fedLabelY = fedY + 4;
    if (fedTickLabelYs.some((tickY) => Math.abs(fedLabelY - tickY) < 14)) {{
      fedLabelY = fedY + 18;
    }}
    latestFedLabel.setAttribute('y', clamp(fedLabelY, plot.y0 + 12, plot.y1 - 8).toFixed(1));
    latestFedLabel.textContent = formatPct(point.fedRate);
  }};

  const renderExtrema = () => {{
    while (extremaLayer.firstChild) {{
      extremaLayer.removeChild(extremaLayer.firstChild);
    }}

    const {{ start, end }} = indexBounds();
    const suppressedExtremaIndices = new Set(downturnAnnotations.map((annotation) => annotation.index));
    let highIndex = start;
    let lowIndex = start;
    for (let index = start; index <= end; index += 1) {{
      if (data[index].ratioPct > data[highIndex].ratioPct) {{
        highIndex = index;
      }}
      if (data[index].ratioPct < data[lowIndex].ratioPct) {{
        lowIndex = index;
      }}
    }}

    const addedIndices = new Set();
    const addExtrema = (index, color, dx, dy) => {{
      if (index < start || index > end || addedIndices.has(index) || suppressedExtremaIndices.has(index)) {{
        return;
      }}
      addedIndices.add(index);
      const point = data[index];
      const x = xOf(index);
      const y = yOf(point.ratioPct);
      let anchor = dx >= 0 ? 'start' : 'end';
      let textX = x + dx;
      const textY = clamp(y + dy, plot.y0 + 14, plot.y1 - 8);
      if (textX < plot.x0 + 10) {{
        anchor = 'start';
        textX = x + Math.abs(dx);
      }} else if (textX > plot.x1 - 10) {{
        anchor = 'end';
        textX = x - Math.abs(dx);
      }}
      const leaderX = anchor === 'start' ? textX - 4 : textX + 4;
      const leaderY = textY - 4;
      extremaLayer.appendChild(createSvg('line', {{
        x1: x.toFixed(1),
        y1: y.toFixed(1),
        x2: leaderX.toFixed(1),
        y2: leaderY.toFixed(1),
        stroke: color,
        'stroke-width': '1.2',
        'stroke-opacity': '0.65',
      }}));
      extremaLayer.appendChild(createSvg('circle', {{
        cx: x.toFixed(1),
        cy: y.toFixed(1),
        r: '4.8',
        fill: '#FFFFFF',
        stroke: color,
        'stroke-width': '2',
      }}));
      const text = createSvg('text', {{
        x: textX.toFixed(1),
        y: textY.toFixed(1),
        fill: color,
        'font-size': '12',
        'font-weight': '700',
        'font-family': "Consolas,'SF Mono',monospace",
        'text-anchor': anchor,
        style: 'paint-order:stroke;stroke:#FFFFFF;stroke-width:4px;stroke-linejoin:round',
      }});
      text.textContent = formatPct(point.ratioPct);
      extremaLayer.appendChild(text);
    }};

    addExtrema(highIndex, '#C8754A', 14, -18);
    if (lowIndex !== highIndex) {{
      addExtrema(lowIndex, '#4569B7', 14, 30);
    }}
    phaseMarkers.forEach((marker) => {{
      addExtrema(marker.index, marker.color, marker.dx, marker.dy);
    }});
  }};

  const renderStatus = () => {{
    zoomStatus.textContent = '';
  }};

  const render = () => {{
    renderStages();
    renderDownturnAnnotations();
    renderFedEvents();
    fedRatePath.setAttribute('d', fedPathForView());
    ratioPath.setAttribute('d', pathForView());
    renderXAxis();
    renderExtrema();
    renderEndpoint();
    renderStatus();
    hide();
  }};

  const setView = (start, end) => {{
    const maxEnd = data.length - 1;
    let span = Math.max(minWindow - 1, Math.min(maxEnd, end - start));
    let nextStart = start;
    let nextEnd = nextStart + span;
    if (nextStart < 0) {{
      nextStart = 0;
      nextEnd = span;
    }}
    if (nextEnd > maxEnd) {{
      nextEnd = maxEnd;
      nextStart = maxEnd - span;
    }}
    viewStart = clamp(nextStart, 0, maxEnd);
    viewEnd = clamp(nextEnd, 0, maxEnd);
    render();
  }};

  const zoom = (factor, anchorRatio = 0.5) => {{
    const span = viewEnd - viewStart;
    const nextSpan = Math.max(minWindow - 1, Math.min(data.length - 1, span * factor));
    const anchorIndex = viewStart + span * anchorRatio;
    const nextStart = anchorIndex - nextSpan * anchorRatio;
    setView(nextStart, nextStart + nextSpan);
  }};

  document.getElementById('zoomIn').addEventListener('click', () => zoom(0.55, 0.5));
  document.getElementById('zoomOut').addEventListener('click', () => zoom(1.8, 0.5));
  document.getElementById('zoomReset').addEventListener('click', () => setView(0, data.length - 1));

  chart.addEventListener('wheel', (event) => {{
    const point = svgPointFromEvent(event);
    if (!inPlot(point)) {{
      return;
    }}
    event.preventDefault();
    const anchorRatio = clamp((point.x - plot.x0) / (plot.x1 - plot.x0), 0, 1);
    zoom(event.deltaY < 0 ? 0.72 : 1.38, anchorRatio);
  }}, {{ passive: false }});

  chart.addEventListener('pointerdown', (event) => {{
    const point = svgPointFromEvent(event);
    if (!inPlot(point)) {{
      return;
    }}
    const plotPixels = (plot.x1 - plot.x0) / viewBox.width * point.rect.width;
    dragging = {{
      pointerId: event.pointerId,
      clientX: event.clientX,
      start: viewStart,
      end: viewEnd,
      plotPixels,
    }};
    chart.setPointerCapture(event.pointerId);
  }});

  chart.addEventListener('pointermove', (event) => {{
    if (!dragging || event.pointerId !== dragging.pointerId) {{
      return;
    }}
    event.preventDefault();
    const span = dragging.end - dragging.start;
    const shift = -(event.clientX - dragging.clientX) / dragging.plotPixels * span * panSpeed;
    setView(dragging.start + shift, dragging.end + shift);
  }});

  const stopDragging = (event) => {{
    if (dragging && event.pointerId === dragging.pointerId) {{
      dragging = null;
    }}
  }};
  chart.addEventListener('pointerup', stopDragging);
  chart.addEventListener('pointercancel', stopDragging);

  chart.addEventListener('mousemove', (event) => {{
    if (dragging) {{
      return;
    }}
    const point = svgPointFromEvent(event);

    if (!inPlot(point)) {{
      hide();
      return;
    }}

    const ratio = (point.x - plot.x0) / (plot.x1 - plot.x0);
    const index = clamp(Math.round(viewStart + ratio * (viewEnd - viewStart)), 0, data.length - 1);
    const row = data[index];
    const lineX = xOf(index);

    let fedEvent = fedEventByIndex.get(index) || null;
    if (!fedEvent) {{
      let nearestDistance = Infinity;
      fedEvents.forEach((candidate) => {{
        const distance = Math.abs(xOf(candidate.index) - lineX);
        if (distance < nearestDistance) {{
          nearestDistance = distance;
          fedEvent = candidate;
        }}
      }});
      if (nearestDistance > 9) {{
        fedEvent = null;
      }}
    }}

    const fedEventHtml = fedEvent
      ? `<div class="fed-event"><div class="fed-action">FOMC${{fedEvent.action}} ${{fedEvent.changeBp > 0 ? '+' : ''}}${{fedEvent.changeBp}}bp，目标区间 ${{fedEvent.target}}</div><div class="fed-reason">原因：${{fedEvent.reason}}</div></div>`
      : '';

    hoverLine.setAttribute('x1', lineX);
    hoverLine.setAttribute('x2', lineX);
    hoverLine.setAttribute('opacity', '0.5');

    tooltip.innerHTML = `<div class="date">${{row.date}}</div><div>百分比：<span class="close">${{formatPct(row.ratioPct)}}</span></div><div>Fed均值：<span class="fed-rate">${{formatPct(row.fedRate)}}</span></div>${{fedEventHtml}}`;
    tooltip.style.display = 'block';

    const tipRect = tooltip.getBoundingClientRect();
    let left = event.clientX + 12;
    let top = event.clientY - tipRect.height - 12;
    if (left + tipRect.width > window.innerWidth - 8) {{
      left = event.clientX - tipRect.width - 12;
    }}
    if (top < 8) {{
      top = event.clientY + 12;
    }}
    tooltip.style.left = `${{left}}px`;
    tooltip.style.top = `${{top}}px`;
  }});

  chart.addEventListener('mouseleave', hide);
  render();
}})();
</script>
</body>
</html>
"""
    HTML_PATH.write_text(html_doc, encoding="utf-8")


def main():
    rows = load_trading_day_rows()
    write_csv(rows)
    svg = make_svg(rows)
    SVG_PATH.write_text(svg, encoding="utf-8")
    write_html(svg, rows)

    latest = rows[-1]
    print(f"rows={len(rows)}")
    print(f"data_start={rows[0]['trading_date']}")
    print(f"latest_date={latest['trading_date']}")
    print(f"latest_market_cap_trn={latest['market_cap_trn_cny']:.4f}")
    print(f"latest_gdp_trn={latest['gdp_trn_cny']:.4f}")
    print(f"latest_ratio={latest['market_cap_to_gdp']:.4%}")
    print(f"csv={CSV_PATH}")
    print(f"svg={SVG_PATH}")
    print(f"html={HTML_PATH}")


if __name__ == "__main__":
    main()
