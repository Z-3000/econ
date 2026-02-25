#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 결측치 복구 스크립트
========================
InfluxDB에서 데이터를 조회하여 CSV의 no_data/N/A 값을 채워넣음

사용법:
    ~/influx_venv/bin/python 01_scripts/08_fix_csv_from_influxdb.py

Author: Claude Code
Created: 2025-12-09
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from config import config

try:
    from influxdb_client import InfluxDBClient
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    print("❌ influxdb-client 미설치")
    exit(1)


def get_influx_client():
    """InfluxDB 클라이언트 반환"""
    if not config.INFLUXDB_TOKEN:
        print("❌ INFLUXDB_TOKEN이 설정되지 않았습니다.")
        return None
    return InfluxDBClient(
        url=config.INFLUXDB_URL,
        token=config.INFLUXDB_TOKEN,
        org=config.INFLUXDB_ORG
    )


def fix_stock_csv():
    """
    주가 CSV의 no_data 행을 InfluxDB에서 복구
    """
    print("\n[주가 CSV 복구]")

    csv_path = f"{config.STOCK_DIR}/stock.csv"
    if not os.path.exists(csv_path):
        print("  ❌ stock.csv 파일이 없습니다.")
        return

    # CSV 읽기
    df = pd.read_csv(csv_path)
    no_data_rows = df[df['status'] != 'success']

    if len(no_data_rows) == 0:
        print("  ✅ 복구할 행이 없습니다.")
        return

    print(f"  📊 no_data 행: {len(no_data_rows)}개")

    # InfluxDB 클라이언트
    client = get_influx_client()
    if not client:
        return

    query_api = client.query_api()
    fixed_count = 0

    for idx, row in no_data_rows.iterrows():
        ticker = row['ticker']
        name = row['name']
        timestamp = row['timestamp']

        # timestamp에서 날짜 추출
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            start_date = dt.strftime("%Y-%m-%dT00:00:00Z")
            end_date = (dt + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        except:
            continue

        # InfluxDB에서 해당 날짜 데이터 조회
        query = f'''
        from(bucket: "{config.INFLUXDB_BUCKET}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r._measurement == "stock_prices")
            |> filter(fn: (r) => r.ticker == "{ticker}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> last()
        '''

        try:
            tables = query_api.query(query)

            for table in tables:
                for record in table.records:
                    # 데이터 복구
                    df.at[idx, 'open'] = record.values.get('open', 'N/A')
                    df.at[idx, 'high'] = record.values.get('high', 'N/A')
                    df.at[idx, 'low'] = record.values.get('low', 'N/A')
                    df.at[idx, 'close'] = record.values.get('close', 'N/A')
                    df.at[idx, 'volume'] = record.values.get('volume', 'N/A')
                    df.at[idx, 'status'] = 'recovered_from_influxdb'
                    fixed_count += 1
                    break
        except Exception as e:
            continue

    client.close()

    if fixed_count > 0:
        # 백업 후 저장
        backup_path = csv_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        os.rename(csv_path, backup_path)
        print(f"  📁 백업: {backup_path}")

        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"  ✅ {fixed_count}개 행 복구 완료")
    else:
        print("  ℹ️ InfluxDB에서 복구할 데이터가 없습니다.")


def fix_economy_csv():
    """
    경제지표 CSV의 no_data 행을 InfluxDB에서 복구
    """
    print("\n[경제지표 CSV 복구]")

    csv_path = f"{config.ECONOMY_DIR}/economy.csv"
    if not os.path.exists(csv_path):
        print("  ❌ economy.csv 파일이 없습니다.")
        return

    # CSV 읽기
    df = pd.read_csv(csv_path)
    no_data_rows = df[df['status'] != 'success']

    if len(no_data_rows) == 0:
        print("  ✅ 복구할 행이 없습니다.")
        return

    print(f"  📊 no_data 행: {len(no_data_rows)}개")

    # InfluxDB 클라이언트
    client = get_influx_client()
    if not client:
        return

    query_api = client.query_api()
    fixed_count = 0

    for idx, row in no_data_rows.iterrows():
        indicator = row['indicator']
        timestamp = row['timestamp']

        # timestamp에서 날짜 추출
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            start_date = dt.strftime("%Y-%m-%dT00:00:00Z")
            end_date = (dt + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        except:
            continue

        # InfluxDB에서 해당 날짜 데이터 조회
        query = f'''
        from(bucket: "{config.INFLUXDB_BUCKET}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r._measurement == "economic_indicators")
            |> filter(fn: (r) => r.indicator == "{indicator}")
            |> filter(fn: (r) => r._field == "value")
            |> last()
        '''

        try:
            tables = query_api.query(query)

            for table in tables:
                for record in table.records:
                    # 데이터 복구
                    df.at[idx, 'value'] = record.get_value()
                    df.at[idx, 'status'] = 'recovered_from_influxdb'
                    fixed_count += 1
                    break
        except Exception as e:
            continue

    client.close()

    if fixed_count > 0:
        # 백업 후 저장
        backup_path = csv_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        os.rename(csv_path, backup_path)
        print(f"  📁 백업: {backup_path}")

        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"  ✅ {fixed_count}개 행 복구 완료")
    else:
        print("  ℹ️ InfluxDB에서 복구할 데이터가 없습니다.")


def show_csv_status():
    """
    CSV 파일 상태 요약
    """
    print("\n" + "=" * 50)
    print("CSV 데이터 상태 요약")
    print("=" * 50)

    # Stock CSV
    stock_path = f"{config.STOCK_DIR}/stock.csv"
    if os.path.exists(stock_path):
        df = pd.read_csv(stock_path)
        print(f"\n📈 Stock CSV: {len(df)}행")
        print(df['status'].value_counts().to_string())

    # Economy CSV
    economy_path = f"{config.ECONOMY_DIR}/economy.csv"
    if os.path.exists(economy_path):
        df = pd.read_csv(economy_path)
        print(f"\n💰 Economy CSV: {len(df)}행")
        print(df['status'].value_counts().to_string())

    # News CSV
    news_path = f"{config.NEWS_DIR}/news.csv"
    if os.path.exists(news_path):
        df = pd.read_csv(news_path)
        print(f"\n📰 News CSV: {len(df)}행")
        print(df['status'].value_counts().to_string())


if __name__ == "__main__":
    print("=" * 50)
    print("CSV 결측치 복구 스크립트")
    print("=" * 50)

    # 현재 상태 표시
    show_csv_status()

    # 복구 실행
    fix_stock_csv()
    fix_economy_csv()

    # 복구 후 상태 표시
    print("\n" + "=" * 50)
    print("복구 후 상태")
    print("=" * 50)
    show_csv_status()
