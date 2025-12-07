#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15년 히스토리 데이터 수집 스크립트 (2010-2025)
- 한국 주가: yfinance (27개 종목)
- 미국 주가 + ETF: yfinance (41개 종목)
- 한국 경제지표: ECOS API
- 미국 경제지표: FRED API
"""

import sys
import os
from datetime import datetime
import pandas as pd
import warnings
import argparse
import time
warnings.filterwarnings('ignore')

# ===========================
# 설정 (config.py에서 로드)
# ===========================
from config import config

BASE_DIR = config.BASE_DIR
ARCHIVE_DIR = config.ARCHIVE_DIR

# 디렉터리 생성
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# ===========================
# 종목 리스트 (DATACOLLECT.md 기준)
# ===========================

# 한국 주가 (yfinance 사용 - .KS 접미사)
KR_TICKERS = {
    # 지수
    '^KS11': '코스피',
    '^KQ11': '코스닥',

    # 한국 ETF
    '069500.KS': 'KODEX200',
    '229200.KS': 'KODEX 코스닥150',
    '360750.KS': 'TIGER 미국S&P500',
    '133690.KS': 'TIGER 미국나스닥100',
    '227560.KS': 'KODEX 배당가치',
    '269370.KS': 'TIGER 코리아배당다우존스',
    '114260.KS': 'KODEX 국고채3년',
    '132030.KS': 'KODEX 골드선물(H)',
    '453530.KS': 'KODEX 미국S&P500커버드콜OTM',

    # 개별종목 (16개)
    '005930.KS': '삼성전자',
    '000660.KS': 'SK하이닉스',
    '373220.KS': 'LG에너지솔루션',
    '207940.KS': '삼성바이오로직스',
    '005380.KS': '현대차',
    '105560.KS': 'KB금융',
    '005490.KS': 'POSCO홀딩스',
    '035420.KS': 'NAVER',
    '352820.KS': 'HYBE',
    '041510.KS': 'SM',
    '035900.KS': 'JYP Ent.',
    '259960.KS': '크래프톤',
    '036570.KS': '엔씨소프트',
    '035760.KS': 'CJ ENM',
    '079160.KS': 'CGV',
    '035720.KS': '카카오',
}

# 미국 주가 (yfinance 사용)
US_TICKERS = {
    # 지수
    '^GSPC': 'S&P500',
    '^IXIC': '나스닥',
    '^VIX': 'VIX',

    # 나스닥 ETF
    'QQQ': 'QQQ (Invesco QQQ Trust)',
    'QLD': 'ProShares Ultra QQQ (2x)',
    'TQQQ': 'ProShares UltraPro QQQ (3x)',

    # S&P500 ETF
    'SPY': 'SPDR S&P 500',
    'VOO': 'Vanguard S&P 500',
    'IVV': 'iShares Core S&P 500',
    'SSO': 'ProShares Ultra S&P500 (2x)',
    'UPRO': 'ProShares UltraPro S&P500 (3x)',
    'SPLG': 'SPDR Portfolio S&P 500',

    # 다우존스 ETF
    'DIA': 'SPDR Dow Jones',

    # 배당 ETF
    'SCHD': 'Schwab US Dividend Equity',
    'DGRO': 'iShares Core Dividend Growth',
    'SPHD': 'Invesco S&P 500 High Dividend',
    'JEPI': 'JPMorgan Equity Premium Income',
    'NUSI': 'Nationwide Risk-Managed Income',
    'MAIN': 'Main Street Capital',
    'GAIN': 'Gladstone Investment',
    'QYLD': 'Global X NASDAQ 100 Covered Call',
    'XYLD': 'Global X S&P 500 Covered Call',
    'RYLD': 'Global X Russell 2000 Covered Call',

    # 기술/반도체 레버리지
    'SOXL': 'Direxion Semiconductor Bull 3x',
    'TECL': 'Direxion Technology Bull 3x',

    # 광범위 지수
    'VTI': 'Vanguard Total Stock Market',
    'VT': 'Vanguard Total World Stock',
    'VEA': 'Vanguard FTSE Developed Markets',
    'EFA': 'iShares MSCI EAFE',
    'SPDW': 'SPDR Portfolio Developed World',
    'ITOT': 'iShares Core S&P Total US',

    # 인버스 (숏)
    'SQQQ': 'ProShares UltraPro Short QQQ (-3x)',
    'QID': 'ProShares UltraShort QQQ (-2x)',
    'PSQ': 'ProShares Short QQQ (-1x)',

    # 중국
    'CWEB': 'Direxion CSI China Internet 2x',

    # 채권/금
    'TLT': 'iShares 20+ Year Treasury',
    'GLD': 'SPDR Gold Trust',
}

# FRED 경제지표 (미국)
FRED_INDICATORS = {
    # 핵심 거시지표
    'GDP': '미국 GDP',
    'CPIAUCSL': '미국 CPI',
    'UNRATE': '미국 실업률',
    'PAYEMS': '미국 비농업 고용자수',

    # 금융시장
    'DFF': '연방기금금리',
    'DGS10': '미국 10년 국채금리',
    'VIXCLS': 'VIX',

    # 제조업/산업
    'INDPRO': '미국 산업생산지수',
    'MANEMP': '미국 제조업 고용자수',  # PMI 대체 지표

    # 환율
    'DEXKOUS': 'USD/KRW 환율',
}

# 한국은행 ECOS 경제지표 (한국)
ECOS_INDICATORS = {
    # 통계표코드, 항목코드, 주기, 지표명
    ('901Y009', '0', 'M'): '한국 소비자물가지수',  # 월별, 총지수 (2020=100)
    ('901Y010', '00', 'M'): '한국 CPI 특수분류',  # 월별, 총지수 (특수분류)
    ('200Y102', '', 'Q'): '한국 GDP 주요지표',  # 분기별, 실질GDP·명목GDP·성장률
}

# ===========================
# 함수: 한국 주가 수집 (yfinance)
# ===========================
def collect_kr_stock(ticker, name, start_date, end_date):
    """
    yfinance로 한국 주가 수집
    """
    return collect_us_stock(ticker, name, start_date, end_date)

# ===========================
# 함수: 미국 주가 수집 (yfinance)
# ===========================
def collect_us_stock(ticker, name, start_date, end_date):
    """
    yfinance로 미국 주가 수집
    """
    try:
        import yfinance as yf

        print(f"  수집 중: {name} ({ticker})", end=" ... ")

        df = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if df is None or len(df) == 0:
            print(f"❌ 데이터 없음")
            return None

        # 컬럼 표준화 (MultiIndex 처리)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        df = df.reset_index()
        df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)

        df['name'] = name
        df['ticker'] = ticker

        # 필수 컬럼만 선택
        df = df[['date', 'name', 'ticker', 'open', 'high', 'low', 'close', 'volume']]

        print(f"✅ {len(df)}건")
        return df

    except Exception as e:
        print(f"❌ 오류: {e}")
        return None

# ===========================
# 함수: FRED 경제지표 수집
# ===========================
def collect_fred_indicators(start_date, end_date):
    """
    FRED API로 미국 경제지표 수집
    """
    try:
        from fredapi import Fred

        print("\n[FRED 경제지표 수집]")
        fred = Fred(api_key=config.FRED_API_KEY)

        all_data = []

        for series_id, name in FRED_INDICATORS.items():
            try:
                print(f"  수집 중: {name} ({series_id})", end=" ... ")

                series = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)

                if series is None or len(series) == 0:
                    print(f"❌ 데이터 없음")
                    continue

                df = pd.DataFrame({
                    'date': series.index,
                    'indicator': name,
                    'value': series.values,
                    'series_id': series_id
                })

                all_data.append(df)
                print(f"✅ {len(df)}건")

                time.sleep(0.1)  # API 레이트 리밋 방지

            except Exception as e:
                print(f"❌ 오류: {e}")
                continue

        if len(all_data) == 0:
            return None

        return pd.concat(all_data, ignore_index=True)

    except Exception as e:
        print(f"❌ FRED API 오류: {e}")
        return None

# ===========================
# 함수: ECOS 경제지표 수집 (한국)
# ===========================
def collect_ecos_indicators(start_date, end_date):
    """
    한국은행 ECOS API로 한국 경제지표 수집
    """
    try:
        import requests

        print("\n[ECOS 경제지표 수집]")

        all_data = []

        for (stat_code, item_code, cycle), name in ECOS_INDICATORS.items():
            try:
                print(f"  수집 중: {name} ({stat_code}/{item_code})", end=" ... ")

                # 날짜 형식 변환 (cycle에 따라 다름)
                start_str = start_date.replace('-', '')
                end_str = end_date.replace('-', '')

                if cycle == 'M':  # 월별: YYYYMM
                    start_str = start_str[:6]  # YYYYMM
                    end_str = end_str[:6]
                elif cycle == 'Q':  # 분기: YYYYQQ
                    start_str = start_str[:4] + 'Q1'
                    end_str = end_str[:4] + 'Q4'
                # D(일별)은 YYYYMMDD 그대로 사용

                # ECOS API URL
                ecos_key = config.BOK_API_KEY
                if item_code:
                    url = (
                        f"https://ecos.bok.or.kr/api/StatisticSearch/{ecos_key}"
                        f"/json/kr/1/100000/{stat_code}/{cycle}/{start_str}/{end_str}/{item_code}"
                    )
                else:
                    url = (
                        f"https://ecos.bok.or.kr/api/StatisticSearch/{ecos_key}"
                        f"/json/kr/1/100000/{stat_code}/{cycle}/{start_str}/{end_str}"
                    )

                response = requests.get(url, timeout=30)
                data = response.json()

                if 'StatisticSearch' not in data or 'row' not in data['StatisticSearch']:
                    print(f"❌ 데이터 없음")
                    continue

                rows = data['StatisticSearch']['row']

                # 데이터 프레임 생성
                dates = []
                values = []

                for row in rows:
                    # 날짜 형식 변환
                    time_str = row['TIME']
                    if cycle == 'Q':  # 분기 (YYYYQ1)
                        year = time_str[:4]
                        quarter = time_str[5]
                        month = int(quarter) * 3
                        date_str = f"{year}-{month:02d}-01"
                    elif cycle == 'M':  # 월 (YYYYMM)
                        date_str = f"{time_str[:4]}-{time_str[4:6]}-01"
                    else:  # 일 (YYYYMMDD)
                        date_str = f"{time_str[:4]}-{time_str[4:6]}-{time_str[6:8]}"

                    dates.append(date_str)
                    values.append(float(row['DATA_VALUE']))

                df = pd.DataFrame({
                    'date': pd.to_datetime(dates),
                    'indicator': name,
                    'value': values,
                    'series_id': f"{stat_code}_{item_code}"
                })

                all_data.append(df)
                print(f"✅ {len(df)}건")

                time.sleep(0.2)  # API 부하 방지

            except Exception as e:
                print(f"❌ 오류: {e}")
                continue

        if len(all_data) == 0:
            return None

        return pd.concat(all_data, ignore_index=True)

    except Exception as e:
        print(f"❌ ECOS API 오류: {e}")
        return None

# ===========================
# 메인 함수
# ===========================
def main(start_date, end_date, output_suffix):
    """
    메인 수집 함수
    """
    print("=" * 80)
    print(f"15년 히스토리 데이터 수집: {start_date} ~ {end_date}")
    print("=" * 80)

    # 1. 한국 주가 수집
    print(f"\n[1/3] 한국 주가 수집 ({len(KR_TICKERS)}개 종목)")
    print("-" * 80)

    kr_stocks = []
    for ticker, name in KR_TICKERS.items():
        df = collect_kr_stock(ticker, name, start_date, end_date)
        if df is not None:
            kr_stocks.append(df)
        time.sleep(0.2)  # API 부하 방지

    if len(kr_stocks) > 0:
        kr_df = pd.concat(kr_stocks, ignore_index=True)
        kr_file = f"{ARCHIVE_DIR}/stock_kr_{output_suffix}.csv"
        kr_df.to_csv(kr_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ 한국 주가 저장: {kr_file} ({len(kr_df)}건)")
    else:
        print(f"\n❌ 한국 주가 수집 실패")

    # 2. 미국 주가 수집
    print(f"\n[2/3] 미국 주가 수집 ({len(US_TICKERS)}개 종목)")
    print("-" * 80)

    us_stocks = []
    for ticker, name in US_TICKERS.items():
        df = collect_us_stock(ticker, name, start_date, end_date)
        if df is not None:
            us_stocks.append(df)
        time.sleep(0.2)  # API 부하 방지

    if len(us_stocks) > 0:
        us_df = pd.concat(us_stocks, ignore_index=True)
        us_file = f"{ARCHIVE_DIR}/stock_us_{output_suffix}.csv"
        us_df.to_csv(us_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ 미국 주가 저장: {us_file} ({len(us_df)}건)")
    else:
        print(f"\n❌ 미국 주가 수집 실패")

    # 3. FRED 경제지표 수집 (미국)
    print(f"\n[3/4] FRED 경제지표 수집 ({len(FRED_INDICATORS)}개 지표)")
    print("-" * 80)

    fred_df = collect_fred_indicators(start_date, end_date)
    if fred_df is not None:
        fred_file = f"{ARCHIVE_DIR}/economy_fred_{output_suffix}.csv"
        fred_df.to_csv(fred_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ FRED 경제지표 저장: {fred_file} ({len(fred_df)}건)")
    else:
        print(f"\n❌ FRED 경제지표 수집 실패")

    # 4. ECOS 경제지표 수집 (한국)
    print(f"\n[4/4] ECOS 경제지표 수집 ({len(ECOS_INDICATORS)}개 지표)")
    print("-" * 80)

    ecos_df = collect_ecos_indicators(start_date, end_date)
    if ecos_df is not None:
        ecos_file = f"{ARCHIVE_DIR}/economy_ecos_{output_suffix}.csv"
        ecos_df.to_csv(ecos_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ ECOS 경제지표 저장: {ecos_file} ({len(ecos_df)}건)")
    else:
        print(f"\n❌ ECOS 경제지표 수집 실패")

    # 통합 요약
    print("\n" + "=" * 80)
    print("수집 완료!")
    print("=" * 80)

    total_records = 0
    if len(kr_stocks) > 0:
        print(f"  한국 주가: {len(kr_df):,}건")
        total_records += len(kr_df)
    if len(us_stocks) > 0:
        print(f"  미국 주가: {len(us_df):,}건")
        total_records += len(us_df)
    if fred_df is not None:
        print(f"  FRED 경제지표 (미국): {len(fred_df):,}건")
        total_records += len(fred_df)
    if ecos_df is not None:
        print(f"  ECOS 경제지표 (한국): {len(ecos_df):,}건")
        total_records += len(ecos_df)

    print(f"  총 레코드: {total_records:,}건")
    print(f"  저장 위치: {ARCHIVE_DIR}/")
    print()

# ===========================
# 실행
# ===========================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='15년 히스토리 데이터 수집')
    parser.add_argument('--start', type=str, required=True, help='시작일 (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='종료일 (YYYY-MM-DD)')
    parser.add_argument('--suffix', type=str, required=True, help='파일명 접미사 (예: 2010_2014)')

    args = parser.parse_args()

    main(args.start, args.end, args.suffix)
