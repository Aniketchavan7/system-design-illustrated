"""
Interactive Demo: Back-of-the-Envelope Estimation Calculator
Automates system capacity planning formulas used in system design interviews:
- QPS (Average & Peak)
- Ingress & Egress Bandwidth
- Storage Growth (Daily, 1-Year, 5-Year)
- 80/20 Caching RAM Requirements
"""

def calculate_system_metrics(dau: int, requests_per_user: int, read_ratio: float, avg_payload_bytes: int):
    print("=" * 65)
    print("BACK-OF-THE-ENVELOPE ESTIMATION REPORT")
    print(f"DAU: {dau:,} | Requests/User: {requests_per_user} | Read Ratio: {read_ratio*100:.0f}%")
    print("=" * 65)

    # 1. Traffic Math
    total_daily_requests = dau * requests_per_user
    avg_qps = total_daily_requests / 86400
    peak_qps = avg_qps * 2.0
    
    read_qps = avg_qps * read_ratio
    write_qps = avg_qps * (1.0 - read_ratio)

    print("\n1. TRAFFIC METRICS (QPS):")
    print(f"   - Total Daily Requests: {total_daily_requests:,}")
    print(f"   - Average QPS:         {avg_qps:,.1f} requests/sec")
    print(f"   - Peak QPS (2x):       {peak_qps:,.1f} requests/sec")
    print(f"   - Read QPS:            {read_qps:,.1f} QPS")
    print(f"   - Write QPS:           {write_qps:,.1f} QPS")

    # 2. Storage Math
    daily_writes = total_daily_requests * (1.0 - read_ratio)
    daily_storage_bytes = daily_writes * avg_payload_bytes
    daily_storage_gb = daily_storage_bytes / (1024**3)
    annual_storage_tb = (daily_storage_bytes * 365) / (1024**4)
    five_year_storage_tb = annual_storage_tb * 5

    print("\n2. STORAGE METRICS:")
    print(f"   - Daily New Data:      {daily_storage_gb:,.2f} GB/day")
    print(f"   - 1-Year Storage:      {annual_storage_tb:,.2f} TB")
    print(f"   - 5-Year Storage:      {five_year_storage_tb:,.2f} TB")

    # 3. 80/20 Caching Tier Math
    daily_read_bytes = (total_daily_requests * read_ratio) * avg_payload_bytes
    cache_ram_needed_gb = (daily_read_bytes * 0.20) / (1024**3)
    
    print("\n3. CACHING SIZING (80/20 Rule):")
    print(f"   - Daily Read Volume:   {daily_read_bytes / (1024**3):,.2f} GB")
    print(f"   - RAM for 20% Hot Data:{cache_ram_needed_gb:,.2f} GB of Redis RAM required")

    # 4. Network Bandwidth
    bandwidth_mbps = (avg_qps * avg_payload_bytes * 8) / 1_000_000
    print("\n4. NETWORK BANDWIDTH:")
    print(f"   - Average Throughput:  {bandwidth_mbps:,.2f} Mbps ({bandwidth_mbps / 1000:,.2f} Gbps)")
    print("=" * 65)

if __name__ == "__main__":
    calculate_system_metrics(
        dau=100_000_000,
        requests_per_user=50,
        read_ratio=0.80,
        avg_payload_bytes=500
    )
