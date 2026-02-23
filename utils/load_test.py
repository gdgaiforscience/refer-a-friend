import concurrent.futures
import requests
import time
import secrets
import string
import statistics
from collections import Counter

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Configuration
# Point this to either the Nginx port (8080) or directly to FastAPI (8000)
BASE_URL = "http://127.0.0.1:8000"  
NUM_REQUESTS = 1000
CONCURRENT_USERS = 50

def generate_random_email():
    return f"{''.join(secrets.choice(string.ascii_lowercase) for _ in range(10))}@example.com"

def test_generate_link():
    email = generate_random_email()
    payload = {
        "member_email": email,
        "event_path": "google-gdg-ai-for-science-australia-presents-the-adversarial-misuse-of-ai-and-how-to-defend-against-it/"
    }
    start = time.time()
    try:
        resp = requests.post(f"{BASE_URL}/generate", json=payload, timeout=5)
        duration = time.time() - start
        code = None
        if resp.status_code in (200, 201):
            try:
                code = resp.json().get("referral_code")
            except:
                pass
        return {"status": resp.status_code, "duration": duration, "code": code}
    except Exception as e:
        return {"status": "Error", "duration": time.time() - start, "error": str(e)}

def test_redirect(code):
    if not code: return None
    start = time.time()
    try:
        # allow_redirects=False because we just want to see if the engine handles the redirect hit
        resp = requests.get(f"{BASE_URL}/ref/{code}", allow_redirects=False, timeout=5)
        duration = time.time() - start
        return {"status": resp.status_code, "duration": duration}
    except Exception as e:
        return {"status": "Error", "duration": time.time() - start, "error": str(e)}

def print_stats(name, results, total_time):
    # Filter out None results (from empty codes) and errors for latency stats
    results = [r for r in results if r is not None]
    valid_results = [r for r in results if r["status"] != "Error"]
    durations = [r["duration"] for r in valid_results]
    statuses = Counter([r["status"] for r in results])
    
    print(f"\n" + "="*40)
    print(f"📊 {name.upper()} SUMMARY")
    print("="*40)
    print(f"Total Requests: {len(results)}")
    print(f"Total Time:     {total_time:.2f}s")
    print(f"Throughput:     {len(results) / total_time:.2f} requests/sec")
    
    if durations:
        print(f"\nLATENCY:")
        print(f"  Average:   {statistics.mean(durations)*1000:.2f}ms")
        print(f"  Median:    {statistics.median(durations)*1000:.2f}ms")
        if len(durations) > 1:
            q = statistics.quantiles(durations, n=100)
            print(f"  P95:       {q[94]*1000:.2f}ms")
            print(f"  P99:       {q[98]*1000:.2f}ms")
    
    print(f"\nSTATUS CODES:")
    for status, count in sorted(statuses.items(), key=lambda x: str(x[0])):
        print(f"  {status}: {count}")

def run_load_test():
    print(f"🚀 Starting load test: {NUM_REQUESTS} requests, {CONCURRENT_USERS} concurrency...")
    print(f"Target: {BASE_URL}")
    
    # --- Capture Hardware Snapshot ---
    disk_start = psutil.disk_io_counters() if HAS_PSUTIL else None
    mem_start = psutil.virtual_memory().used if HAS_PSUTIL else None
    
    # Simple CPU sampling in background
    cpu_samples = []
    def sample_cpu(stop_event):
        while not stop_event.is_set():
            cpu_samples.append(psutil.cpu_percent(interval=0.5))

    import threading
    stop_cpu = threading.Event()
    if HAS_PSUTIL:
        threading.Thread(target=sample_cpu, args=(stop_cpu,), daemon=True).start()

    # --- Phase 1: Generation ---
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        gen_results = list(executor.map(lambda _: test_generate_link(), range(NUM_REQUESTS)))
    gen_total_time = time.time() - start_time
    
    print_stats("Link Generation", gen_results, gen_total_time)
    
    # --- Phase 2: Redirects ---
    codes = [r["code"] for r in gen_results if r and r.get("code")]
    if codes:
        print(f"\n🚀 Testing redirects using {len(codes)} unique codes...")
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
            red_results = list(executor.map(test_redirect, codes))
        red_total_time = time.time() - start_time
        print_stats("Redirects", red_results, red_total_time)

    # --- Stop hardware sampling ---
    stop_cpu.set()

    # --- Print Hardware Summary ---
    if HAS_PSUTIL and disk_start:
        disk_end = psutil.disk_io_counters()
        mem_end = psutil.virtual_memory().used
        
        print("\n" + "="*40)
        print("💻 SYSTEM RESOURCE USAGE DURING TEST")
        print("="*40)
        
        # CPU Stats
        if cpu_samples:
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            peak_cpu = max(cpu_samples)
            print(f"CPU Usage:  Avg {avg_cpu:.1f}%, Peak {peak_cpu:.1f}%")
        
        # Memory Stats
        mem_delta = (mem_end - mem_start) / (1024 * 1024)
        print(f"RAM Usage:  Delta {mem_delta:+.2f} MB")

        # Disk Stats
        if disk_end:
            read_mb = (disk_end.read_bytes - disk_start.read_bytes) / (1024 * 1024)
            write_mb = (disk_end.write_bytes - disk_start.write_bytes) / (1024 * 1024)
            print(f"Disk Read:  {read_mb:.2f} MB")
            print(f"Disk Write: {write_mb:.2f} MB")
            print(f"Disk Busy:  {(disk_end.write_time - disk_start.write_time)/1000:.2f}s")
    elif not HAS_PSUTIL:
        print("\nNote: Install 'psutil' to see CPU, RAM, and Disk statistics (pip install psutil)")

if __name__ == "__main__":
    try:
        run_load_test()
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
    except Exception as e:
        print(f"\nFailed to run test: {e}")
        print("\nUsage Troubleshooting:")
        print("1. Ensure your app is running locally (e.g. docker run or uvicorn/streamlit).")
        print("2. Check if BASE_URL in this script matches your app's port.")
