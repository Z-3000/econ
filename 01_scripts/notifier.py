#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram 알림 모듈 (Notifier)
==============================
데이터 수집 결과를 Telegram으로 전송

원리:
1. Telegram Bot API 사용 (HTTP POST 요청)
2. Bot Token으로 봇 인증
3. Chat ID로 수신자 지정
4. sendMessage 엔드포인트로 메시지 전송

API 엔드포인트:
    https://api.telegram.org/bot{TOKEN}/sendMessage

필수 설정 (.env):
    TELEGRAM_BOT_TOKEN: BotFather에서 발급받은 토큰
    TELEGRAM_CHAT_ID: 메시지 받을 채팅방 ID

Author: Claude Code
Created: 2025-12-07
"""

import requests
from datetime import datetime
from config import config


class TelegramNotifier:
    """
    Telegram 알림 클래스

    사용법:
        notifier = TelegramNotifier()
        notifier.send_collection_result(result_dict)
    """

    def __init__(self):
        """초기화: 설정 로드"""
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.enabled = config.TELEGRAM_ENABLED
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Telegram으로 메시지 전송

        Args:
            message: 전송할 메시지 (HTML 형식 지원)
            parse_mode: 파싱 모드 ("HTML" 또는 "Markdown")

        Returns:
            bool: 전송 성공 여부
        """
        if not self.enabled:
            print("  ⚠️ Telegram 알림 비활성화 (토큰/채팅ID 미설정)")
            return False

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            response = requests.post(self.api_url, json=payload, timeout=10)

            if response.status_code == 200:
                print("  📱 Telegram 알림 전송 완료")
                return True
            else:
                print(f"  ❌ Telegram 전송 실패: {response.status_code}")
                return False

        except Exception as e:
            print(f"  ❌ Telegram 오류: {e}")
            return False

    def send_collection_result(self, results: dict) -> bool:
        """
        수집 결과를 포맷팅하여 전송

        Args:
            results: 수집 결과 딕셔너리
                {
                    'news': {'success': 20, 'fail': 0, 'time_ms': 1500},
                    'stock': {'success': 68, 'fail': 0, 'no_data': 5, 'time_ms': 45000},
                    'economy': {'success': 5, 'fail': 2, 'no_data': 2, 'time_ms': 3000},
                    'total_time_ms': 50000,
                    'has_error': False,
                    'market_info': '주말 휴장',
                    'failed_items': ['KODEX 미국S&P500커버드콜OTM(453530.KS)']
                }

        Returns:
            bool: 전송 성공 여부
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 전체 성공 여부 판단 (실제 에러만 카운트, 휴장은 제외)
        has_error = results.get('has_error', False)

        # 총 실행 시간 (초)
        total_sec = results.get('total_time_ms', 0) / 1000

        # 상태 아이콘 결정
        status_icon = "❌" if has_error else "✅"
        status_text = "실패" if has_error else "성공"

        # 메시지 구성
        message = f"""
<b>{status_icon} 데이터 수집 {status_text}</b>
<code>─────────────────────</code>
📅 {now}
⏱️ 총 {total_sec:.1f}초
"""

        # 휴장/시장 정보 표시
        market_info = results.get('market_info', '')
        if market_info:
            message += f"📌 {market_info}\n"

        message += "\n<b>📊 수집 결과</b>\n"

        # 각 작업별 결과 추가
        task_icons = {
            'news': '📰',
            'stock': '📈',
            'economy': '💰'
        }

        for task, icon in task_icons.items():
            if task in results:
                r = results[task]
                success = r.get('success', 0)
                fail = r.get('fail', 0)
                no_data = r.get('no_data', 0)  # 휴장/데이터 없음
                time_sec = r.get('time_ms', 0) / 1000

                # 결과 라인 구성
                parts = [f"{success}✓"]
                if no_data > 0:
                    parts.append(f"{no_data}📅")  # 휴장 표시
                if fail > 0:
                    parts.append(f"{fail}✗")

                line = f"{icon} {task}: {' / '.join(parts)} ({time_sec:.1f}s)"
                if fail > 0:
                    line += " ⚠️"

                message += line + "\n"

        # 과거 데이터 사용 항목 (있을 경우) - 성공이지만 최신 데이터가 아닌 경우
        delayed_items = results.get('delayed_items', [])
        if delayed_items:
            message += "\n<b>📅 과거 데이터 사용</b>\n"
            for item in delayed_items[:7]:  # 최대 7개
                message += f"• {item}\n"

        # 실패 종목 상세 정보 (있을 경우)
        failed_items = results.get('failed_items', [])
        if failed_items:
            message += "\n<b>⚠️ 실패 항목</b>\n"
            for item in failed_items[:5]:  # 최대 5개
                message += f"• {item[:40]}\n"
            if len(failed_items) > 5:
                message += f"• ... 외 {len(failed_items) - 5}개\n"

        # 에러 상세 정보 (있을 경우)
        if has_error and 'errors' in results:
            message += "\n<b>❌ 에러 상세</b>\n"
            for err in results.get('errors', [])[:3]:  # 최대 3개
                message += f"• {err[:50]}\n"

        message += """
