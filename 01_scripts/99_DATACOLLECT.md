# DATACOLLECT - 데이터 수집 지침서

> 데이터 수집, 전처리, 시각화 스크립트 현황 및 설정 가이드

---

## 1. 스크립트 목록

| 파일명 | 용도 | 실행 환경 | 스케줄 |
|--------|------|----------|--------|
| `01_data_collector.py` | 일간 데이터 수집 (CSV + InfluxDB) | 라즈베리파이 | Cron (1일 3회) |
| **`02_collect_15year_historical.py`** | **15년 히스토리 데이터 수집** (2010-2025) | 라즈베리파이 | 1회성 |
| **`collect_gdp_only.py`** | **한국 GDP 데이터 수집** (ECOS 200Y102) | 라즈베리파이 | 1회성 |
| **`03_merge_historical_data.py`** | **CSV 병합** (3개 기간 → 1개 파일) | 라즈베리파이 | 1회성 |
| **`04_influxdb_backfill_15years.py`** | **InfluxDB 백필** (118,312건) | 라즈베리파이 | 1회성 |
| **`05_create_grafana_dashboard_v2.py`** | **Grafana 4행 대시보드 생성** | 라즈베리파이 | 수동 |
| **`06_upload_grafana_dashboard.py`** | **대시보드 자동 업로드** | 라즈베리파이 | 수동 |
| `collect_historical_news.py` | 뉴스 수집 (네이버 API) | 로컬 | 수동 |
| `preprocessor.py` | 데이터 전처리 | 로컬 | 수동 |
| `dashboard.py` | Streamlit 대시보드 | 로컬 | `streamlit run` |

---

## 2. 01_data_collector.py (일간 수집)

### 2.1 용도
- 라즈베리파이에서 Cron으로 자동 실행
- 뉴스, 주가, 경제지표 일간 수집

### 2.2 API 키
```python
# 환경변수(.env)에서 로드 - 직접 하드코딩 금지
from config import config

NAVER_CLIENT_ID = config.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = config.NAVER_CLIENT_SECRET
BOK_API_KEY = config.BOK_API_KEY
```

### 2.3 저장 경로 (라즈베리파이)
```python
BASE_DIR = "/raspi/WD4T"
NEWS_DIR = f"{BASE_DIR}/data/news"      # news.csv
STOCK_DIR = f"{BASE_DIR}/data/stock"    # stock.csv
ECONOMY_DIR = f"{BASE_DIR}/data/economy" # economy.csv
```

### 2.4 수집 대상

#### 뉴스 (네이버 검색 API)
| 항목 | 값 |
|------|-----|
| 키워드 | 경제, 부동산, 반도체, 코스피 |
| 키워드당 수집 | 5건 |
| 정렬 | sim (관련도순) |
| API 엔드포인트 | `https://openapi.naver.com/v1/search/news.json` |


#### 주가 (yfinance)

