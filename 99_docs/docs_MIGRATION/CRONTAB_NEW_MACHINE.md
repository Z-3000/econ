# 새 기기용 crontab 정리

> 이 문서는 cron 등록만 다룬다.
> 서비스 설치, 데이터 복구, Grafana/InfluxDB 장애 대응은 [docs/MIGRATION_RUNBOOK_RASPI5_TRIXIE.md](docs/MIGRATION_RUNBOOK_RASPI5_TRIXIE.md)를 기준으로 본다.

## 결론

새 기기에서는 절대경로 `/WD4T/econ` 대신 실제 배치 경로를 기준으로 cron을 다시 등록해야 한다.

아래 예시는 프로젝트가 `/home/USER/econ`에 있다고 가정한다.

## 1. 사전 조건

- 프로젝트 경로: `/home/USER/econ`
- 가상환경: `/home/USER/econ/.venv`
- 로그 폴더: `/home/USER/econ/98_logs`
- 환경파일: `/home/USER/econ/.env`

먼저 1회 확인:

```bash
cd /home/USER/econ
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p 98_logs
python 01_scripts/healthcheck.py
```

라즈베리파이 OS Trixie라면 기본 `python3`가 3.13 계열일 수 있으므로 `python3.12`를 전제로 두지 않는 편이 안전합니다.

## 2. 권장 crontab

편집:

```bash
crontab -e
```

등록:

```cron
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

0 8 * * * cd /home/USER/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
0 16 * * 1-5 cd /home/USER/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
0 20 * * * cd /home/USER/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
```

## 3. 경로만 바꿔서 쓰는 템플릿

`/home/USER/econ`만 실제 경로로 치환해서 사용:

```cron
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

0 8 * * * cd /실제/프로젝트/경로/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
0 16 * * 1-5 cd /실제/프로젝트/경로/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
0 20 * * * cd /실제/프로젝트/경로/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
```

## 4. 기타 필요사항

- `.env`가 없으면 API, InfluxDB, Grafana 연결이 실패할 수 있음
- `98_logs/`가 없으면 로그 리다이렉션이 실패할 수 있음
- cron은 로그인 셸 환경을 거의 사용하지 않으므로 `PATH`를 명시하는 편이 안전함
- 프로젝트 루트로 `cd`한 뒤 상대경로 실행해야 경로 오류 가능성이 낮음
- 첫 등록 전에 수동 실행 1회로 정상 동작 확인이 필요함

수동 실행:

```bash
cd /home/USER/econ
source .venv/bin/activate
python 01_scripts/01_data_collector.py
```

로그 확인:

```bash
tail -f /home/USER/econ/98_logs/cron.log
```

## 5. 등록 후 검증

- `crontab -l`로 등록값 확인
- `python 01_scripts/healthcheck.py` 통과 확인
- `python 01_scripts/01_data_collector.py` 수동 실행 성공 확인
- 다음 예약 시간 이후 `98_logs/cron.log` 갱신 확인

## 6. 실패 원인 우선순위

1. 실제 프로젝트 경로 오기입
2. `.venv` 미생성 또는 패키지 미설치
3. `.env` 누락
4. `98_logs` 폴더 누락
5. InfluxDB 또는 Grafana 외부 서비스 미가동
