# 투자 데이터 파이프라인 & 모니터링 시스템

라즈베리파이 기반 **경제지표/주가 자동 수집 시스템**

76개 종목 (한국 27 + 미국 41) + 경제지표 **15년치 118,312건** 데이터를 자동 수집하고, **InfluxDB + Grafana**로 실시간 모니터링합니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| **자동 수집** | Cron으로 하루 3회 (08:00/16:00/20:00) 자동 실행 |
| **이중 저장** | CSV 백업 + InfluxDB 시계열 저장 |
| **실시간 대시보드** | Grafana 18개 패널로 시각화 |
| **15년 히스토리** | 2010~2025년 118,312건 데이터 |

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     라즈베리파이 5                                │
│                                                                 │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐            │
│  │   Cron     │───▶│  Python    │───▶│    CSV     │            │
│  │ 08/16/20시 │    │ Collector  │    │   백업     │            │
│  └────────────┘    └─────┬──────┘    └────────────┘            │
│                          │                                      │
│                          ▼                                      │
│                   ┌────────────┐    ┌────────────┐             │
│                   │  InfluxDB  │───▶│  Grafana   │             │
│                   │ 118,312건  │    │ 18개 패널  │             │
│                   └────────────┘    └────────────┘             │
└─────────────────────────────────────────────────────────────────┘
        ▲                    ▲
        │                    │
   ┌────┴────┐         ┌────┴────┐
   │ yfinance │         │ECOS/FRED│
   │  주가    │         │경제지표  │
   └─────────┘         └─────────┘
```

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| **언어** | Python 3.12 |
| **데이터 처리** | pandas, numpy |
| **데이터 수집** | yfinance, requests |
| **시계열 DB** | InfluxDB 2.x |
| **시각화** | Grafana 12.3 |
| **자동화** | Cron |
| **하드웨어** | Raspberry Pi 5 |

---

## 프로젝트 구조

```
/raspi/WD4T/
├── .env                   # API 키/토큰/비밀번호 (Git 제외)
├── .env.example           # 환경변수 템플릿
├── 00_data_raw/           # 원본 데이터
│   ├── archive/           # 15년 히스토리 데이터
│   ├── stock_kr_*.csv     # 한국 주가
│   ├── stock_us_*.csv     # 미국 주가
│   └── economy_*.csv      # 경제지표
├── 00-1_data_processed/   # 전처리 데이터
├── 01_scripts/            # Python 스크립트
│   ├── config.py                       # 설정 관리 (환경변수 로드)
│   ├── 01_data_collector.py            # 일간 수집 (Cron)
│   ├── 02_collect_15year_historical.py # 15년 데이터 수집
│   ├── 04_influxdb_backfill_15years.py # InfluxDB 백필
│   └── preprocessor.py                 # 전처리기
├── 02_notebooks/          # Jupyter 노트북
├── 03_outputs/            # 시각화 결과물
├── 98_logs/               # 로그
├── 99_docs/               # 문서
├── data/                  # 일간 수집 데이터 (Cron)
│   ├── news/              # 뉴스 (news.csv)
│   ├── stock/             # 주가 (stock.csv)
│   └── economy/           # 경제지표 (economy.csv)
└── README.md
```

---

## 수집 데이터

### 주가 (68개 종목)

| 구분 | 종목 수 | 예시 |
|------|---------|------|
| 한국 지수 | 2 | 코스피, 코스닥 |
| 한국 ETF | 9 | KODEX200, TIGER 미국S&P500 등 |
| 한국 개별 | 16 | 삼성전자, SK하이닉스, NAVER 등 |
| 미국 지수 | 3 | S&P500, 나스닥, VIX |
| 미국 ETF | 38 | QQQ, SPY, SCHD, TLT, GLD 등 |

### 경제지표

| 출처 | 지표 |
|------|------|
| ECOS (한국은행) | 환율, 기준금리, CPI, GDP |
| FRED (미국) | GDP, CPI, 실업률, 10년 국채금리 |

### 데이터 규모

| 항목 | 건수 |
|------|------|
| 한국 주가 | 64,190건 |
| 미국 주가 | 32,016건 |
| FRED 경제지표 | 19,275건 |
| ECOS 경제지표 | 2,831건 |
| **총합** | **118,312건** |

---

## 설치 및 실행

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv ~/influx_venv
source ~/influx_venv/bin/activate

# 패키지 설치
pip install pandas numpy yfinance requests influxdb-client python-dotenv fredapi
```

### 2. API 키 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

```env
NAVER_CLIENT_ID=your_id
NAVER_CLIENT_SECRET=your_secret
BOK_API_KEY=your_key
FRED_API_KEY=your_key
INFLUXDB_TOKEN=your_token
```

### 3. 데이터 수집 실행

```bash
# 일간 수집
python 01_scripts/01_data_collector.py

# 15년 히스토리 수집 (1회성)
python 01_scripts/02_collect_15year_historical.py --start 2010-01-01 --end 2025-12-31 --suffix 2010_2025

# InfluxDB 백필
python 01_scripts/04_influxdb_backfill_15years.py
```

### 4. Cron 스케줄 설정

```bash
crontab -e
```

```cron
0 8 * * * /home/raspi/influx_venv/bin/python /raspi/WD4T/01_scripts/01_data_collector.py >> /raspi/WD4T/98_logs/cron.log 2>&1
0 16 * * 1-5 /home/raspi/influx_venv/bin/python /raspi/WD4T/01_scripts/01_data_collector.py >> /raspi/WD4T/98_logs/cron.log 2>&1
0 20 * * * /home/raspi/influx_venv/bin/python /raspi/WD4T/01_scripts/01_data_collector.py >> /raspi/WD4T/98_logs/cron.log 2>&1
```

---

## Grafana 대시보드

### 패널 구성 (18개)

| 행 | 패널 | 내용 |
|----|------|------|
| 1 | 한국 지수/ETF | 코스피, 코스닥, KODEX200 등 |
| 1 | 미국 지수/ETF | S&P500, 나스닥, QQQ 등 |
| 2 | 한국 GDP+산업생산 | ECOS 데이터 |
| 2 | 한국·미국 CPI | 물가 지표 |
| 3 | 미국 금리 | 연방기금금리, 10년물 |
| 3 | 환율 | 원/달러, 원/엔, 원/유로 |
| 4 | IT플랫폼 | NAVER, 카카오 |
| 4 | 엔터/게임 | HYBE, SM, 크래프톤 등 |
| 4 | 대형주 | 삼성전자, SK하이닉스 등 |

---

## InfluxDB 데이터 모델

```
Bucket: econ_market
├── Measurement: stock_prices
│   ├── Tags: name, ticker
│   └── Fields: open, high, low, close, volume
│
└── Measurement: economic_indicators
    ├── Tags: indicator, period
    └── Fields: value
```

### Flux 쿼리 예시

```flux
from(bucket: "econ_market")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "삼성전자")
  |> filter(fn: (r) => r._field == "close")
```

---

## 문서

| 문서 | 설명 |
|------|------|
| [ARCHITECTURE.md](99_docs/ARCHITECTURE.md) | 시스템 아키텍처 |
| [DASHBOARD_DESIGN.md](99_docs/DASHBOARD_DESIGN.md) | 대시보드 설계 |
| [DATA_SOURCE_POLICY.md](99_docs/DATA_SOURCE_POLICY.md) | 데이터 소스 정책 |
| [CHANGELOG.md](99_docs/CHANGELOG.md) | 변경 이력 |

---

## 라이선스

MIT License

---

## 작성자

[Your Name]

- 작성일: 2025-11
- 최종 수정: 2025-12-03
