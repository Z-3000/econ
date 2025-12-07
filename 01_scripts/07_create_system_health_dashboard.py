#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 헬스 대시보드 생성 스크립트
Telegraf에서 수집한 라즈베리파이 리소스 모니터링
- CPU 사용률
- 메모리 사용량
- 디스크 용량
- CPU 온도
- 네트워크 트래픽
"""

import json
import requests
import os
from dotenv import load_dotenv

load_dotenv('/raspi/WD4T/.env')

GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://localhost:3000')
GRAFANA_USER = os.getenv('GRAFANA_USER', 'admin')
GRAFANA_PASSWORD = os.getenv('GRAFANA_PASSWORD', '')


def create_dashboard():
    """시스템 헬스 대시보드 생성"""

    dashboard = {
        "dashboard": {
            "uid": "system-health-raspi5",
            "title": "시스템 헬스 모니터링 (Raspberry Pi)",
            "tags": ["system", "telegraf", "raspi"],
            "timezone": "Asia/Seoul",
            "refresh": "1m",
            "time": {
                "from": "now-6h",
                "to": "now"
            },
            "panels": []
        },
        "folderId": 0,
        "overwrite": True
    }

    panel_id = 1
    y_pos = 0

    # ===========================
    # 1행: Stat 패널들 (요약 정보)
    # ===========================

    # 1-1. CPU 사용률 (Gauge)
    cpu_gauge = {
        "id": panel_id,
        "title": "CPU 사용률",
        "type": "gauge",
        "gridPos": {"x": 0, "y": y_pos, "w": 4, "h": 6},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "cpu")
  |> filter(fn: (r) => r._field == "usage_idle")
  |> last()
  |> map(fn: (r) => ({r with _value: 100.0 - r._value}))
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 50},
                        {"color": "orange", "value": 70},
                        {"color": "red", "value": 90}
                    ]
                }
            }
        },
        "options": {
            "showThresholdLabels": False,
            "showThresholdMarkers": True
        }
    }
    dashboard["dashboard"]["panels"].append(cpu_gauge)
    panel_id += 1

    # 1-2. 메모리 사용률 (Gauge)
    mem_gauge = {
        "id": panel_id,
        "title": "메모리 사용률",
        "type": "gauge",
        "gridPos": {"x": 4, "y": y_pos, "w": 4, "h": 6},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "mem")
  |> filter(fn: (r) => r._field == "used_percent")
  |> last()
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 60},
                        {"color": "orange", "value": 80},
                        {"color": "red", "value": 90}
                    ]
                }
            }
        }
    }
    dashboard["dashboard"]["panels"].append(mem_gauge)
    panel_id += 1

    # 1-3. 디스크 사용률 (Gauge)
    disk_gauge = {
        "id": panel_id,
        "title": "디스크 사용률 (rootfs)",
        "type": "gauge",
        "gridPos": {"x": 8, "y": y_pos, "w": 4, "h": 6},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "disk")
  |> filter(fn: (r) => r._field == "used_percent")
  |> filter(fn: (r) => r.path == "/")
  |> last()
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 60},
                        {"color": "orange", "value": 80},
                        {"color": "red", "value": 90}
                    ]
                }
            }
        }
    }
    dashboard["dashboard"]["panels"].append(disk_gauge)
    panel_id += 1

    # 1-4. CPU 온도 (Gauge)
    temp_gauge = {
        "id": panel_id,
        "title": "CPU 온도",
        "type": "gauge",
        "gridPos": {"x": 12, "y": y_pos, "w": 4, "h": 6},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "cpu_temp")
  |> filter(fn: (r) => r._field == "value")
  |> last()
  |> map(fn: (r) => ({r with _value: r._value / 1000.0}))
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "celsius",
                "min": 0,
                "max": 100,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 50},
                        {"color": "orange", "value": 65},
                        {"color": "red", "value": 80}
                    ]
                }
            }
        }
    }
    dashboard["dashboard"]["panels"].append(temp_gauge)
    panel_id += 1

    # 1-5. 업타임 (Stat)
    uptime_stat = {
        "id": panel_id,
        "title": "시스템 업타임",
        "type": "stat",
        "gridPos": {"x": 16, "y": y_pos, "w": 4, "h": 6},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "system")
  |> filter(fn: (r) => r._field == "uptime")
  |> last()
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "s",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [{"color": "green", "value": None}]
                }
            }
        },
        "options": {
            "colorMode": "value",
            "graphMode": "none",
            "justifyMode": "auto",
            "textMode": "value"
        }
    }
    dashboard["dashboard"]["panels"].append(uptime_stat)
    panel_id += 1

    # 1-6. 디스크 여유 공간 (Stat)
    disk_free_stat = {
        "id": panel_id,
        "title": "디스크 여유 (WD4T)",
        "type": "stat",
        "gridPos": {"x": 20, "y": y_pos, "w": 4, "h": 6},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "disk")
  |> filter(fn: (r) => r._field == "free")
  |> filter(fn: (r) => r.path == "/raspi/WD4T")
  |> last()
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "bytes",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "red", "value": None},
                        {"color": "yellow", "value": 107374182400},
                        {"color": "green", "value": 536870912000}
                    ]
                }
            }
        },
        "options": {
            "colorMode": "value",
            "graphMode": "none"
        }
    }
    dashboard["dashboard"]["panels"].append(disk_free_stat)
    panel_id += 1

    y_pos += 6

    # ===========================
    # 2행: 시계열 차트들
    # ===========================

    # 2-1. CPU 사용률 추이
    cpu_timeseries = {
        "id": panel_id,
        "title": "CPU 사용률 추이",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": y_pos, "w": 8, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "cpu")
  |> filter(fn: (r) => r._field == "usage_idle")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({r with _value: 100.0 - r._value, _field: "사용률"}))
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100,
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 20,
                    "lineWidth": 2
                },
                "color": {"fixedColor": "blue", "mode": "fixed"}
            }
        }
    }
    dashboard["dashboard"]["panels"].append(cpu_timeseries)
    panel_id += 1

    # 2-2. 메모리 사용량 추이
    mem_timeseries = {
        "id": panel_id,
        "title": "메모리 사용량 추이",
        "type": "timeseries",
        "gridPos": {"x": 8, "y": y_pos, "w": 8, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "mem")
  |> filter(fn: (r) => r._field == "used" or r._field == "available")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "bytes",
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 20,
                    "lineWidth": 2,
                    "stacking": {"mode": "normal"}
                }
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "used"},
                    "properties": [{"id": "color", "value": {"fixedColor": "orange", "mode": "fixed"}}]
                },
                {
                    "matcher": {"id": "byName", "options": "available"},
                    "properties": [{"id": "color", "value": {"fixedColor": "green", "mode": "fixed"}}]
                }
            ]
        }
    }
    dashboard["dashboard"]["panels"].append(mem_timeseries)
    panel_id += 1

    # 2-3. CPU 온도 추이
    temp_timeseries = {
        "id": panel_id,
        "title": "CPU 온도 추이",
        "type": "timeseries",
        "gridPos": {"x": 16, "y": y_pos, "w": 8, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "cpu_temp")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({r with _value: r._value / 1000.0, _field: "온도"}))
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "celsius",
                "min": 30,
                "max": 85,
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 20,
                    "lineWidth": 2
                },
                "color": {"fixedColor": "red", "mode": "fixed"},
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 50},
                        {"color": "orange", "value": 65},
                        {"color": "red", "value": 80}
                    ]
                }
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(temp_timeseries)
    panel_id += 1

    y_pos += 8

    # ===========================
    # 3행: 네트워크 및 디스크 I/O
    # ===========================

    # 3-1. 네트워크 트래픽
    net_timeseries = {
        "id": panel_id,
        "title": "네트워크 트래픽",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": y_pos, "w": 12, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "net")
  |> filter(fn: (r) => r._field == "bytes_recv" or r._field == "bytes_sent")
  |> filter(fn: (r) => r.interface == "eth0" or r.interface == "tailscale0")
  |> derivative(unit: 1s, nonNegative: true)
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "Bps",
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 20,
                    "lineWidth": 2
                }
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(net_timeseries)
    panel_id += 1

    # 3-2. 디스크 I/O
    diskio_timeseries = {
        "id": panel_id,
        "title": "디스크 I/O (SD카드)",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": y_pos, "w": 12, "h": 8},
        "targets": [{
            "datasource": {"type": "influxdb", "uid": "influxdb"},
            "query": '''
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "diskio")
  |> filter(fn: (r) => r._field == "read_bytes" or r._field == "write_bytes")
  |> derivative(unit: 1s, nonNegative: true)
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
            ''',
            "refId": "A"
        }],
        "fieldConfig": {
            "defaults": {
                "unit": "Bps",
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 20,
                    "lineWidth": 2
                }
            }
        },
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"}
        }
    }
    dashboard["dashboard"]["panels"].append(diskio_timeseries)
    panel_id += 1

    return dashboard


def upload_dashboard(dashboard_json):
    """Grafana에 대시보드 업로드"""
    url = f"{GRAFANA_URL}/api/dashboards/db"
    headers = {"Content-Type": "application/json"}
    auth = (GRAFANA_USER, GRAFANA_PASSWORD)

    try:
        response = requests.post(url, json=dashboard_json, headers=headers, auth=auth, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"대시보드 업로드 성공!")
            print(f"  - UID: {result.get('uid', 'N/A')}")
            print(f"  - URL: {GRAFANA_URL}{result.get('url', '')}")
            return True
        else:
            print(f"업로드 실패: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"오류: {e}")
        return False


def main():
    print("=" * 50)
    print("시스템 헬스 대시보드 생성")
    print("=" * 50)

    dashboard = create_dashboard()

    # JSON 파일 저장
    output_path = "/raspi/WD4T/03_outputs/system_health_dashboard.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    print(f"\nJSON 저장: {output_path}")

    # Grafana 업로드
    print("\nGrafana에 업로드 중...")
    upload_dashboard(dashboard)


if __name__ == "__main__":
    main()
