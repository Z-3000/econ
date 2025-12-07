#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grafana 대시보드 자동 업로드
"""

import requests
import json
import os

# 설정 (config.py에서 로드)
from config import config

# Grafana 설정 (환경변수에서 로드)
GRAFANA_URL = config.GRAFANA_URL
GRAFANA_USER = config.GRAFANA_USER
GRAFANA_PASSWORD = config.GRAFANA_PASSWORD

# 대시보드 JSON 파일
DASHBOARD_FILE = os.path.join(config.BASE_DIR, "03_outputs", "grafana_dashboard_final.json")

print("=" * 80)
print("Grafana 대시보드 자동 업로드")
print("=" * 80)

# 1. 대시보드 JSON 읽기
print("\n[1/3] 대시보드 JSON 읽기")
with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
    dashboard_json = json.load(f)

print(f"  ✅ 파일 읽기 완료: {DASHBOARD_FILE}")
print(f"  제목: {dashboard_json['dashboard']['title']}")
print(f"  패널 수: {len(dashboard_json['dashboard']['panels'])}개")

# 2. Grafana API로 업로드
print("\n[2/3] Grafana API 업로드")

# API 엔드포인트
url = f"{GRAFANA_URL}/api/dashboards/db"

# 업로드용 페이로드 (datasource UID 자동 매핑 포함)
payload = {
    "dashboard": dashboard_json["dashboard"],
    "overwrite": True,
    "message": "15년 히스토리 대시보드 (GDP 포함) - 자동 업로드"
}

try:
    response = requests.post(
        url,
        json=payload,
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    if response.status_code in [200, 201]:
        result = response.json()
        dashboard_url = f"{GRAFANA_URL}{result.get('url', '')}"

        print(f"  ✅ 대시보드 업로드 성공!")
        print(f"  Dashboard ID: {result.get('id')}")
        print(f"  Dashboard UID: {result.get('uid')}")
        print(f"  URL: {dashboard_url}")

        # 3. InfluxDB 데이터소스 UID 확인 및 업데이트
        print("\n[3/3] 데이터소스 확인")

        ds_url = f"{GRAFANA_URL}/api/datasources"
        ds_response = requests.get(
            ds_url,
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            timeout=10
        )

        if ds_response.status_code == 200:
            datasources = ds_response.json()
            influxdb_ds = None

            for ds in datasources:
                if ds.get('type') == 'influxdb':
                    influxdb_ds = ds
                    break

            if influxdb_ds:
                print(f"  ✅ InfluxDB 데이터소스 발견")
                print(f"  이름: {influxdb_ds.get('name')}")
                print(f"  UID: {influxdb_ds.get('uid')}")
                print(f"  URL: {influxdb_ds.get('url')}")
            else:
                print(f"  ⚠️  InfluxDB 데이터소스를 찾을 수 없습니다.")
                print(f"  Grafana에서 수동으로 InfluxDB 데이터소스를 추가하세요.")

        print("\n" + "=" * 80)
        print("대시보드 업로드 완료!")
        print("=" * 80)
        print(f"\n대시보드 접속: {dashboard_url}")
        print()

    else:
        print(f"  ❌ 업로드 실패 (HTTP {response.status_code})")
        print(f"  응답: {response.text}")

        if response.status_code == 401:
            print("\n해결 방법:")
            print("  1. Grafana 기본 비밀번호 확인 (admin/admin)")
            print("  2. 비밀번호 변경했다면 스크립트의 GRAFANA_PASSWORD 수정")
        elif response.status_code == 412:
            print("\n해결 방법:")
            print("  1. 'overwrite: true'로 기존 대시보드 덮어쓰기")
            print("  2. 또는 Grafana에서 기존 대시보드 삭제 후 재시도")

except requests.exceptions.ConnectionError:
    print(f"  ❌ Grafana 연결 실패")
    print(f"  Grafana가 실행 중인지 확인하세요: {GRAFANA_URL}")
    print(f"  명령어: systemctl status grafana-server")

except Exception as e:
    print(f"  ❌ 오류: {e}")
    import traceback
    traceback.print_exc()
