# Grafana Flux 전처리 쿼리

> **목적**: Grafana 대시보드에서 사용 중인 Flux 쿼리 정리
> **작성일**: 2025-12-04
> **대시보드**: 경제·주가 통합 모니터링 (15년, GDP 포함)

---

## 전처리 원칙

> **"원본 데이터는 InfluxDB에 그대로 저장하고, Grafana에서 Flux 쿼리로 필터링·집계·변환한다."**

즉, Python으로 미리 가공하지 않고, 차트를 그릴 때 실시간으로 처리합니다.

---

## Flux란?

**Flux**는 InfluxDB에서 데이터를 조회하고 변환하는 언어입니다.
SQL과 비슷하지만, **파이프라인(`|>`)** 방식으로 데이터를 단계별로 처리합니다.

```
데이터 가져오기 → 시간 범위 지정 → 필터링 → 집계 → 변환 → 출력
```

**비유**: 물이 파이프를 통해 흐르듯, 데이터가 각 단계를 거쳐 최종 결과가 됩니다.

---

## 기본 구조 (모든 쿼리의 뼈대)

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.name }))
  |> drop(columns: ["name", "ticker"])
```

### 한 줄씩 해석

| 줄 | 코드 | 의미 | 비유 |
|----|------|------|------|
| 1 | `from(bucket: "econ_market")` | "econ_market" 저장소에서 데이터 가져오기 | 창고에서 상자 꺼내기 |
| 2 | `range(start:..., stop:...)` | 시간 범위 지정 (Grafana 화면의 시간 선택기와 연동) | "최근 1년치만 볼래" |
| 3 | `filter(fn: (r) => r._measurement == "...")` | 측정 종류 선택 (주가? 경제지표?) | "주가 데이터만 골라줘" |
| 4 | `filter(fn: (r) => r._field == "close")` | 필드 선택 (종가? 시가? 거래량?) | "종가만 볼래" |
| 5 | `aggregateWindow(every: 1d, fn: last)` | 시간 단위로 묶어서 집계 | "하루에 하나씩, 마지막 값으로" |
| 6 | `map(fn: (r) => ...)` | 데이터 변환 (범례 이름 바꾸기 등) | "라벨 붙이기" |
| 7 | `drop(columns: [...])` | 불필요한 컬럼 제거 | "필요 없는 정보 버리기" |

---

## 핵심 개념 설명

### 1. `_measurement` (측정 종류)

InfluxDB에서 데이터를 분류하는 첫 번째 기준입니다.

| _measurement | 저장된 데이터 |
|--------------|--------------|
| `stock_prices` | 주가 (코스피, 삼성전자, QQQ 등) |
| `economic_indicators` | 경제지표 (GDP, CPI, 금리, 환율 등) |

**예시**: "주가 데이터만 보고 싶다" → `r._measurement == "stock_prices"`

---

### 2. `_field` (필드)

하나의 데이터 포인트 안에 여러 값이 있을 수 있습니다.

**주가 데이터의 필드들**:
| _field | 의미 |
|--------|------|
| `open` | 시가 (장 시작 가격) |
| `high` | 고가 (하루 중 최고가) |
| `low` | 저가 (하루 중 최저가) |
| `close` | **종가** (장 마감 가격) ← 보통 이걸 씀 |
| `volume` | 거래량 |

**경제지표 데이터의 필드**:
| _field | 의미 |
|--------|------|
| `value` | 지표 값 |

---

### 3. `tag` (태그)

데이터를 구분하는 라벨입니다. 필터링에 사용합니다.

**주가 데이터의 태그들**:
| tag | 예시 |
|-----|------|
| `name` | "코스피", "삼성전자", "QQQ" |
| `ticker` | "^KS11", "005930.KS", "QQQ" |

**경제지표의 태그들**:
| tag | 예시 |
|-----|------|
| `indicator` | "한국 소비자물가지수", "연방기금금리" |
| `period` | "M" (월간), "Q" (분기) |

---

### 4. `aggregateWindow()` (시간 집계)

시간을 기준으로 데이터를 묶어서 하나의 값으로 만듭니다.

```flux
aggregateWindow(every: 1d, fn: last, createEmpty: false)
```

| 파라미터 | 의미 | 옵션 |
|----------|------|------|
| `every` | 묶는 단위 | `1d`(일), `1w`(주), `1mo`(월), `3mo`(분기), `1y`(년) |
| `fn` | 집계 함수 | `last`(마지막), `first`(처음), `mean`(평균), `max`(최대), `min`(최소) |
| `createEmpty` | 빈 구간 생성 | `false`로 하면 데이터 없는 날은 건너뜀 |

**왜 필요한가?**
- 하루에 데이터가 여러 개 있을 수 있음 (장중 여러 번 수집)
- 차트에는 "하루에 하나의 점"만 찍고 싶음
- → `every: 1d, fn: last` = "하루의 마지막 값만 사용"

---

## 1. 주가 쿼리

### 1-1. 한국 주가지수/ETF

**목적**: 코스피, 코스닥, KODEX200의 종가 추이를 본다

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "코스피" or r.name == "코스닥" or r.name == "KODEX200")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.name }))
  |> drop(columns: ["name", "ticker"])
```

