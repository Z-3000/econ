# CHANGELOG

## [2025-12-07] 문서 정리 및 통합

### 변경 내용
- **삭제된 파일** (중복/오래된 정보):
  - `raspi_influxdb_context.md` - PROGRESS.md로 대체
  - `SESSION_2025-12-03.md` - CHANGELOG.md로 대체
  - `INFLUXDB_EXTENSION_GUIDE.md` - ARCHITECTURE.md로 대체
  - `TODO.md` - PROGRESS.md에 통합
  - `FUTURE_ENHANCEMENTS.md` - PROGRESS.md에 통합

- **PROGRESS.md 통합 문서화**:
  - 진행 현황 + TODO 항목 + 장기 로드맵 + 우선순위 매트릭스
  - 한 문서에서 현재 상태와 향후 계획 파악 가능
  - 6개월 로드맵, 데이터 소스 확장 계획, 인프라 개선 계획 포함

### 현재 99_docs/ 파일 목록
| 파일 | 용도 |
|------|------|
| `PROGRESS.md` | 진행 현황 + TODO + 로드맵 (통합) |
| `ARCHITECTURE.md` | 시스템 아키텍처 |
| `CHANGELOG.md` | 변경 이력 |
| `PRD.md` | 제품 요구사항 |
| `DATA_SOURCE_POLICY.md` | 데이터 소스 정책 |
| `DASHBOARD_DESIGN.md` | 대시보드 설계 원칙 |
| `차트 분석 가이드 .md` | 초보자용 대시보드 해석 가이드 |
| `PORTFOLIO_SLIDE.md/pptx` | 포트폴리오 슬라이드 |
| `00_긴급_채용공고 대응.md` | 채용 대응 |
| `01_프로젝트_학습자료.md` | 학습 자료 |
| `02_운영기능_개발계획.md` | Phase 2.7 상세 계획 |
| `03_추가개발_아이디어.md` | 아이디어 메모 |

---

## [2025-12-07] Telegraf 시스템 모니터링 구현

### 배경
- 라즈베리파이 하드웨어 상태 모니터링 필요
- CPU 과열, 디스크 부족 등으로 인한 수집 중단 방지
- 채용공고 "하드웨어/서버 유지관리" 직무 매칭

### 구현 내용

#### 1. Telegraf 설치 및 설정
- **설치**: `sudo apt install telegraf`
- **설정 파일**: `/etc/telegraf/telegraf.d/raspi.conf`
- **수집 주기**: 60초
- **출력**: InfluxDB `econ_market` 버킷

#### 2. 수집 항목
| Measurement | 내용 |
|-------------|------|
| `cpu` | CPU 사용률 (idle, user, system) |
| `mem` | 메모리 사용량 (used, available, percent) |
| `disk` | 디스크 용량 (/, /raspi/WD4T) |
| `cpu_temp` | CPU 온도 (밀리섭씨) |
| `net` | 네트워크 트래픽 (eth0, tailscale0) |
| `diskio` | 디스크 I/O (mmcblk0) |
| `system` | 시스템 업타임 |

#### 3. 시스템 헬스 대시보드 생성
- **스크립트**: `01_scripts/07_create_system_health_dashboard.py`
- **대시보드 UID**: `system-health-raspi5`
- **패널 수**: 12개

**1행: 요약 게이지 (6개)**
- CPU 사용률, 메모리 사용률, 디스크 사용률, CPU 온도, 업타임, 디스크 여유

**2행: 시계열 차트 (3개)**
- CPU 사용률 추이, 메모리 사용량 추이, CPU 온도 추이

**3행: 네트워크/I/O (3개)**
- 네트워크 트래픽, 디스크 I/O

#### 4. 임계값 설정 (색상 코딩)
| 항목 | 정상(녹색) | 경고(노랑) | 위험(빨강) |
|------|-----------|-----------|-----------|
| CPU 사용률 | < 50% | 50-70% | > 90% |
| 메모리 | < 60% | 60-80% | > 90% |
| 디스크 | < 60% | 60-80% | > 90% |
| CPU 온도 | < 50°C | 50-65°C | > 80°C |

### 수정된 파일
| 파일 | 변경 내용 |
|------|-----------|
| `01_scripts/telegraf_raspi.conf` | Telegraf 설정 (신규) |
| `01_scripts/07_create_system_health_dashboard.py` | 대시보드 생성 스크립트 (신규) |
| `03_outputs/system_health_dashboard.json` | 대시보드 JSON (신규) |
| `/etc/telegraf/telegraf.d/raspi.conf` | 시스템 설정 |
| `/etc/default/telegraf` | 환경변수 (INFLUXDB_TOKEN) |

