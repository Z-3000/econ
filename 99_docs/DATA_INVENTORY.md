# 데이터 파일 목록 (Data Inventory)

> 생성일: 2026-01-06  
> 목적: 00_data_raw 및 00-1_data_processed 폴더의 데이터 파일 구조 정리

---

## 📁 폴더 구조

```
econ/
├── 00_data_raw/              # 원본 데이터 (가공 전)
│   ├── economy_ecos_2010_2025.csv
│   ├── economy_fred_2010_2025.csv
│   ├── stock_kr_2010_2025.csv
│   ├── stock_us_2010_2025.csv
│   ├── economy/              # 하위 폴더
│   ├── news/                 # 하위 폴더
│   ├── stock/                # 하위 폴더
│   └── archive/              # 백업 폴더
│
└── 00-1_data_processed/      # 가공된 데이터 (분석용)
    ├── economy_processed.csv
    ├── etf_1year_prediction.csv
    ├── news_processed.csv
    └── stock_processed.csv
```

---

## 📊 00-1_data_processed (가공 데이터)

### 1. economy_processed.csv

**파일 경로**: `00-1_data_processed/economy_processed.csv`  
**데이터 행 수**: 4,447개  
**컬럼 수**: 9개  
**기간**: 2020-01-01 00:00:00 ~ 2025-12-02 00:00:00  

**컬럼 목록**:
- `date`
- `indicator`
- `value`
- `period`
- `is_holiday_gap`
- `pct_1d`
- `pct_1w`
- `pct_1m`
- `event_flag`

**샘플 데이터** (상위 3행):

| date | indicator | value | period | is_holiday_gap | pct_1d | pct_1w | pct_1m | event_flag |
|---|---|---|---|---|---|---|---|---|
| 2020-01-01 | 기준금리 | 1.25 | M | False | nan | nan | nan | nan |
| 2020-02-01 | 기준금리 | 1.25 | M | False | 0.0 | nan | nan | nan |
| 2020-03-01 | 기준금리 | 0.75 | M | False | -40.0 | nan | nan | nan |

---

### 2. etf_1year_prediction.csv

**파일 경로**: `00-1_data_processed/etf_1year_prediction.csv`  
**데이터 행 수**: 42개  
**컬럼 수**: 13개  

**컬럼 목록**:
- `ticker`
- `name`
- `historical_mean_1y`
- `historical_median_1y`
- `historical_std_1y`
- `positive_probability`
- `recent_momentum_6m`
- `recent_volatility`
- `predicted_1y_return`
- `prediction_lower`
- `prediction_upper`
- `risk_adjusted_score`
- `total_score`

**샘플 데이터** (상위 3행):

| ticker | name | historical_mean_1y | historical_median_1y | historical_std_1y | positive_probability | recent_momentum_6m | recent_volatility | predicted_1y_return | prediction_lower | prediction_upper | risk_adjusted_score | total_score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 360750.KS | TIGER 미국S&P500 | 0.2040203480987713 | 0.2063025702031953 | 0.152059233089921 | 0.8950437317784257 | 0.2193075714020567 | 0.1987305638102846 | 0.1829481327133702 | -0.0451407169215113 | 0.4110369823482518 | 0.9205837753674322 | 61.78675052291055 |
| 133690.KS | TIGER 미국나스닥100 | 0.2180236131259685 | 0.2135182588616999 | 0.1570021581304026 | 0.9365910413030832 | 0.2441098425188022 | 0.2412415005672185 | 0.1990719292934454 | -0.0364313079021585 | 0.4345751664890495 | 0.8251976912155581 | 60.81653914729705 |
| NUSI | Nationwide Risk-Managed Income | 0.3810923648264016 | 0.2638394636416397 | 0.5068681216895299 | 0.789049919484702 | 0.1135589211747689 | 1.0109114682768046 | 0.5742671143987982 | -0.1860350681354966 | 1.334569296933093 | 0.5680686513307555 | 60.71355712446372 |

---

### 3. news_processed.csv

**파일 경로**: `00-1_data_processed/news_processed.csv`  
**데이터 행 수**: 962개  
**컬럼 수**: 9개  
**기간**: 2025-11-06 09:38:00 ~ 2025-11-30 08:00:02  

**컬럼 목록**:
- `timestamp`
- `keyword`
- `title`
- `link`
- `description`
- `pubDate`
- `Unnamed: 6`
- `date`
- `session`

**샘플 데이터** (상위 3행):