**줄별 해석**:
1. `from(...)` → econ_market 버킷에서 데이터 가져오기
2. `range(...)` → Grafana에서 선택한 시간 범위 적용
3. `filter(_measurement)` → 주가 데이터만 선택
4. `filter(name)` → 코스피, 코스닥, KODEX200만 선택
5. `filter(_field)` → 종가(close)만 선택
6. `aggregateWindow` → 일별 마지막 값으로 집계
7. `map` → 범례에 종목명이 표시되도록 변환
8. `drop` → 차트에 불필요한 컬럼 제거

---

### 1-2. 미국 주가지수/ETF

**목적**: S&P500, 나스닥, 주요 ETF의 종가 추이를 본다

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "S&P500" or r.name == "나스닥" or r.name == "QQQ" or r.name == "SPY" or r.name == "DIA")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.name }))
  |> drop(columns: ["name", "ticker"])
```

**종목 변경하려면**: 4번째 줄의 `r.name == "..."` 부분을 수정

---

### 1-3. IT 플랫폼 (NAVER·카카오)

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "NAVER" or r.name == "카카오")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.name }))
  |> drop(columns: ["name", "ticker"])
```

---

### 1-4. 엔터테인먼트·게임

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "HYBE" or r.name == "SM" or r.name == "JYP Ent." or r.name == "크래프톤" or r.name == "엔씨소프트")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.name }))
  |> drop(columns: ["name", "ticker"])
```

---

### 1-5. 대형주 (반도체·자동차·금융)

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "삼성전자" or r.name == "SK하이닉스" or r.name == "현대차" or r.name == "KB금융")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.name }))
  |> drop(columns: ["name", "ticker"])
```

---

## 2. 경제지표 쿼리

### 2-1. 한국 GDP 성장률

**목적**: 한국 실질GDP 성장률 (전기비, 전년동기비) 추이를 본다

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator =~ /한국 GDP.*실질.*전기비/ or r.indicator =~ /한국 GDP.*실질.*전년동기비/)
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 3mo, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
```

**특별한 부분**:
- `r.indicator =~ /정규표현식/`: 정규식으로 지표명 매칭
  - `/한국 GDP.*실질.*전기비/` = "한국 GDP"로 시작하고 "실질"과 "전기비"가 포함된 모든 지표
- `every: 3mo`: GDP는 분기별 데이터이므로 3개월 단위로 집계

---

### 2-2. 미국 산업생산지수

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "미국 산업생산지수")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
```

**차이점**: `every: 1mo` - 산업생산지수는 월별 발표

---

### 2-3. 물가 (CPI)

**한국 CPI**:
```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "한국 소비자물가지수")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
```

**미국 CPI**:
```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "미국 CPI")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1mo, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
```

---

### 2-4. 미국 금리