### 면접 어필 포인트
> "하드웨어 과부하로 인한 수집 중단을 방지하기 위해, 서버 리소스(CPU, 메모리, 디스크)까지 통합 모니터링하고 있습니다. 특히 라즈베리파이는 발열에 취약하므로 CPU 온도를 상시 확인합니다."

---

## [2025-12-07] Telegram 알림 시스템 구현

### 배경
- Cron으로 24시간 자동 수집 중, 실패/오류 발생 시 즉시 인지 불가
- 실시간 알림으로 장애 대응 시간 단축 필요

### 구현 내용

#### 1. notifier.py 모듈 생성
- **위치**: `01_scripts/notifier.py`
- **기능**:
  - `TelegramNotifier` 클래스: Telegram Bot API 연동
  - `send_collection_result()`: 수집 결과 포맷팅 및 전송
  - `send_error_alert()`: 긴급 에러 알림
  - `send_test_message()`: 연결 테스트

#### 2. Telegram Bot API 연동
- **API 엔드포인트**: `https://api.telegram.org/bot{TOKEN}/sendMessage`
- **메시지 형식**: HTML (볼드, 코드블록 지원)
- **알림 내용**:
  - 수집 성공/실패 상태
  - 작업별(뉴스/주가/경제지표) 결과
  - 총 실행 시간
  - Grafana 대시보드 링크

#### 3. config.py 확장
- `TELEGRAM_BOT_TOKEN`: BotFather 발급 토큰
- `TELEGRAM_CHAT_ID`: 수신자 채팅방 ID
- `TELEGRAM_ENABLED`: 자동 활성화 여부 판단

#### 4. data_collector.py 통합
- `update_collection_result()` 함수 추가
- 각 수집 함수 완료 시 결과 업데이트
- `collect_all()` 완료 후 Telegram 알림 전송

### 수정된 파일
| 파일 | 변경 내용 |
|------|-----------|
| `01_scripts/notifier.py` | 신규 생성 |
| `01_scripts/config.py` | Telegram 설정 속성 추가 |
| `01_scripts/01_data_collector.py` | 알림 기능 통합 |
| `.env` | Telegram 토큰/Chat ID 추가 |
| `.env.example` | Telegram 설정 템플릿 추가 |
| `99_docs/TODO.md` | 완료 항목 체크 |
| `99_docs/CHANGELOG.md` | 이 항목 추가 |
| `CLAUDE.md` | Telegram 섹션 추가 |

### 메시지 예시
```
✅ 데이터 수집 성공
─────────────────────
📅 2025-12-07 12:34:56
⏱️ 총 45.2초

📊 수집 결과
📰 news: 20건 (1.5s)
📈 stock: 68건 (40.0s)
💰 economy: 5건 (3.0s)
─────────────────────
🔗 Grafana 대시보드
```

### 설정 방법
1. Telegram에서 @BotFather 검색 → /newbot
2. 봇 토큰을 `.env`의 `TELEGRAM_BOT_TOKEN`에 입력
3. 봇에게 메시지 전송 후 getUpdates API로 Chat ID 확인
4. Chat ID를 `.env`의 `TELEGRAM_CHAT_ID`에 입력

---

## [2025-12-04] 수집 로그 모니터링 대시보드 분리

### 배경
- 기존 메인 대시보드에 로그/DQ 패널 추가 시 28개 패널로 과밀
- 운영 모니터링과 데이터 분석 목적 분리 필요

### 변경 내용

#### 1. 메인 대시보드 정리
- `경제·주가 통합 모니터링_실제 데이터`: 28패널 → 18패널
- 로그/DQ 관련 10개 패널 제거

#### 2. 수집 로그 모니터링 대시보드 신규 생성
- **UID**: `94ce2c05-a215-4dc0-a539-ce76734bcc47`
- **패널 수**: 13개

**📊 수집 현황 요약 (5개)**
| 패널 | 타입 | 내용 |
|------|------|------|
| 오늘 수집 종목 | Stat | 오늘 수집된 주가 종목 수 |
| 최근 3일 경제지표 | Stat | 최근 3일간 수집된 경제지표 수 |
| 마지막 수집 시간 | Stat | 가장 최근 수집 작업 시간 |
| 수집 성공률 | Gauge | 최근 7일 성공률 (%) |
| 전체 주가 데이터 | Stat | InfluxDB 총 주가 레코드 수 |

**⏱️ 수집 실행 로그 (2개)**
| 패널 | 타입 | 내용 |
|------|------|------|
| 수집 실행 로그 | Table | 작업별(stock/economy/news) 통합 테이블 |
| 최근 수집 로그 | Table | 최근 20건 이력 |

