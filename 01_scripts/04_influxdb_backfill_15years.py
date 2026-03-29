#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15년 히스토리 데이터 InfluxDB 백필 스크립트
- 병합된 CSV 파일을 InfluxDB에 적재
"""

import pandas as pd
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException
import os

# ===========================
# 설정 (config.py에서 로드)
# ===========================
from config import config

BASE_DIR = config.BASE_DIR
DATA_DIR = config.DATA_DIR

# InfluxDB 설정 (환경변수에서 로드)
INFLUXDB_URL = config.INFLUXDB_URL
INFLUXDB_TOKEN = config.INFLUXDB_TOKEN
INFLUXDB_ORG = config.INFLUXDB_ORG
INFLUXDB_BUCKET = config.INFLUXDB_BUCKET

# 배치 크기 (백필은 일반 수집보다 더 작은 배치가 안정적)
BATCH_SIZE = int(os.getenv("INFLUXDB_BACKFILL_BATCH_SIZE", "100"))

print("=" * 80)
print("15년 히스토리 데이터 InfluxDB 백필")
print("=" * 80)

# ===========================
# InfluxDB 클라이언트 생성
# ===========================
client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG,
    timeout=60_000  # 타임아웃 60초로 설정
)
write_api = client.write_api(write_options=SYNCHRONOUS)


def write_points_with_retry(points, depth=0):
    """타임아웃 시 배치를 절반으로 쪼개 재시도"""
    if not points:
        return 0

    try:
        write_api.write(bucket=INFLUXDB_BUCKET, record=points)
        return len(points)
    except ApiException as e:
        message = str(e).lower()
        if "timeout" not in message or len(points) == 1:
            raise

        if depth == 0:
            print(f"\n  ⚠️  write timeout 발생, 배치를 더 잘게 나눠 재시도합니다. ({len(points)}건)")

        mid = len(points) // 2
        return write_points_with_retry(points[:mid], depth + 1) + write_points_with_retry(points[mid:], depth + 1)

# ===========================
# 1. 한국 주가 백필
# ===========================
print("\n[1/4] 한국 주가 백필")
print("-" * 80)

kr_file = f"{DATA_DIR}/stock_kr_2010_2025_with_adj.csv"
if os.path.exists(kr_file):
    kr_df = pd.read_csv(kr_file, encoding='utf-8-sig')
    kr_df['date'] = pd.to_datetime(kr_df['date'])

    print(f"  파일: {os.path.basename(kr_file)}")
    print(f"  레코드: {len(kr_df):,}건")
    print(f"  기간: {kr_df['date'].min()} ~ {kr_df['date'].max()}")
    print(f"  종목: {kr_df['ticker'].nunique()}개")

    total_written = 0
    for i in range(0, len(kr_df), BATCH_SIZE):
        batch = kr_df.iloc[i:i+BATCH_SIZE]
        points = []

        for _, row in batch.iterrows():
            try:
                # KST를 UTC로 변환 (9시간 차이)
                dt = row['date'].to_pydatetime().replace(tzinfo=timezone.utc)

                p = Point("stock_prices") \
                    .tag("name", row['name']) \
                    .tag("ticker", row['ticker']) \
                    .field("open", float(row['open'])) \
                    .field("high", float(row['high'])) \
                    .field("low", float(row['low'])) \
                    .field("close", float(row['close'])) \
                    .field("adj_close", float(row.get('adj_close', row['close']))) \
                    .field("volume", int(row['volume'])) \
                    .field("status_code", int(row.get('status_code', 1))) \
                    .time(dt, WritePrecision.S)
                points.append(p)
            except Exception as e:
                print(f"  ⚠️  레코드 변환 오류: {e}")
                continue

        if points:
            total_written += write_points_with_retry(points)
            print(f"  진행: {total_written:,}/{len(kr_df):,}건 ({total_written/len(kr_df)*100:.1f}%)", end='\r')

    print(f"\n✅ 한국 주가 백필 완료: {total_written:,}건")
else:
    print(f"❌ 파일 없음: {kr_file}")

# ===========================
# 2. 미국 주가 백필
# ===========================
print("\n[2/4] 미국 주가 백필")
print("-" * 80)

us_file = f"{DATA_DIR}/stock_us_2010_2025_with_adj.csv"
if os.path.exists(us_file):
    us_df = pd.read_csv(us_file, encoding='utf-8-sig')
    us_df['date'] = pd.to_datetime(us_df['date'])

    print(f"  파일: {os.path.basename(us_file)}")
    print(f"  레코드: {len(us_df):,}건")
    print(f"  기간: {us_df['date'].min()} ~ {us_df['date'].max()}")
    print(f"  종목: {us_df['ticker'].nunique()}개")

    total_written = 0
    for i in range(0, len(us_df), BATCH_SIZE):
        batch = us_df.iloc[i:i+BATCH_SIZE]
        points = []

        for _, row in batch.iterrows():
            try:
                dt = row['date'].to_pydatetime().replace(tzinfo=timezone.utc)

                p = Point("stock_prices") \
                    .tag("name", row['name']) \
                    .tag("ticker", row['ticker']) \
                    .field("open", float(row['open'])) \
                    .field("high", float(row['high'])) \
                    .field("low", float(row['low'])) \
                    .field("close", float(row['close'])) \
                    .field("volume", int(row['volume'])) \
                    .time(dt, WritePrecision.S)
                points.append(p)
            except Exception as e:
                print(f"  ⚠️  레코드 변환 오류: {e}")
                continue

        if points:
            total_written += write_points_with_retry(points)
            print(f"  진행: {total_written:,}/{len(us_df):,}건 ({total_written/len(us_df)*100:.1f}%)", end='\r')

    print(f"\n✅ 미국 주가 백필 완료: {total_written:,}건")
else:
    print(f"❌ 파일 없음: {us_file}")

# ===========================
# 3. FRED 경제지표 백필
# ===========================
print("\n[3/4] FRED 경제지표 백필")
print("-" * 80)

fred_file = f"{DATA_DIR}/economy_fred_2010_2025.csv"
if os.path.exists(fred_file):
    fred_df = pd.read_csv(fred_file, encoding='utf-8-sig')
    fred_df['date'] = pd.to_datetime(fred_df['date'])

    print(f"  파일: {os.path.basename(fred_file)}")
    print(f"  레코드: {len(fred_df):,}건")
    print(f"  기간: {fred_df['date'].min()} ~ {fred_df['date'].max()}")
    print(f"  지표: {fred_df['series_id'].nunique()}개")

    total_written = 0
    for i in range(0, len(fred_df), BATCH_SIZE):
        batch = fred_df.iloc[i:i+BATCH_SIZE]
        points = []

        for _, row in batch.iterrows():
            try:
                dt = row['date'].to_pydatetime().replace(tzinfo=timezone.utc)

                p = Point("economic_indicators") \
                    .tag("indicator", row['indicator']) \
                    .tag("period", "daily") \
                    .field("value", float(row['value'])) \
                    .time(dt, WritePrecision.S)
                points.append(p)
            except Exception as e:
                print(f"  ⚠️  레코드 변환 오류: {e}")
                continue

        if points:
            total_written += write_points_with_retry(points)
            print(f"  진행: {total_written:,}/{len(fred_df):,}건 ({total_written/len(fred_df)*100:.1f}%)", end='\r')

    print(f"\n✅ FRED 경제지표 백필 완료: {total_written:,}건")
else:
    print(f"❌ 파일 없음: {fred_file}")

# ===========================
# 4. ECOS 경제지표 백필
# ===========================
print("\n[4/4] ECOS 경제지표 백필")
print("-" * 80)

ecos_file = f"{DATA_DIR}/economy_ecos_2010_2025.csv"
if os.path.exists(ecos_file):
    ecos_df = pd.read_csv(ecos_file, encoding='utf-8-sig')
    ecos_df['date'] = pd.to_datetime(ecos_df['date'])

    print(f"  파일: {os.path.basename(ecos_file)}")
    print(f"  레코드: {len(ecos_df):,}건")
    print(f"  기간: {ecos_df['date'].min()} ~ {ecos_df['date'].max()}")
    print(f"  지표: {ecos_df['series_id'].nunique()}개")

    total_written = 0
    for i in range(0, len(ecos_df), BATCH_SIZE):
        batch = ecos_df.iloc[i:i+BATCH_SIZE]
        points = []

        for _, row in batch.iterrows():
            try:
                dt = row['date'].to_pydatetime().replace(tzinfo=timezone.utc)

                p = Point("economic_indicators") \
                    .tag("indicator", row['indicator']) \
                    .tag("period", "monthly") \
                    .field("value", float(row['value'])) \
                    .time(dt, WritePrecision.S)
                points.append(p)
            except Exception as e:
                print(f"  ⚠️  레코드 변환 오류: {e}")
                continue

        if points:
            total_written += write_points_with_retry(points)
            print(f"  진행: {total_written:,}/{len(ecos_df):,}건 ({total_written/len(ecos_df)*100:.1f}%)", end='\r')

    print(f"\n✅ ECOS 경제지표 백필 완료: {total_written:,}건")
else:
    print(f"❌ 파일 없음: {ecos_file}")

# ===========================
# 완료
# ===========================
client.close()

print("\n" + "=" * 80)
print("백필 완료!")
print("=" * 80)
print(f"  InfluxDB: {INFLUXDB_URL}")
print(f"  Bucket: {INFLUXDB_BUCKET}")
print()
print("다음 단계: Grafana 대시보드 확인")
print()
