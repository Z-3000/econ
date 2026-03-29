# Raspberry Pi 5 마이그레이션 런북

## 목적

이 문서는 다른 기기에서 정상 동작하던 경제 데이터 수집 시스템을 `Raspberry Pi 5 + Raspberry Pi OS (Debian Trixie 기반)` 환경으로 옮기는 과정에서 실제로 발생한 오류와 해결 절차를 정리한 운영 런북이다.

대상 시스템:

- Python 기반 데이터 수집기
- InfluxDB 2.x
- Grafana
- Tailscale을 통한 원격 접속
- CSV 원본/백업 데이터 기반 복구

이 문서의 목적은 아래 3개다.

1. 마이그레이션 중 어떤 문제가 실제로 발생하는지 빠르게 식별
2. 문제별 원인과 해결 절차를 재현 가능하게 정리
3. 최종적으로 운영 가능한 상태까지 점검 절차를 표준화

---

## 최종 결론

이번 사례에서 시스템이 정상 복구되기까지 핵심 이슈는 아래 순서였다.

1. 프로젝트 파일 복사 후 누락 파일 복원 필요
2. Raspberry Pi OS Trixie 환경에서는 `python3` 기본 버전이 3.13 계열이므로 `python3.12` 고정 전제를 버려야 함
3. `requirements.txt`의 `mplfinance>=0.12.10` 제약이 설치 실패를 일으킴
4. Grafana 저장소 등록 명령 오타로 Grafana 설치 실패
5. InfluxDB/Grafana는 새 인스턴스로 시작되므로 기존 데이터와 대시보드는 자동 복구되지 않음
6. InfluxDB 토큰이 새 토큰으로 갱신되지 않아 `401 Unauthorized` 발생
7. 백필 시 대량 동기 write로 InfluxDB write timeout 발생
8. Grafana 데이터소스가 InfluxDB 2.x `Flux` 기준으로 다시 설정되지 않아 대시보드가 `No data` 상태였음

최종 정상 상태 기준:

- `python 01_scripts/healthcheck.py` 전체 PASS
- InfluxDB/Grafana 서비스 기동
- CSV 기반 InfluxDB 백필 완료
- Grafana 데이터소스가 `Flux + InfluxDB OSS 2.x` 기준으로 정상 연결
- Grafana 대시보드에서 실제 시계열 확인 가능

---

## 환경 요약

실제 복구 환경은 아래 기준으로 정리하는 것이 맞다.

- OS: Raspberry Pi OS, Debian Trixie 기반
- Python: `python3` 기본 버전 사용
- 권장 가상환경: `.venv`
- InfluxDB URL: `http://localhost:8086`
- Grafana 내부 API 기준 URL: `http://localhost:3000`
- Grafana 외부 접속 기준 URL: `http://<라즈베리파이_Tailscale_IP>:3000`
- InfluxDB Organization: `my-org`
- InfluxDB Bucket: `econ_market`

중요 원칙:

- 같은 라즈베리파이 내부에서 호출하는 Python 스크립트는 `localhost` 기준이 가장 안정적이다.
- 다른 기기에서 브라우저로 접속하는 주소는 `Tailscale IP` 기준으로 본다.
- 내부 API 주소와 외부 접속 주소를 혼동하면 디버깅이 길어진다.

---

## 장애 요약표

| 증상 | 실제 원인 | 해결 |
|---|---|---|
| `python3.12: command not found` | Trixie 기본 Python이 3.13 계열 | `python3 -m venv .venv` 기준으로 전환 |
| 패키지 설치 중 `No matching distribution found for mplfinance>=0.12.10` | 버전 제약이 실제 배포 버전과 불일치 | `mplfinance==0.12.10b0`로 수정 |
| `Unable to locate package grafana` | APT 저장소 파일 생성 실패 | `/etc/apt/sources.list.d/grafana.list`에 올바르게 저장소 등록 |
| `Unit grafana-server.service could not be found` | Grafana 미설치 | 저장소 재등록 후 Grafana 설치 |
| `401 Unauthorized` during backfill | InfluxDB 새 토큰 미반영 또는 쓰기 권한 부족 | All Access 또는 write 가능한 새 토큰 발급 후 `.env` 교체 |
| `500 internal error ... timeout` during backfill | 대량 동기 write 배치로 InfluxDB write timeout | 백필 배치를 줄이고 timeout 시 분할 재시도 로직 추가 |
| Grafana에서 대시보드 `No data` | InfluxDB 데이터소스 설정 방식 오류 | InfluxDB 2.x + Flux 기준 데이터소스 재설정 |
| Grafana 대시보드 업로드 스크립트 실패 | `GRAFANA_URL`에 외부 Tailscale 주소를 넣어 내부 API 호출과 혼용 | 내부 API 호출은 `localhost`, 외부 접속은 브라우저에서 Tailscale 주소 사용 |