**🔍 데이터 품질 (6개)**
| 패널 | 타입 | 내용 |
|------|------|------|
| 일별 주가 수집 건수 | Bar Chart | 30일 추이 |
| 일별 경제지표 수집 건수 | Bar Chart | 30일 추이 |
| 종목별 마지막 수집일 | Table | 종목/티커/종가 |
| 가격 변동률 TOP 10 | Table | 이상치 감지 |
| 실행 시간 추이 | Time Series | 작업별 실행 시간 |
| 에러율 추이 | Time Series | 작업별 에러율 |

#### 3. collection_logger.py 모듈 생성
- **위치**: `01_scripts/collection_logger.py`
- **Measurement**: `system_logs`
- **Tags**: `task_name` (news, stock, economy, total)
- **Fields**: execution_time_ms, success_count, fail_count, total_count, error_rate

#### 4. Flux 쿼리 개선
- 테이블 피벗으로 드롭다운 제거
- `|> group()` 으로 단일 테이블 병합
- 타입 변환 오류 수정 (`float(v: r.value)`)

### 수정된 파일
| 파일 | 변경 내용 |
|------|-----------|
| `01_scripts/collection_logger.py` | 신규 생성 |
| `01_scripts/01_data_collector.py` | 로깅 기능 통합 |
| `CLAUDE.md` | 대시보드 목록 업데이트 |
| `99_docs/TODO.md` | 완료 항목 체크, 업데이트 이력 추가 |
| `99_docs/DASHBOARD_DESIGN.md` | 섹션 11 추가 (수집 로그 모니터링) |
| `99_docs/CHANGELOG.md` | 이 항목 추가 |

### 대시보드 현황
| 대시보드 | UID | 패널 |
|----------|-----|------|
| `_실제 데이터` | `61949380-...` | 18개 |
| `_정규화 데이터` | `021d427b-...` | 18개 |
| `수집 로그 모니터링` | `94ce2c05-...` | 13개 |

---

## [2025-12-03] Grafana 대시보드 - 리스크 구간별 분석 패널 9개 추가

### 추가
- **리스크 시나리오별 차트**: 기존 9개 패널 아래에 9개 패널 추가 (총 18개)

#### 섹션 1: 정상장/상승장 레이아웃 (3개 패널)
- **성장 주도**: KODEX200, KODEX 코스닥150, TIGER 미국S&P500, TIGER 미국나스닥100
- **인컴 방어**: KODEX 배당가치, TIGER 코리아배당다우존스, KODEX 국고채3년
- **헤지 자산**: KODEX 골드선물(H), KODEX 국고채3년

#### 섹션 2: 급락장 (코로나 2020-02~04) (3개 패널)
- **지수 ETF**: KODEX200, KODEX 코스닥150, TIGER 미국S&P500, TIGER 미국나스닥100
- **배당/커버드콜**: KODEX 배당가치, TIGER 코리아배당다우존스, KODEX 미국S&P500커버드콜OTM
- **방어 자산**: KODEX 국고채3년, KODEX 골드선물(H)

#### 섹션 3: 금리 상승기 vs 하락기 (3개 패널)
- **금리 사이클**: KODEX 국고채3년 단독 (전체 폭)
- **한국 지수/배당**: KODEX200, KODEX 코스닥150, KODEX 배당가치, TIGER 코리아배당다우존스
- **미국 지수/커버드콜**: TIGER 미국S&P500, TIGER 미국나스닥100, KODEX 미국S&P500커버드콜OTM

### 목적
- 시장 구간별 자산군 성과 비교 (성장주 vs 배당주 vs 채권 vs 금)
- 급락장에서 방어 자산의 역할 검증
- 금리 사이클에 따른 성장/가치 로테이션 분석
- 커버드콜 전략의 변동성 장세 효과 측정

### 대시보드 버전
- Version: 3 → 4
- 총 패널: 9개 → 18개

---

## [2025-12-03] 한국 ETF 8개 추가 (1개 → 9개)

### 추가
- **한국 ETF 확장**: KODEX200만 → 9개 ETF (+8개)
  - **지수 추종**: KODEX 코스닥150
  - **해외 지수**: TIGER 미국S&P500, TIGER 미국나스닥100
  - **배당**: KODEX 배당가치, TIGER 코리아배당다우존스
  - **채권**: KODEX 국고채3년
  - **원자재**: KODEX 골드선물(H)
  - **인컴**: KODEX 미국S&P500커버드콜OTM

### 목적
- 한국 ETF 시장 대표 상품 포함
- 자산군별 분산 투자 분석 (주식, 채권, 원자재)
- 배당/인컴 전략 벤치마크 추가
- 해외 지수 추종 ETF 성과 비교

