# sampler 단일 리더 락 승계 시간 측정 — budget P-06 (승계 < 5s)
"""
사용법.
  python test_leader_failover.py \
    --metrics-urls http://api1:5000/metrics http://api2:5000/metrics \
    --leader-container team-claude-api-1 \
    --threshold-seconds 5.0

동작.
  1. 현재 리더 인스턴스 식별 (queue_emitter_leader == 1.0)
  2. 리더 컨테이너 강제 종료 (docker kill)
  3. 비-리더 인스턴스가 queue_emitter_leader=1 이 될 때까지 대기
  4. 승계 시간 < threshold_seconds 검증
"""
import argparse
import subprocess
import sys
import time

import requests


def get_leader_url(metrics_urls: list[str]) -> str | None:
    for url in metrics_urls:
        try:
            text = requests.get(url, timeout=2).text
            for line in text.splitlines():
                if line.startswith("queue_emitter_leader") and not line.startswith("#"):
                    _, value = line.rsplit(" ", 1)
                    if float(value) == 1.0:
                        return url
        except Exception:
            continue
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="P-06 리더 승계 시간 검증")
    parser.add_argument("--metrics-urls", nargs="+", required=True)
    parser.add_argument("--leader-container", required=True, help="리더 컨테이너 이름")
    parser.add_argument("--threshold-seconds", type=float, default=5.0)
    args = parser.parse_args()

    print("[P-06] 현재 리더 확인 중...")
    leader_url = get_leader_url(args.metrics_urls)
    if not leader_url:
        print("[P-06] 리더를 찾을 수 없음 — 서비스 상태 확인 필요.")
        sys.exit(1)
    print(f"[P-06] 리더: {leader_url}")

    print(f"[P-06] 리더 컨테이너 강제 종료: {args.leader_container}")
    subprocess.run(["docker", "kill", args.leader_container], check=True)
    kill_time = time.monotonic()

    remaining_urls = [u for u in args.metrics_urls if u != leader_url]
    timeout = args.threshold_seconds * 3

    print("[P-06] 승계 대기 중...")
    while True:
        new_leader = get_leader_url(remaining_urls)
        if new_leader:
            elapsed = time.monotonic() - kill_time
            print(f"[P-06] 승계 완료: {elapsed:.2f}s (임계값 {args.threshold_seconds}s)")
            if elapsed <= args.threshold_seconds:
                print("[P-06] PASS")
                sys.exit(0)
            else:
                print("[P-06] FAIL — 임계값 초과")
                sys.exit(1)
        if time.monotonic() - kill_time > timeout:
            print("[P-06] FAIL — 타임아웃 (리더 미확인)")
            sys.exit(1)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
