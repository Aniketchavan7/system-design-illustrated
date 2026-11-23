#!/usr/bin/env python3
"""
Back-of-the-Envelope System Capacity & Infrastructure Calculator
Standalone, zero-dependency CLI tool for sizing distributed systems.
Usage:
  python calculate.py --help
  python calculate.py --preset twitter
  python calculate.py --dau 100000000 --writes 2 --reads 20 --write-size-kb 1 --read-size-kb 10
"""

import argparse
import sys
import math

PRESETS = {
    "twitter": {
        "name": "Twitter / X (Posts & Home Timeline)",
        "dau": 300_000_000,
        "writes_per_user": 2,
        "reads_per_user": 20,
        "write_size_kb": 1.0,      # Tweet text + media pointers + metadata
        "read_size_kb": 10.0,      # Paginated 20-tweet timeline
        "retention_years": 5,
        "replication_factor": 3,
        "peak_multiplier": 2.5
    },
    "youtube": {
        "name": "YouTube (Video Streaming & Metadata)",
        "dau": 100_000_000,
        "writes_per_user": 0.05,   # 1 upload every 20 days per active user
        "reads_per_user": 5,       # 5 video views per day
        "write_size_kb": 250_000.0, # 250 MB average video file
        "read_size_kb": 100_000.0,  # 100 MB stream per view
        "retention_years": 5,
        "replication_factor": 3,
        "peak_multiplier": 2.0
    },
    "uber": {
        "name": "Uber / Ride-Sharing (Driver GPS & Dispatch)",
        "dau": 25_000_000,
        "writes_per_user": 120,    # Driver pings location every 4s during shift
        "reads_per_user": 10,      # Rider app queries nearby drivers
        "write_size_kb": 0.2,      # 200 bytes per GPS coordinate ping
        "read_size_kb": 2.0,       # 2 KB nearby driver list
        "retention_years": 2,
        "replication_factor": 3,
        "peak_multiplier": 3.0
    },
    "chat": {
        "name": "WhatsApp / Real-Time Chat Application",
        "dau": 500_000_000,
        "writes_per_user": 40,     # 40 messages sent per day
        "reads_per_user": 40,      # 40 messages read per day
        "write_size_kb": 0.5,      # 500 bytes per text message
        "read_size_kb": 0.5,
        "retention_years": 5,
        "replication_factor": 3,
        "peak_multiplier": 3.0
    }
}

def format_number(n: float) -> str:
    if n >= 1e12:
        return f"{n / 1e12:.2f} Trillion"
    elif n >= 1e9:
        return f"{n / 1e9:.2f} Billion"
    elif n >= 1e6:
        return f"{n / 1e6:.2f} Million"
    elif n >= 1e3:
        return f"{n / 1e3:.2f} Thousand"
    else:
        return f"{n:.2f}"

def format_bytes(bytes_val: float) -> str:
    if bytes_val >= 1024**5:
        return f"{bytes_val / (1024**5):.2f} PB"
    elif bytes_val >= 1024**4:
        return f"{bytes_val / (1024**4):.2f} TB"
    elif bytes_val >= 1024**3:
        return f"{bytes_val / (1024**3):.2f} GB"
    elif bytes_val >= 1024**2:
        return f"{bytes_val / (1024**2):.2f} MB"
    elif bytes_val >= 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val:.2f} Bytes"

def format_bps(bps: float) -> str:
    if bps >= 1e12:
        return f"{bps / 1e12:.2f} Tbps"
    elif bps >= 1e9:
        return f"{bps / 1e9:.2f} Gbps"
    elif bps >= 1e6:
        return f"{bps / 1e6:.2f} Mbps"
    elif bps >= 1e3:
        return f"{bps / 1e3:.2f} Kbps"
    else:
        return f"{bps:.2f} bps"