### 수정된 파일
- `01_scripts/collect_15year_historical.py`: KR_TICKERS에 8개 ETF 추가
- `01_scripts/data_collector.py`: tickers 딕셔너리에 9개 ETF 반영
- `CLAUDE.md`: 한국 지수/ETF 섹션 상세 기록
- `01_scripts/DATACOLLECT.md`: 한국 ETF 상세 테이블 추가
- `99_docs/CHANGELOG.md`: 이 항목 추가

### 데이터 영향
- 총 종목 수: **76개** (한국 27 + 미국 41 + 지수 8)
- 한국 종목: 2 (지수) + 9 (ETF) + 16 (개별) = 27개

---

## [2025-12-03] 미국 ETF 33개 추가 (8개 → 41개)

### 추가
- **미국 ETF 대폭 확장**: 8개 → 41개 (+33개)
  - **나스닥 ETF**: QLD (2x), TQQQ (3x), QQQ5 추가
  - **S&P500 ETF**: VOO, IVV, SSO (2x), UPRO (3x), SPLG 추가
  - **배당 ETF**: SCHD, DGRO, SPHD, JEPI, NUSI, MAIN, GAIN, QYLD, XYLD, RYLD (10개)
  - **기술/반도체 레버리지**: SOXL (3x), TECL (3x)
  - **광범위 지수**: VTI, VT, VEA, EFA, SPDW, ITOT (6개)
  - **인버스 (숏)**: SQQQ (-3x), QID (-2x), PSQ (-1x)
  - **중국**: CWEB (2x)

### 목적
- 레버리지 ETF 추가 → 변동성 및 베타 분석
- 배당 ETF 추가 → 인컴 투자 전략 분석
- 인버스 ETF 추가 → 헤징 및 하락장 대응 분석
- 광범위 지수 ETF 추가 → 글로벌 분산 투자 벤치마크

### 수정된 파일
- `01_scripts/collect_15year_historical.py`: US_TICKERS에 33개 ETF 추가
- `01_scripts/data_collector.py`: tickers 딕셔너리에 41개 ETF 반영
- `CLAUDE.md`: 수집 종목 27개 → 68개로 업데이트
- `01_scripts/DATACOLLECT.md`: 미국 ETF 섹션 상세 기록 (7개 카테고리)
- `99_docs/CHANGELOG.md`: 이 항목 추가

### 카테고리별 ETF
| 카테고리 | ETF 수 | 주요 목적 |
|----------|--------|-----------|
| 나스닥 | 4개 | 기술주 레버리지 전략 |
| S&P500 | 6개 | 시장 대표 지수 비교 |
| 다우 | 1개 | 대형 블루칩 |
| 배당 | 10개 | 인컴 투자 전략 |
| 기술/반도체 | 2개 | 섹터 레버리지 |
| 광범위 | 6개 | 글로벌 분산 |
| 인버스 | 3개 | 헤징 및 숏 전략 |
| 중국 | 1개 | 신흥시장 |
| 채권/금 | 2개 | 안전자산 |

### 데이터 영향
- 총 종목 수: 27개 (한국) + 3개 (미국 지수) + 41개 (미국 ETF) = **71개**
- 일간 수집 데이터 증가: 27건 → 71건 (2.6배)
- Historical 데이터 재수집 필요 (33개 ETF 15년치)

---

## [2025-12-03] 15년 히스토리 데이터 + Grafana 대시보드 고도화

### 배경
- 5년 데이터(2020-2025)에서 15년 데이터(2010-2025)로 확장
- GDP 데이터 추가 수집
- Grafana 대시보드 4행 레이아웃으로 재설계
- 범례 레이블 최적화로 가독성 향상

### 15년 히스토리 데이터 수집
- **`collect_15year_historical.py` 생성**: 3개 기간 분할 수집
  - Period 1: 2010-2014 (5년)
  - Period 2: 2015-2019 (5년)
  - Period 3: 2020-2025 (5년)

- **수집 결과 (총 88,906건)**:
  | 데이터 | Period 1 | Period 2 | Period 3 | 합계 |
  |--------|----------|----------|----------|------|
  | 한국 주가 | 21,243건 | 21,195건 | 21,752건 | 64,190건 |
  | 미국 주가 | 11,231건 | 10,423건 | 10,362건 | 32,016건 |
  | FRED 지표 | 6,425건 | 6,425건 | 6,425건 | 19,275건 |
  | ECOS 지표 | 1,458건 | 1,458건 | 1,461건 | 4,377건 |

