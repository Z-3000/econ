#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 수집기 (Data Collector)
==============================
주가, 경제지표, 뉴스를 수집하여 CSV와 InfluxDB에 저장

수집 대상:
- 뉴스: 네이버 검색 API (4개 키워드)
- 주가: yfinance (한국 27개 + 미국 41개 = 68개 종목)
- 경제지표: 한국은행 ECOS API (환율, 금리 등)

실행 방법:
    # 가상환경 활성화 후 실행
    source ~/influx_venv/bin/activate
    python /raspi/WD4T/01_scripts/data_collector.py

Cron 스케줄:
    0 8 * * * /home/raspi/influx_venv/bin/python /raspi/WD4T/01_scripts/data_collector.py
    0 16 * * 1-5 /home/raspi/influx_venv/bin/python /raspi/WD4T/01_scripts/data_collector.py
    0 20 * * * /home/raspi/influx_venv/bin/python /raspi/WD4T/01_scripts/data_collector.py

Author: [Your Name]
Created: 2025-11
Updated: 2025-12-03
"""

import os
import re
import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone

# 설정 모듈에서 로드
from config import config

# 수집 로그 모듈
from collection_logger import log_collection_result

# Telegram 알림 모듈
from notifier import send_collection_result as notify_telegram

# InfluxDB 클라이언트 (선택적 import)
try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    print("경고: influxdb-client 미설치. CSV만 저장됩니다.")


# =============================================================================
# 디렉터리 생성
# =============================================================================
os.makedirs(config.NEWS_DIR, exist_ok=True)
os.makedirs(config.STOCK_DIR, exist_ok=True)
os.makedirs(config.ECONOMY_DIR, exist_ok=True)


# =============================================================================
# 유틸리티 함수
# =============================================================================
def get_timestamp():
    """현재 타임스탬프 반환 (KST)"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clean_html(text):
    """HTML 태그 제거"""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', str(text))


# =============================================================================
# InfluxDB 클라이언트
# =============================================================================
def get_influx_client():
    """InfluxDB 클라이언트 반환"""
    if not INFLUXDB_AVAILABLE:
        return None
    if not config.INFLUXDB_TOKEN:
        print("경고: INFLUXDB_TOKEN이 설정되지 않았습니다.")
        return None
    return InfluxDBClient(
        url=config.INFLUXDB_URL,
        token=config.INFLUXDB_TOKEN,
        org=config.INFLUXDB_ORG
    )


def write_to_influx(points, data_type="data"):
    """
    InfluxDB에 데이터 저장 (공통 함수)

    Args:
        points: Point 객체 리스트
        data_type: 로그 출력용 데이터 타입명
    """
    if not INFLUXDB_AVAILABLE or not points:
        return

    client = get_influx_client()
    if not client:
        return

    try:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=config.INFLUXDB_BUCKET, record=points)
        print(f"  InfluxDB {data_type} 저장: {len(points)}건")
    except Exception as e:
        print(f"  InfluxDB {data_type} 저장 오류: {e}")
    finally:
        client.close()