**지수 및 ETF**
| 구분 | 종목 | 티커 |
|------|------|------|
| 한국 지수 | 코스피 | ^KS11 |
| 한국 지수 | 코스닥 | ^KQ11 |
| 한국 ETF | KODEX200 | 069500.KS |
| 한국 ETF | KODEX 코스닥150 | 229200.KS |
| 한국 ETF | TIGER 미국S&P500 | 360750.KS |
| 한국 ETF | TIGER 미국나스닥100 | 133690.KS |
| 한국 ETF | KODEX 배당가치 | 227560.KS |
| 한국 ETF | TIGER 코리아배당다우존스 | 269370.KS |
| 한국 ETF | KODEX 국고채3년 | 114260.KS |
| 한국 ETF | KODEX 골드선물(H) | 132030.KS |
| 한국 ETF | KODEX 미국S&P500커버드콜OTM | 453530.KS |
| 미국 지수 | S&P500 | ^GSPC |
| 미국 지수 | 나스닥 | ^IXIC |
| 미국 지수 | VIX | ^VIX |
| 미국 ETF (나스닥) | QQQ (Invesco QQQ Trust) | QQQ |
| 미국 ETF (나스닥) | ProShares Ultra QQQ (2x) | QLD |
| 미국 ETF (나스닥) | ProShares UltraPro QQQ (3x) | TQQQ |
| 미국 ETF (나스닥) | Defiance Nasdaq-100 Enhanced | QQQ5 |
| 미국 ETF (S&P500) | SPDR S&P 500 | SPY |
| 미국 ETF (S&P500) | Vanguard S&P 500 | VOO |
| 미국 ETF (S&P500) | iShares Core S&P 500 | IVV |
| 미국 ETF (S&P500) | ProShares Ultra S&P500 (2x) | SSO |
| 미국 ETF (S&P500) | ProShares UltraPro S&P500 (3x) | UPRO |
| 미국 ETF (S&P500) | SPDR Portfolio S&P 500 | SPLG |
| 미국 ETF (다우) | SPDR Dow Jones | DIA |
| 미국 ETF (배당) | Schwab US Dividend Equity | SCHD |
| 미국 ETF (배당) | iShares Core Dividend Growth | DGRO |
| 미국 ETF (배당) | Invesco S&P 500 High Dividend | SPHD |
| 미국 ETF (배당) | JPMorgan Equity Premium Income | JEPI |
| 미국 ETF (배당) | Nationwide Risk-Managed Income | NUSI |
| 미국 ETF (배당) | Main Street Capital | MAIN |
| 미국 ETF (배당) | Gladstone Investment | GAIN |
| 미국 ETF (배당) | Global X NASDAQ 100 Covered Call | QYLD |
| 미국 ETF (배당) | Global X S&P 500 Covered Call | XYLD |
| 미국 ETF (배당) | Global X Russell 2000 Covered Call | RYLD |
| 미국 ETF (기술) | Direxion Semiconductor Bull 3x | SOXL |
| 미국 ETF (기술) | Direxion Technology Bull 3x | TECL |
| 미국 ETF (광범위) | Vanguard Total Stock Market | VTI |
| 미국 ETF (광범위) | Vanguard Total World Stock | VT |
| 미국 ETF (광범위) | Vanguard FTSE Developed Markets | VEA |
| 미국 ETF (광범위) | iShares MSCI EAFE | EFA |
| 미국 ETF (광범위) | SPDR Portfolio Developed World | SPDW |
| 미국 ETF (광범위) | iShares Core S&P Total US | ITOT |
| 미국 ETF (인버스) | ProShares UltraPro Short QQQ (-3x) | SQQQ |
| 미국 ETF (인버스) | ProShares UltraShort QQQ (-2x) | QID |
| 미국 ETF (인버스) | ProShares Short QQQ (-1x) | PSQ |
| 미국 ETF (중국) | Direxion CSI China Internet 2x | CWEB |
| 미국 ETF (채권/금) | iShares 20+ Year Treasury | TLT |
| 미국 ETF (채권/금) | SPDR Gold Trust | GLD |

**한국 개별종목 (섹터별)**
| 섹터 | 종목 | 티커 | 용도 태그 |
|------|------|------|-----------|
| 반도체 | 삼성전자 | 005930.KS | `수출`, `경기민감`, `기술` |
| 반도체 | SK하이닉스 | 000660.KS | `수출`, `경기민감`, `기술` |
| 2차전지 | LG에너지솔루션 | 373220.KS | `수출`, `성장`, `친환경` |
| 바이오 | 삼성바이오로직스 | 207940.KS | `성장`, `헬스케어`, `방어` |
| 자동차 | 현대차 | 005380.KS | `수출`, `경기민감`, `제조` |
| 금융 | KB금융 | 105560.KS | `금리민감`, `배당`, `내수` |
| 철강 | POSCO홀딩스 | 005490.KS | `경기민감`, `수출`, `소재` |
| IT/플랫폼 | NAVER | 035420.KS | `성장`, `내수`, `기술` |
| 엔터 | HYBE | 352820.KS | `문화`, `성장`, `K-콘텐츠` |
| 엔터 | SM | 041510.KS | `문화`, `성장`, `K-콘텐츠` |
| 엔터 | JYP Ent. | 035900.KS | `문화`, `성장`, `K-콘텐츠` |
| 게임 | 크래프톤 | 259960.KS | `문화`, `성장`, `글로벌` |
| 게임 | 엔씨소프트 | 036570.KS | `문화`, `기술`, `IP` |
| 콘텐츠 | CJ ENM | 035760.KS | `문화`, `내수`, `미디어` |
| 영화 | CGV | 079160.KS | `문화`, `경기민감`, `내수` |
| IT/플랫폼 | 카카오 | 035720.KS | `성장`, `내수`, `IP` |

