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
    source .venv/bin/activate
    python 01_scripts/01_data_collector.py

Cron 스케줄:
    0 8 * * * cd /실제/프로젝트/경로/econ && ./.venv/bin/python 01_scripts/01_data_collector.py
    0 16 * * 1-5 cd /실제/프로젝트/경로/econ && ./.venv/bin/python 01_scripts/01_data_collector.py
    0 20 * * * cd /실제/프로젝트/경로/econ && ./.venv/bin/python 01_scripts/01_data_collector.py

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
from datetime import datetime, timezone, timedelta
import pytz

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


def is_kr_ticker(ticker: str) -> bool:
    """한국 시장 티커 여부 (.KS/.KQ/지수 ^KS/^KQ)"""
    return ticker.endswith('.KS') or ticker.endswith('.KQ') or ticker.startswith('^K')


def get_target_trade_date(is_kr: bool, now_utc: datetime) -> datetime.date:
    """장 마감 여부에 따라 목표 거래일을 결정 (주말 보정 포함)"""
    kst = now_utc.astimezone(pytz.timezone('Asia/Seoul'))
    est = now_utc.astimezone(pytz.timezone('America/New_York'))

    if is_kr:
        # 한국 장 마감 15:30, 버퍼 10분
        if kst.time() < datetime.strptime("15:40", "%H:%M").time():
            target = kst.date() - timedelta(days=1)
        else:
            target = kst.date()
    else:
        # 미국 장 마감 16:00 ET, 버퍼 10분
        if est.time() < datetime.strptime("16:10", "%H:%M").time():
            target = est.date() - timedelta(days=1)
        else:
            target = est.date()

    # 주말 보정 (휴일 캘린더 없으므로 토/일 → 최근 금요일)
    while target.weekday() >= 5:  # 5=토,6=일
        target -= timedelta(days=1)
    return target


def fetch_history_with_retry(ticker: str, period: str = "5d", max_retries: int = 3, delay: float = 2.0):
    """일반 용도 히스토리 조회 (경제지표 등에서 사용)"""
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if not hist.empty:
                return hist, None
            if attempt < max_retries - 1:
                time.sleep(delay)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                return None, str(e)[:80]
    return None, "no_data_after_retry"


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
def is_market_open_today():
    """
    오늘 시장이 열리는 날인지 확인
    - 토요일/일요일은 휴장
    - 공휴일은 별도 체크 필요 (현재는 주말만 체크)

    Returns:
        tuple: (한국장 오픈 여부, 미국장 오픈 여부)
    """
    from datetime import datetime
    today = datetime.now()
    weekday = today.weekday()  # 0=월, 6=일

    # 주말 체크 (토=5, 일=6)
    is_weekend = weekday >= 5

    # 한국은 현재 시간으로, 미국은 전일 기준
    kr_open = not is_weekend
    us_open = not is_weekend

    return kr_open, us_open


def fetch_stock_bar_with_retry(ticker: str, target_date, max_retries: int = 3, delay: float = 2.0):
    """목표 거래일의 일봉을 가져오고, 없으면 상태와 함께 반환"""
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)

            start = target_date
            end = target_date + timedelta(days=1)

            hist = stock.history(start=start, end=end, interval="1d", auto_adjust=False)

            # 백업: 최근 5일 조회 후 타겟 날짜 필터
            if hist.empty:
                hist = stock.history(period="5d", interval="1d", auto_adjust=False)

            if not hist.empty:
                df = hist.reset_index()
                df.rename(columns={'Date': 'date'}, inplace=True)
                df['bar_date'] = pd.to_datetime(df['date']).dt.tz_localize(None).dt.date

                # 타겟 날짜 일치 여부
                target_rows = df[df['bar_date'] == target_date]
                if not target_rows.empty:
                    return target_rows.iloc[-1], 'success', None

                # 타겟 없음 → 가장 최신 행 반환 (stale)
                latest = df.iloc[-1]
                return latest, 'stale', None

            if attempt < max_retries - 1:
                time.sleep(delay)

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                return None, 'error', str(e)[:80]

    return None, 'no_data', 'no_data_after_retry'


