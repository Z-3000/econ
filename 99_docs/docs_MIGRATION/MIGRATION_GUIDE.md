# 마이그레이션 가이드

> 이 문서는 과거 이관 과정을 보존한 상세 기록이다.
> 현재 기준 운영 절차는 [MIGRATION_ONEPAGE.md](MIGRATION_ONEPAGE.md), 실제 장애 대응과 Raspberry Pi 5 Trixie 복구 절차는 [docs/MIGRATION_RUNBOOK_RASPI5_TRIXIE.md](docs/MIGRATION_RUNBOOK_RASPI5_TRIXIE.md)를 우선 사용한다.
> 아래 본문에는 과거 시점의 경로, 서비스 버전, 하드코딩 사례가 남아 있을 수 있다. 현재 사실로 바로 사용하지 말고 참고 기록으로만 본다.

라즈베리파이 → 서버용 노트북 마이그레이션

---

## 현재 환경 정보

| 항목 | 값 |
|------|-----|
| 프로젝트 경로 | `/WD4T/econ` |
| 가상환경 | `/home/raspi/influx_venv/` |
| 총 용량 | 약 200MB |
| Cron 작업 | 3개 (08:00, 16:00 평일, 20:00) |

---

## 1단계: 라즈베리파이에서 준비

### 1.1 Git 커밋 (선택)
```bash
# 라즈베리파이에서 실행
cd /WD4T/econ
git add .
git commit -m "마이그레이션 전 최종 커밋"
git push origin main
```

### 1.2 Cron 중지
```bash
# 현재 cron 백업
crontab -l > ~/crontab_backup.txt

# cron 작업 비활성화 (주석 처리)
crontab -e
# 아래 3줄 앞에 # 추가
# 0 8 * * * /home/raspi/influx_venv/bin/python /WD4T/econ/01_scripts/01_data_collector.py ...
# 0 16 * * 1-5 /home/raspi/influx_venv/bin/python /WD4T/econ/01_scripts/01_data_collector.py ...
# 0 20 * * * /home/raspi/influx_venv/bin/python /WD4T/econ/01_scripts/01_data_collector.py ...
```

### 1.3 .env 파일 백업
```bash
# .env 파일은 Git에 없으므로 별도 복사 필요
cp /WD4T/econ/.env ~/econ_env_backup.txt
```

> **rsync/scp 방법 사용 시**: .env 파일도 함께 전송되므로 이 단계와 3.2 복원 단계를 생략할 수 있습니다.
> **Git 방법 사용 시**: .env는 .gitignore로 제외되므로 이 백업과 3.2 복원이 반드시 필요합니다.

---

## 2단계: 서버용 노트북으로 파일 전송

### 방법 A: rsync를 통한 전송 (권장)
```bash
# 서버용 노트북에서 실행
rsync -avz --progress raspi@라즈베리파이IP:/WD4T/econ /원하는/경로/
```

> rsync를 권장하는 이유: `00_data_raw/`, `00-1_data_processed/`, `data/`, `98_logs/` 폴더는 Git에 포함되지 않습니다. rsync는 이 폴더들을 포함한 전체를 그대로 복사하므로 누락 위험이 없습니다.

### 방법 B: SCP를 통한 직접 전송
```bash
# 서버용 노트북에서 실행
scp -r raspi@라즈베리파이IP:/WD4T/econ /원하는/경로/
```

### 방법 C: Git을 통한 전송
```bash
# 서버용 노트북에서 실행
cd /원하는/경로
git clone https://github.com/사용자/econ.git
```

> **Git 사용 시 필수 추가 작업**: 아래 4개 폴더는 Git에 포함되지 않으므로 반드시 별도로 복사해야 합니다.
> ```bash
> # 라즈베리파이에서 서버로 누락 폴더 추가 복사
> rsync -avz --progress raspi@라즈베리파이IP:/WD4T/econ/00_data_raw /원하는/경로/econ/
> rsync -avz --progress raspi@라즈베리파이IP:/WD4T/econ/00-1_data_processed /원하는/경로/econ/
> rsync -avz --progress raspi@라즈베리파이IP:/WD4T/econ/data /원하는/경로/econ/
> mkdir -p /원하는/경로/econ/98_logs
> ```

---

## 3단계: 서버용 노트북 환경 설정

