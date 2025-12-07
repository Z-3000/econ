#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grafana 대시보드 자동 생성 스크립트 v2
사용자 요청대로 4행 레이아웃 재구성:
1행: 한국·미국 주가지수/ETF
2행: GDP·CPI (경기·물가)
3행: 금리·환율
4행: 섹터/테마
"""

import json

def create_dashboard():
    """
    4행 레이아웃 대시보드 생성
    """

    dashboard = {
        "dashboard": {
            "title": "경제·주가 통합 모니터링 (15년, GDP 포함)",
            "tags": ["econ", "market", "15years", "gdp"],
            "timezone": "Asia/Seoul",
            "refresh": "5m",
            "time": {
                "from": "now-15y",
                "to": "now"
            },
            "timepicker": {
                "refresh_intervals": ["5m", "15m", "30m", "1h", "1d"],
                "time_options": ["1y", "5y", "10y", "15y"]
            },
            "panels": []
        },
        "folderId": 0,
        "overwrite": True
    }

    panel_id = 1
    y_pos = 0

    # ===========================
    # 1행: 한국·미국 주가지수/ETF
    # ===========================

    # 1-1. 한국 지수 (KOSPI, KOSDAQ, KODEX200)
    korean_indices = {
        "id": panel_id,
        "title": "한국 주가지수/ETF",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": y_pos, "w": 12, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "코스피" or r.name == "코스닥" or r.name == "KODEX200")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.name }))
  |> drop(columns: ["name", "ticker"])
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 0,
                    "lineWidth": 2,
                    "showPoints": "never"
                },
                "color": {"mode": "palette-classic"}
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(korean_indices)
    panel_id += 1

    # 1-2. 미국 지수 (S&P500, 나스닥, QQQ, SPY, DIA)
    us_indices = {
        "id": panel_id,
        "title": "미국 주가지수/ETF",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": y_pos, "w": 12, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "S&P500" or r.name == "나스닥" or r.name == "QQQ" or r.name == "SPY" or r.name == "DIA")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.name }))
  |> drop(columns: ["name", "ticker"])
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 0,
                    "lineWidth": 2,
                    "showPoints": "never"
                },
                "color": {"mode": "palette-classic"}
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(us_indices)
    panel_id += 1
    y_pos += 8

    # ===========================
    # 2행: GDP·CPI (경기·물가)
    # ===========================

    # 2-1. 한국 실질 GDP 성장률 + 산업생산
    korean_gdp = {
        "id": panel_id,
        "title": "한국 경기 (실질GDP 성장률·산업생산)",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": y_pos, "w": 12, "h": 8},
        "targets": [
            {
                "datasource": {"type": "influxdb", "uid": "influxdb"},
                "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator =~ /한국 GDP.*실질.*전기비/ or r.indicator =~ /한국 GDP.*실질.*전년동기비/)
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 3mo, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
                ''',
                "refId": "GDP"
            },
            {
                "datasource": {"type": "influxdb", "uid": "influxdb"},
                "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "미국 산업생산지수")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
                ''',
                "refId": "IND"
            }
        ],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 10,
                    "lineWidth": 2
                },
                "unit": "percent",
                "color": {"mode": "palette-classic"}
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(korean_gdp)
    panel_id += 1

    # 2-2. 한국 CPI + 미국 CPI
    cpi_panel = {
        "id": panel_id,
        "title": "물가 (한국·미국 CPI)",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": y_pos, "w": 12, "h": 8},
        "targets": [
            {
                "datasource": {"type": "influxdb", "uid": "influxdb"},
                "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "한국 소비자물가지수")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
                |> map(fn: (r) => ({ r with _field: r.indicator }))
                |> drop(columns: ["indicator", "series_id", "period"])
                ''',
                "refId": "KR_CPI"
            },
            {
                "datasource": {"type": "influxdb", "uid": "influxdb"},
                "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "미국 CPI")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
                |> map(fn: (r) => ({ r with _field: r.indicator }))
                |> drop(columns: ["indicator", "series_id", "period"])
                ''',
                "refId": "US_CPI"
            }
        ],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 10,
                    "lineWidth": 2
                },
                "unit": "short",
                "color": {"mode": "palette-classic"}
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(cpi_panel)
    panel_id += 1
    y_pos += 8

    # ===========================
    # 3행: 금리·환율
    # ===========================

    # 3-1. 미국 금리 (연방기금금리 + 10년 국채) - 수익률곡선
    us_rates = {
        "id": panel_id,
        "title": "미국 금리 (연방기금금리 vs 10년 국채)",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": y_pos, "w": 12, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "연방기금금리" or r.indicator == "미국 10년 국채금리")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 0,
                    "lineWidth": 2,
                    "showPoints": "never"
                },
                "unit": "percent",
                "color": {"mode": "palette-classic"}
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(us_rates)
    panel_id += 1

    # 3-2. USD/KRW 환율 + 미국 10년물
    exchange_rate = {
        "id": panel_id,
        "title": "환율 (USD/KRW) + 미국 10년물 금리",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": y_pos, "w": 12, "h": 8},
        "targets": [
            {
                "datasource": {"type": "influxdb", "uid": "influxdb"},
                "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "USD/KRW 환율")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
                ''',
                "refId": "FX"
            },
            {
                "datasource": {"type": "influxdb", "uid": "influxdb"},
                "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "미국 10년 국채금리")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _value: r._value * 100.0, _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
                ''',
                "refId": "US10Y"
            }
        ],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 10,
                    "lineWidth": 2,
                    "axisPlacement": "auto"
                },
                "color": {"mode": "palette-classic"}
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "USD/KRW 환율"},
                    "properties": [
                        {"id": "custom.axisPlacement", "value": "left"},
                        {"id": "unit", "value": "short"}
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "미국 10년 국채금리"},
                    "properties": [
                        {"id": "custom.axisPlacement", "value": "right"},
                        {"id": "unit", "value": "percent"}
                    ]
                }
            ]
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(exchange_rate)
    panel_id += 1
    y_pos += 8

    # ===========================
    # 4행: 섹터/테마
    # ===========================

    # 4-1. IT 플랫폼 (NAVER, 카카오)
    it_platform = {
        "id": panel_id,
        "title": "IT 플랫폼 (NAVER·카카오)",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": y_pos, "w": 8, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "NAVER" or r.name == "카카오")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
            |> map(fn: (r) => ({ r with _field: r.name }))
            |> drop(columns: ["name", "ticker"])
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 0,
                    "lineWidth": 2
                },
                "color": {"mode": "palette-classic"}
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(it_platform)
    panel_id += 1

    # 4-2. 엔터/게임
    entertainment = {
        "id": panel_id,
        "title": "엔터테인먼트·게임",
        "type": "timeseries",
        "gridPos": {"x": 8, "y": y_pos, "w": 8, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "HYBE" or r.name == "SM" or r.name == "JYP Ent." or r.name == "크래프톤" or r.name == "엔씨소프트")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
            |> map(fn: (r) => ({ r with _field: r.name }))
            |> drop(columns: ["name", "ticker"])
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 0,
                    "lineWidth": 2
                },
                "color": {"mode": "palette-classic"}
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(entertainment)
    panel_id += 1

    # 4-3. 대형주 (삼성전자, SK하이닉스, 현대차, KB금융)
    large_cap = {
        "id": panel_id,
        "title": "대형주 (반도체·자동차·금융)",
        "type": "timeseries",
        "gridPos": {"x": 16, "y": y_pos, "w": 8, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "삼성전자" or r.name == "SK하이닉스" or r.name == "현대차" or r.name == "KB금융")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
            |> map(fn: (r) => ({ r with _field: r.name }))
            |> drop(columns: ["name", "ticker"])
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 0,
                    "lineWidth": 2
                },
                "color": {"mode": "palette-classic"}
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(large_cap)

    return dashboard

def main():
    """
    대시보드 생성 및 저장
    """
    print("=" * 80)
    print("Grafana 대시보드 생성 v2 (GDP 포함)")
    print("=" * 80)

    dashboard = create_dashboard()

    # JSON 파일로 저장
    output_file = "/raspi/WD4T/03_outputs/grafana_dashboard_final.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 대시보드 JSON 생성 완료: {output_file}")
    print("\n레이아웃 구성:")
    print("  1행: 한국 지수/ETF | 미국 지수/ETF")
    print("  2행: 한국 실질GDP+산업생산 | 한국·미국 CPI")
    print("  3행: 미국 금리(연방기금+10년물) | 환율+미국10년물")
    print("  4행: IT플랫폼 | 엔터/게임 | 대형주")
    print("\nGrafana 수동 import:")
    print("  1. http://localhost:3000 접속")
    print("  2. Dashboards > New > Import")
    print(f"  3. Upload: {output_file}")
    print("  4. InfluxDB 데이터소스 선택 > Import")
    print()

if __name__ == "__main__":
    main()