**용도 태그 설명**
| 태그 | 설명 | 분석 활용 |
|------|------|-----------|
| `경기민감` | 경기 사이클에 민감 | 경기선행지표 상관분석 |
| `금리민감` | 금리 변동에 민감 | 기준금리 상관분석 |
| `수출` | 수출 비중 높음 | 환율 상관분석 |
| `내수` | 내수 비중 높음 | 소비심리 상관분석 |
| `성장` | 성장주 특성 | 성장 vs 가치 비교 |
| `배당` | 고배당 특성 | 배당주 분석 |
| `방어` | 방어적 성격 | 시장 하락기 분석 |
| `문화` | 문화/콘텐츠 산업 | K-콘텐츠 섹터 분석 |
| `기술` | 기술/IT 섹터 | 기술주 상관분석 |
| `IP` | IP(지적재산권) 기반 | IP사업 트렌드 분석 |

#### 경제지표 (한국은행 ECOS API)
| 지표 | 통계코드 | 항목코드 | 주기 |
|------|----------|----------|------|
| 원/달러 환율 | 731Y001 | 0000001 | D (일별) |
| 원/엔 환율 | 731Y001 | 0000002 | D |
| 원/유로 환율 | 731Y001 | 0000003 | D |
| 기준금리 | 722Y001 | 0101000 | M (월별) |
| 두바이유 가격 | 902Y007 | DUBAIOIL | D |
| 금 시세 | 902Y007 | GOLD | D |
| 콜금리 | 722Y001 | 0101000 | D |

> **참고**: 두바이유/금 시세는 ECOS API에서 no_data 반환됨

### 2.5 Cron 스케줄
```bash
# 라즈베리파이 crontab
0 8 * * * /home/raspi/influx_venv/bin/python /raspi/WD4T/01_scripts/01_data_collector.py   # 08:00 (매일)
0 16 * * 1-5 /home/raspi/influx_venv/bin/python /raspi/WD4T/01_scripts/01_data_collector.py # 16:00 (평일)
0 20 * * * /home/raspi/influx_venv/bin/python /raspi/WD4T/01_scripts/01_data_collector.py   # 20:00 (매일)
```

### 2.6 출력 스키마

#### news.csv
| 컬럼 | 설명 |
|------|------|
| timestamp | 수집 시간 |
| keyword | 검색 키워드 |
| title | 뉴스 제목 |
| link | 뉴스 링크 |
| description | 뉴스 요약 |
| pubDate | 발행일 |
| status | 수집 상태 (success/error) |

#### stock.csv
| 컬럼 | 설명 |
|------|------|
| timestamp | 수집 시간 |
| name | 종목명 |
| ticker | 티커 |
| open | 시가 |
| high | 고가 |
| low | 저가 |
| close | 종가 |
| volume | 거래량 |
| status | 수집 상태 |

#### economy.csv
| 컬럼 | 설명 |
|------|------|
| timestamp | 수집 시간 |
| indicator | 지표명 |
| value | 값 |
| date | 지표 기준일 |
| status | 수집 상태 |

---

## 3. 02_collect_15year_historical.py (15년 히스토리)

### 3.1 용도
- **15년치 과거 데이터 1회성 수집 (2010-2025)**
- 3개 기간으로 분할 수집 → CSV 병합

### 3.2 수집 기간 (3단계)
```python
# Period 1: 2010-2014 (5년)
# Period 2: 2015-2019 (5년)
# Period 3: 2020-2025 (5년)
```

### 3.3 데이터 소스
- **주가**: yfinance (한국 27종목 + 미국 11종목)
- **경제지표**: FRED API (미국 경제지표)
- **환율/금리**: 한국은행 ECOS API

### 3.4 저장 경로 (라즈베리파이)
```python
BASE_DIR = "/raspi/WD4T/00_data_raw/archive"
# korean_stocks_*.csv (3개 파일)
# us_stocks_*.csv (3개 파일)
# fred_indicators_*.csv (3개 파일)
# ecos_*.csv (3개 파일)
```

### 3.5 실행 방법
```bash
# 라즈베리파이
source ~/influx_venv/bin/activate
python /raspi/WD4T/01_scripts/02_collect_15year_historical.py
```