**목적**: 연방기금금리와 10년 국채금리 비교

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "연방기금금리" or r.indicator == "미국 10년 국채금리")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
```

---

### 2-5. 환율 (USD/KRW)

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "USD/KRW 환율")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
```

---

### 2-6. 스케일 조정 예시 (값 변환)

**문제**: 환율(1,300원)과 금리(4.5%)를 같은 차트에 그리면 금리가 안 보임
**해결**: 금리에 100을 곱해서 스케일 맞추기

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "economic_indicators")
  |> filter(fn: (r) => r.indicator == "미국 10년 국채금리")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _value: r._value * 100.0, _field: r.indicator }))
  |> drop(columns: ["indicator", "series_id", "period"])
```

**핵심**: `_value: r._value * 100.0` → 값을 100배로 키움

---

## 3. 주요 Flux 함수 정리

| 함수 | 하는 일 | 예시 |
|------|---------|------|
| `from(bucket:)` | 데이터 저장소 선택 | `from(bucket: "econ_market")` |
| `range(start:, stop:)` | 시간 범위 지정 | `range(start: -1y)` = 최근 1년 |
| `filter(fn:)` | 조건에 맞는 데이터만 선택 | `filter(fn: (r) => r.name == "코스피")` |
| `aggregateWindow()` | 시간 단위로 묶어서 집계 | `aggregateWindow(every: 1d, fn: last)` |
| `map(fn:)` | 값이나 컬럼 변환 | `map(fn: (r) => ({ r with _value: r._value * 2 }))` |
| `drop(columns:)` | 컬럼 삭제 | `drop(columns: ["ticker"])` |
| `movingAverage(n:)` | 이동평균 계산 | `movingAverage(n: 20)` = 20일 이평 |
| `difference()` | 이전 값과의 차이 | 전일 대비 변동 계산에 사용 |

---

## 4. 집계 주기 가이드

| 데이터 유형 | 집계 주기 | 이유 |
|-------------|----------|------|
| 주가 | `1d` | 하루에 한 번 장 마감 |
| GDP | `3mo` | 분기별 발표 |
| CPI, 산업생산 | `1mo` | 월별 발표 |
| 금리, 환율 | `1d` | 매일 변동 |

---

## 5. 응용 쿼리 (나중에 써볼 것들)

### 5-1. 20일 이동평균선

**목적**: 코스피의 20일 이동평균 추이

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "코스피")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> movingAverage(n: 20)
```

**핵심**: `movingAverage(n: 20)` → 최근 20개 값의 평균

---

### 5-2. 전일 대비 변동량

```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "코스피")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> difference()
```

**핵심**: `difference()` → (오늘 값) - (어제 값)

---

### 5-3. 특정 기간만 보기 (코로나 급락장)

```flux
from(bucket: "econ_market")
  |> range(start: 2020-02-01T00:00:00Z, stop: 2020-04-30T00:00:00Z)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r.name == "코스피")
  |> filter(fn: (r) => r._field == "close")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
```

**핵심**: `range(start: 2020-02-01..., stop: 2020-04-30...)` → 고정된 날짜 범위

---

## 6. 자주 하는 실수

| 실수 | 증상 | 해결 |
|------|------|------|
| `_measurement` 오타 | 데이터가 안 나옴 | `stock_prices` 또는 `economic_indicators` 확인 |
| `name` vs `indicator` 혼동 | 필터가 안 먹음 | 주가는 `name`, 경제지표는 `indicator` 사용 |
| `every` 단위 잘못 지정 | 점이 너무 많거나 적음 | 데이터 주기에 맞게 `1d`, `1mo`, `3mo` 선택 |
| `createEmpty: true` | 빈 날짜에 0이 찍힘 | `createEmpty: false`로 변경 |

---

## 참고 자료

- InfluxDB Flux 공식 문서: https://docs.influxdata.com/flux/
- Grafana InfluxDB 연동: https://grafana.com/docs/grafana/latest/datasources/influxdb/
- Flux 함수 목록: https://docs.influxdata.com/flux/v0/stdlib/
