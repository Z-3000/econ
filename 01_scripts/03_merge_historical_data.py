#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15년 히스토리 데이터 병합 스크립트
- 3개 기간(2010-2014, 2015-2019, 2020-2025)을 하나의 파일로 병합
- 중복 제거 및 정렬
"""

import pandas as pd
import os
from datetime import datetime

# ===========================
# 설정
# ===========================
BASE_DIR = "/raspi/WD4T"
ARCHIVE_DIR = f"{BASE_DIR}/00_data_raw/archive"
OUTPUT_DIR = f"{BASE_DIR}/00_data_raw"

print("=" * 80)
print("15년 히스토리 데이터 병합")
print("=" * 80)

# ===========================
# 1. 한국 주가 병합
# ===========================
print("\n[1/3] 한국 주가 병합")
print("-" * 80)

kr_files = [
    f"{ARCHIVE_DIR}/stock_kr_2010_2014_v3.csv",
    f"{ARCHIVE_DIR}/stock_kr_2015_2019_v3.csv",
    f"{ARCHIVE_DIR}/stock_kr_2020_2025_v3.csv"
]

kr_dfs = []
for file in kr_files:
    if os.path.exists(file):
        df = pd.read_csv(file, encoding='utf-8-sig')
        print(f"  읽기: {os.path.basename(file)} ({len(df):,}건)")
        kr_dfs.append(df)
    else:
        print(f"  ⚠️  파일 없음: {file}")

if len(kr_dfs) > 0:
    kr_merged = pd.concat(kr_dfs, ignore_index=True)

    # 날짜 변환
    kr_merged['date'] = pd.to_datetime(kr_merged['date'])

    # 중복 제거 (같은 날짜, 같은 종목)
    before_count = len(kr_merged)
    kr_merged = kr_merged.drop_duplicates(subset=['date', 'ticker'], keep='last')
    after_count = len(kr_merged)

    # 정렬 (날짜, 종목)
    kr_merged = kr_merged.sort_values(['ticker', 'date']).reset_index(drop=True)

    # 저장
    kr_output = f"{OUTPUT_DIR}/stock_kr_2010_2025.csv"
    kr_merged.to_csv(kr_output, index=False, encoding='utf-8-sig')

    print(f"\n✅ 한국 주가 병합 완료")
    print(f"   - 원본: {before_count:,}건")
    print(f"   - 중복 제거: {before_count - after_count:,}건")
    print(f"   - 최종: {after_count:,}건")
    print(f"   - 저장: {kr_output}")
    print(f"   - 기간: {kr_merged['date'].min()} ~ {kr_merged['date'].max()}")
    print(f"   - 종목 수: {kr_merged['ticker'].nunique()}개")
else:
    print("❌ 한국 주가 파일을 찾을 수 없습니다")

# ===========================
# 2. 미국 주가 병합
# ===========================
print("\n[2/3] 미국 주가 병합")
print("-" * 80)

us_files = [
    f"{ARCHIVE_DIR}/stock_us_2010_2014_v3.csv",
    f"{ARCHIVE_DIR}/stock_us_2015_2019_v3.csv",
    f"{ARCHIVE_DIR}/stock_us_2020_2025_v3.csv"
]

us_dfs = []
for file in us_files:
    if os.path.exists(file):
        df = pd.read_csv(file, encoding='utf-8-sig')
        print(f"  읽기: {os.path.basename(file)} ({len(df):,}건)")
        us_dfs.append(df)
    else:
        print(f"  ⚠️  파일 없음: {file}")

if len(us_dfs) > 0:
    us_merged = pd.concat(us_dfs, ignore_index=True)

    # 날짜 변환
    us_merged['date'] = pd.to_datetime(us_merged['date'])

    # 중복 제거
    before_count = len(us_merged)
    us_merged = us_merged.drop_duplicates(subset=['date', 'ticker'], keep='last')
    after_count = len(us_merged)

    # 정렬
    us_merged = us_merged.sort_values(['ticker', 'date']).reset_index(drop=True)

    # 저장
    us_output = f"{OUTPUT_DIR}/stock_us_2010_2025.csv"
    us_merged.to_csv(us_output, index=False, encoding='utf-8-sig')

    print(f"\n✅ 미국 주가 병합 완료")
    print(f"   - 원본: {before_count:,}건")
    print(f"   - 중복 제거: {before_count - after_count:,}건")
    print(f"   - 최종: {after_count:,}건")
    print(f"   - 저장: {us_output}")
    print(f"   - 기간: {us_merged['date'].min()} ~ {us_merged['date'].max()}")
    print(f"   - 종목 수: {us_merged['ticker'].nunique()}개")
else:
    print("❌ 미국 주가 파일을 찾을 수 없습니다")

# ===========================
# 3. FRED 경제지표 병합
# ===========================
print("\n[3/4] FRED 경제지표 병합")
print("-" * 80)

fred_files = [
    f"{ARCHIVE_DIR}/economy_fred_2010_2014_v3.csv",
    f"{ARCHIVE_DIR}/economy_fred_2015_2019_v3.csv",
    f"{ARCHIVE_DIR}/economy_fred_2020_2025_v3.csv"
]

fred_dfs = []
for file in fred_files:
    if os.path.exists(file):
        df = pd.read_csv(file, encoding='utf-8-sig')
        print(f"  읽기: {os.path.basename(file)} ({len(df):,}건)")
        fred_dfs.append(df)
    else:
        print(f"  ⚠️  파일 없음: {file}")

if len(fred_dfs) > 0:
    fred_merged = pd.concat(fred_dfs, ignore_index=True)

    # 날짜 변환
    fred_merged['date'] = pd.to_datetime(fred_merged['date'])

    # 중복 제거
    before_count = len(fred_merged)
    fred_merged = fred_merged.drop_duplicates(subset=['date', 'series_id'], keep='last')
    after_count = len(fred_merged)

    # 정렬
    fred_merged = fred_merged.sort_values(['series_id', 'date']).reset_index(drop=True)

    # 저장
    fred_output = f"{OUTPUT_DIR}/economy_fred_2010_2025.csv"
    fred_merged.to_csv(fred_output, index=False, encoding='utf-8-sig')

    print(f"\n✅ FRED 경제지표 병합 완료")
    print(f"   - 원본: {before_count:,}건")
    print(f"   - 중복 제거: {before_count - after_count:,}건")
    print(f"   - 최종: {after_count:,}건")
    print(f"   - 저장: {fred_output}")
    print(f"   - 기간: {fred_merged['date'].min()} ~ {fred_merged['date'].max()}")
    print(f"   - 지표 수: {fred_merged['series_id'].nunique()}개")
else:
    print("❌ FRED 경제지표 파일을 찾을 수 없습니다")

# ===========================
# 4. ECOS 경제지표 병합
# ===========================
print("\n[4/4] ECOS 경제지표 병합")
print("-" * 80)

ecos_files = [
    f"{ARCHIVE_DIR}/economy_ecos_2010_2014_v3.csv",
    f"{ARCHIVE_DIR}/economy_ecos_2015_2019_v3.csv",
    f"{ARCHIVE_DIR}/economy_ecos_2020_2025_v3.csv"
]

ecos_dfs = []
for file in ecos_files:
    if os.path.exists(file):
        df = pd.read_csv(file, encoding='utf-8-sig')
        print(f"  읽기: {os.path.basename(file)} ({len(df):,}건)")
        ecos_dfs.append(df)
    else:
        print(f"  ⚠️  파일 없음: {file}")

if len(ecos_dfs) > 0:
    ecos_merged = pd.concat(ecos_dfs, ignore_index=True)

    # 날짜 변환 (에러 처리)
    ecos_merged['date'] = pd.to_datetime(ecos_merged['date'], errors='coerce')

    # 중복 제거 (날짜 + 지표명으로 중복 판단)
    before_count = len(ecos_merged)
    ecos_merged = ecos_merged.drop_duplicates(subset=['date', 'indicator'], keep='last')
    after_count = len(ecos_merged)

    # 정렬
    ecos_merged = ecos_merged.sort_values(['series_id', 'date']).reset_index(drop=True)

    # 저장
    ecos_output = f"{OUTPUT_DIR}/economy_ecos_2010_2025.csv"
    ecos_merged.to_csv(ecos_output, index=False, encoding='utf-8-sig')

    print(f"\n✅ ECOS 경제지표 병합 완료")
    print(f"   - 원본: {before_count:,}건")
    print(f"   - 중복 제거: {before_count - after_count:,}건")
    print(f"   - 최종: {after_count:,}건")
    print(f"   - 저장: {ecos_output}")
    print(f"   - 기간: {ecos_merged['date'].min()} ~ {ecos_merged['date'].max()}")
    print(f"   - 지표 수: {ecos_merged['series_id'].nunique()}개")
else:
    print("❌ ECOS 경제지표 파일을 찾을 수 없습니다")

# ===========================
# 최종 요약
# ===========================
print("\n" + "=" * 80)
print("병합 완료!")
print("=" * 80)

total_records = 0
if len(kr_dfs) > 0:
    print(f"  한국 주가: {after_count:,}건 (종목 {kr_merged['ticker'].nunique()}개)")
    total_records += len(kr_merged)

if len(us_dfs) > 0:
    print(f"  미국 주가: {len(us_merged):,}건 (종목 {us_merged['ticker'].nunique()}개)")
    total_records += len(us_merged)

if len(fred_dfs) > 0:
    print(f"  FRED 경제지표: {len(fred_merged):,}건 (지표 {fred_merged['series_id'].nunique()}개)")
    total_records += len(fred_merged)

if len(ecos_dfs) > 0:
    print(f"  ECOS 경제지표: {len(ecos_merged):,}건 (지표 {ecos_merged['series_id'].nunique()}개)")
    total_records += len(ecos_merged)

print(f"  총 레코드: {total_records:,}건")
print(f"  저장 위치: {OUTPUT_DIR}/")
print()
print("다음 단계: InfluxDB 백필")
print()