### 3.6 수집 결과 (2025-12-03 기준)
| 데이터 | 파일명 | 레코드 | 기간 |
|--------|--------|--------|------|
| 한국 주가 (Period 1) | korean_stocks_2010_2014.csv | 21,243건 | 2010-2014 |
| 한국 주가 (Period 2) | korean_stocks_2015_2019.csv | 21,195건 | 2015-2019 |
| 한국 주가 (Period 3) | korean_stocks_2020_2025.csv | 21,752건 | 2020-2025 |
| 미국 주가 (Period 1) | us_stocks_2010_2014.csv | 11,231건 | 2010-2014 |
| 미국 주가 (Period 2) | us_stocks_2015_2019.csv | 10,423건 | 2015-2019 |
| 미국 주가 (Period 3) | us_stocks_2020_2025.csv | 10,362건 | 2020-2025 |
| FRED (Period 1) | fred_indicators_2010_2014.csv | 6,425건 | 2010-2014 |
| FRED (Period 2) | fred_indicators_2015_2019.csv | 6,425건 | 2015-2019 |
| FRED (Period 3) | fred_indicators_2020_2025.csv | 6,425건 | 2020-2025 |
| ECOS (Period 1) | ecos_2010_2014.csv | 1,458건 | 2010-2014 |
| ECOS (Period 2) | ecos_2015_2019.csv | 1,458건 | 2015-2019 |
| ECOS (Period 3) | ecos_2020_2025.csv | 1,461건 | 2020-2025 |

---

## 4. collect_gdp_only.py (한국 GDP)

### 4.1 용도
- 한국 분기별 GDP 데이터 수집
- **ECOS API 통계코드: 200Y102** (주요지표-분기지표)

### 4.2 수집 항목 (52개)
| 항목 예시 | 설명 |
|----------|------|
| 국내총생산(GDP)(계절조정,실질) | 실질 GDP |
| 민간소비 | 민간 소비 지출 |
| 정부소비 | 정부 소비 지출 |
| 설비투자 | 기업 설비 투자 |
| 건설투자 | 건설 부문 투자 |
| 수출(재화와 서비스) | 총 수출액 |
| 수입(재화와 서비스) | 총 수입액 |

### 4.3 수집 기간
```python
# 2010Q1 ~ 2025Q4 (15년, 분기별)
# 총 52개 항목 × 60분기 = 3,120건
```

### 4.4 저장 경로
```python
OUTPUT_FILE = "/raspi/WD4T/00_data_raw/archive/gdp_2010_2025.csv"
```

### 4.5 실행 방법
```bash
source ~/influx_venv/bin/activate
python /raspi/WD4T/01_scripts/collect_gdp_only.py
```

### 4.6 수집 결과
- **총 3,319건** (52개 항목 × 60분기 + 일부 추가 데이터)
- CSV 스키마: `date, indicator, value, series_id`

---

## 5. 03_merge_historical_data.py (CSV 병합)

### 5.1 용도
- 3개 기간 CSV 파일 → 1개 통합 파일
- 중복 제거 및 날짜 정렬

### 5.2 병합 대상
```python
# 입력 (12개 파일)
korean_stocks_2010_2014.csv
korean_stocks_2015_2019.csv
korean_stocks_2020_2025.csv
us_stocks_2010_2014.csv
us_stocks_2015_2019.csv
us_stocks_2020_2025.csv
fred_indicators_2010_2014.csv
fred_indicators_2015_2019.csv
fred_indicators_2020_2025.csv
ecos_2010_2014.csv
ecos_2015_2019.csv
ecos_2020_2025.csv
gdp_2010_2025.csv

# 출력 (4개 파일)
stock_korean_merged.csv
stock_us_merged.csv
economy_fred_merged.csv
economy_ecos_merged.csv
```

### 5.3 중복 제거 로직
```python
# 주가: 날짜 + 종목명으로 중복 판단
stock_df.drop_duplicates(subset=['date', 'name'], keep='last')

# 경제지표: 날짜 + 지표명으로 중복 판단 (GDP 보존)
economy_df.drop_duplicates(subset=['date', 'indicator'], keep='last')
```

### 5.4 실행 방법
```bash
source ~/influx_venv/bin/activate
python /raspi/WD4T/01_scripts/03_merge_historical_data.py
```

