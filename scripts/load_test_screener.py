"""
Load test: 10 concurrent GET /api/v1/screener requests.

Sprint 6 - Day 43
"""

import threading
import time

import requests

URL = "http://localhost:8000/api/v1/screener?min_roe=15"
NUM_REQUESTS = 10

results = []
results_lock = threading.Lock()


def make_request(request_id):
    start = time.time()
    try:
        response = requests.get(URL, timeout=15)
        elapsed = time.time() - start
        with results_lock:
            results.append({
                "id": request_id,
                "status": response.status_code,
                "elapsed_sec": round(elapsed, 3),
            })
    except requests.RequestException as e:
        elapsed = time.time() - start
        with results_lock:
            results.append({
                "id": request_id,
                "status": "ERROR",
                "elapsed_sec": round(elapsed, 3),
                "error": str(e),
            })


def main():
    threads = []
    overall_start = time.time()

    for i in range(NUM_REQUESTS):
        t = threading.Thread(target=make_request, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    overall_elapsed = time.time() - overall_start

    print(f"\n{'='*50}")
    print(f"Load test: {NUM_REQUESTS} concurrent requests to /api/v1/screener")
    print(f"{'='*50}\n")

    for r in sorted(results, key=lambda x: x["id"]):
        print(f"Request {r['id']:2d}: status={r['status']} time={r['elapsed_sec']}s")

    print(f"\nTotal wall-clock time for all {NUM_REQUESTS} requests: {round(overall_elapsed, 3)}s")
    print(f"Target: all 10 complete within 10 seconds — "
          f"{'PASS' if overall_elapsed <= 10 else 'FAIL'}")

    slowest = max(results, key=lambda x: x["elapsed_sec"])
    print(f"Slowest individual request: #{slowest['id']} at {slowest['elapsed_sec']}s")


if __name__ == "__main__":
    main()