<code>─────────────────────</code>
🔗 <a href="http://100.125.124.53:3000">Grafana 대시보드</a>
"""

        return self.send_message(message)

    def send_error_alert(self, task_name: str, error_msg: str) -> bool:
        """
        긴급 에러 알림 전송

        Args:
            task_name: 작업명 (news, stock, economy)
            error_msg: 에러 메시지

        Returns:
            bool: 전송 성공 여부
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""
🚨 <b>긴급: 데이터 수집 오류</b>
<code>─────────────────────</code>
📅 {now}
📌 작업: {task_name}

<b>에러 내용:</b>
<code>{error_msg[:200]}</code>

<code>─────────────────────</code>
즉시 확인이 필요합니다.
"""

        return self.send_message(message)

    def send_test_message(self) -> bool:
        """
        테스트 메시지 전송

        Returns:
            bool: 전송 성공 여부
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""
🔔 <b>Telegram 알림 테스트</b>
<code>─────────────────────</code>
📅 {now}
✅ 연결 성공!

이 메시지가 보이면 Telegram 알림이 정상 작동합니다.
앞으로 데이터 수집 결과를 이 채널로 받게 됩니다.
"""

        return self.send_message(message)


# 편의 함수: 모듈 레벨에서 바로 사용
_notifier = None


def get_notifier() -> TelegramNotifier:
    """싱글톤 Notifier 인스턴스 반환"""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier


def send_collection_result(results: dict) -> bool:
    """수집 결과 전송 (편의 함수)"""
    return get_notifier().send_collection_result(results)


def send_error_alert(task_name: str, error_msg: str) -> bool:
    """에러 알림 전송 (편의 함수)"""
    return get_notifier().send_error_alert(task_name, error_msg)


def send_test_message() -> bool:
    """테스트 메시지 전송 (편의 함수)"""
    return get_notifier().send_test_message()


# 스크립트로 직접 실행 시 테스트
if __name__ == "__main__":
    print("=" * 50)
    print("Telegram 알림 테스트")
    print("=" * 50)

    notifier = TelegramNotifier()

    if not notifier.enabled:
        print("\n❌ Telegram 설정이 완료되지 않았습니다.")
        print("\n[설정 방법]")
        print("1. Telegram에서 @BotFather 검색")
        print("2. /newbot 명령으로 봇 생성")
        print("3. 발급받은 토큰을 .env 파일의 TELEGRAM_BOT_TOKEN에 입력")
        print("4. 생성된 봇에게 아무 메시지나 전송")
        print("5. 브라우저에서 다음 URL 접속:")
        print(f"   https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates")
        print("6. 응답에서 chat.id 값을 .env 파일의 TELEGRAM_CHAT_ID에 입력")
    else:
        print(f"\n✅ Telegram 설정 확인됨")
        print(f"   Bot Token: {notifier.bot_token[:10]}...")
        print(f"   Chat ID: {notifier.chat_id}")

        print("\n테스트 메시지 전송 중...")
        if notifier.send_test_message():
            print("✅ 테스트 성공! Telegram을 확인하세요.")
        else:
            print("❌ 테스트 실패. 토큰/채팅ID를 확인하세요.")