---

## 표준 복구 절차

## 1. 프로젝트 파일 무결성 확인

우선 복사된 프로젝트가 실행 가능한 구조인지 확인한다.

필수 확인 대상:

- `.env`
- `requirements.txt`
- `01_scripts/`
- `00_data_raw/`
- `00-1_data_processed/`
- `03_outputs/`
- `data/`

확인 명령:

```bash
cd /home/raspi16/01_project/econ
ls -la
find 01_scripts -maxdepth 1 -type f | sort
find 00_data_raw -maxdepth 2 -type f | sort | head -n 50
find data -maxdepth 2 -type f | sort
```

판정 기준:

- 실행 스크립트가 빠져 있으면 먼저 파일 복원을 해야 한다.
- `.env`가 없으면 외부 서비스 인증이 모두 실패한다.
- 원본 CSV가 없으면 백필이 불가능하다.

---

## 2. Python 환경 복구

### 증상

- `python3.12` 없음
- 문서에는 `Python 3.12` 기준으로 적혀 있음

### 원인

Raspberry Pi OS Trixie 기반 환경에서는 `python3` 기본 버전이 3.13 계열일 수 있다. 이 환경에서 `3.11` 또는 `3.12`를 맞추려면 별도 빌드가 필요할 수 있다.

### 해결

운영 기준을 `python3` 중심으로 바꾼다.

```bash
cd /home/raspi16/01_project/econ
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

### 검증 포인트

- `.venv/bin/python`이 존재하는지
- `python --version`이 실제 기본 Python과 일치하는지
- `pip install -r requirements.txt`가 끝까지 성공하는지

---

## 3. `mplfinance` 설치 실패

### 증상

패키지 설치 중 아래와 비슷한 오류 발생:

```text
ERROR: Could not find a version that satisfies the requirement mplfinance>=0.12.10
```

### 원인

`requirements.txt`의 버전 표기가 실제 배포 가능한 버전과 어긋나 있었다.

### 해결

`requirements.txt`를 아래처럼 수정했다.

```txt
mplfinance==0.12.10b0
```

### 검증 포인트

- `pip install -r requirements.txt` 재실행 후 성공하는지
- `python -m pip show mplfinance`에서 실제 설치 버전이 보이는지

---

## 4. Grafana 설치 실패

### 증상

- `Unable to locate package grafana`
- `grafana-server.service could not be found`

### 원인

APT 저장소 등록 명령에서 저장 위치를 잘못 입력했다.

실패 사례:

```bash
echo "deb [signed-by=/etc/apt/keyrings/grafana.asc] https://apt.grafana.com stable main" | sudo tee /
```

위 명령은 `/etc/apt/sources.list.d/grafana.list`로 저장하지 못한다.

### 해결

정확한 저장소 파일 위치로 다시 등록한다.

```bash
sudo mkdir -p /etc/apt/keyrings
sudo wget -O /etc/apt/keyrings/grafana.asc https://apt.grafana.com/gpg-full.key
sudo chmod 644 /etc/apt/keyrings/grafana.asc
echo "deb [signed-by=/etc/apt/keyrings/grafana.asc] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list > /dev/null
sudo apt-get update
sudo apt-get install -y grafana
```

기동:

```bash
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
sudo systemctl status grafana-server --no-pager
```

### 검증 포인트

- `apt-cache policy grafana`에 후보 버전이 보이는지
- `curl http://localhost:3000/api/health` 응답이 오는지

---

## 5. InfluxDB/Grafana 외부 접속 가능 여부 판단

### 증상

다른 기기에서 `http://<tailscale-ip>:3000` 접속 시 연결 거부

### 원인 후보

- 서비스 미기동
- 포트 미개방
- `127.0.0.1`에만 bind

### 해결 절차

라즈베리파이에서 아래를 확인한다.