### 한국 GDP 데이터 수집
- **`collect_gdp_only.py` 생성**: ECOS API 200Y102 통계코드
- **수집 항목**: 52개 GDP 관련 지표 (분기별)
  - 실질 GDP, 민간소비, 정부소비, 설비투자, 건설투자, 수출/수입 등
- **수집 결과**: 3,319건 (2010Q1 ~ 2025Q4)
- **데이터 저장**: `/raspi/WD4T/00_data_raw/archive/gdp_2010_2025.csv`

### 데이터 병합 및 중복 제거
- **`merge_historical_data.py` 생성**: 3개 기간 파일 → 1개 통합 파일
- **중복 제거 로직 개선**:
  - 주가: `['date', 'name']` 기준 중복 제거
  - 경제지표: `['date', 'indicator']` 기준 (GDP 데이터 보존)
  - 이전 버그: `['date', 'series_id']` 사용 시 GDP 데이터 3,701건→421건 오류

- **병합 결과**:
  | 파일명 | 레코드 | 종목/지표 |
  |--------|--------|-----------|
  | stock_korean_merged.csv | 64,190건 | 27종목 |
  | stock_us_merged.csv | 32,016건 | 11종목 |
  | economy_fred_merged.csv | 19,275건 | 5지표 |
  | economy_ecos_merged.csv | 2,831건 | 56지표 (CPI + GDP) |

### InfluxDB 백필 (15년)
- **`influxdb_backfill_15years.py` 생성**: 병합 CSV → InfluxDB 적재
- **총 118,312건 백필 완료**:
  - 한국 주가: 64,190건
  - 미국 주가: 32,016건
  - FRED 지표: 19,275건
  - ECOS 지표: 2,831건

### Grafana 대시보드 4행 레이아웃 재설계
- **`create_grafana_dashboard_v2.py` 생성**: 8개 패널, 4행 구성
  - **1행**: 한국 지수/ETF, GDP/CPI
  - **2행**: 한국 대형주, IT 플랫폼
  - **3행**: 엔터/게임, 미국 지수
  - **4행**: 환율/금리, 뉴스 빈도

### Grafana 자동 업로드
- **`upload_grafana_dashboard.py` 생성**: Grafana API 자동 배포
- **업로드 설정**:
  - URL: `http://localhost:3000`
  - 인증: Basic Auth (admin / !Qwer3004352)
  - overwrite: True (기존 대시보드 덮어쓰기)
- **결과**: 대시보드 UID `55cf3a41-b6d2-48ad-8f98-1ec417944655`

### Grafana 범례 레이블 최적화
- **문제**: 범례에 불필요한 메타데이터 표시 (ticker, source, period 등)
- **해결**: Flux 쿼리 최적화
  ```flux
  |> map(fn: (r) => ({ r with _field: r.name }))
  |> drop(columns: ["name", "ticker"])
  ```
- **효과**: 종목명/지표명만 표시되어 가독성 대폭 향상

### 버그 수정
1. **GDP 날짜 형식 오류** (`collect_gdp_only.py`)
   - 문제: datetime 객체로 변환 시 병합 후 날짜 손실
   - 해결: 날짜를 문자열로 유지

2. **GDP 데이터 과다 중복 제거** (`merge_historical_data.py`)
   - 문제: `['date', 'series_id']` 기준으로 중복 제거 시 동일 날짜의 모든 GDP 항목 삭제
   - 해결: `['date', 'indicator']` 기준으로 변경

3. **ECOS API stat code 탐색**
   - 방법: StatisticTableList API로 872개 테이블 전체 검색
   - 발견: 200Y102 ("2.1.1.2. 주요지표(분기지표)")

### 문서 업데이트
- **CLAUDE.md**: 15년 데이터 현황, Grafana URL 업데이트
- **DATACOLLECT.md**: 새 스크립트 8개 추가, 섹션 재구성 (15개 섹션)
- **CHANGELOG.md**: 이 항목 추가

### 접속 정보
- **Grafana (외부)**: `http://112.167.173.132:3000`
- **Grafana (내부)**: `http://100.125.124.53:3000`
- **대시보드 URL**: `/d/55cf3a41-b6d2-48ad-8f98-1ec417944655`

---

## [2025-11-30] 프로젝트 초기화
- Git 저장소 초기화
- CLAUDE.md 생성 (베스트 프랙티스 적용)
- 99_docs/ 폴더 생성
- 디렉토리 구조 정의:
  - 00_data_raw/: 원본 데이터
  - 00-1_data_processed/: 전처리 데이터
  - 01_scripts/: 스크립트
  - 02_notebooks/: 분석 노트북
  - 03_outputs/: 시각화 결과물
  - 98_logs/: 로그
  - 99_docs/: 문서