| timestamp | keyword | title | link | description | pubDate | Unnamed: 6 | date | session |
|---|---|---|---|---|---|---|---|---|
| 2025-11-06 09:38:00 | 경제 | WWF “COP30, 약속에서 행동으로 전환하는 분기점 돼야” | https://www.naeil.com/news/read/566729?ref=naver | 혼란과 경제적 피해로 이어질 것”이라고 밝혔다. 박 총장은 또 “‘기후에너지환경부’ 확대  | Thu, 06 Nov 2025 18:38:00 +0900 | nan | 2025-11-06 | regular |
| 2025-11-06 09:38:00 | 금리 | 은행계열 캐피탈채도 '오버 두자리' 거래…&quot;지옥같은 하루&quot; | https://news.einfomax.co.kr/news/articleView.html? | 은행 계열 캐피탈사가 발행한 채권이 민평금리보다 크게 높은 수준에 거래되는 등 크레디트 시 | Thu, 06 Nov 2025 18:26:00 +0900 | nan | 2025-11-06 | regular |
| 2025-11-06 09:38:00 | 금리 | 동덕여대, '2025년 경제학과 학술제' 성료 | https://www.joongangenews.com/news/articleView.htm | 2부 학술제 발표에서는 총 5팀이 참여했으며 △플랫폼 경제로 인한 독과점 문제와 앞으로의  | Thu, 06 Nov 2025 18:26:00 +0900 | nan | 2025-11-06 | regular |

---

### 4. stock_processed.csv

**파일 경로**: `00-1_data_processed/stock_processed.csv`  
**데이터 행 수**: 38,319개  
**컬럼 수**: 12개  
**기간**: 2020-01-02 00:00:00 ~ 2025-12-01 00:00:00  

**컬럼 목록**:
- `date`
- `name`
- `ticker`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `log_return`
- `volatility_20d`
- `volume_zscore`
- `volume_ma5`

**샘플 데이터** (상위 3행):

| date | name | ticker | open | high | low | close | volume | log_return | volatility_20d | volume_zscore | volume_ma5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020-01-02 | SK하이닉스 | 000660.KS | 90285.49102428724 | 90473.58579725448 | 88498.5906810982 | 89062.875 | 2342070 | nan | nan | nan | nan |
| 2020-01-03 | SK하이닉스 | 000660.KS | 90755.72900132276 | 92072.39242724868 | 88686.68647486772 | 88874.78125 | 3021380 | -0.0021141541821269 | nan | nan | nan |
| 2020-01-06 | SK하이닉스 | 000660.KS | 87464.04833311241 | 89627.13770049046 | 87275.95360551433 | 88686.6640625 | 2577573 | -0.0021188975743221 | nan | nan | 2647007.6666666665 |

---

## 📦 00_data_raw (원본 데이터)

### 1. economy_ecos_2010_2025.csv

**파일 경로**: `00_data_raw/economy_ecos_2010_2025.csv`  
**데이터 행 수**: 445개  
**컬럼 수**: 4개  
**기간**: 2010-01-01 00:00:00 ~ 2025-11-01 00:00:00  

**컬럼 목록**:
- `date`
- `indicator`
- `value`
- `series_id`

**샘플 데이터** (상위 3행):

| date | indicator | value | series_id |
|---|---|---|---|
| 2010-03-01 | 한국 GDP 주요지표 | 11878.1 | 200Y102_ |
| 2010-06-01 | 한국 GDP 주요지표 | 16189.6 | 200Y102_ |
| 2010-09-01 | 한국 GDP 주요지표 | 18355.3 | 200Y102_ |

---

### 2. economy_fred_2010_2025.csv

**파일 경로**: `00_data_raw/economy_fred_2010_2025.csv`  
**데이터 행 수**: 19,275개  
**컬럼 수**: 4개  
**기간**: 2010-01-01 00:00:00 ~ 2025-12-01 00:00:00  

**컬럼 목록**:
- `date`
- `indicator`
- `value`
- `series_id`

**샘플 데이터** (상위 3행):

| date | indicator | value | series_id |
|---|---|---|---|
| 2010-01-01 | 미국 CPI | 217.488 | CPIAUCSL |
| 2010-02-01 | 미국 CPI | 217.281 | CPIAUCSL |
| 2010-03-01 | 미국 CPI | 217.353 | CPIAUCSL |

---

### 3. stock_kr_2010_2025.csv

**파일 경로**: `00_data_raw/stock_kr_2010_2025.csv`  
**데이터 행 수**: 83,968개  
**컬럼 수**: 8개  
**기간**: 2010-01-04 00:00:00 ~ 2025-12-02 00:00:00  

**컬럼 목록**:
- `date`
- `name`
- `ticker`
- `open`
- `high`
- `low`
- `close`
- `volume`

**샘플 데이터** (상위 3행):

| date | name | ticker | open | high | low | close | volume |
|---|---|---|---|---|---|---|---|
| 2010-01-04 | SK하이닉스 | 000660.KS | 19909.30771038641 | 20591.42531930757 | 19909.30771038641 | 20548.79296875 | 7327477 |
| 2010-01-05 | SK하이닉스 | 000660.KS | 20889.8567987152 | 21230.91568522484 | 19653.518335117773 | 19909.3125 | 12080229 |
| 2010-01-06 | SK하이닉스 | 000660.KS | 20207.732521321283 | 20932.482421875 | 20122.46782713849 | 20932.482421875 | 7698642 |