# =============================================================================
# 1. 뉴스 수집 (네이버 검색 API)
# =============================================================================
def collect_naver_news():
    """
    네이버 검색 API로 뉴스 수집

    - 키워드: 경제, 부동산, 반도체, 코스피
    - 키워드당 5건씩 수집
    - CSV 파일에 append
    - InfluxDB에 저장
    """
    print("\n[뉴스 수집]")
    start_time = time.time()
    success_count = 0
    fail_count = 0

    if not config.NAVER_CLIENT_ID or not config.NAVER_CLIENT_SECRET:
        print("  ❌ 네이버 API 키가 설정되지 않았습니다.")
        log_collection_result("news", 0, 1, 0)
        return

    all_news = []

    for keyword in config.NEWS_KEYWORDS:
        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            "X-Naver-Client-Id": config.NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": config.NAVER_CLIENT_SECRET
        }
        params = {"query": keyword, "display": 5, "sort": "sim"}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                items = response.json().get("items", [])
                for item in items:
                    all_news.append({
                        "timestamp": get_timestamp(),
                        "keyword": keyword,
                        "title": item["title"],
                        "link": item["link"],
                        "description": item["description"],
                        "pubDate": item["pubDate"],
                        "status": "success"
                    })
                success_count += len(items)
                print(f"  {keyword}: {len(items)}건 수집")
            else:
                all_news.append({
                    "timestamp": get_timestamp(),
                    "keyword": keyword,
                    "title": "N/A", "link": "N/A", "description": "N/A", "pubDate": "N/A",
                    "status": f"error_code_{response.status_code}"
                })
                fail_count += 1
                print(f"  {keyword}: API 오류 (상태코드 {response.status_code})")

        except Exception as e:
            all_news.append({
                "timestamp": get_timestamp(),
                "keyword": keyword,
                "title": "N/A", "link": "N/A", "description": "N/A", "pubDate": "N/A",
                "status": f"error: {str(e)[:50]}"
            })
            fail_count += 1
            print(f"  {keyword}: 오류 - {e}")

    # CSV 저장
    if all_news:
        df = pd.DataFrame(all_news)
        filepath = f"{config.NEWS_DIR}/news.csv"
        header = not os.path.exists(filepath)
        df.to_csv(filepath, mode='a', header=header, index=False, encoding='utf-8-sig')
        print(f"  CSV 저장: {len(all_news)}건")

        # InfluxDB 저장
        points = []
        for item in all_news:
            if item.get('status') != 'success':
                continue
            try:
                p = Point("news") \
                    .tag("keyword", item['keyword']) \
                    .field("title", clean_html(item.get('title', ''))[:200]) \
                    .field("description", clean_html(item.get('description', ''))[:500]) \
                    .field("link", item.get('link', '')[:500]) \
                    .field("count", 1) \
                    .time(datetime.now(timezone.utc), WritePrecision.S)
                points.append(p)
            except (ValueError, TypeError):
                continue
        write_to_influx(points, "뉴스")

    # 수집 로그 저장
    execution_time_ms = int((time.time() - start_time) * 1000)
    log_collection_result("news", success_count, fail_count, execution_time_ms)

    # Telegram 알림용 결과 업데이트
    update_collection_result("news", success_count, fail_count, execution_time_ms)


# =============================================================================
# 2. 주가 수집 (yfinance)
# =============================================================================
def collect_stock_data():
    """
    yfinance로 주가 데이터 수집

    - 한국: 27개 종목 (지수 2 + ETF 9 + 개별 16)
    - 미국: 41개 종목 (지수 3 + ETF 38)
    - CSV 파일에 append
    - InfluxDB에 저장
    """
    print("\n[주가 수집]")
    start_time = time.time()

    # 한국 + 미국 종목 병합
    all_tickers = {**config.KR_TICKERS, **config.US_TICKERS}
    stock_data = []
    success_count = 0
    fail_count = 0

    for name, ticker in all_tickers.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")

            if not hist.empty:
                stock_data.append({
                    "timestamp": get_timestamp(),
                    "name": name,
                    "ticker": ticker,
                    "open": hist["Open"].iloc[-1],
                    "high": hist["High"].iloc[-1],
                    "low": hist["Low"].iloc[-1],
                    "close": hist["Close"].iloc[-1],
                    "volume": int(hist["Volume"].iloc[-1]),
                    "status": "success"
                })
                success_count += 1
            else:
                stock_data.append({
                    "timestamp": get_timestamp(),
                    "name": name, "ticker": ticker,
                    "open": "N/A", "high": "N/A", "low": "N/A", "close": "N/A", "volume": "N/A",
                    "status": "no_data"
                })
                fail_count += 1

        except Exception as e:
            stock_data.append({
                "timestamp": get_timestamp(),
                "name": name, "ticker": ticker,
                "open": "N/A", "high": "N/A", "low": "N/A", "close": "N/A", "volume": "N/A",
                "status": f"error: {str(e)[:50]}"
            })
            fail_count += 1

    print(f"  수집 완료: {success_count}/{len(all_tickers)}개 종목")

    # CSV 저장
    if stock_data:
        df = pd.DataFrame(stock_data)
        filepath = f"{config.STOCK_DIR}/stock.csv"
        header = not os.path.exists(filepath)
        df.to_csv(filepath, mode='a', header=header, index=False, encoding='utf-8-sig')
        print(f"  CSV 저장: {len(stock_data)}건")

        # InfluxDB 저장
        points = []
        for item in stock_data:
            if item.get('status') != 'success':
                continue
            try:
                dt = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
                p = Point("stock_prices") \
                    .tag("name", item['name']) \
                    .tag("ticker", item['ticker']) \
                    .field("open", float(item['open'])) \
                    .field("high", float(item['high'])) \
                    .field("low", float(item['low'])) \
                    .field("close", float(item['close'])) \
                    .field("volume", int(item['volume'])) \
                    .time(dt, WritePrecision.S)
                points.append(p)
            except (ValueError, TypeError):
                continue
        write_to_influx(points, "주가")

    # 수집 로그 저장
    execution_time_ms = int((time.time() - start_time) * 1000)
    log_collection_result("stock", success_count, fail_count, execution_time_ms)

    # Telegram 알림용 결과 업데이트
    update_collection_result("stock", success_count, fail_count, execution_time_ms)