## 기존 데이터 현황
- news.csv: 네이버 뉴스 (경제/부동산/반도체/코스피)
- stock.csv: 주가 (코스피, 코스닥, KODEX200, 삼성전자, SK하이닉스)
- economy.csv: 경제지표 (환율, 금리, 유가)

## [2025-11-30] PRD 작성
- PRD.md 생성 (99_docs/)
- 4개 Phase 정의:
  - Phase 1: 데이터 전처리
  - Phase 2: 시각화
  - Phase 3: 감성분석
  - Phase 4: 고급 분석
- 기능 요구사항 18개 정의
- 마일스톤, 리스크, 성공 지표 수립

## [2025-11-30] PROGRESS.md 작성
- 진행 현황 문서 생성
- 포함 내용:
  - 기존 데이터 현황 (news, stock, economy)
  - 합의된 전처리 규칙
  - 파생 컬럼 정의
  - 시각화/감성분석 계획
  - 추가 필요 데이터
  - 주요 결정 사항
- 다음 세션 시작 가이드 포함

## [2025-11-30] Phase 1 전처리 완료

### 작업 내용
- `preprocessor.py` 스크립트 작성
- 3개 CSV 전처리 완료

### 결과
| 파일 | 원본 | 전처리 후 |
|------|------|-----------|
| news | 1,120건 | 962건 |
| stock | 260건 | 125건 |
| economy | 339건 | 171건 |

### 생성된 파생 컬럼
- **stock**: log_return, volatility_20d, volume_zscore, volume_ma5
- **economy**: is_holiday_gap, pct_1d, pct_1w, pct_1m, event_flag
- **news**: session, date