def run_calculation(dau: float, writes_per_user: float, reads_per_user: float,
                    write_size_kb: float, read_size_kb: float,
                    retention_years: float = 5, replication_factor: int = 3,
                    peak_multiplier: float = 2.0, title: str = "Custom Calculation"):
    
    SECONDS_PER_DAY = 86_400

    # 1. Throughput calculations
    total_daily_writes = dau * writes_per_user
    total_daily_reads = dau * reads_per_user

    avg_write_qps = total_daily_writes / SECONDS_PER_DAY
    peak_write_qps = avg_write_qps * peak_multiplier

    avg_read_qps = total_daily_reads / SECONDS_PER_DAY
    peak_read_qps = avg_read_qps * peak_multiplier

    total_qps = avg_write_qps + avg_read_qps
    total_peak_qps = peak_write_qps + peak_read_qps

    # 2. Storage calculations
    write_bytes_per_op = write_size_kb * 1024.0
    daily_raw_storage = total_daily_writes * write_bytes_per_op
    annual_raw_storage = daily_raw_storage * 365.0
    multi_year_raw_storage = annual_raw_storage * retention_years
    
    # Total with replication factor and 70% headroom
    total_storage_with_rep = (multi_year_raw_storage * replication_factor) / 0.70

    # 3. Bandwidth calculations (in bytes and network bits)
    read_bytes_per_op = read_size_kb * 1024.0
    ingress_bytes_sec = avg_write_qps * write_bytes_per_op
    ingress_bits_sec = ingress_bytes_sec * 8.0

    egress_bytes_sec = avg_read_qps * read_bytes_per_op
    egress_bits_sec = egress_bytes_sec * 8.0

    peak_egress_bits_sec = egress_bits_sec * peak_multiplier

    # 4. Memory & Cache Sizing (80/20 Rule)
    daily_read_volume_bytes = total_daily_reads * read_bytes_per_op
    # Cache 20% of daily read working set
    cache_ram_bytes = daily_read_volume_bytes * 0.20
    # Add 25% safety buffer for Redis key overhead / fragmentation
    cache_ram_with_buffer = cache_ram_bytes * 1.25

    # 5. Approximate Server Counts (assuming modern 16-core cloud instances)
    # API Servers: ~10,000 QPS capacity per Go/Java container instance
    app_servers = math.ceil(total_peak_qps / 10_000.0) * 2  # 2x redundancy
    # Redis Nodes: ~64GB RAM per node
    redis_nodes = math.ceil(cache_ram_with_buffer / (64.0 * (1024**3))) * 2 # with replicas

    # Print Report
    print("=" * 70)
    print(f" SYSTEM DESIGN CAPACITY ESTIMATION REPORT")
    print(f" Target Scenario: {title}")
    print("=" * 70)
    print(f" Input Parameters:")
    print(f"   • Daily Active Users (DAU): {format_number(dau)} ({dau:,.0f})")
    print(f"   • Writes/User/Day:         {writes_per_user} (Write Size: {write_size_kb:,.2f} KB)")
    print(f"   • Reads/User/Day:          {reads_per_user} (Read Size: {read_size_kb:,.2f} KB)")
    print(f"   • Retention Window:        {retention_years:.0f} Years (Replication Factor: {replication_factor}x)")
    print(f"   • Peak Traffic Multiplier: {peak_multiplier:.1f}x")
    print("-" * 70)

    print(f" 1. QUERY THROUGHPUT (QPS):")
    print(f"   • Total Daily Writes:      {format_number(total_daily_writes)} writes/day")
    print(f"   • Total Daily Reads:       {format_number(total_daily_reads)} reads/day")
    print(f"   • Read-to-Write Ratio:     {reads_per_user / max(0.0001, writes_per_user):.1f} : 1")
    print(f"   • Average Write QPS:       {avg_write_qps:,.1f} writes/sec")
    print(f"   • Peak Write QPS:          {peak_write_qps:,.1f} writes/sec (at {peak_multiplier}x peak)")
    print(f"   • Average Read QPS:        {avg_read_qps:,.1f} reads/sec")
    print(f"   • Peak Read QPS:           {peak_read_qps:,.1f} reads/sec")
    print(f"   • Combined Peak QPS:       {total_peak_qps:,.1f} total requests/sec")
    print("-" * 70)

    print(f" 2. STORAGE FOOTPRINT:")
    print(f"   • Daily Raw Storage:       {format_bytes(daily_raw_storage)} / day")
    print(f"   • Annual Raw Storage:      {format_bytes(annual_raw_storage)} / year")
    print(f"   • {retention_years:.0f}-Year Raw Storage:      {format_bytes(multi_year_raw_storage)}")
    print(f"   • Total Production Disk:   {format_bytes(total_storage_with_rep)} (with {replication_factor}x replication & 70% headroom)")
    print("-" * 70)

    print(f" 3. NETWORK BANDWIDTH:")
    print(f"   • Ingress Bandwidth:       {format_bytes(ingress_bytes_sec)}/s  ({format_bps(ingress_bits_sec)})")
    print(f"   • Egress Bandwidth (Avg):  {format_bytes(egress_bytes_sec)}/s  ({format_bps(egress_bits_sec)})")
    print(f"   • Egress Bandwidth (Peak): {format_bytes(egress_bytes_sec * peak_multiplier)}/s  ({format_bps(peak_egress_bits_sec)})")
    print("-" * 70)

    print(f" 4. MEMORY & CACHE SIZING (80/20 PARETO RULE):")
    print(f"   • 24-Hour Read Volume:     {format_bytes(daily_read_volume_bytes)}")
    print(f"   • 20% Hot Working Set:     {format_bytes(cache_ram_bytes)}")
    print(f"   • Recommended Cache RAM:   {format_bytes(cache_ram_with_buffer)} (including 25% fragmentation buffer)")
    print("-" * 70)

    print(f" 5. ESTIMATED CLUSTER INFRASTRUCTURE:")
    print(f"   • Stateless API Servers:   ~{max(2, app_servers)} instances (10k QPS/node + N+1 redundancy)")
    print(f"   • Redis Cache Nodes:       ~{max(2, redis_nodes)} nodes (64 GB RAM/node with primary-replica)")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description="System Design Back-of-the-Envelope Capacity Planning Calculator")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Load a pre-configured architecture scenario (twitter, youtube, uber, chat)")
    parser.add_argument("--dau", type=float, default=10_000_000, help="Daily Active Users (default: 10M)")
    parser.add_argument("--writes", type=float, default=2.0, help="Average write operations per user per day (default: 2)")
    parser.add_argument("--reads", type=float, default=10.0, help="Average read operations per user per day (default: 10)")
    parser.add_argument("--write-size-kb", type=float, default=1.0, help="Average write payload size in Kilobytes (default: 1 KB)")
    parser.add_argument("--read-size-kb", type=float, default=5.0, help="Average read payload size in Kilobytes (default: 5 KB)")
    parser.add_argument("--retention-years", type=float, default=5.0, help="Data retention duration in years (default: 5)")
    parser.add_argument("--replication", type=int, default=3, help="Database replication factor (default: 3)")
    parser.add_argument("--peak-mult", type=float, default=2.0, help="Peak traffic multiplier (default: 2.0x)")

    args = parser.parse_args()

    if args.preset:
        p = PRESETS[args.preset]
        run_calculation(
            dau=p["dau"],
            writes_per_user=p["writes_per_user"],
            reads_per_user=p["reads_per_user"],
            write_size_kb=p["write_size_kb"],
            read_size_kb=p["read_size_kb"],
            retention_years=p["retention_years"],
            replication_factor=p["replication_factor"],
            peak_multiplier=p["peak_multiplier"],
            title=p["name"]
        )
    else:
        run_calculation(
            dau=args.dau,
            writes_per_user=args.writes,
            reads_per_user=args.reads,
            write_size_kb=args.write_size_kb,
            read_size_kb=args.read_size_kb,
            retention_years=args.retention_years,
            replication_factor=args.replication,
            peak_multiplier=args.peak_mult,
            title="Custom Calculation"
        )

if __name__ == "__main__":
    main()
