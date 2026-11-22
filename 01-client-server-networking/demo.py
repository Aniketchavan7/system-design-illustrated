"""
Interactive Demo: Network Protocols & Handshake Simulator
Run this script to understand TCP Handshakes, Round-Trip Times (RTT),
and HTTP/1.1 Head-of-Line Blocking vs HTTP/2 Multiplexing.
"""

import time
import random

def simulate_tcp_handshake(one_way_latency_ms: float = 35.0):
    print("=" * 70)
    print(" 🤝 STEP 1: TCP THREE-WAY HANDSHAKE SIMULATION")
    print(f" (Network One-Way Transit Time: {one_way_latency_ms} ms -> 1 RTT = {one_way_latency_ms * 2} ms)")
    print("=" * 70)

    client_isn = 1000
    server_isn = 5000

    # 1. SYN
    print(f"\n[Client: CLOSED] -> Sending SYN packet...")
    time.sleep(0.3)
    print(f"  --> [WIRE] SYN (seq={client_isn}) traveling across internet ({one_way_latency_ms} ms)")
    time.sleep(0.3)
    print(f"[Server: LISTEN] -> Received SYN. Transitioned to SYN-RECEIVED.")

    # 2. SYN-ACK
    print(f"[Server: SYN-RECEIVED] -> Sending SYN-ACK response...")
    time.sleep(0.3)
    print(f"  <-- [WIRE] SYN-ACK (seq={server_isn}, ack={client_isn + 1}) traveling ({one_way_latency_ms} ms)")
    time.sleep(0.3)
    print(f"[Client: SYN-SENT] -> Received SYN-ACK. Verified ack={client_isn + 1}. Transitioned to ESTABLISHED.")

    # 3. ACK
    print(f"[Client: ESTABLISHED] -> Sending final ACK...")
    time.sleep(0.3)
    print(f"  --> [WIRE] ACK (ack={server_isn + 1}) traveling ({one_way_latency_ms} ms)")
    time.sleep(0.3)
    print(f"[Server: SYN-RECEIVED] -> Received ACK. Transitioned to ESTABLISHED.")

    total_handshake_time = one_way_latency_ms * 3
    print(f"\n✅ Connection Established! Elapsed Handshake Time: {total_handshake_time} ms (1.5 RTT)")
    print("-" * 70)

def simulate_http_comparison():
    print("\n" + "=" * 70)
    print(" ⚡ STEP 2: HTTP/1.1 HEAD-OF-LINE BLOCKING vs HTTP/2 MULTIPLEXING")
    print(" Scenario: A web page needs to fetch 4 assets:")
    print("   1. index.html   (20 ms server processing)")
    print("   2. styles.css   (60 ms server processing)")
    print("   3. bundle.js   (120 ms server processing - heavy script)")
    print("   4. avatar.png   (15 ms server processing)")
    print("=" * 70)

    assets = [
        ("index.html", 20),
        ("styles.css", 60),
        ("bundle.js", 120),
        ("avatar.png", 15)
    ]
    rtt = 50  # ms network round trip per request

    # --- HTTP/1.1 Simulation ---
    print("\n📦 Simulation A: HTTP/1.1 (Serial requests on a single connection)")
    h1_total = 0
    for name, server_proc in assets:
        h1_total += rtt + server_proc
        print(f"  [HTTP/1.1] Request '{name}': wait RTT ({rtt}ms) + server ({server_proc}ms) = {rtt + server_proc}ms")
    print(f"  ❌ HTTP/1.1 Total Page Load Time: {h1_total} ms (Suffers from Head-of-Line blocking)")

    # --- HTTP/2 Simulation ---
    print("\n🚀 Simulation B: HTTP/2 (Multiplexed streams over a single connection)")
    print("  [HTTP/2] Client sends all 4 stream requests concurrently in single frame bundle!")
    max_proc = max(proc for _, proc in assets)
    h2_total = rtt + max_proc
    print(f"  --> Stream 1 (index.html), Stream 3 (styles.css), Stream 5 (bundle.js), Stream 7 (avatar.png)")
    print(f"  --> Streams process in parallel. Total time bounded by slowest asset ({max_proc}ms) + 1 RTT ({rtt}ms)")
    print(f"  ✅ HTTP/2 Total Page Load Time: {h2_total} ms")

    saved = h1_total - h2_total
    speedup = h1_total / h2_total
    print(f"\n🎯 Result: HTTP/2 was {speedup:.1f}x faster ({saved} ms saved) on the exact same network!")
    print("=" * 70)

if __name__ == "__main__":
    simulate_tcp_handshake(one_way_latency_ms=25.0)
    simulate_http_comparison()