### 저장 위치
- `R:\00-1_data_processed\`

---

## [2025-11-30] 미국 데이터 소스 추가

### 추가된 종목 (8개)
| 구분 | 티커 | 설명 |
|------|------|------|
| 미국 지수 | ^GSPC | S&P 500 |
| 미국 지수 | ^IXIC | 나스닥 종합 |
| 미국 지수 | ^VIX | 공포 지수 |
| 미국 ETF | QQQ | 나스닥 100 ETF |
| 미국 ETF | SPY | S&P 500 ETF |
| 미국 ETF | DIA | 다우존스 ETF |
| 미국 ETF | TLT | 미국 장기국채 ETF |
| 미국 ETF | GLD | 금 ETF |

### 수정 파일
- `01_scripts/data_collector.py`: tickers 딕셔너리에 미국 종목 추가

## [2025-11-30] 수집 스케줄 설정

### Cron 스케줄 (1일 3회)
| 시간 | 수집 항목 | 요일 |
|------|-----------|------|
| 08:00 | 미국 주가 + 경제지표 + 뉴스 | 매일 |
| 16:00 | 한국 주가 + 경제지표 + 뉴스 | 평일 |
| 20:00 | 경제지표 + 뉴스 | 매일 |

### 시장 시간 참고
- 한국: 09:00~15:30 KST
- 미국: 23:30~06:00 KST

---

## [2025-11-30] Phase 2 시각화 개발

### 생성된 파일
- `99_docs/ARCHITECTURE.md`: Mermaid 차트 문서
- `02_notebooks/analysis.ipynb`: 시각화 노트북

### 시각화 차트 (4개)
| 차트 | 파일명 | 내용 |
|------|--------|------|
| 차트 1 | chart1_kospi_usd.png | 환율-코스피 듀얼축 + 롤링상관 |
| 차트 2 | chart2_semiconductor.png | 삼성전자/SK하이닉스 수익률 + 거래량 |
| 차트 3 | chart3_news_frequency.png | 뉴스 키워드별 빈도 |
| 차트 4 | chart4_correlation.png | 미국-한국 상관 히트맵 |

### ARCHITECTURE.md 포함 내용
- 전체 시스템 구조 (Mermaid)
- 데이터 수집 흐름
- 데이터 처리 파이프라인
- 수집 종목 구조
- Phase별 진행 흐름
- 폴더 구조
- 데이터 수집 기준

---

## [2025-11-30] Phase 2 시각화 완료 (전체)

### 차트 이미지 생성
- `03_outputs/chart1_kospi_usd.png`: 환율-코스피 듀얼축 + 7일 롤링 상관
- `03_outputs/chart2_semiconductor.png`: 삼성전자/SK하이닉스 누적수익률 + 거래량
- `03_outputs/chart3_news_frequency.png`: 키워드별 일간 뉴스 빈도
- `03_outputs/chart4_correlation.png`: 한국 종목 수익률 상관 히트맵

### Streamlit 대시보드 개발
- `01_scripts/dashboard.py` 생성
- 5개 탭 구성: 개요, 주가분석, 경제지표, 뉴스분석, 상관관계
- Plotly 인터랙티브 차트 적용
- 실행: `streamlit run 01_scripts/dashboard.py`

### 의존성 설치
- streamlit 1.51.0
- plotly 6.5.0

---

## 다음 작업
- [ ] Phase 3 감성분석 개발
- [ ] Phase 4 Streamlit 포트폴리오 앱
- [ ] Grafana 알림 설정 (선택)

---

## [2025-12-03] Phase 2.5: InfluxDB + Grafana 상시 모니터링 시스템

### 배경
- 최초 계획의 핵심 목표: "InfluxDB에 시계열로 저장하고 Grafana로 상시 모니터링"
- CSV 기반 분석에서 시계열 DB 기반 실시간 모니터링으로 확장

### InfluxDB 구축
- InfluxDB 2.x 라즈베리파이 설치 완료
- 초기 설정:
  - Organization: `my-org`
  - Bucket: `econ_market`
  - API Token 발급

### 시계열 데이터 모델 설계
| Measurement | Tags | Fields |
|-------------|------|--------|
| stock_prices | name, ticker | open, high, low, close, volume |
| economic_indicators | indicator, period | value |
| news | keyword | title, description, link, count |

### 데이터 백필 완료
| 데이터 | 레코드 수 | 기간 |
|--------|----------|------|
| 주가 | 38,319건 | 2020-01-02 ~ 현재 |
| 경제지표 | 4,447건 | 2020-01-01 ~ 현재 |
| 뉴스 | 실시간 | 수집 시점 ~ |

### 일간 수집 InfluxDB 연동
- `data_collector.py` 수정: CSV + InfluxDB 이중 저장
- 뉴스, 주가, 경제지표 모두 InfluxDB 자동 저장
- Cron 스케줄: 가상환경 Python 직접 호출로 변경

### Grafana 대시보드 구축
- Grafana 12.3 설치 완료
- InfluxDB 데이터소스 연동 (Flux 쿼리)
- 대시보드 자동 생성 스크립트 작성 (`grafana_dashboard_setup.py`)
- **8개 패널 구성**:
  1. 한국 지수 (코스피/코스닥)
  2. 한국 ETF (KODEX200)
  3. 한국 대형주 (삼성전자, SK하이닉스 등)
  4. IT/플랫폼 (NAVER/카카오)
  5. 엔터/게임 (HYBE, SM, JYP 등)
  6. 미국 지수/ETF (S&P500, 나스닥 등)
  7. 환율/금리
  8. 뉴스 키워드별 수집 건수

### 생성된 스크립트
| 파일 | 용도 |
|------|------|
| `influxdb_loader_v2.py` | 과거 데이터 InfluxDB 백필 (1회성) |
| `grafana_dashboard_setup.py` | Grafana 대시보드 API 자동 생성 |

### 접속 정보
- InfluxDB: `http://<IP>:8086`
- Grafana: `http://<IP>:3000`
- 대시보드 URL: `http://<IP>:3000/d/55cf3a41-b6d2-48ad-8f98-1ec417944655`

### 문서 업데이트
- CLAUDE.md: InfluxDB + Grafana 정보 추가
- ARCHITECTURE.md: 시스템 구조도 업데이트, Phase 2.5 추가
- PROGRESS.md: 진행 현황 업데이트
- DATACOLLECT.md: 크론 스케줄 가상환경 경로 반영 필요

---

## [2025-12-02] 과거 5년 데이터 수집

### 배경
- 기존 데이터 수집 시작일(2025-11-06)이 너무 짧아 분석에 부족
- 통계적 유의성 확보를 위해 5년치 과거 데이터 필요

### 작업 내용
- `01_scripts/collect_historical_data.py` 생성
- yfinance로 주가 5년치 수집 (2020-01-01 ~ 현재)
- 한국은행 ECOS API로 경제지표 5년치 수집

### 수집 결과
| 데이터 | 파일명 | 레코드 수 | 기간 |
|--------|--------|----------|------|
| 주가 | stock_historical.csv | 19,124건 | 2020-01-02 ~ 2025-12-01 |
| 경제지표 | economy_historical.csv | 4,447건 | 2020-01 ~ 2025-12 |

### 주가 수집 종목 (13개)
- 한국: 코스피, 코스닥, KODEX200, 삼성전자, SK하이닉스
- 미국 지수: S&P500, 나스닥, VIX
- 미국 ETF: QQQ, SPY, DIA, TLT, GLD