```bash
curl http://localhost:8086/health
curl http://localhost:3000/api/health
sudo ss -ltnp | grep -E ':3000|:8086'
```

정상 사례:

```text
LISTEN ... *:3000
LISTEN ... *:8086
```

### 판정 기준

- `*:3000`, `*:8086`이면 외부 인터페이스에서도 접속 가능
- `127.0.0.1:포트`만 보이면 같은 기기 내부에서만 접근 가능

---

## 6. InfluxDB는 새 인스턴스라는 점을 전제로 복구

### 증상

- InfluxDB와 Grafana 접속은 되는데 기존 데이터가 없음
- Grafana 대시보드도 비어 있음

### 원인

새 기기에 설치한 InfluxDB/Grafana는 기존 데이터와 메타데이터를 자동으로 가져오지 않는다.

### 해결 원칙

- InfluxDB 데이터는 CSV에서 다시 적재
- Grafana는 대시보드 JSON을 다시 import 또는 업로드

InfluxDB 초기 설정값은 프로젝트와 맞춰야 한다.

- Organization: `my-org`
- Bucket: `econ_market`

---

## 7. InfluxDB 토큰 문제

### 증상

백필 실행 시:

```text
ApiException: (401) Unauthorized
```

### 원인

- `.env`의 `INFLUXDB_TOKEN`이 새 토큰으로 바뀌지 않았음
- 또는 읽기 전용 토큰을 사용함

### 해결

InfluxDB UI에서 `All Access API Token` 또는 쓰기 가능한 토큰을 새로 만든다.

UI 기준 절차:

1. InfluxDB 로그인
2. `Load Data` 또는 `Data`
3. `API Tokens`
4. `Generate API Token`
5. `All Access API Token`
6. 생성된 토큰을 복사
7. `.env`의 `INFLUXDB_TOKEN` 교체

`.env` 예시:

```env
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=<새 토큰>
INFLUXDB_ORG=my-org
INFLUXDB_BUCKET=econ_market
```

### 검증 포인트

```bash
source .venv/bin/activate
python 01_scripts/healthcheck.py
```

`InfluxDB 연결 성공`이 나와야 한다.

---

## 8. 백필 timeout 문제

### 증상

백필 실행 중:

```text
500 Internal Server Error
unexpected error writing points to database: timeout
```

### 원인

기존 스크립트가 대량 포인트를 동기식으로 한 번에 쓰면서 InfluxDB write timeout이 발생했다.

### 해결

백필 스크립트를 수정했다.

- 기본 배치 크기를 더 작게 조정
- timeout 발생 시 배치를 절반으로 나누어 재시도

수정 후 재실행:

```bash
cd /home/raspi16/01_project/econ
source .venv/bin/activate
python 01_scripts/04_influxdb_backfill_15years.py
```

추가로 더 보수적으로 실행할 필요가 있으면:

```bash
export INFLUXDB_BACKFILL_BATCH_SIZE=20
python 01_scripts/04_influxdb_backfill_15years.py
```

### 검증 포인트

- 스크립트가 끝까지 완료되는지
- 이후 Grafana Explore 또는 정합성 점검에서 데이터가 조회되는지

---

## 9. Grafana 대시보드가 `No data`인 경우

### 증상

- 백필은 완료됨
- InfluxDB도 연결 성공
- Grafana 패널은 모두 `No data`

### 실제 원인

가장 치명적인 원인은 Grafana 데이터소스를 InfluxDB 2.x `Flux` 기준으로 설정하지 않은 것이었다.

초기에는 `Database / User / Password` 중심의 화면에서 값을 넣고 있었는데, 이 프로젝트는 `InfluxDB OSS 2.x + Flux + Token + Organization + Bucket` 기준이다.

### 정답 설정

Grafana 데이터소스:

- Type: `InfluxDB`
- Query language: `Flux`
- URL: `http://127.0.0.1:8086`
- Basic auth: 끔
- Organization: `my-org`
- Token: 현재 `.env`의 `INFLUXDB_TOKEN`
- Default Bucket: `econ_market`

### Explore 검증 쿼리

```flux
from(bucket: "econ_market")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "stock_prices")
  |> filter(fn: (r) => r._field == "close")
  |> limit(n: 10)
```

이 쿼리에서 데이터가 나오면 InfluxDB 데이터소스는 정상이다.

