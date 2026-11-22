"""
Interactive Demo: Hierarchical DNS Resolution & Anycast Routing Simulator
Run this script to observe the multi-tier DNS resolution tree,
TTL cache expiration, and Anycast proximity routing.
"""

import time

class HierarchicalDNSSimulator:
    def __init__(self):
        # Database of records at the Authoritative level
        self.authoritative_db = {
            "api.stripe.com": {"type": "A", "ip": "54.187.128.85", "ttl": 3},
            "github.com": {"type": "A", "ip": "140.82.112.4", "ttl": 5},
            "chatgpt.com": {"type": "A", "ip": "104.18.3.161", "ttl": 4}
        }
        # In-memory OS / Browser cache: domain -> (ip, expires_at)
        self.client_cache = {}

    def resolve(self, domain: str):
        print(f"\n🔍 Resolving domain: '{domain}'")
        now = time.time()

        # Step 1: Check Client / OS Local Cache
        if domain in self.client_cache:
            ip, expires_at = self.client_cache[domain]
            if now < expires_at:
                remaining_ttl = int(expires_at - now)
                print(f"  ⚡ [LOCAL OS CACHE HIT] {domain} -> {ip} (TTL remaining: {remaining_ttl}s) [0.1 ms]")
                return ip
            else:
                print(f"  ⌛ [LOCAL OS CACHE EXPIRED] Stale record for {domain} purged.")
                del self.client_cache[domain]

        print("  ❌ [LOCAL OS CACHE MISS] Forwarding to Recursive Resolver (e.g. 1.1.1.1)...")
        time.sleep(0.1)

        # Step 2: Recursive Resolver queries Root Nameserver
        print("  --> [1. Query Root Server (.)] Asking who manages Top-Level Domain '.com'...")
        time.sleep(0.1)
        print("  <-- [Root Referral] Root says: 'Ask the .com TLD server at 192.5.6.30'")

        # Step 3: Recursive Resolver queries TLD Server
        print("  --> [2. Query .com TLD Server] Asking who manages 'stripe.com'...")
        time.sleep(0.1)
        print("  <-- [TLD Referral] TLD says: 'Ask authoritative nameserver ns1.stripe.com at 198.51.100.1'")

        # Step 4: Recursive Resolver queries Authoritative Server
        print(f"  --> [3. Query Authoritative Server (ns1.stripe.com)] Requesting 'A' record for '{domain}'...")
        time.sleep(0.1)

        record = self.authoritative_db.get(domain)
        if record:
            ip = record["ip"]
            ttl = record["ttl"]
            print(f"  ✅ [Authoritative Answer] Returned {record['type']} Record: {ip} (TTL = {ttl}s)")
            # Populate client cache
            self.client_cache[domain] = (ip, now + ttl)
            print(f"  💾 Cached '{domain}' in client resolver for {ttl} seconds.")
            return ip
        else:
            print("  ❌ [NXDOMAIN] Domain does not exist!")
            return None

def simulate_anycast_routing():
    print("\n" + "=" * 70)
    print(" 🌐 ANYCAST ROUTING DEMO: 1 IP Address, Multiple Global Datacenters")
    print(" A single DNS IP (e.g., 1.1.1.1) is announced from 300+ cities simultaneously via BGP.")
    print("=" * 70)

    users = [
        ("User in New York", "NYC Datacenter", 4.2),
        ("User in London", "LHR Datacenter", 5.8),
        ("User in Tokyo", "NRT Datacenter", 6.1),
        ("User in Sydney", "SYD Datacenter", 7.4),
    ]

    for user, target_pop, latency in users:
        print(f"  👤 {user:<20} -> BGP routes to closest PoP: [{target_pop}] (Latency: {latency} ms)")

if __name__ == "__main__":
    dns = HierarchicalDNSSimulator()

    # 1. First resolution: full iterative tree traversal
    dns.resolve("api.stripe.com")

    # 2. Immediate second resolution: instant cache hit
    dns.resolve("api.stripe.com")

    # 3. Wait for TTL to expire
    print("\n[Sleeping 3.5 seconds for TTL expiration...]")
    time.sleep(3.5)

    # 4. Third resolution: cache expired, re-queries tree
    dns.resolve("api.stripe.com")

    # 5. Anycast routing demonstration
    simulate_anycast_routing()