### 경제지표 수집 항목
| 지표 | 건수 | 주기 |
|------|------|------|
| 원/달러 환율 | 1,459건 | 일별 |
| 원/엔 환율 | 1,459건 | 일별 |
| 원/유로 환율 | 1,459건 | 일별 |
| 기준금리 | 70건 | 월별 |

### 수집 실패 항목
- 두바이유 가격: ECOS API 미제공
- 금 시세: ECOS API 미제공

---

## [2025-12-02] preprocessor.py 업데이트

### 변경 내용
- `USE_HISTORICAL` 설정 추가 (기본값: True)
- historical 파일과 daily 파일 선택 가능

### 데이터 소스 설정
```python
# preprocessor.py
USE_HISTORICAL = True   # 5년치 데이터 사용 (기본값)
USE_HISTORICAL = False  # 최근 수집 데이터 사용
```

### 전처리 결과 (historical 사용)
| 파일 | 레코드 수 |
|------|----------|
| stock_processed.csv | 19,124건 |
| economy_processed.csv | 4,447건 |
| news_processed.csv | 962건 |


---

## [2025-12-02] 뉴스 Historical 수집 시도

### 작업 내용
- `01_scripts/collect_historical_news.py` 생성
- 네이버 검색 API로 뉴스 수집 시도

### 수집 설정
- 키워드: 경제, 부동산, 반도체, 코스피
- 키워드당 100건 (API 최대)
- 정렬: sim (관련도순 = 이슈된 순서)

### 수집 결과
| 항목 | 값 |
|------|-----|
| 총 수집 | 400건 |
| 중복 제거 후 | 361건 |
| 날짜 범위 | 2025-11-30 ~ 2025-12-02 |
| 저장 파일 | news_historical.csv |

### 키워드별 현황
| 키워드 | 건수 |
|--------|------|
| 경제 | 93건 |
| 부동산 | 92건 |
| 반도체 | 89건 |
| 코스피 | 87건 |

### 한계
- 네이버 API는 과거 날짜 필터링 미지원
- 최신 뉴스(2~3일)만 수집됨
- 과거 5년치 뉴스 필요시 빅카인즈(bigkinds.or.kr) 수동 다운로드 권장

---

## [2025-12-02] 한국 개별종목 확대 및 용도 태그 추가

### 추가된 종목 (14개)
| 섹터 | 종목 | 티커 | 용도 태그 |
|------|------|------|-----------|
| 2차전지 | LG에너지솔루션 | 373220.KS | 수출, 성장, 친환경 |
| 바이오 | 삼성바이오로직스 | 207940.KS | 성장, 헬스케어, 방어 |
| 자동차 | 현대차 | 005380.KS | 수출, 경기민감, 제조 |
| 금융 | KB금융 | 105560.KS | 금리민감, 배당, 내수 |
| 철강 | POSCO홀딩스 | 005490.KS | 경기민감, 수출, 소재 |
| IT/플랫폼 | NAVER | 035420.KS | 성장, 내수, 기술 |
| 엔터 | HYBE | 352820.KS | 문화, 성장, K-콘텐츠 |
| 엔터 | SM | 041510.KS | 문화, 성장, K-콘텐츠 |
| 엔터 | JYP Ent. | 035900.KS | 문화, 성장, K-콘텐츠 |
| 게임 | 크래프톤 | 259960.KS | 문화, 성장, 글로벌 |
| 게임 | 엔씨소프트 | 036570.KS | 문화, 기술, IP |
| 콘텐츠 | CJ ENM | 035760.KS | 문화, 내수, 미디어 |
| 영화 | CGV | 079160.KS | 문화, 경기민감, 내수 |
| IT/플랫폼 | 카카오 | 035720.KS | 성장, 내수, IP |

### 용도 태그 체계 신규 도입
- 분석 목적에 따른 종목 분류 체계
- 태그: 경기민감, 금리민감, 수출, 내수, 성장, 배당, 방어, 문화, 기술, IP

### 수정 파일
- `01_scripts/DATACOLLECT.md`: 종목 테이블 및 태그 설명 추가
- `01_scripts/data_collector.py`: tickers 딕셔너리 확장
- `01_scripts/collect_historical_data.py`: tickers 딕셔너리 확장

### 과거 데이터 재수집
| 데이터 | 이전 | 변경 후 |
|--------|------|---------|
| 주가 | 19,124건 (13종목) | 38,319건 (27종목) |
| 경제지표 | 4,447건 | 4,447건 (변동없음) |

### 신규 종목 데이터 기간
- LG에너지솔루션: 2022-01-27 ~ (937일)
- HYBE: 2020-10-15 ~ (1,256일)
- 크래프톤: 2021-08-10 ~ (1,051일)
- 기타 종목: 2020-01-02 ~ (1,450일 이상)
