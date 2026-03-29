#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "[1/6] python3 확인"
python3 --version

echo "[2/6] 가상환경 생성"
python3 -m venv .venv

echo "[3/6] 가상환경 활성화"
source .venv/bin/activate

echo "[4/6] 패키지 설치"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

echo "[5/6] 로그 디렉터리 확인"
mkdir -p 98_logs

echo "[6/6] 헬스체크 실행"
python 01_scripts/healthcheck.py

echo
echo "수동 실행 테스트:"
echo "source .venv/bin/activate && python 01_scripts/01_data_collector.py"