# =============================================================================
# 3. 경제지표 수집 (한국은행 ECOS API)
# =============================================================================
def collect_bok_data():
    """
    한국은행 ECOS API로 경제지표 수집

    - 환율: 원/달러, 원/엔, 원/유로
    - 금리: 기준금리, 콜금리
    - 원자재: 두바이유, 금
    - CSV 파일에 append
    - InfluxDB에 저장
    """
    print("\n[경제지표 수집]")
    start_time = time.time()
    success_count = 0
    fail_count = 0

    if not config.BOK_API_KEY:
        print("  ❌ BOK_API_KEY가 설정되지 않았습니다.")
        log_collection_result("economy", 0, 1, 0)
        return

    bok_data = []
    today = datetime.now().strftime('%Y%m%d')
    this_month = datetime.now().strftime('%Y%m')

    # 수집할 지표 정의
    indicators = [
        (f"731Y001/D/{today}/{today}/0000001", "원/달러 환율"),
        (f"731Y001/D/{today}/{today}/0000002", "원/엔 환율"),
        (f"731Y001/D/{today}/{today}/0000003", "원/유로 환율"),
        (f"722Y001/M/{this_month}/{this_month}/0101000", "기준금리"),
        (f"902Y007/D/{today}/{today}/DUBAIOIL", "두바이유 가격"),
        (f"902Y007/D/{today}/{today}/GOLD", "금 시세"),
        (f"722Y001/D/{today}/{today}/0101000", "콜금리"),
    ]

    for api_path, indicator_name in indicators:
        url = f"https://ecos.bok.or.kr/api/StatisticSearch/{config.BOK_API_KEY}/json/kr/1/1/{api_path}"

        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if "StatisticSearch" in data and "row" in data["StatisticSearch"]:
                    row = data["StatisticSearch"]["row"][0]
                    bok_data.append({
                        "timestamp": get_timestamp(),
                        "indicator": indicator_name,
                        "value": row["DATA_VALUE"],
                        "date": row["TIME"],
                        "status": "success"
                    })
                    success_count += 1
                    print(f"  {indicator_name}: {row['DATA_VALUE']}")
                else:
                    bok_data.append({
                        "timestamp": get_timestamp(),
                        "indicator": indicator_name,
                        "value": "N/A", "date": today,
                        "status": "no_data"
                    })
                    fail_count += 1
            else:
                bok_data.append({
                    "timestamp": get_timestamp(),
                    "indicator": indicator_name,
                    "value": "N/A", "date": today,
                    "status": f"error_code_{response.status_code}"
                })
                fail_count += 1

        except Exception as e:
            bok_data.append({
                "timestamp": get_timestamp(),
                "indicator": indicator_name,
                "value": "N/A", "date": today,
                "status": f"error: {str(e)[:50]}"
            })
            fail_count += 1
            print(f"  {indicator_name}: 오류 - {e}")

    # CSV 저장
    if bok_data:
        df = pd.DataFrame(bok_data)
        filepath = f"{config.ECONOMY_DIR}/economy.csv"
        header = not os.path.exists(filepath)
        df.to_csv(filepath, mode='a', header=header, index=False, encoding='utf-8-sig')
        print(f"  CSV 저장: {len(bok_data)}건")

        # InfluxDB 저장
        points = []
        for item in bok_data:
            if item.get('status') != 'success':
                continue
            try:
                date_str = str(item['date'])
                if len(date_str) == 8:  # YYYYMMDD
                    dt = datetime.strptime(date_str, '%Y%m%d').replace(hour=12, tzinfo=timezone.utc)
                elif len(date_str) == 6:  # YYYYMM
                    dt = datetime.strptime(date_str + '01', '%Y%m%d').replace(hour=12, tzinfo=timezone.utc)
                else:
                    continue

                p = Point("economic_indicators") \
                    .tag("indicator", item['indicator']) \
                    .tag("period", "daily") \
                    .field("value", float(item['value'])) \
                    .time(dt, WritePrecision.S)
                points.append(p)
            except (ValueError, TypeError):
                continue
        write_to_influx(points, "경제지표")

    # 수집 로그 저장
    execution_time_ms = int((time.time() - start_time) * 1000)
    log_collection_result("economy", success_count, fail_count, execution_time_ms)

    # Telegram 알림용 결과 업데이트
    update_collection_result("economy", success_count, fail_count, execution_time_ms)


