#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InfluxDB 정합성 점검 스크립트

검증 대상:
- stock_prices (KR/US): date+ticker+name, date+ticker
- economic_indicators (FRED/ECOS): date+indicator+period

사용 예:
    source ~/influx_venv/bin/activate
    python 01_scripts/09_validate_influx_integrity.py --bucket econ_market
    python 01_scripts/09_validate_influx_integrity.py --bucket econ_market_backfill_2010_2025
"""

import argparse
import json
from pathlib import Path

import pandas as pd
from influxdb_client import InfluxDBClient

from config import config


def load_csv_sets():
    data_dir = Path(config.DATA_DIR)

    kr = pd.read_csv(data_dir / "stock_kr_2010_2025_with_adj.csv", encoding="utf-8-sig")
    us = pd.read_csv(data_dir / "stock_us_2010_2025_with_adj.csv", encoding="utf-8-sig")
    fred = pd.read_csv(data_dir / "economy_fred_2010_2025.csv", encoding="utf-8-sig")
    ecos = pd.read_csv(data_dir / "economy_ecos_2010_2025.csv", encoding="utf-8-sig")

    for df in (kr, us, fred, ecos):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    fred_num = pd.to_numeric(fred["value"], errors="coerce")
    ecos_num = pd.to_numeric(ecos["value"], errors="coerce")

    def stock_key(df):
        return set(zip(df["date"].dt.strftime("%Y-%m-%d"), df["ticker"].astype(str), df["name"].astype(str)))

    def stock_key_dt_ticker(df):
        return set(zip(df["date"].dt.strftime("%Y-%m-%d"), df["ticker"].astype(str)))

    def econ_key(df, period):
        return set(zip(df["date"].dt.strftime("%Y-%m-%d"), df["indicator"].astype(str), [period] * len(df)))

    return {
        "kr": kr,
        "us": us,
        "fred": fred,
        "ecos": ecos,
        "csv_keys": {
            "kr_full": stock_key(kr),
            "us_full": stock_key(us),
            "kr_dt_ticker": stock_key_dt_ticker(kr),
            "us_dt_ticker": stock_key_dt_ticker(us),
            "fred_raw": econ_key(fred, "daily"),
            "ecos_raw": econ_key(ecos, "monthly"),
            "fred_valid": econ_key(fred[fred_num.notna()], "daily"),
            "ecos_valid": econ_key(ecos[ecos_num.notna()], "monthly"),
        },
        "nan_count": {
            "fred_nan_value": int(fred_num.isna().sum()),
            "ecos_nan_value": int(ecos_num.isna().sum()),
        },
    }


def load_influx_sets(bucket, start, stop):
    client = InfluxDBClient(
        url=config.INFLUXDB_URL,
        token=config.INFLUXDB_TOKEN,
        org=config.INFLUXDB_ORG,
        timeout=120000,
    )
    q = client.query_api()

    stock_flux = f"""
from(bucket: "{bucket}")
  |> range(start: {start}, stop: {stop})
  |> filter(fn: (r) => r._measurement == "stock_prices" and r._field == "close")
  |> keep(columns: ["_time", "ticker", "name"])
"""
    econ_flux = f"""
from(bucket: "{bucket}")
  |> range(start: {start}, stop: {stop})
  |> filter(fn: (r) => r._measurement == "economic_indicators" and r._field == "value")
  |> keep(columns: ["_time", "indicator", "period"])
