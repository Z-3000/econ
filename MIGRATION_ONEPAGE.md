# 새 기기 이전 전체 절차

> 이 문서는 "빠른 실행 절차" 전용이다.
> 실제 장애 사례, 원인 판별, Raspberry Pi 5 Trixie 환경에서의 복구 흐름은 [docs/MIGRATION_RUNBOOK_RASPI5_TRIXIE.md](docs/MIGRATION_RUNBOOK_RASPI5_TRIXIE.md)를 기준 문서로 사용한다.

## 결론

이 문서 하나만 순서대로 따라 하면 새 기기에서 이 프로젝트를 다시 실행할 수 있다.

이전 완료 기준은 아래 4개다.

- 프로젝트 파일이 새 기기에 복사됨
- `.venv`, `.env`, 패키지 설치가 완료됨
- `python 01_scripts/healthcheck.py`가 통과함
- `crontab`이 새 경로 기준으로 등록됨

## 중요 메모

이 문서는 현재 코드 기준으로 재검토를 한 번 더 거친 상태다.

재검토 결과:

- 실행용 Python 스크립트의 `/WD4T/econ` 절대경로 의존은 제거된 상태
- cron 기준 운영 스케줄은 `08:00 매일`, `16:00 평일`, `20:00 매일`
- `README.md`의 예전 cron 시간 표기도 현재 스케줄로 정정 완료

남은 주의점:

- 서비스만 새로 설치하면 기존 InfluxDB 데이터와 Grafana 메타데이터는 자동 복구되지 않는다
- 새 InfluxDB를 쓰면 `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET` 정합성을 다시 맞춰야 한다
- Grafana 데이터소스는 `InfluxDB OSS 2.x + Flux` 기준으로 다시 설정해야 한다

---

## 0. 이전 전에 이해해야 할 점

- 현재 코드는 실행 경로를 기준으로 프로젝트 루트를 계산하도록 수정되어 있다
- 따라서 예전처럼 `/WD4T/econ`에 반드시 둘 필요는 없다
- 대신 `cron`에는 새 기기의 실제 경로를 정확히 넣어야 한다
- `.env`는 Git에 포함되지 않을 수 있으므로 별도 복원 대상이다
- InfluxDB, Grafana, API 키는 외부 의존이라 파일만 복사해도 자동으로 살아나지 않는다
- 현재 문서 기준 운영 스케줄은 `08:00 매일`, `16:00 평일`, `20:00 매일`이다

---

## 1. 준비물

새 기기에서 아래가 필요하다.

- Python 3.x (`python3`, Trixie 기본 3.13)
- Bash 셸
- 프로젝트를 둘 실제 경로
- 기존 기기의 프로젝트 폴더
- 기존 `.env`
- InfluxDB 접속 정보
- Grafana 접속 정보
- 네이버 API 키
- BOK API 키
- FRED API 키

`.env`에 필요한 핵심 변수:

```env
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
BOK_API_KEY=
FRED_API_KEY=
INFLUXDB_URL=
INFLUXDB_TOKEN=
INFLUXDB_ORG=
INFLUXDB_BUCKET=
GRAFANA_URL=
GRAFANA_USER=
GRAFANA_PASSWORD=
```

참고:

- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`는 Telegram 알림을 쓸 때만 필요
- `healthcheck.py`는 현재 `NAVER`, `BOK`, `FRED`, `INFLUXDB_TOKEN`, `GRAFANA_PASSWORD`를 필수처럼 검사한다
- Grafana 외부 공개 주소와 내부 API 호출 주소를 혼동하면 복구 시간이 길어진다. 이 사례 정리는 런북을 참고한다

---

## 2. 새 기기 배치 경로 결정

예시 경로:

```bash
/home/USER/econ
```

이 문서에서는 이후 경로를 모두 `/home/USER/econ`으로 예시한다.

실제 적용 시 해야 할 일:

- `USER`를 실제 사용자명으로 바꾼다
- 다른 위치를 쓰면 문서의 `/home/USER/econ`을 전부 실제 경로로 바꾼다

---

## 3. 기존 기기에서 파일 복사

가장 단순한 방법은 프로젝트 폴더 전체를 `rsync`로 복사하는 것이다.

기존 기기에서 실행:

```bash
rsync -av /WD4T/econ/ USER@새기기IP:/home/USER/econ/
```

주의:

- 슬래시(`/WD4T/econ/`)를 끝에 붙이면 폴더 내용이 복사된다
- `/home/USER/econ/`이 새 기기에서 최종 프로젝트 루트가 된다
- `.env`가 실제로 프로젝트 폴더에 있으면 같이 복사된다
- `.env`가 누락될 가능성이 있으면 별도로 다시 확인한다

복사 후 새 기기에서 확인:

```bash
ls /home/USER/econ
```

최소 확인 대상:

- `01_scripts/`
- `00_data_raw/`
- `00-1_data_processed/`
- `data/`
- `03_outputs/`
- `requirements.txt`
- `.env.example`

---

## 4. 새 기기에서 Python 환경 구성

새 기기에서 실행:

```bash
cd /home/USER/econ
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p 98_logs
```

검증:

```bash
python --version
pip --version
```

판단 기준:

- `python --version`이 현재 시스템 `python3`와 일치하면 적합
- `pip install -r requirements.txt` 중 오류가 없어야 함

실패 시 우선 확인:

1. `python3`와 `venv`가 설치되어 있는지
2. 인터넷/패키지 저장소 접근이 되는지
3. 현재 디렉터리가 `/home/USER/econ`인지

---

## 5. `.env` 복원

### 방법 A. 기존 `.env`가 같이 복사된 경우

확인:

```bash
ls -la /home/USER/econ/.env
```

파일이 보이면 내용만 점검한다.

```bash
sed -n '1,200p' /home/USER/econ/.env
```

### 방법 B. `.env`가 없을 때

생성:

```bash
cd /home/USER/econ
cp .env.example .env
```

그 다음 실제 값 입력:

```env
NAVER_CLIENT_ID=실제값
NAVER_CLIENT_SECRET=실제값
BOK_API_KEY=실제값
FRED_API_KEY=실제값
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=실제값
INFLUXDB_ORG=my-org
INFLUXDB_BUCKET=econ_market
GRAFANA_URL=http://localhost:3000
GRAFANA_USER=admin
GRAFANA_PASSWORD=실제값
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

중요:

- `INFLUXDB_URL`, `GRAFANA_URL`이 새 기기 기준으로 맞는지 확인
- 서비스가 같은 기기에서 돌면 `localhost` 유지 가능
- 다른 서버에 있으면 실제 호스트 주소로 수정 필요

---

## 6. 데이터와 경로 상태 확인

새 기기에서 실행:

```bash
cd /home/USER/econ
find 00_data_raw -maxdepth 2 -type f | head
find data -maxdepth 2 -type f | head
```

절대경로 잔존 여부 확인:

```bash
cd /home/USER/econ
rg -n "/WD4T/econ" 01_scripts --glob '*.py'
```

판단 기준:

- 결과가 없어야 정상
- 결과가 문서 파일이 아니라 Python 실행 파일에 나오면 추가 수정 필요

---

## 7. 헬스체크 실행

새 기기에서 실행:

```bash
cd /home/USER/econ
source .venv/bin/activate
python 01_scripts/healthcheck.py
```

정상 기준:

- 환경변수 확인 통과
- InfluxDB 연결 성공
- Grafana 연결 성공
- 데이터 파일 확인 통과

실패 해석:

- 환경변수 실패: `.env` 값 누락 또는 오기입
- InfluxDB 실패: URL, 토큰, ORG, BUCKET 오류 또는 서비스 미기동
- Grafana 실패: URL, 계정, 비밀번호 오류 또는 서비스 미기동
- 데이터 파일 실패: 복사 누락 또는 경로 오류

주의:

- 이 단계가 실패하면 `cron` 등록하지 않는다

---

## 8. 수동 실행 검증

새 기기에서 실행:

```bash
cd /home/USER/econ
source .venv/bin/activate
python 01_scripts/01_data_collector.py
```

이 단계에서 확인할 것:

- 스크립트가 바로 종료되지 않는지
- API 호출 오류가 없는지
- 데이터 저장 오류가 없는지
- InfluxDB 쓰기 오류가 없는지

로그를 남기고 싶으면:

```bash
cd /home/USER/econ
source .venv/bin/activate
python 01_scripts/01_data_collector.py >> 98_logs/manual_run.log 2>&1
tail -n 100 98_logs/manual_run.log
```

판단 기준:

- 수동 1회 실행이 끝까지 완료되어야 함
- 에러가 있으면 `cron`보다 먼저 해결해야 함

---

## 9. crontab 백업

새 기기에서 기존 `cron`이 있다면 먼저 백업:

```bash
crontab -l > ~/crontab_backup_before_econ.txt
```

`no crontab for USER`가 나오면 기존 항목이 없는 상태다.

---

## 10. crontab 등록

편집:

```bash
crontab -e
```

아래 내용을 붙여넣는다.

```cron
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

0 8 * * * cd /home/USER/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
0 16 * * 1-5 cd /home/USER/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
0 20 * * * cd /home/USER/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
```

저장 후 확인:

```bash
crontab -l
```

반드시 확인할 것:

- `/home/USER/econ`이 실제 경로인지
- `.venv/bin/python` 경로가 맞는지
- `98_logs` 폴더가 있는지
- 스케줄이 현재 운영 의도와 맞는지
  - 현재 기준: `08:00 매일`, `16:00 평일`, `20:00 매일`

---

## 11. cron 등록 후 검증

즉시 확인:

```bash
ls -ld /home/USER/econ/98_logs
crontab -l
```

다음 예약 시간 이후 확인:

```bash
tail -n 100 /home/USER/econ/98_logs/cron.log
```

정상 기준:

- 로그 파일이 생성되거나 갱신됨
- Python 실행 오류가 없음
- API, DB 연결 오류가 없음

---

## 12. 자주 실패하는 원인

1. 프로젝트 실제 경로와 cron 경로가 다름
2. `.venv`를 만들지 않았거나 패키지 설치가 안 됨
3. `.env` 값 누락
4. InfluxDB 또는 Grafana가 실제로 실행 중이 아님
5. `98_logs` 폴더가 없어 로그 리다이렉션 실패
6. 데이터 폴더가 일부만 복사됨
7. `localhost`를 써야 할 곳에 다른 주소를 넣었거나 그 반대
8. Telegram 사용 시 `notifier.py` 내 Grafana 링크가 이전 환경 주소로 남아 있음

---

## 13. 최종 완료 체크

아래 7개가 모두 맞아야 이전 완료로 본다.

- [ ] `/home/USER/econ`에 프로젝트 파일이 존재함
- [ ] `/home/USER/econ/.venv` 생성 완료
- [ ] `/home/USER/econ/.env` 복원 완료
- [ ] `pip install -r requirements.txt` 완료
- [ ] `python 01_scripts/healthcheck.py` 통과
- [ ] `python 01_scripts/01_data_collector.py` 수동 실행 성공
- [ ] `crontab -l`에 새 경로 기준 스케줄이 등록됨

---

## 14. 가장 짧은 실행 순서

```bash
rsync -av /WD4T/econ/ USER@새기기IP:/home/USER/econ/

cd /home/USER/econ
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p 98_logs

# .env 확인 또는 복원
ls -la .env || cp .env.example .env

python 01_scripts/healthcheck.py
python 01_scripts/01_data_collector.py
crontab -e
```

`crontab -e`에는 아래를 넣는다.

```cron
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

0 8 * * * cd /home/USER/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
0 16 * * 1-5 cd /home/USER/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
0 20 * * * cd /home/USER/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
```