### 3.1 Python 가상환경 생성
```bash
cd /원하는/경로/econ

# 가상환경 생성
python3 -m venv .venv
# Trixie에서는 기본 python3가 3.13 계열일 수 있습니다.

# 활성화 (Linux/Mac)
source .venv/bin/activate

# 활성화 (Windows)
.venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 3.2 .env 파일 복원
```bash
# 백업한 .env 내용을 새 위치에 복사
cp ~/econ_env_backup.txt /원하는/경로/econ/.env

# 또는 .env.example을 복사 후 수정
cp .env.example .env
# 편집기로 API 키 입력
```

### 3.3 경로 설정 (참고용)

주의: 아래 내용은 과거 코드 기준 분석이다. 현재는 프로젝트 루트를 동적으로 계산하므로 `/WD4T/econ` 심볼릭 링크를 반드시 만들 필요는 없다.

다만 문서 예시, cron 예시, 기타 운영 스크립트에는 `/WD4T/econ` 문자열이 남아 있을 수 있으므로 새 경로로 교체해 확인해야 합니다.

**영향 받는 파일 목록 (5개)**

| 파일 | 내용 |
|------|------|
| `01_scripts/config.py` | `BASE_DIR = "/WD4T/econ"` — 모든 CSV 저장 경로의 기준 |
| `01_scripts/03_merge_historical_data.py` | `BASE_DIR = "/WD4T/econ"` — config를 사용하지 않고 직접 하드코딩 |
| `01_scripts/07_create_system_health_dashboard.py` | `load_dotenv('/WD4T/econ/.env')` — .env를 절대경로로 로드 |
| `01_scripts/07_create_system_health_dashboard.py` | `output_path = "/WD4T/econ/03_outputs/..."` — JSON 저장 경로 |
| `01_scripts/05_create_grafana_dashboard_v2.py` | `output_file = "/WD4T/econ/03_outputs/..."` — JSON 저장 경로 |

> `config.py`만 수정하면 나머지 4개는 그대로 남습니다. 심볼릭 링크를 만들면 5개 모두 한 번에 해결됩니다.

**방법 1) 심볼릭 링크 생성 (권장)**

rsync 방법 A(권장)로 파일을 받은 경우, `/WD4T/econ`은 새 서버에 존재하지 않으므로 바로 링크 생성이 가능합니다.

```bash
# /WD4T 디렉터리가 없으면 먼저 생성 (root 권한 필요)
sudo mkdir -p /WD4T

# 심볼릭 링크 생성
ln -s /원하는/경로/econ /WD4T/econ

# 확인
ls -la /WD4T/
```

> **`ln -s`가 실패하는 경우**: `/WD4T/econ`이 이미 실제 디렉터리로 존재할 때입니다 (rsync/scp를 `/WD4T/` 아래에 직접 받은 경우). 이때는 먼저 제거 후 링크를 생성하세요.
> ```bash
> rm -rf /WD4T/econ        # 실제 디렉터리 삭제 (파일은 /원하는/경로/econ에 이미 있어야 함)
> ln -s /원하는/경로/econ /WD4T/econ
> ```

**방법 2) 코드 직접 수정 (5개 파일 모두 수정 필요)**
```bash
# 수정이 필요한 파일들
# - 01_scripts/config.py (BASE_DIR)
# - 01_scripts/03_merge_historical_data.py (BASE_DIR)
# - 01_scripts/07_create_system_health_dashboard.py (load_dotenv 경로, output_path)
# - 01_scripts/05_create_grafana_dashboard_v2.py (output_file)
```

### 3.4 Grafana 외부 링크/공개 주소 (참고용)

현재 운영에서는 Grafana 내부 API 주소와 외부 공개 주소를 구분해 보는 편이 안전하다.
이 구분과 실제 수정 사례는 런북 문서를 우선 참고한다.

### 3.5 필요한 API 키 목록
| 서비스 | 환경변수 | 발급처 |
|--------|----------|--------|
| 네이버 검색 | `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` | developers.naver.com |
| 한국은행 ECOS | `BOK_API_KEY` | ecos.bok.or.kr/api |
| FRED (미국) | `FRED_API_KEY` | fred.stlouisfed.org |
| InfluxDB | `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET` | 로컬 설치 |
| Grafana | `GRAFANA_URL`, `GRAFANA_USER`, `GRAFANA_PASSWORD` | 로컬 설치 |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | @BotFather |

---

## 4단계: InfluxDB & Grafana 설정 (필요시)

### 4.1 InfluxDB 설치
```bash
# Ubuntu/Debian
wget https://dl.influxdata.com/influxdb/releases/influxdb2-2.7.1-amd64.deb
sudo dpkg -i influxdb2-2.7.1-amd64.deb
sudo systemctl start influxdb
sudo systemctl enable influxdb
```

### 4.2 Grafana 설치
```bash
# Ubuntu/Debian
sudo apt-get install -y adduser libfontconfig1
wget https://dl.grafana.com/oss/release/grafana_10.2.0_amd64.deb
sudo dpkg -i grafana_10.2.0_amd64.deb
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

