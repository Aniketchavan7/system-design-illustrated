"""
Standalone Simulation of Distributed Job & Task Scheduler.
Demonstrates:
  1. Priority Delayed Queue using timestamp scheduling.
  2. Multi-worker task processing pool.
  3. Worker heartbeating and deadline expiration tracking.
  4. Automatic detection and failover re-queueing of crashed worker tasks.
"""

import time
import heapq
import threading
from typing import Dict, List, Optional, Tuple

class ScheduledJob:
    def __init__(self, job_id: str, name: str, run_at: float, payload: dict):
        self.job_id = job_id
        self.name = name
        self.run_at = run_at
        self.payload = payload
        self.status = "SCHEDULED"  # SCHEDULED, RUNNING, COMPLETED, FAILED
        self.assigned_worker: Optional[str] = None
        self.last_heartbeat: float = 0.0
        self.deadline: float = 0.0
        self.attempts = 0

    def __lt__(self, other: 'ScheduledJob'):
        return self.run_at < other.run_at

class DistributedScheduler:
    def __init__(self):
        # Min-heap delayed queue: (run_at, job)
        self.delayed_queue: List[ScheduledJob] = []
        self.all_jobs: Dict[str, ScheduledJob] = {}
        self.lock = threading.Lock()
        self.is_running = True

    def schedule_job(self, job_id: str, name: str, delay_secs: float, payload: dict):
        now = time.time()
        job = ScheduledJob(job_id, name, now + delay_secs, payload)
        with self.lock:
            self.all_jobs[job_id] = job
            heapq.heappush(self.delayed_queue, job)
        print(f"  [SCHEDULED] '{name}' (ID: {job_id}) set to run in {delay_secs:.1f}s")

    def fetch_due_job(self) -> Optional[ScheduledJob]:
        now = time.time()
        with self.lock:
            if self.delayed_queue and self.delayed_queue[0].run_at <= now:
                job = heapq.heappop(self.delayed_queue)
                job.status = "RUNNING"
                job.attempts += 1
                job.last_heartbeat = now
                job.deadline = now + 0.4  # 400ms execution timeout
                return job
        return None

    def heartbeat(self, job_id: str):
        now = time.time()
        with self.lock:
            job = self.all_jobs.get(job_id)
            if job and job.status == "RUNNING":
                job.last_heartbeat = now
                job.deadline = now + 0.4

    def complete_job(self, job_id: str):
        with self.lock:
            job = self.all_jobs.get(job_id)
            if job:
                job.status = "COMPLETED"
                print(f"  [COMPLETED] Job '{job.name}' ({job_id}) finished successfully!")

    def check_and_recover_stalled_jobs(self):
        """Scans running jobs; re-queues any whose heartbeat deadline has elapsed."""
        now = time.time()
        with self.lock:
            for job in list(self.all_jobs.values()):
                if job.status == "RUNNING" and now > job.deadline:
                    print(f"  [FAILOVER] Worker crashed or timed out on '{job.name}' ({job.job_id})! Re-queueing...")
                    job.status = "SCHEDULED"
                    job.assigned_worker = None
                    job.run_at = now  # Run immediately
                    heapq.heappush(self.delayed_queue, job)

def worker_thread(scheduler: DistributedScheduler, worker_name: str, should_crash: bool = False):
    while scheduler.is_running:
        job = scheduler.fetch_due_job()
        if job:
            job.assigned_worker = worker_name
            print(f"  [DISPATCHED] {worker_name} picked up '{job.name}' (Attempt {job.attempts})")

            if should_crash:
                print(f"  [SIMULATED CRASH] {worker_name} crashed mid-execution on '{job.name}'!")
                # Worker ceases heartbeats and exits immediately!
                return

            # Normal worker execution with heartbeats
            for _ in range(2):
                time.sleep(0.1)
                scheduler.heartbeat(job.job_id)
            scheduler.complete_job(job.job_id)
        else:
            time.sleep(0.05)

def run_simulation():
    print("=" * 65)
    print("DISTRIBUTED JOB & TASK SCHEDULER SIMULATION")
    print("=" * 65)

    scheduler = DistributedScheduler()

    # 1. Schedule various delayed jobs
    print("Step 1: Enqueueing scheduled jobs with staggered execution times:")
    scheduler.schedule_job("j1", "Send Daily Digest Email", delay_secs=0.05, payload={"user": "u1"})
    scheduler.schedule_job("j2", "Heavy DB Backup", delay_secs=0.15, payload={"db": "prod"})
    scheduler.schedule_job("j3", "Process Subscription Renewal", delay_secs=0.25, payload={"sub": "sub_99"})

    # 2. Launch workers (Worker A will crash on its assigned job)
    print("\nStep 2: Spawning worker fleet (Worker_A will crash on its first task):\n")
    t1 = threading.Thread(target=worker_thread, args=(scheduler, "Worker_A", True))
    t2 = threading.Thread(target=worker_thread, args=(scheduler, "Worker_B", False))

    t1.start()
    t2.start()

    # 3. Scheduler supervisor loop (detecting crashed jobs)
    for _ in range(10):
        time.sleep(0.15)
        scheduler.check_and_recover_stalled_jobs()

    # Stop scheduler and wait for workers
    scheduler.is_running = False
    t1.join()
    t2.join()

    print("\nStep 3: Verification of final job states:")
    for jid, job in scheduler.all_jobs.items():
        print(f"  {job.job_id}: '{job.name:32}' -> Status: {job.status} (Total Attempts: {job.attempts})")

    assert all(j.status == "COMPLETED" for j in scheduler.all_jobs.values())
    assert any(j.attempts >= 2 for j in scheduler.all_jobs.values())

    print("\nSUCCESS: Worker failure detected, stalled task re-queued, and all jobs completed!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