### 5.5 병합 결과 (2025-12-03)
| 파일명 | 레코드 | 종목/지표 | 기간 |
|--------|--------|-----------|------|
| stock_korean_merged.csv | 64,190건 | 27종목 | 2010-2025 |
| stock_us_merged.csv | 32,016건 | 11종목 | 2010-2025 |
| economy_fred_merged.csv | 19,275건 | 5지표 | 2010-2025 |
| economy_ecos_merged.csv | 2,831건 | 56지표 | 2010-2025 |

---

## 6. 04_influxdb_backfill_15years.py (InfluxDB 백필)

### 6.1 용도
- 병합된 15년 CSV → InfluxDB 적재
- 상시 모니터링 시스템 구축

### 6.2 InfluxDB 설정
```python
# 환경변수(.env)에서 로드 - 직접 하드코딩 금지
from config import config

INFLUXDB_URL = config.INFLUXDB_URL
INFLUXDB_TOKEN = config.INFLUXDB_TOKEN
INFLUXDB_ORG = config.INFLUXDB_ORG
INFLUXDB_BUCKET = config.INFLUXDB_BUCKET
```

### 6.3 데이터 모델
| Measurement | Tags | Fields |
|-------------|------|--------|
| stock_prices | name, ticker | open, high, low, close, volume |
| economic_indicators | indicator, source, period | value |

### 6.4 실행 방법
```bash
source ~/influx_venv/bin/activate
python /raspi/WD4T/01_scripts/04_influxdb_backfill_15years.py
```

### 6.5 백필 결과 (2025-12-03)
| 데이터 | 레코드 | 비고 |
|--------|--------|------|
| 한국 주가 | 64,190건 | 27종목 |
| 미국 주가 | 32,016건 | 11종목 |
| FRED 지표 | 19,275건 | 5지표 |
| ECOS 지표 | 2,831건 | CPI + GDP 56지표 |
| **총합** | **118,312건** | 2010-2025 |

---

## 7. 05_create_grafana_dashboard_v2.py (대시보드 생성)

### 7.1 용도
- Grafana 대시보드 JSON 자동 생성
- 4행 레이아웃, 8개 패널 구성

### 7.2 대시보드 구조
| 행 | 패널 | 데이터 소스 | 지표 |
|----|------|-------------|------|
| 1행 | 한국 지수 + ETF | InfluxDB | 코스피, 코스닥, KODEX200 |
| 1행 | GDP/CPI | InfluxDB | GDP, CPI (분기/월별) |
| 2행 | 한국 대형주 | InfluxDB | 삼성전자, SK하이닉스, LG에너지솔루션, 삼성바이오, 현대차, KB금융 |
| 2행 | IT 플랫폼 | InfluxDB | NAVER, 카카오, POSCO홀딩스 |
| 3행 | 엔터/게임 | InfluxDB | HYBE, SM, JYP, 크래프톤, 엔씨소프트, CJ ENM, CGV |
| 3행 | 미국 지수 + 변동성 | InfluxDB | S&P500, 나스닥, VIX |
| 4행 | 환율/금리 | InfluxDB | 원/달러, 원/엔, 원/유로, 기준금리 |
| 4행 | 뉴스 빈도 | InfluxDB | 키워드별 뉴스 수 |

### 7.3 Flux 쿼리 최적화
```python
# 범례 레이블 단순화 (종목명만 표시)
|> map(fn: (r) => ({ r with _field: r.name }))
|> drop(columns: ["name", "ticker"])

# 경제지표 레이블 단순화
|> map(fn: (r) => ({ r with _field: r.indicator }))
|> drop(columns: ["indicator", "source", "period"])
```

### 7.4 실행 방법
```bash
source ~/influx_venv/bin/activate
python /raspi/WD4T/01_scripts/05_create_grafana_dashboard_v2.py
```

### 7.5 출력 파일
```
/raspi/WD4T/03_outputs/grafana_dashboard_final.json
```

---

## 8. 06_upload_grafana_dashboard.py (자동 업로드)

### 8.1 용도
- Grafana API로 대시보드 자동 업로드
- 수동 JSON 붙여넣기 불필요

### 8.2 Grafana 설정
```python
# 환경변수(.env)에서 로드 - 직접 하드코딩 금지
from config import config

GRAFANA_URL = config.GRAFANA_URL
GRAFANA_USER = config.GRAFANA_USER
GRAFANA_PASSWORD = config.GRAFANA_PASSWORD
```