### 4.3 기존 데이터 마이그레이션 (선택)
```bash
# InfluxDB 데이터 백업 (라즈베리파이)
influx backup /path/to/backup --bucket econ_market

# InfluxDB 데이터 복원 (서버 노트북)
influx restore /path/to/backup
```

### 4.4 Grafana 대시보드 복원
1) Grafana 웹 UI 접속 후 InfluxDB 데이터소스 재생성 (URL/토큰/ORG/Bucket 동일하게 입력)  
2) `03_outputs/grafana_dashboard_*.json`, `03_outputs/system_health_dashboard.json`을 Grafana에서 Import하여 대시보드 복원

---

## 5단계: Cron 설정 (서버용 노트북)

### 5.1 경로 수정 후 cron 등록
```bash
crontab -e
```

아래 내용 추가 (경로를 새 환경에 맞게 수정):
```cron
# 데이터 수집 (가상환경 Python 사용)
0 8 * * * /새경로/econ/venv/bin/python /새경로/econ/01_scripts/01_data_collector.py >> /새경로/econ/98_logs/cron.log 2>&1
0 16 * * 1-5 /새경로/econ/venv/bin/python /새경로/econ/01_scripts/01_data_collector.py >> /새경로/econ/98_logs/cron.log 2>&1
0 20 * * * /새경로/econ/venv/bin/python /새경로/econ/01_scripts/01_data_collector.py >> /새경로/econ/98_logs/cron.log 2>&1
```
- 로그 파일이 Git에 없으므로 먼저 `mkdir -p /새경로/econ/98_logs`로 디렉터리를 생성하세요.

---

## 6단계: 테스트

### 6.1 헬스체크 (먼저 실행)

데이터 수집 전에 환경 설정이 올바른지 먼저 확인합니다.

```bash
cd /새경로/econ
source venv/bin/activate

python 01_scripts/healthcheck.py
```

`healthcheck.py`는 아래 4가지를 한 번에 점검합니다.

| 항목 | 확인 내용 |
|------|----------|
| 환경변수 | API 키 6개 설정 여부 |
| InfluxDB | 연결 및 데이터 건수 |
| Grafana | 연결 및 인증 |
| 데이터 파일 | 15년 히스토리 CSV 4개 존재 여부 |

모든 항목이 PASS가 되면 다음 단계로 진행합니다.

### 6.2 수동 테스트
```bash
# 데이터 수집 테스트
python 01_scripts/01_data_collector.py
```

### 6.3 확인 사항
- [ ] healthcheck.py 전체 PASS
- [ ] 데이터 수집 정상 동작
- [ ] InfluxDB 연결 확인 (설치한 경우)
- [ ] Grafana 대시보드 확인 (설치한 경우)
- [ ] Telegram 알림 테스트

---

## 7단계: 라즈베리파이 정리 (선택)

마이그레이션 완료 확인 후:
```bash
# cron 완전 제거
crontab -r

# 프로젝트 폴더 삭제 (주의!)
# rm -rf /WD4T/econ
```

---

## 체크리스트

| 단계 | 작업 | 완료 |
|------|------|------|
| 1 | Git 커밋 & push | ☐ |
| 2 | Cron 중지 | ☐ |
| 3 | .env 백업 | ☐ |
| 4 | 파일 전송 | ☐ |
| 5 | 가상환경 생성 | ☐ |
| 6 | .env 설정 | ☐ |
| 7 | 경로 설정 (심볼릭 링크 또는 코드 수정) | ☐ |
| 8 | notifier.py Grafana IP 수정 | ☐ |
| 9 | InfluxDB/Grafana (선택) | ☐ |
| 10 | Cron 설정 | ☐ |
| 11 | 테스트 | ☐ |
| 12 | 라즈베리파이 정리 | ☐ |

