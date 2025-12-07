#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수집 로그 모듈 (Collection Logger)
==================================
데이터 수집 작업의 실행 시간, 성공/실패 건수를 InfluxDB에 저장

Measurement: system_logs
Tags: task_name (news, stock, economy, total)
Fields: execution_time_ms, success_count, fail_count, total_count, error_rate

Author: Claude Code
Created: 2025-12-04
"""

import time
from datetime import datetime, timezone
from config import config

# InfluxDB 클라이언트 (선택적 import)
try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False


class CollectionLogger:
    """수집 작업 로깅 클래스"""

    def __init__(self, task_name: str):
        """
        Args:
            task_name: 작업명 (news, stock, economy, total)
        """
        self.task_name = task_name
        self.start_time = None
        self.success_count = 0
        self.fail_count = 0
        self.errors = []

    def start(self):
        """수집 시작 시간 기록"""
        self.start_time = time.time()
        self.success_count = 0
        self.fail_count = 0
        self.errors = []

    def add_success(self, count: int = 1):
        """성공 건수 추가"""
        self.success_count += count

    def add_fail(self, count: int = 1, error_msg: str = None):
        """실패 건수 추가"""
        self.fail_count += count
        if error_msg:
            self.errors.append(error_msg[:100])  # 100자 제한

    def finish(self) -> dict:
        """
        수집 완료 및 로그 저장

        Returns:
            dict: 수집 결과 요약
        """
        if self.start_time is None:
            return None

        execution_time_ms = int((time.time() - self.start_time) * 1000)
        total_count = self.success_count + self.fail_count
        error_rate = (self.fail_count / total_count * 100) if total_count > 0 else 0.0

        result = {
            'task_name': self.task_name,
            'execution_time_ms': execution_time_ms,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'total_count': total_count,
            'error_rate': round(error_rate, 2),
            'errors': self.errors[:5]  # 최대 5개 에러만 기록
        }

        # InfluxDB에 저장
        self._save_to_influx(result)

        return result

    def _save_to_influx(self, result: dict):
        """InfluxDB에 로그 저장"""
        if not INFLUXDB_AVAILABLE:
            return

        if not config.INFLUXDB_TOKEN:
            return

        try:
            client = InfluxDBClient(
                url=config.INFLUXDB_URL,
                token=config.INFLUXDB_TOKEN,
                org=config.INFLUXDB_ORG
            )

            point = Point("system_logs") \
                .tag("task_name", result['task_name']) \
                .field("execution_time_ms", result['execution_time_ms']) \
                .field("success_count", result['success_count']) \
                .field("fail_count", result['fail_count']) \
                .field("total_count", result['total_count']) \
                .field("error_rate", result['error_rate']) \
                .time(datetime.now(timezone.utc), WritePrecision.S)

            write_api = client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket=config.INFLUXDB_BUCKET, record=point)

            client.close()

        except Exception as e:
            print(f"  로그 저장 오류: {e}")


def log_collection_result(task_name: str, success: int, fail: int,
                          execution_time_ms: int, errors: list = None):
    """
    단순 로그 저장 함수 (기존 코드와 호환)

    Args:
        task_name: 작업명
        success: 성공 건수
        fail: 실패 건수
        execution_time_ms: 실행 시간 (ms)
        errors: 에러 메시지 리스트
    """
    if not INFLUXDB_AVAILABLE or not config.INFLUXDB_TOKEN:
        return

    total = success + fail
    error_rate = (fail / total * 100) if total > 0 else 0.0

    try:
        client = InfluxDBClient(
            url=config.INFLUXDB_URL,
            token=config.INFLUXDB_TOKEN,
            org=config.INFLUXDB_ORG
        )

        point = Point("system_logs") \
            .tag("task_name", task_name) \
            .field("execution_time_ms", execution_time_ms) \
            .field("success_count", success) \
            .field("fail_count", fail) \
            .field("total_count", total) \
            .field("error_rate", round(error_rate, 2)) \
            .time(datetime.now(timezone.utc), WritePrecision.S)

        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=config.INFLUXDB_BUCKET, record=point)

        client.close()
        print(f"  📊 로그 저장: {task_name} ({execution_time_ms}ms, 성공:{success}, 실패:{fail})")

    except Exception as e:
        print(f"  로그 저장 오류: {e}")
