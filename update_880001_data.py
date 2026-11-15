# -*- coding: utf-8 -*-
"""把通达信 880001（A 股总市值，每点 100 亿元）更新到最新交易日。

取数
  pytdxdata（2026-09 通达信换协议后的新通道），显式 800 根/页分段拉取；单次大 count
  的分页会偶发空洞，故不用库内置的整段接口。

落盘
  marketcap_gdp_raw.json 只追加：已存在的交易日一律不动，只补快照里晚于最后一条的
  交易日；GDP 沿用最后一行的值（新交易日仍属同一「上年 GDP」）。写入走临时文件再替换。

校验
  交易日唯一且严格递增；最新交易日不早于今天 7 天；收盘点位在 1000–50000 之间。
  任一条不过就拒绝写入。

用法
  python update_880001_data.py            只更新数据
  python update_880001_data.py --generate 更新后重新生成 CSV / SVG / HTML
  python update_880001_data.py --dry-run  只取数与校验，不写文件
"""

import argparse
import asyncio
import json
import sys
from datetime import date
from pathlib import Path

from pytdxdata import TdxData
from pytdxdata.models import KlinePeriod

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "marketcap_gdp_raw.json"
GENERATOR = ROOT / "generate_marketcap_gdp_chart.py"
PAGE_SIZE = 800
MAX_PAGES = 20


def parse_args():
    parser = argparse.ArgumentParser(description="更新 880001 总市值数据。")
    parser.add_argument("--generate", action="store_true", help="更新后重新生成图表。")
    parser.add_argument("--dry-run", action="store_true", help="只取数与校验，不写文件。")
    args = parser.parse_args()
    if args.generate and args.dry_run:
        parser.error("--generate 不能与 --dry-run 同时使用")
    return args


async def fetch_bars():
    async with TdxData() as td:
        bars = []
        start = 0
        for _ in range(MAX_PAGES):
            batch = await td.get_bars("sh880001", KlinePeriod.DAY, start=start, count=PAGE_SIZE)
            if not batch:
                break
            bars.extend(batch)
            start += len(batch)
            if len(batch) < PAGE_SIZE:
                break
    rows = {}
    for bar in bars:
        day = bar.trading_date if isinstance(bar.trading_date, str) else bar.datetime.strftime("%Y-%m-%d")
        rows[day] = {"date": day, "close": round(float(bar.close), 3)}
    return rows


def build_new_rows(bars, last):
    new_rows = []
    for day in sorted(bars):
        if day <= last["date"]:
            continue
        close = bars[day]["close"]
        if not 1000 <= close <= 50000:
            raise SystemExit(f"{day} 收盘点位量级异常：{close}")
        new_rows.append({"date": day, "marketCap": round(close * 100.0, 3),
                         "gdp": last["gdp"], "close": close,
                         "market_cap_source": "tdx_880001"})
    if new_rows:
        if (date.today() - date.fromisoformat(new_rows[-1]["date"])).days > 7:
            raise SystemExit(f"最新交易日过旧：{new_rows[-1]['date']}")
        if any(a["date"] >= b["date"] for a, b in zip(new_rows, new_rows[1:])):
            raise SystemExit("新增交易日未严格递增")
    return new_rows


async def main():
    args = parse_args()
    bars = await fetch_bars()
    if len(bars) < 1000:
        raise SystemExit(f"880001 快照异常偏少：{len(bars)} 天")

    payload = json.loads(RAW.read_text(encoding="utf-8"))
    data = payload["data"]
    last = data[-1]
    new_rows = build_new_rows(bars, last)

    print(f"snapshot_days={len(bars)} first={min(bars)} last={max(bars)}")
    if not new_rows:
        print(f"no new trading days; raw last={last['date']}")
        return
    print("added=" + ", ".join(f"{r['date']}:{r['close']}" for r in new_rows))
    if args.dry_run:
        print("dry-run：未写文件")
        return

    payload["data"] = data + new_rows
    tmp = RAW.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(RAW)
    print(f"raw rows {len(data)} -> {len(payload['data'])}; latest={new_rows[-1]['date']}")

    if args.generate:
        import subprocess
        subprocess.run([sys.executable, "-B", str(GENERATOR)], cwd=str(ROOT), check=True)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    asyncio.run(main())