def collect_stock_data():
    """장마감 확정 일봉만 수집하고 당일 여부 검증"""
    print("\n[주가 수집]")
    start_time = time.time()

    all_tickers = {**config.KR_TICKERS, **config.US_TICKERS}
    stock_rows = []
    success_count = 0
    fail_count = 0
    stale_count = 0
    failed_tickers = []

    now_utc = datetime.now(timezone.utc)

    for name, ticker in all_tickers.items():
        is_kr = is_kr_ticker(ticker)
        target_date = get_target_trade_date(is_kr, now_utc)

        bar, status, error = fetch_stock_bar_with_retry(
            ticker, target_date, max_retries=3, delay=2.0
        )

        if bar is not None and status == 'success':
            stock_rows.append({
                "timestamp": get_timestamp(),
                "bar_date": target_date,
                "name": name,
                "ticker": ticker,
                "open": float(bar['Open']),
                "high": float(bar['High']),
                "low": float(bar['Low']),
                "close": float(bar['Close']),
                "adj_close": float(bar.get('Adj Close', bar['Close'])),
                "volume": int(bar['Volume']),
                "status": "success"
            })
            success_count += 1
        elif bar is not None and status == 'stale':
            stock_rows.append({
                "timestamp": get_timestamp(),
                "bar_date": bar['bar_date'],
                "name": name,
                "ticker": ticker,
                "open": float(bar['Open']),
                "high": float(bar['High']),
                "low": float(bar['Low']),
                "close": float(bar['Close']),
                "adj_close": float(bar.get('Adj Close', bar['Close'])),
                "volume": int(bar['Volume']),
                "status": "stale"
            })
            stale_count += 1
        else:
            fail_count += 1
            failed_tickers.append(f"{name}({ticker})")
            stock_rows.append({
                "timestamp": get_timestamp(),
                "bar_date": target_date,
                "name": name,
                "ticker": ticker,
                "open": "N/A",
                "high": "N/A",
                "low": "N/A",
                "close": "N/A",
                "adj_close": "N/A",
                "volume": "N/A",
                "status": f"error: {error or 'no_data'}"
            })

    total = len(all_tickers)
    print(f"  수집 완료: {success_count}/{total} 성공, {stale_count} 지연, {fail_count} 실패")

    # CSV 저장 (bar_date + ticker 키 중복 제거 후 append)
    if stock_rows:
        df_new = pd.DataFrame(stock_rows)
        filepath = f"{config.STOCK_DIR}/stock.csv"
        if os.path.exists(filepath):
            df_old = pd.read_csv(filepath)
            df = pd.concat([df_old, df_new], ignore_index=True)
            df.drop_duplicates(subset=["bar_date", "ticker"], keep="last", inplace=True)
        else:
            df = df_new
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"  CSV 저장/갱신: {len(df_new)}건 (중복 제거 후 총 {len(df)}행)")

        # InfluxDB 저장 (성공+stale 모두 기록, status 필드 포함)
        points = []
        for item in stock_rows:
            if item.get('status') in ('success', 'stale'):
                try:
                    dt = datetime.combine(item['bar_date'], datetime.min.time()).replace(tzinfo=timezone.utc)
                    p = Point("stock_prices") \
                        .tag("name", item['name']) \
                        .tag("ticker", item['ticker']) \
                        .field("open", float(item['open'])) \
                        .field("high", float(item['high'])) \
                        .field("low", float(item['low'])) \
                        .field("close", float(item['close'])) \
                        .field("adj_close", float(item['adj_close'])) \
                        .field("volume", int(item['volume'])) \
                        .field("status_code", 1 if item['status'] == 'success' else 0) \
                        .time(dt, WritePrecision.S)
                    points.append(p)
                except (ValueError, TypeError):
                    continue
        write_to_influx(points, "주가")

    # 로그/알림
    execution_time_ms = int((time.time() - start_time) * 1000)
    log_collection_result("stock", success_count, fail_count, execution_time_ms)

    update_collection_result(
        "stock", success_count, fail_count, execution_time_ms,
        no_data=stale_count, failed_items=failed_tickers,
        delayed_items=[f"{row['name']} ({row['bar_date']})" for row in stock_rows if row.get('status') == 'stale']
    )

    if stale_count > 0:
        _collection_results['market_info'] = '일봉 게시 지연 발생'


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
    - 최근 7일/3개월 기간 조회로 데이터 없음 방지
    """
    print("\n[경제지표 수집]")
    start_time = time.time()
    success_count = 0
    fail_count = 0
    delayed_count = 0  # 과거 데이터 사용 카운트
    failed_indicators = []  # 실패한 지표 목록
    delayed_indicators = []  # 과거 데이터 사용 지표 목록

    if not config.BOK_API_KEY:
        print("  ❌ BOK_API_KEY가 설정되지 않았습니다.")
        log_collection_result("economy", 0, 1, 0)
        return

    bok_data = []
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')

    # 최근 7일 기간 (일간 데이터용)
    seven_days_ago = (today - pd.Timedelta(days=7)).strftime('%Y%m%d')

    # 최근 3개월 기간 (월간 데이터용)
    three_months_ago = (today - pd.Timedelta(days=90)).strftime('%Y%m')
    this_month = today.strftime('%Y%m')

    # 수집할 지표 정의 (기간을 넓혀서 조회)
    # (API경로, 지표명, 주기)
    indicators = [
        (f"731Y001/D/{seven_days_ago}/{today_str}/0000001", "원/달러 환율", "D"),
        (f"731Y001/D/{seven_days_ago}/{today_str}/0000002", "원/엔 환율", "D"),
        (f"731Y001/D/{seven_days_ago}/{today_str}/0000003", "원/유로 환율", "D"),
        (f"722Y001/M/{three_months_ago}/{this_month}/0101000", "기준금리", "M"),
        (f"722Y001/D/{seven_days_ago}/{today_str}/0101000", "콜금리", "D"),
    ]

    for api_path, indicator_name, period in indicators:
        # 최근 10건 조회 (기간 내 가장 최신 데이터 사용)
        url = f"https://ecos.bok.or.kr/api/StatisticSearch/{config.BOK_API_KEY}/json/kr/1/10/{api_path}"

        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if "StatisticSearch" in data and "row" in data["StatisticSearch"]:
                    rows = data["StatisticSearch"]["row"]
                    # 가장 최근 데이터 사용 (마지막 row)
                    row = rows[-1]
                    data_date = row["TIME"]

                    # 오늘 날짜와 비교하여 지연 여부 확인
                    is_delayed = False
                    if period == "D":
                        is_delayed = (data_date != today_str)
                    elif period == "M":
                        is_delayed = (data_date != this_month)

                    status = "success_delayed" if is_delayed else "success"

                    bok_data.append({
                        "timestamp": get_timestamp(),
                        "indicator": indicator_name,
                        "value": row["DATA_VALUE"],
                        "date": data_date,
                        "status": status
                    })
                    success_count += 1

                    # 날짜 포맷팅 (출력용)
                    if len(data_date) == 8:  # YYYYMMDD
                        display_date = f"{data_date[4:6]}/{data_date[6:8]}"
                    else:  # YYYYMM
                        display_date = f"{data_date[4:6]}월"

                    if is_delayed:
                        delayed_count += 1
                        delayed_indicators.append(f"{indicator_name}({display_date})")
                        print(f"  {indicator_name}: {row['DATA_VALUE']} (📅 {display_date} 기준)")
                    else:
                        print(f"  {indicator_name}: {row['DATA_VALUE']}")
                else:
                    # 기간 내 데이터 없음 = 실패
                    bok_data.append({
                        "timestamp": get_timestamp(),
                        "indicator": indicator_name,
                        "value": "N/A", "date": today_str,
                        "status": "no_data"
                    })
                    fail_count += 1
                    failed_indicators.append(indicator_name)
                    print(f"  {indicator_name}: 데이터 없음")
            else:
                bok_data.append({
                    "timestamp": get_timestamp(),
                    "indicator": indicator_name,
                    "value": "N/A", "date": today_str,
                    "status": f"error_code_{response.status_code}"
                })
                fail_count += 1
                failed_indicators.append(indicator_name)
                print(f"  {indicator_name}: API 오류 ({response.status_code})")

        except Exception as e:
            bok_data.append({
                "timestamp": get_timestamp(),
                "indicator": indicator_name,
                "value": "N/A", "date": today_str,
                "status": f"error: {str(e)[:50]}"
            })
            fail_count += 1
            failed_indicators.append(indicator_name)
            print(f"  {indicator_name}: 오류 - {e}")

    # yfinance로 원자재 데이터 수집 (WTI 유가, 금 선물)
    commodity_tickers = {
        "WTI 유가": "CL=F",
        "금 선물": "GC=F"
    }

    for commodity_name, ticker in commodity_tickers.items():
        try:
            hist, error = fetch_history_with_retry(ticker, max_retries=2, delay=1.0)

            if hist is not None and not hist.empty:
                # 가장 최근 데이터 사용
                last_date = hist.index[-1]
                close_price = round(hist["Close"].iloc[-1], 2)

                # 날짜 포맷팅
                data_date = last_date.strftime('%Y%m%d')
                display_date = last_date.strftime('%m/%d')
                is_delayed = (data_date != today_str)

                status = "success_delayed" if is_delayed else "success"

                bok_data.append({
                    "timestamp": get_timestamp(),
                    "indicator": commodity_name,
                    "value": close_price,
                    "date": data_date,
                    "status": status
                })
                success_count += 1

                if is_delayed:
                    delayed_count += 1
                    delayed_indicators.append(f"{commodity_name}({display_date})")
                    print(f"  {commodity_name}: ${close_price} (📅 {display_date} 기준, yfinance)")
                else:
                    print(f"  {commodity_name}: ${close_price} (yfinance)")
            else:
                bok_data.append({
                    "timestamp": get_timestamp(),
                    "indicator": commodity_name,
                    "value": "N/A", "date": today_str,
                    "status": f"error: {error or 'no_data'}"
                })
                fail_count += 1
                failed_indicators.append(commodity_name)
                print(f"  {commodity_name}: 데이터 없음 (yfinance)")

        except Exception as e:
            bok_data.append({
                "timestamp": get_timestamp(),
                "indicator": commodity_name,
                "value": "N/A", "date": today_str,
                "status": f"error: {str(e)[:50]}"
            })
            fail_count += 1
            failed_indicators.append(commodity_name)
            print(f"  {commodity_name}: 오류 - {e}")

    # 총 지표 수 업데이트 (ECOS + yfinance)
    total_indicators = len(indicators) + len(commodity_tickers)

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
            # success 또는 success_delayed 모두 저장
            if not item.get('status', '').startswith('success'):
                continue
            try:
                date_str = str(item['date'])
                if len(date_str) == 8:  # YYYYMMDD
                    dt = datetime.strptime(date_str, '%Y%m%d').replace(hour=12, tzinfo=timezone.utc)
                    period_tag = "daily"
                elif len(date_str) == 6:  # YYYYMM
                    dt = datetime.strptime(date_str + '01', '%Y%m%d').replace(hour=12, tzinfo=timezone.utc)
                    period_tag = "monthly"
                else:
                    continue

                p = Point("economic_indicators") \
                    .tag("indicator", item['indicator']) \
                    .tag("period", period_tag) \
                    .field("value", float(item['value'])) \
                    .time(dt, WritePrecision.S)
                points.append(p)
            except (ValueError, TypeError):
                continue
        write_to_influx(points, "경제지표")

    # 결과 출력
    print(f"  수집 완료: {success_count}/{total_indicators}개 지표")
    if delayed_count > 0:
        print(f"  📅 과거 데이터 사용: {delayed_count}개")
    if failed_indicators:
        print(f"  ⚠️ 실패 지표: {', '.join(failed_indicators)}")

    # 수집 로그 저장
    execution_time_ms = int((time.time() - start_time) * 1000)
    log_collection_result("economy", success_count, fail_count, execution_time_ms)

    # Telegram 알림용 결과 업데이트 (과거 데이터 사용 정보 포함)
    update_collection_result(
        "economy", success_count, fail_count, execution_time_ms,
        no_data=delayed_count, failed_items=failed_indicators,
        delayed_items=delayed_indicators
    )


# =============================================================================
# 메인 실행
# =============================================================================

# 수집 결과를 저장할 전역 변수 (각 함수에서 업데이트)
_collection_results = {
    'news': {'success': 0, 'fail': 0, 'no_data': 0, 'time_ms': 0},
    'stock': {'success': 0, 'fail': 0, 'no_data': 0, 'time_ms': 0},
    'economy': {'success': 0, 'fail': 0, 'no_data': 0, 'time_ms': 0},
    'total_time_ms': 0,
    'has_error': False,
    'errors': [],
    'failed_items': [],
    'delayed_items': [],  # 과거 데이터 사용 항목 (날짜 포함)
    'market_info': ''
}


def update_collection_result(task: str, success: int, fail: int, time_ms: int,
                             no_data: int = 0, errors: list = None, failed_items: list = None,
                             delayed_items: list = None):
    """
    수집 결과 업데이트 (Telegram 알림용)

    Args:
        task: 작업명 (news, stock, economy)
        success: 성공 건수
        fail: 실패 건수 (실제 에러)
        time_ms: 실행 시간 (ms)
        no_data: 휴장/과거 데이터 사용 건수
        errors: 에러 메시지 리스트
        delayed_items: 과거 데이터 사용 지표 리스트 (날짜 포함)
        failed_items: 실패한 항목 이름 리스트
    """
    global _collection_results
    _collection_results[task] = {
        'success': success,
        'fail': fail,
        'no_data': no_data,
        'time_ms': time_ms
    }
    # 실제 에러가 있을 때만 has_error 설정 (휴장/과거데이터는 제외)
    if fail > 0:
        _collection_results['has_error'] = True
    if errors:
        _collection_results['errors'].extend(errors[:3])
    if failed_items:
        _collection_results['failed_items'].extend(failed_items[:5])
    if delayed_items:
        _collection_results['delayed_items'].extend(delayed_items[:7])


def collect_all():
    """전체 데이터 수집 실행"""
    global _collection_results

    # 결과 초기화
    _collection_results = {
        'news': {'success': 0, 'fail': 0, 'no_data': 0, 'time_ms': 0},
        'stock': {'success': 0, 'fail': 0, 'no_data': 0, 'time_ms': 0},
        'economy': {'success': 0, 'fail': 0, 'no_data': 0, 'time_ms': 0},
        'total_time_ms': 0,
        'has_error': False,
        'errors': [],
        'delayed_items': [],
        'failed_items': [],
        'market_info': ''
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
