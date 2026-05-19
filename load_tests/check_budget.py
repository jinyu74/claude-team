# CI에서 Prometheus 메트릭 기반 perf budget 검증 — 카맥 §3.7
"""
사용법.
  python check_budget.py --scenario P-01 --threshold-p95 200 --metrics-url http://localhost:5000/metrics
"""
import argparse
import sys

import requests

QUANTILE_LABELS: dict[str, tuple[str, dict[str, str]]] = {
    "P-01": ("http_request_duration_seconds", {"quantile": "0.95"}),
    "P-02": (
        "sse_emit_to_receive_seconds",
        {"quantile": "0.95", "channel": "user", "client_type": "test"},
    ),
    "P-03": (
        "sse_emit_to_receive_seconds",
        {"quantile": "0.95", "channel": "job", "client_type": "test"},
    ),
    "P-07": (
        "http_request_duration_seconds",
        {"quantile": "0.95", "route": "/api/jobs"},
    ),
}


def get_metric_value(metrics_text: str, metric_name: str, labels: dict[str, str]) -> float | None:
    label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    for line in metrics_text.splitlines():
        if line.startswith("#"):
            continue
        if not line.startswith(metric_name):
            continue
        if label_str in line:
            try:
                return float(line.split()[-1]) * 1000  # seconds → ms
            except ValueError:
                continue
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Perf budget 검증")
    parser.add_argument("--scenario", required=True, choices=list(QUANTILE_LABELS))
    parser.add_argument("--threshold-p95", type=float, required=True, help="ms 단위 임계값")
    parser.add_argument("--metrics-url", default="http://localhost:5000/metrics")
    args = parser.parse_args()

    try:
        text = requests.get(args.metrics_url, timeout=5).text
    except Exception as e:
        print(f"[budget] 메트릭 수집 실패: {e}")
        sys.exit(1)

    metric_name, labels = QUANTILE_LABELS[args.scenario]
    value = get_metric_value(text, metric_name, labels)

    if value is None:
        print(f"[budget] 메트릭 {metric_name} 값을 찾을 수 없음.")
        sys.exit(1)

    print(f"[budget] {args.scenario}: p95 = {value:.1f}ms (임계값 {args.threshold_p95}ms)")
    if value <= args.threshold_p95:
        print("[budget] PASS")
        sys.exit(0)
    else:
        print(f"[budget] FAIL — {value:.1f}ms > {args.threshold_p95}ms")
        sys.exit(1)


if __name__ == "__main__":
    main()
