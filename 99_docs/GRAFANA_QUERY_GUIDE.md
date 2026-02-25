# Grafana 쿼리 업데이트 가이드 (일봉 대표성 강화)

## 배경
- 주가 수집이 장마감 확정 일봉만 적재하도록 변경되면서 `stock_prices` 측정값에 `adj_close`와 `status_code`(1=success, 0=stale) 필드가 추가됨.
- 게시 지연된 바(`stale`)가 섞이지 않도록 대시보드 Flux 쿼리에 필터를 넣어야 함.

## 공통 쿼리 패턴
```flux
from(bucket: "econ_market")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r._field == "close")            // 또는 "adj_close"
  |> filter(fn: (r) => r.status_code == 1)              // 확정 일봉만
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> map(fn: (r) => ({ r with _field: r.name }))
  |> drop(columns: ["name", "ticker", "status_code"])
```

## 패널 유형별 적용
- **라인 차트(여러 종목)**: `_field`를 종목명으로 매핑 후 `status_code` 필터를 추가. 위 공통 패턴 사용.
- **단일 지표 패널**: `filter(name == "코스피")` 뒤에 `status_code == 1` 필터 추가.
- **테이블/Stat에서 지연 여부 표시**: 필터를 제거하고 `keep(["_time","_value","status_code","name"])`로 남겨 색상규칙을 `status_code`에 매핑.

## adj_close 사용 시
- `_field == "adj_close"`로 교체하거나, 두 필드를 비교해야 할 경우 `pivot` 후 계산.
```flux
|> filter(fn: (r) => r._field == "adj_close" or r._field == "close")
|> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
|> map(fn: (r) => ({ r with premium: (r.close - r.adj_close) }))
```

## 적용 체크리스트
- [ ] 각 패널 Flux에 `status_code == 1` 필터 추가 (예외: 지연 표시용 패널).
- [ ] `_field`가 `close`인 패널을 `adj_close`로 전환할지 결정.
- [ ] `drop(columns: ["status_code"])`가 필터 전에 들어가 있지 않은지 확인.
- [ ] 변경 후 패널 리프레시/대시보드 저장.

## 참고
- 데이터 수집 스케줄: 06:10(미국), 15:40(한국) KST 1일 2회.
- Influx measurement: `stock_prices`에 `adj_close`, `status_code` 추가 (2026-02-25).

---


---

<!-- DOC_UPDATE_2026-02-25 -->
## Grafana 쿼리 운영 메모 (2026-02-25)
- 동일 패널을 운영/백필 버킷에서 모두 검증할 수 있도록 `bucket` 변수를 권장합니다.
- 백필 검증 시에는 `econ_market_backfill_2010_2025`를 기본값으로 사용합니다.
- 운영 버킷(`econ_market`)은 상시 수집 데이터가 섞여 있으므로 count 비교 시 `extra`가 자연 발생합니다.

## 추가 쿼리 권장
1. `stock_prices`에서 `date+ticker` 기준 중복/누락 확인 패널
2. `economic_indicators`에서 `period`별 건수 추이 패널
