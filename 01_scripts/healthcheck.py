#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 헬스체크 스크립트
========================
- 환경변수 설정 확인
- InfluxDB 연결 테스트
- Grafana 연결 테스트
- 데이터 파일 존재 확인

실행 방법:
    source .venv/bin/activate
    python 01_scripts/healthcheck.py
"""

import os
import sys

# 설정 로드
try:
    from config import config
except ImportError:
    print("❌ config.py를 찾을 수 없습니다.")
    sys.exit(1)


def check_env_vars():
    """환경변수 설정 확인"""
    print("\n[1/4] 환경변수 확인")
    print("-" * 50)

    checks = {
        'NAVER_CLIENT_ID': config.NAVER_CLIENT_ID,
        'NAVER_CLIENT_SECRET': config.NAVER_CLIENT_SECRET,
        'BOK_API_KEY': config.BOK_API_KEY,
        'FRED_API_KEY': config.FRED_API_KEY,
        'INFLUXDB_TOKEN': config.INFLUXDB_TOKEN,
        'GRAFANA_PASSWORD': config.GRAFANA_PASSWORD,
    }

    all_ok = True
    for name, value in checks.items():
        if value:
            print(f"  ✅ {name}: 설정됨")
        else:
            print(f"  ❌ {name}: 미설정")
            all_ok = False

    return all_ok


def check_influxdb():
    """InfluxDB 연결 테스트"""
    print("\n[2/4] InfluxDB 연결 테스트")
    print("-" * 50)

    try:
        from influxdb_client import InfluxDBClient

        client = InfluxDBClient(
            url=config.INFLUXDB_URL,
            token=config.INFLUXDB_TOKEN,
            org=config.INFLUXDB_ORG
        )

        # 헬스 체크
        health = client.health()
        if health.status == "pass":
            print(f"  ✅ InfluxDB 연결 성공")
            print(f"     URL: {config.INFLUXDB_URL}")
            print(f"     Bucket: {config.INFLUXDB_BUCKET}")

            # 데이터 건수 확인
            query_api = client.query_api()
            query = f'''
            from(bucket: "{config.INFLUXDB_BUCKET}")
              |> range(start: -15y)
              |> count()
              |> group()
              |> sum(column: "_value")
            '''
            try:
                result = query_api.query(query)
                for table in result:
                    for record in table.records:
                        print(f"     총 데이터: {record.get_value():,}건")
            except Exception:
                print(f"     데이터 건수 확인 실패")

            client.close()
            return True
        else:
            print(f"  ❌ InfluxDB 상태: {health.status}")
            client.close()
            return False

    except ImportError:
        print("  ❌ influxdb-client 미설치")
        print("     pip install influxdb-client")
        return False
    except Exception as e:
        print(f"  ❌ InfluxDB 연결 실패: {e}")
        return False


def check_grafana():
    """Grafana 연결 테스트"""
    print("\n[3/4] Grafana 연결 테스트")
    print("-" * 50)

    try:
        import requests

        url = f"{config.GRAFANA_URL}/api/health"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            print(f"  ✅ Grafana 연결 성공")
            print(f"     URL: {config.GRAFANA_URL}")

            # 로그인 테스트
            auth_url = f"{config.GRAFANA_URL}/api/org"
            auth_response = requests.get(
                auth_url,
                auth=(config.GRAFANA_USER, config.GRAFANA_PASSWORD),
                timeout=5
            )

            if auth_response.status_code == 200:
                org_info = auth_response.json()
                print(f"     Organization: {org_info.get('name', 'N/A')}")
                return True
            else:
                print(f"  ⚠️  Grafana 인증 실패 (HTTP {auth_response.status_code})")
                return False
        else:
            print(f"  ❌ Grafana 응답 실패 (HTTP {response.status_code})")
            return False

    except ImportError:
        print("  ❌ requests 미설치")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Grafana 연결 실패: {config.GRAFANA_URL}")
        return False
    except Exception as e:
        print(f"  ❌ Grafana 오류: {e}")
        return False


def check_data_files():
    """데이터 파일 존재 확인"""
    print("\n[4/4] 데이터 파일 확인")
    print("-" * 50)

    files = [
        (f"{config.DATA_DIR}/stock_kr_2010_2025.csv", "한국 주가"),
        (f"{config.DATA_DIR}/stock_us_2010_2025.csv", "미국 주가"),
        (f"{config.DATA_DIR}/economy_fred_2010_2025.csv", "FRED 경제지표"),
        (f"{config.DATA_DIR}/economy_ecos_2010_2025.csv", "ECOS 경제지표"),
    ]

    all_ok = True
    for filepath, name in files:
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  ✅ {name}: {size_mb:.1f}MB")
        else:
            print(f"  ❌ {name}: 파일 없음")
            all_ok = False

    return all_ok


def main():
    """메인 함수"""
    print("=" * 60)
    print("시스템 헬스체크")
    print("=" * 60)

    results = {
        '환경변수': check_env_vars(),
        'InfluxDB': check_influxdb(),
        'Grafana': check_grafana(),
        '데이터파일': check_data_files(),
    }

    print("\n" + "=" * 60)
    print("헬스체크 결과")
    print("=" * 60)

    all_ok = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_ok = False

    print()
    if all_ok:
        print("🎉 모든 검사를 통과했습니다!")
        return 0
    else:
        print("⚠️  일부 검사가 실패했습니다. 위의 오류를 확인하세요.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