---

### 4. stock_us_2010_2025.csv

**파일 경로**: `00_data_raw/stock_us_2010_2025.csv`  
**데이터 행 수**: 134,470개  
**컬럼 수**: 8개  
**기간**: 2010-01-04 00:00:00 ~ 2025-12-02 00:00:00  

**컬럼 목록**:
- `date`
- `name`
- `ticker`
- `open`
- `high`
- `low`
- `close`
- `volume`

**샘플 데이터** (상위 3행):

| date | name | ticker | open | high | low | close | volume |
|---|---|---|---|---|---|---|---|
| 2016-11-10 | Direxion CSI China Internet 2x | CWEB | 201.5062255859375 | 201.7725360820784 | 201.41745090551905 | 201.5062255859375 | 50 |
| 2016-11-11 | Direxion CSI China Internet 2x | CWEB | 201.5062255859375 | 201.5062255859375 | 201.5062255859375 | 201.5062255859375 | 0 |
| 2016-11-14 | Direxion CSI China Internet 2x | CWEB | 201.6838199282219 | 244.82568583358983 | 184.1074981689453 | 184.1074981689453 | 240 |

---

## 🎯 파일 용도 정리

| 파일명 | 데이터 출처 | 용도 | 특징 |
|--------|-------------|------|------|
| **economy_ecos_2010_2025.csv** | 한국은행 ECOS | 한국 경제지표 원본 | 기준금리, CPI 등 |
| **economy_fred_2010_2025.csv** | 미국 FRED | 미국 경제지표 원본 | 금리, GDP, 실업률 등 |
| **stock_kr_2010_2025.csv** | 한국 증시 | 한국 ETF/주식 원본 | KODEX, TIGER 등 |
| **stock_us_2010_2025.csv** | 미국 증시 | 미국 ETF 원본 | SPY, QQQ, GLD 등 |
| **economy_processed.csv** | 위 데이터 병합 | InfluxDB 적재용 | 정제된 경제지표 |
| **stock_processed.csv** | 위 데이터 병합 | InfluxDB 적재용 | 정제된 주가 데이터 |
| **news_processed.csv** | 뉴스 크롤링 | InfluxDB 적재용 | 뉴스 제목/요약 |
| **etf_1year_prediction.csv** | ML 예측 결과 | 분석용 | ETF 1년 예측값 |

---

## 🔄 데이터 처리 흐름

```
[원본 데이터 수집]
    ↓
00_data_raw/
    ├── economy_ecos_2010_2025.csv  (한국 경제지표)
    ├── economy_fred_2010_2025.csv  (미국 경제지표)
    ├── stock_kr_2010_2025.csv      (한국 주식)
    └── stock_us_2010_2025.csv      (미국 주식)
    ↓
[데이터 정제 & 병합]
01_scripts/03_merge_historical_data.py
    ↓
00-1_data_processed/
    ├── economy_processed.csv       (병합된 경제지표)
    ├── stock_processed.csv         (병합된 주가)
    ├── news_processed.csv          (뉴스 데이터)
    └── etf_1year_prediction.csv    (ML 예측)
    ↓
[InfluxDB 적재]
01_scripts/01_data_collector.py
    ↓
[Grafana 시각화]
```

---

## 📝 참고사항

1. **원본 데이터(00_data_raw)**: 절대 수정하지 말 것 (백업 목적)
2. **가공 데이터(00-1_data_processed)**: 분석 및 InfluxDB 적재용
3. **데이터 갱신**: `01_scripts/01_data_collector.py` 실행 시 자동 갱신
4. **백업**: `00_data_raw/archive/` 폴더에 이전 버전 보관

---

## 🔗 관련 문서

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 시스템 아키텍처
- [DATA_SOURCE_POLICY.md](./DATA_SOURCE_POLICY.md) - 데이터 소스 정책
- [PROGRESS.md](./PROGRESS.md) - 프로젝트 진행 상황

---


---

<!-- DOC_UPDATE_2026-02-25 -->
## 인벤토리 최신화 (2026-02-25)
### 신규/변경 자산
- 백필 입력 파일
  - `00_data_raw/stock_kr_2010_2025_with_adj.csv`
  - `00_data_raw/stock_us_2010_2025_with_adj.csv`
- 정합성 리포트
  - `98_logs/dq_econ_market.json`
  - `98_logs/dq_econ_market_backfill_2010_2025.json`
- 검증 스크립트
  - `01_scripts/09_validate_influx_integrity.py`

### 버킷 구분
- 운영: `econ_market`
- 백필 검증: `econ_market_backfill_2010_2025`