### 추가 주의

대시보드 JSON은 기본적으로 `datasource uid = influxdb`를 전제한다. Grafana에서 만든 데이터소스 이름과 UID가 다르면 import 후에도 일부 패널이 비어 보일 수 있다.

가능하면 데이터소스 이름을 `influxdb`로 맞춘다.

---

## 10. `GRAFANA_URL`의 역할 구분

### 혼동 포인트

처음에는 `.env`의 `GRAFANA_URL`을 Tailscale 주소로 바꾸었다.

예:

```env
GRAFANA_URL=http://100.112.72.127:3000
```

이 값은 외부 브라우저 접속용으로는 편하지만, 같은 라즈베리파이 내부에서 실행하는 Python 스크립트가 API를 호출할 때는 `localhost`가 더 안정적이다.

### 운영 원칙

- 내부 스크립트 API 호출: `http://localhost:3000`
- 다른 기기 브라우저 접속: `http://100.112.72.127:3000`

### 권장 대응

기본 운영은 `.env`에서 `GRAFANA_URL=http://localhost:3000`을 유지한다.

다른 기기 브라우저 접속은 사용자가 직접 Tailscale 주소로 접근한다.

필요하면 추후 아래처럼 역할을 분리한다.

- `GRAFANA_URL`: 내부 API 호출용
- `GRAFANA_PUBLIC_URL`: Telegram/외부 링크용

---

## 표준 명령 모음

### Python 환경 확인

```bash
cd /home/raspi16/01_project/econ
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 헬스체크

```bash
source .venv/bin/activate
python 01_scripts/healthcheck.py
```

### InfluxDB 백필

```bash
source .venv/bin/activate
python 01_scripts/04_influxdb_backfill_15years.py
```

### Grafana 대시보드 업로드

```bash
source .venv/bin/activate
python 01_scripts/06_upload_grafana_dashboard.py
```

### 수동 수집 테스트

```bash
source .venv/bin/activate
python 01_scripts/01_data_collector.py
```

---

## 문제 발생 시 우선순위

문제를 다시 만나면 아래 순서로 본다.

1. 파일 누락 여부
2. `.env`의 URL, token, password 일치 여부
3. InfluxDB/Grafana 서비스 기동 여부
4. InfluxDB 토큰 권한 여부
5. Grafana 데이터소스가 `Flux` 기준인지
6. 백필 또는 수집 데이터가 실제로 들어갔는지
7. 대시보드 쿼리와 데이터소스 UID가 맞는지

이 순서를 어기면 문제를 잘못 진단할 가능성이 높다.

---

## 재발 방지 권장 사항

1. `python3.12` 같은 특정 마이너 버전을 문서에 고정하지 말고 `python3` 기준으로 적는다.
2. `.env.example`에 `INFLUXDB_ORG`, `INFLUXDB_BUCKET`, `GRAFANA_URL` 의미를 더 명확히 적는다.
3. `GRAFANA_URL`과 외부 공개 링크를 분리한다.
4. Grafana 데이터소스 생성 절차를 `Flux` 기준으로 별도 문서화한다.
5. InfluxDB 백필은 소배치 기본값을 사용하고 timeout 재시도 로직을 유지한다.
6. 새 기기 복구 시 `healthcheck -> backfill -> dashboard` 순서를 표준 절차로 삼는다.

---

## 최종 운영 체크리스트

메모:

- `.venv` 활성화 후 `python 01_scripts/healthcheck.py` 전체 PASS
- `python 01_scripts/01_data_collector.py` 수동 실행 성공
- `.env`의 `INFLUXDB_URL`, `TOKEN`, `ORG`, `BUCKET` 최신값 유지
- Grafana 데이터소스는 `Flux`, URL `http://127.0.0.1:8086`, Org `my-org`, Bucket `econ_market`
- Grafana 로그인 정보와 `.env`의 `GRAFANA_USER`, `GRAFANA_PASSWORD` 일치
- 다른 기기에서는 `http://100.112.72.127:3000`으로 접속 확인
- 백필 후 Grafana Explore 쿼리에서 실제 데이터 확인
- Cron은 `.venv/bin/python 01_scripts/01_data_collector.py` 기준으로 등록
- InfluxDB/Grafana 자동 시작 설정 유지
- `.env`, 토큰, 대시보드 JSON 별도 백업