### 8.3 실행 방법
```bash
source ~/influx_venv/bin/activate
python /raspi/WD4T/01_scripts/06_upload_grafana_dashboard.py
```

### 8.4 업로드 결과
- 대시보드 제목: "15년 히스토리 데이터 모니터링 (GDP 포함)"
- URL: `http://112.167.173.132:3000/d/55cf3a41-b6d2-48ad-8f98-1ec417944655`
- 패널 수: 8개
- overwrite: True (기존 대시보드 덮어쓰기)

---

## 9. collect_historical_news.py (뉴스 수집)

### 9.1 용도
- 네이버 API로 뉴스 수집
- API 한계: **과거 날짜 필터링 미지원** (최신 뉴스만 수집)

### 9.2 설정
```python
KEYWORDS = ["경제", "부동산", "반도체", "코스피"]
NEWS_PER_KEYWORD = 100  # API 최대 한도
```

### 9.3 저장 경로
```python
BASE_DIR = r"R:\00_data_raw"
NEWS_DIR = f"{BASE_DIR}/news"  # news_historical.csv
```

### 9.4 실행 방법
```bash
python R:/01_scripts/collect_historical_news.py
```

### 9.5 한계 및 대안
| 문제 | 대안 |
|------|------|
| 네이버 API는 과거 날짜 필터링 미지원 | 빅카인즈 수동 다운로드 |
| 최신 2~3일 뉴스만 수집됨 | https://www.bigkinds.or.kr |

---

## 10. preprocessor.py (전처리)

### 10.1 용도
- 원본 데이터 정제 및 파생컬럼 생성
- historical/daily 파일 선택 가능

### 10.2 데이터 소스 설정
```python
# 15년치 데이터 사용 (기본값)
USE_HISTORICAL = True

# 최근 수집 데이터 사용
USE_HISTORICAL = False
```

### 10.3 경로 설정
```python
BASE_DIR = "R:/"
DATA_DIR = f"{BASE_DIR}00_data_raw"        # 입력
OUTPUT_DIR = f"{BASE_DIR}00-1_data_processed"  # 출력
```

### 10.4 실행 방법
```bash
python R:/01_scripts/preprocessor.py
```

### 10.5 전처리 작업

#### 뉴스 (news_processed.csv)
| 작업 | 설명 |
|------|------|
| HTML 제거 | `<b>`, `</b>` 등 태그 제거 |
| 세션 분류 | pre (09시 이전), regular (09~16시), post (16시 이후) |
| 중복 제거 | 같은 제목 + 같은 날짜 |
| 정렬 | 시간순 오름차순 |

#### 주가 (stock_processed.csv)
| 파생컬럼 | 계산식 | 용도 |
|----------|--------|------|
| log_return | ln(close / close[-1]) | 수익률 분석 |
| volatility_20d | std(log_return, 20) × √252 | 연율화 변동성 |
| volume_zscore | (vol - ma20) / std20 | 거래량 이상치 탐지 |
| volume_ma5 | ma(volume, 5) | 거래량 추세 |

#### 경제지표 (economy_processed.csv)
| 파생컬럼 | 계산식 | 용도 |
|----------|--------|------|
| is_holiday_gap | value.isna() | 휴일 갭 플래그 |
| pct_1d | (v - v[-1]) / v[-1] × 100 | 일간 변동률 |
| pct_1w | (v - v[-5]) / v[-5] × 100 | 주간 변동률 |
| pct_1m | (v - v[-20]) / v[-20] × 100 | 월간 변동률 |
| event_flag | (수동 입력) | 이벤트 태깅용 |

---

## 11. dashboard.py (대시보드)

### 11.1 용도
- Streamlit 기반 인터랙티브 대시보드
- Plotly 차트 활용

### 11.2 실행 방법
```bash
streamlit run R:/01_scripts/dashboard.py
```

### 11.3 의존성
```
streamlit==1.51.0
plotly==6.5.0
pandas
numpy
```

### 11.4 탭 구성
| 탭 | 내용 |
|----|------|
| 📈 개요 | KPI 카드 (코스피, 코스닥, 환율, 뉴스) + 차트 이미지 |
| 💹 주가 분석 | 종목별 종가, 누적수익률, 거래량 |
| 💱 경제지표 | 지표별 추이, 변동률 테이블 |
| 📰 뉴스 분석 | 일간 기사 수, 키워드 분포, 최근 뉴스 |
| 🔗 상관관계 | 종목간 상관 히트맵, 환율-코스피 롤링 상관 |