# =============================================================================
# 메인 실행
# =============================================================================

# 수집 결과를 저장할 전역 변수 (각 함수에서 업데이트)
_collection_results = {
    'news': {'success': 0, 'fail': 0, 'time_ms': 0},
    'stock': {'success': 0, 'fail': 0, 'time_ms': 0},
    'economy': {'success': 0, 'fail': 0, 'time_ms': 0},
    'total_time_ms': 0,
    'has_error': False,
    'errors': []
}


def update_collection_result(task: str, success: int, fail: int, time_ms: int, errors: list = None):
    """
    수집 결과 업데이트 (Telegram 알림용)

    Args:
        task: 작업명 (news, stock, economy)
        success: 성공 건수
        fail: 실패 건수
        time_ms: 실행 시간 (ms)
        errors: 에러 메시지 리스트
    """
    global _collection_results
    _collection_results[task] = {
        'success': success,
        'fail': fail,
        'time_ms': time_ms
    }
    if fail > 0:
        _collection_results['has_error'] = True
    if errors:
        _collection_results['errors'].extend(errors[:3])


def collect_all():
    """전체 데이터 수집 실행"""
    global _collection_results

    # 결과 초기화
    _collection_results = {
        'news': {'success': 0, 'fail': 0, 'time_ms': 0},
        'stock': {'success': 0, 'fail': 0, 'time_ms': 0},
        'economy': {'success': 0, 'fail': 0, 'time_ms': 0},
        'total_time_ms': 0,
        'has_error': False,
        'errors': []
    }

    print("=" * 60)
    print(f"데이터 수집 시작: {get_timestamp()}")
    print("=" * 60)

    total_start = time.time()

    collect_naver_news()
    collect_stock_data()
    collect_bok_data()

    # 전체 수집 로그 저장
    total_execution_ms = int((time.time() - total_start) * 1000)
    log_collection_result("total", 1, 0, total_execution_ms)

    # Telegram 알림 결과 업데이트
    _collection_results['total_time_ms'] = total_execution_ms

    print("\n" + "=" * 60)
    print(f"데이터 수집 완료: {get_timestamp()} (총 {total_execution_ms}ms)")
    print("=" * 60)

    # Telegram 알림 전송
    print("\n[Telegram 알림]")
    notify_telegram(_collection_results)


if __name__ == "__main__":
    collect_all()
