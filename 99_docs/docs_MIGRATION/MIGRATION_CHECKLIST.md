# 이식 체크리스트

> 이 문서는 점검표 전용이다.
> 오류 원인 분석, InfluxDB/Grafana 복구, Python 3.13/Trixie 이슈는 [docs/MIGRATION_RUNBOOK_RASPI5_TRIXIE.md](docs/MIGRATION_RUNBOOK_RASPI5_TRIXIE.md)를 참고한다.

목표: 현재 작업을 다른 기기 또는 다른 폴더에서 같은 방식으로 실행

## 1. 파일 이동

- [ ] 프로젝트 폴더 전체 복사
- [ ] `.env` 별도 백업 후 새 위치에 복원
- [ ] 필요 데이터 폴더 포함 여부 확인
  - `00_data_raw/`
  - `00-1_data_processed/`
  - `data/`
  - `03_outputs/`
  - `98_logs/`

예시:

```bash
rsync -av /기존경로/econ/ /새경로/econ/
```

## 2. 실행 환경 재구성

- [ ] `python3` 설치 확인
- [ ] 가상환경 생성
- [ ] 패키지 설치
- [ ] `.env` 값 복원

```bash
cd /새경로/econ
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 3. 외부 의존 확인

- [ ] InfluxDB 접속 정보 확인
  - `INFLUXDB_URL`
  - `INFLUXDB_TOKEN`
  - `INFLUXDB_ORG`
  - `INFLUXDB_BUCKET`
- [ ] Grafana 접속 정보 확인
  - `GRAFANA_URL`
  - `GRAFANA_USER`
  - `GRAFANA_PASSWORD`
- [ ] API 키 확인
  - `NAVER_CLIENT_ID`
  - `NAVER_CLIENT_SECRET`
  - `BOK_API_KEY`
  - `FRED_API_KEY`

## 4. 경로 이식 확인

- [ ] 실행 코드에서 프로젝트 루트를 현재 파일 위치 기준으로 계산하는지 확인
- [ ] 크론은 실제 새 경로 기준으로 다시 등록
- [ ] 문서 예시에 있는 기존 경로 `/WD4T/econ`은 참고용인지 구분

검사 명령:

```bash
rg -n "/WD4T/econ" .
```

판단 기준:

- `01_scripts/*.py`에 남아 있으면 수정 필요
- `README.md`, `MIGRATION_GUIDE.md`에만 남아 있으면 문서 예시일 수 있음

## 5. 실행 검증

```bash
cd /새경로/econ
source .venv/bin/activate
python 01_scripts/healthcheck.py
python 01_scripts/01_data_collector.py
```

- [ ] 헬스체크 통과
- [ ] 데이터 파일 읽기 가능
- [ ] InfluxDB 연결 성공
- [ ] Grafana 연결 성공

## 6. 자동화 복구

- [ ] 기존 `crontab -l` 백업
- [ ] 새 경로 기준으로 cron 재등록

예시:

```cron
10 6 * * * cd /새경로/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
40 15 * * 1-5 cd /새경로/econ && ./.venv/bin/python 01_scripts/01_data_collector.py >> 98_logs/cron.log 2>&1
```

## 7. 최종 판정

이식 완료 조건:

- [ ] `python 01_scripts/healthcheck.py` 성공
- [ ] `python 01_scripts/01_data_collector.py` 1회 수동 실행 성공
- [ ] cron 경로가 새 위치로 반영됨
- [ ] `.env`와 외부 서비스 연결 확인됨