---

## 문제 해결

### 패키지 설치 오류
```bash
# numpy/pandas 설치 실패 시
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### cron 실행 안됨
```bash
# 로그 확인
tail -f /새경로/econ/98_logs/cron.log

# cron 서비스 상태 확인
systemctl status cron
```

### InfluxDB 연결 실패
```bash
# InfluxDB 상태 확인
systemctl status influxdb

# 토큰 재발급
influx auth create --org my-org --all-access
```

---

## 업데이트 내역

### 2026-03-29
- 실행 영향이 큰 경로 하드코딩 4건 수정: `config.py`, `03_merge_historical_data.py`, `05_create_grafana_dashboard_v2.py`, `07_create_system_health_dashboard.py`
- `healthcheck.py` 실행 예시를 상대경로 기준으로 수정
- 간단 이식 문서 `MIGRATION_CHECKLIST.md` 추가
- `README.md` 설치/cron 예시를 새 경로 기준으로 재작성

### 2026-02-25 (코드 검토 반영 — 2차)
- **1.3 .env 백업** 주석 추가: rsync/scp 방법 사용 시 .env도 함께 전송되므로 백업·복원 단계 생략 가능, Git 방법 사용 시 필수라는 구분 안내 추가
- **3.3 심볼릭 링크 mv 명령어 수정**: 권장 rsync 시나리오에서는 `/WD4T/econ`이 존재하지 않으므로 `mv` 없이 바로 `ln -s` 가능. 기존 `/WD4T/econ`이 실제 디렉터리로 있는 경우에만 `rm -rf` 후 링크 생성하도록 안내 재작성
- **6단계 테스트** 재구성: `healthcheck.py`를 6.1로 먼저 실행하도록 추가 (환경변수·InfluxDB·Grafana·데이터 파일 4종 일괄 점검), 기존 수동 테스트는 6.2로 이동

### 2026-02-25 (코드 검토 반영 — 1차)
- **2단계 파일 전송** 순서 변경: rsync를 방법 A(권장)로 격상, Git을 방법 C로 이동. Git 사용 시 누락 폴더 4개를 rsync로 추가 복사하는 필수 단계 명시
- **3.3 경로 설정** 전면 보강: `/WD4T/econ`이 하드코딩된 파일 5개 목록 명시, 심볼릭 링크 방식 권장 이유 추가, `sudo mkdir -p /WD4T` 선행 단계 추가, `/WD4T/econ` 이미 존재 시 `ln -s` 실패 경우 안내 추가
- **3.4 신규 추가**: `notifier.py:179` 하드코딩 IP(`100.125.124.53`) 수정 안내 — 심볼릭 링크로 해결 불가, 코드 직접 수정 필요
- **체크리스트** 업데이트: "경로 설정(심볼릭 링크)", "notifier.py IP 수정" 항목 추가

### 2026-01-07
- Python 버전 명시(`python3.12 -m venv`) 추가
- `BASE_DIR` 경로 수정/심볼릭 링크 안내 추가
- Git에 없는 데이터/로그 폴더 복사 및 `98_logs` 생성 안내 추가
- Grafana 대시보드 JSON 임포트 및 데이터소스 재설정 절차 추가

---


---

<!-- DOC_UPDATE_2026-02-25 -->
## 마이그레이션 후속 반영 (2026-02-25)
- 마이그레이션 검증을 위해 백필 전용 버킷 `econ_market_backfill_2010_2025`를 추가했습니다.
- 운영 버킷(`econ_market`)은 실시간 수집 데이터가 계속 누적되므로, 백필 정합성 판정은 전용 버킷 기준으로 수행하도록 변경했습니다.
- 무결성 체크 자동화 스크립트 `09_validate_influx_integrity.py`를 기준 검증 도구로 지정합니다.

## 마이그레이션 체크포인트 추가
1. 백필 완료 후 전용 버킷 DQ 리포트 보관
2. 운영 버킷은 누락 중심 모니터링, extra는 분리 해석