### 11.5 데이터 경로
```python
DATA_DIR = BASE_DIR / "00-1_data_processed"  # 전처리된 데이터
OUTPUT_DIR = BASE_DIR / "03_outputs"          # 차트 이미지
```

---

## 12. 수정 가이드

### 12.1 종목 추가/제거

**data_collector.py** (일간):
```python
# 104~122행: tickers 딕셔너리 수정
tickers = {
    "종목명": "티커",
    # ...
}
```

**collect_15year_historical.py** (15년):
```python
# tickers 딕셔너리 수정
tickers = {
    "종목명": "티커",
    # ...
}
```

### 12.2 뉴스 키워드 추가/제거

**data_collector.py**:
```python
# 27행: keywords 리스트 수정
keywords = ["경제", "부동산", "반도체", "코스피", "새키워드"]
```

**collect_historical_news.py**:
```python
# 27행: KEYWORDS 리스트 수정
KEYWORDS = ["경제", "부동산", "반도체", "코스피", "새키워드"]
```

### 12.3 경제지표 추가

**data_collector.py**:
```python
# 186~194행: indicators 리스트에 튜플 추가
indicators = [
    (URL, "지표명"),
    # ...
]
```

**collect_15year_historical.py**:
```python
# FRED_INDICATORS 또는 ECOS_INDICATORS에 추가
FRED_INDICATORS = ["DGS10", "UNRATE", ...]
```

### 12.4 수집 주기 변경

**뉴스 수집량**:
```python
# data_collector.py 38행
params = {"display": 5}  # 키워드당 5건 → 10건 등

# collect_historical_news.py 28행
NEWS_PER_KEYWORD = 100  # 최대 100건 (API 한도)
```

### 12.5 전처리 옵션 변경

**데이터 소스 변경**:
```python
# preprocessor.py 26행
USE_HISTORICAL = True   # 15년치 데이터
USE_HISTORICAL = False  # 최근 수집 데이터
```

---

## 13. API 제한 사항

| API | 제한 | 비고 |
|-----|------|------|
| 네이버 검색 | 일 25,000건 | 키워드당 100건 최대 |
| yfinance | 없음 | 단, IP 차단 주의 |
| 한국은행 ECOS | 1회 100,000건 | 키당 일 3,000건 |

---

## 14. 파일 구조

```
01_scripts/
├── 99_DATACOLLECT.md                      # 이 문서
├── config.py                              # 설정 관리 (환경변수 로드)
├── 01_data_collector.py                   # 일간 수집 (Cron, CSV + InfluxDB)
├── 02_collect_15year_historical.py        # 15년 데이터 수집 (1회성)
├── collect_gdp_only.py                    # 한국 GDP 수집 (1회성)
├── 03_merge_historical_data.py            # CSV 병합 (1회성)
├── 04_influxdb_backfill_15years.py        # InfluxDB 백필 (1회성)
├── 05_create_grafana_dashboard_v2.py      # Grafana 대시보드 생성
├── 06_upload_grafana_dashboard.py         # Grafana 대시보드 자동 업로드
├── collect_historical_news.py             # 뉴스 수집 (네이버 API)
├── preprocessor.py                        # 전처리
└── dashboard.py                           # Streamlit 대시보드
```

---

## 15. 관련 문서

| 문서 | 위치 | 내용 |
|------|------|------|
| CLAUDE | `CLAUDE.md` | 프로젝트 개요 및 작업 지침 |
| PRD | `99_docs/PRD.md` | 프로젝트 요구사항 |
| ARCHITECTURE | `99_docs/ARCHITECTURE.md` | 시스템 구조도 |
| CHANGELOG | `99_docs/CHANGELOG.md` | 변경 이력 |
| DATA_SOURCE_POLICY | `99_docs/DATA_SOURCE_POLICY.md` | 데이터 소스 정책 |
| DASHBOARD_DESIGN | `99_docs/DASHBOARD_DESIGN.md` | 대시보드 설계 |
| ANALYSIS_GUIDE | `02_notebooks/ANALYSIS_GUIDE.md` | 분석 노트북 가이드 |

---

*최종 업데이트: 2025-12-03*