"""

    stock_keys = set()
    for table in q.query(stock_flux):
        for r in table.records:
            v = r.values
            stock_keys.add(
                (
                    pd.to_datetime(v["_time"]).strftime("%Y-%m-%d"),
                    str(v.get("ticker", "")),
                    str(v.get("name", "")),
                )
            )

    econ_keys = set()
    for table in q.query(econ_flux):
        for r in table.records:
            v = r.values
            econ_keys.add(
                (
                    pd.to_datetime(v["_time"]).strftime("%Y-%m-%d"),
                    str(v.get("indicator", "")),
                    str(v.get("period", "")),
                )
            )

    client.close()
    return {"stock_full": stock_keys, "econ_full": econ_keys}


def summarize(csv_data, influx_data):
    kr_tickers = set(csv_data["kr"]["ticker"].astype(str).unique())
    us_tickers = set(csv_data["us"]["ticker"].astype(str).unique())

    influx_kr_full = set(k for k in influx_data["stock_full"] if k[1] in kr_tickers)
    influx_us_full = set(k for k in influx_data["stock_full"] if k[1] in us_tickers)
    influx_kr_dt_ticker = set((d, t) for d, t, _ in influx_kr_full)
    influx_us_dt_ticker = set((d, t) for d, t, _ in influx_us_full)

    influx_fred = set(k for k in influx_data["econ_full"] if k[2] == "daily")
    influx_ecos = set(k for k in influx_data["econ_full"] if k[2] == "monthly")

    c = csv_data["csv_keys"]
    return {
        "stock": {
            "kr_full": {
                "csv": len(c["kr_full"]),
                "influx": len(influx_kr_full),
                "missing": len(c["kr_full"] - influx_kr_full),
                "extra": len(influx_kr_full - c["kr_full"]),
            },
            "us_full": {
                "csv": len(c["us_full"]),
                "influx": len(influx_us_full),
                "missing": len(c["us_full"] - influx_us_full),
                "extra": len(influx_us_full - c["us_full"]),
            },
            "kr_dt_ticker": {
                "csv": len(c["kr_dt_ticker"]),
                "influx": len(influx_kr_dt_ticker),
                "missing": len(c["kr_dt_ticker"] - influx_kr_dt_ticker),
                "extra": len(influx_kr_dt_ticker - c["kr_dt_ticker"]),
            },
            "us_dt_ticker": {
                "csv": len(c["us_dt_ticker"]),
                "influx": len(influx_us_dt_ticker),
                "missing": len(c["us_dt_ticker"] - influx_us_dt_ticker),
                "extra": len(influx_us_dt_ticker - c["us_dt_ticker"]),
            },
        },
        "econ": {
            "fred_raw": {
                "csv": len(c["fred_raw"]),
                "influx": len(influx_fred),
                "missing": len(c["fred_raw"] - influx_fred),
                "extra": len(influx_fred - c["fred_raw"]),
            },
            "fred_valid": {
                "csv": len(c["fred_valid"]),
                "influx": len(influx_fred),
                "missing": len(c["fred_valid"] - influx_fred),
                "extra": len(influx_fred - c["fred_valid"]),
            },
            "ecos_raw": {
                "csv": len(c["ecos_raw"]),
                "influx": len(influx_ecos),
                "missing": len(c["ecos_raw"] - influx_ecos),
                "extra": len(influx_ecos - c["ecos_raw"]),
            },
            "ecos_valid": {
                "csv": len(c["ecos_valid"]),
                "influx": len(influx_ecos),
                "missing": len(c["ecos_valid"] - influx_ecos),
                "extra": len(influx_ecos - c["ecos_valid"]),
            },
            "csv_nan_value": csv_data["nan_count"],
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default=config.INFLUXDB_BUCKET, help="검증할 InfluxDB bucket")
    parser.add_argument("--start", default="2010-01-01T00:00:00Z")
    parser.add_argument("--stop", default="2026-03-01T00:00:00Z")
    parser.add_argument("--json-out", default="", help="결과 JSON 파일 경로")
    args = parser.parse_args()

    csv_data = load_csv_sets()
    influx_data = load_influx_sets(args.bucket, args.start, args.stop)
    report = summarize(csv_data, influx_data)
    report["bucket"] = args.bucket
    report["range"] = {"start": args.start, "stop": args.stop}

    print(f"[DQ] bucket={args.bucket} range={args.start}..{args.stop}")
    print("[STOCK]")
    print(" KR(full)   ", report["stock"]["kr_full"])
    print(" US(full)   ", report["stock"]["us_full"])
    print(" KR(dt+tkr) ", report["stock"]["kr_dt_ticker"])
    print(" US(dt+tkr) ", report["stock"]["us_dt_ticker"])
    print("[ECON]")
    print(" FRED(raw)  ", report["econ"]["fred_raw"])
    print(" FRED(valid)", report["econ"]["fred_valid"])
    print(" ECOS(raw)  ", report["econ"]["ecos_raw"])
    print(" ECOS(valid)", report["econ"]["ecos_valid"])
    print(" CSV NaN    ", report["econ"]["csv_nan_value"])

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[DQ] saved json -> {out}")


if __name__ == "__main__":
    main()
