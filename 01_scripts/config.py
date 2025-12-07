#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
설정 관리 모듈
=============
- 환경변수에서 API 키 로드
- 공통 설정값 관리
- .env 파일 지원

사용법:
    from config import Config
    config = Config()
    print(config.NAVER_CLIENT_ID)
"""

import os
from pathlib import Path

# .env 파일 로드 (python-dotenv 설치 필요)
try:
    from dotenv import load_dotenv
    # 프로젝트 루트의 .env 파일 로드
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    DOTENV_LOADED = True
except ImportError:
    DOTENV_LOADED = False


class Config:
    """
    프로젝트 설정 클래스

    환경변수 우선순위:
    1. 시스템 환경변수
    2. .env 파일
    3. 기본값 (None)
    """

    # ========================================
    # 경로 설정
    # ========================================
    BASE_DIR = "/raspi/WD4T"
    DATA_DIR = f"{BASE_DIR}/00_data_raw"
    PROCESSED_DIR = f"{BASE_DIR}/00-1_data_processed"
    ARCHIVE_DIR = f"{BASE_DIR}/00_data_raw/archive"
    NEWS_DIR = f"{BASE_DIR}/data/news"
    STOCK_DIR = f"{BASE_DIR}/data/stock"
    ECONOMY_DIR = f"{BASE_DIR}/data/economy"

    # ========================================
    # API 키 (환경변수에서 로드)
    # ========================================
    @property
    def NAVER_CLIENT_ID(self):
        return os.getenv('NAVER_CLIENT_ID')

    @property
    def NAVER_CLIENT_SECRET(self):
        return os.getenv('NAVER_CLIENT_SECRET')

    @property
    def BOK_API_KEY(self):
        """한국은행 ECOS API 키"""
        return os.getenv('BOK_API_KEY')

    @property
    def FRED_API_KEY(self):
        """FRED API 키"""
        return os.getenv('FRED_API_KEY')

    # ========================================
    # InfluxDB 설정
    # ========================================
    @property
    def INFLUXDB_URL(self):
        return os.getenv('INFLUXDB_URL', 'http://localhost:8086')

    @property
    def INFLUXDB_TOKEN(self):
        return os.getenv('INFLUXDB_TOKEN')

    @property
    def INFLUXDB_ORG(self):
        return os.getenv('INFLUXDB_ORG', 'my-org')

    @property
    def INFLUXDB_BUCKET(self):
        return os.getenv('INFLUXDB_BUCKET', 'econ_market')

    # ========================================
    # Grafana 설정
    # ========================================
    @property
    def GRAFANA_URL(self):
        return os.getenv('GRAFANA_URL', 'http://localhost:3000')

    @property
    def GRAFANA_USER(self):
        return os.getenv('GRAFANA_USER', 'admin')

    @property
    def GRAFANA_PASSWORD(self):
        return os.getenv('GRAFANA_PASSWORD')

    # ========================================
    # Telegram 알림 설정
    # ========================================
    @property
    def TELEGRAM_BOT_TOKEN(self):
        """Telegram 봇 토큰 (BotFather에서 발급)"""
        return os.getenv('TELEGRAM_BOT_TOKEN')

    @property
    def TELEGRAM_CHAT_ID(self):
        """Telegram 채팅방 ID (개인 또는 그룹)"""
        return os.getenv('TELEGRAM_CHAT_ID')

    @property
    def TELEGRAM_ENABLED(self):
        """Telegram 알림 활성화 여부"""
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID
                    and self.TELEGRAM_BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE')

    # ========================================
    # 수집 설정
    # ========================================
    # 뉴스 키워드
    NEWS_KEYWORDS = ["경제", "부동산", "반도체", "코스피"]

    # 배치 크기 (InfluxDB 적재용)
    BATCH_SIZE = 500

    # ========================================
    # 종목 리스트
    # ========================================
    # 한국 주가 (yfinance)
    KR_TICKERS = {
        # 지수
        "코스피": "^KS11",
        "코스닥": "^KQ11",

        # ETF (9개)
        "KODEX200": "069500.KS",
        "KODEX 코스닥150": "229200.KS",
        "TIGER 미국S&P500": "360750.KS",
        "TIGER 미국나스닥100": "133690.KS",
        "KODEX 배당가치": "227560.KS",
        "TIGER 코리아배당다우존스": "269370.KS",
        "KODEX 국고채3년": "114260.KS",
        "KODEX 골드선물(H)": "132030.KS",
        "KODEX 미국S&P500커버드콜OTM": "453530.KS",

        # 개별종목 (16개)
        "삼성전자": "005930.KS",
        "SK하이닉스": "000660.KS",
        "LG에너지솔루션": "373220.KS",
        "삼성바이오로직스": "207940.KS",
        "현대차": "005380.KS",
        "KB금융": "105560.KS",
        "POSCO홀딩스": "005490.KS",
        "NAVER": "035420.KS",
        "HYBE": "352820.KS",
        "SM": "041510.KS",
        "JYP Ent.": "035900.KS",
        "크래프톤": "259960.KS",
        "엔씨소프트": "036570.KS",
        "CJ ENM": "035760.KS",
        "CGV": "079160.KS",
        "카카오": "035720.KS",
    }

    # 미국 주가 (yfinance)
    US_TICKERS = {
        # 지수
        "S&P500": "^GSPC",
        "나스닥": "^IXIC",
        "VIX": "^VIX",

        # 나스닥 ETF
        "QQQ": "QQQ",
        "QLD (2x)": "QLD",
        "TQQQ (3x)": "TQQQ",

        # S&P500 ETF
        "SPY": "SPY",
        "VOO": "VOO",
        "IVV": "IVV",
        "SSO (2x)": "SSO",
        "UPRO (3x)": "UPRO",
        "SPLG": "SPLG",

        # 다우존스 ETF
        "DIA": "DIA",

        # 배당 ETF
        "SCHD": "SCHD",
        "DGRO": "DGRO",
        "SPHD": "SPHD",
        "JEPI": "JEPI",
        "NUSI": "NUSI",
        "MAIN": "MAIN",
        "GAIN": "GAIN",
        "QYLD": "QYLD",
        "XYLD": "XYLD",
        "RYLD": "RYLD",

        # 기술/반도체 레버리지
        "SOXL (3x)": "SOXL",
        "TECL (3x)": "TECL",

        # 광범위 지수
        "VTI": "VTI",
        "VT": "VT",
        "VEA": "VEA",
        "EFA": "EFA",
        "SPDW": "SPDW",
        "ITOT": "ITOT",

        # 인버스 (숏)
        "SQQQ (-3x)": "SQQQ",
        "QID (-2x)": "QID",
        "PSQ (-1x)": "PSQ",

        # 중국
        "CWEB (2x)": "CWEB",

        # 채권/금
        "TLT": "TLT",
        "GLD": "GLD",
    }

    # FRED 경제지표
    FRED_INDICATORS = {
        'GDP': '미국 GDP',
        'CPIAUCSL': '미국 CPI',
        'UNRATE': '미국 실업률',
        'PAYEMS': '미국 비농업 고용자수',
        'DFF': '연방기금금리',
        'DGS10': '미국 10년 국채금리',
        'VIXCLS': 'VIX',
        'INDPRO': '미국 산업생산지수',
        'MANEMP': '미국 제조업 고용자수',
        'DEXKOUS': 'USD/KRW 환율',
    }

    # ECOS 경제지표 (한국은행)
    ECOS_INDICATORS = {
        ('901Y009', '0', 'M'): '한국 소비자물가지수',
        ('901Y010', '00', 'M'): '한국 CPI 특수분류',
        ('200Y102', '', 'Q'): '한국 GDP 주요지표',
    }

    # ========================================
    # 유틸리티 메서드
    # ========================================
    def validate(self):
        """필수 설정값 검증"""
        missing = []

        if not self.NAVER_CLIENT_ID:
            missing.append('NAVER_CLIENT_ID')
        if not self.NAVER_CLIENT_SECRET:
            missing.append('NAVER_CLIENT_SECRET')
        if not self.BOK_API_KEY:
            missing.append('BOK_API_KEY')
        if not self.FRED_API_KEY:
            missing.append('FRED_API_KEY')
        if not self.INFLUXDB_TOKEN:
            missing.append('INFLUXDB_TOKEN')
        if not self.GRAFANA_PASSWORD:
            missing.append('GRAFANA_PASSWORD')

        if missing:
            print(f"경고: 다음 환경변수가 설정되지 않았습니다: {', '.join(missing)}")
            print(f"  .env 파일을 생성하거나 환경변수를 설정하세요.")
            return False
        return True

    def print_status(self):
        """설정 상태 출력 (키 값은 마스킹)"""
        def mask(value):
            if value is None:
                return "❌ 미설정"
            return f"✅ 설정됨 ({value[:4]}...)"

        print("=" * 50)
        print("설정 상태")
        print("=" * 50)
        print(f"  NAVER_CLIENT_ID: {mask(self.NAVER_CLIENT_ID)}")
        print(f"  NAVER_CLIENT_SECRET: {mask(self.NAVER_CLIENT_SECRET)}")
        print(f"  BOK_API_KEY: {mask(self.BOK_API_KEY)}")
        print(f"  FRED_API_KEY: {mask(self.FRED_API_KEY)}")
        print(f"  INFLUXDB_TOKEN: {mask(self.INFLUXDB_TOKEN)}")
        print(f"  INFLUXDB_URL: {self.INFLUXDB_URL}")
        print(f"  INFLUXDB_BUCKET: {self.INFLUXDB_BUCKET}")
        print(f"  GRAFANA_URL: {self.GRAFANA_URL}")
        print(f"  GRAFANA_PASSWORD: {mask(self.GRAFANA_PASSWORD)}")
        print("=" * 50)


# 싱글톤 인스턴스
config = Config()


if __name__ == "__main__":
    # 설정 상태 확인
    config.print_status()
    config.validate()
