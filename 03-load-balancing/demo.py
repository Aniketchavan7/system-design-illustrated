"""
Interactive Demo: Load Balancer Algorithms & Health Checking Simulator
Run this script to observe Round-Robin, Weighted Round-Robin, Least Connections,
IP Hashing, and automatic failover when a server dies.
"""

import zlib

class BackendServer:
    def __init__(self, name: str, weight: int = 1):
        self.name = name
        self.weight = weight
        self.active_conns = 0
        self.is_healthy = True

    def __repr__(self):
        status = "HEALTHY" if self.is_healthy else "DEAD"
        return f"[{self.name} | weight={self.weight} | conns={self.active_conns} | {status}]"

class LoadBalancerSimulator:
    def __init__(self, servers):
        self.servers = servers
        self.rr_index = 0

    def healthy_pool(self):
        return [s for s in self.servers if s.is_healthy]

    def route_round_robin(self):
        pool = self.healthy_pool()
        if not pool:
            raise RuntimeError("All servers are DEAD! HTTP 503 Service Unavailable")
        chosen = pool[self.rr_index % len(pool)]
        self.rr_index += 1
        return chosen

    def route_least_connections(self):
        pool = self.healthy_pool()
        if not pool:
            raise RuntimeError("All servers are DEAD! HTTP 503 Service Unavailable")
        # Score = active_conns / weight
        return min(pool, key=lambda s: s.active_conns / s.weight)

    def route_ip_hash(self, client_ip: str):
        pool = self.healthy_pool()
        if not pool:
            raise RuntimeError("All servers are DEAD! HTTP 503 Service Unavailable")
        hash_val = zlib.crc32(client_ip.encode('utf-8'))
        return pool[hash_val % len(pool)]

    def health_check(self):
        print("\n🩺 Running active HTTP health check probe (`GET /healthz`)...")
        for s in self.servers:
            status = "✅ 200 OK" if s.is_healthy else "❌ TIMEOUT / 500"
            print(f"  Probe {s.name:<10} -> {status}")

if __name__ == "__main__":
    servers = [
        BackendServer("srv-1", weight=1),
        BackendServer("srv-2", weight=2),
        BackendServer("srv-3", weight=1)
    ]
    lb = LoadBalancerSimulator(servers)

    print("=" * 70)
    print(" ⚖️ STEP 1: ROUND-ROBIN ROUTING (All servers healthy)")
    print("=" * 70)
    for i in range(1, 7):
        target = lb.route_round_robin()
        print(f"  Request #{i} -> Routed to {target.name}")

    print("\n" + "=" * 70)
    print(" ⚡ STEP 2: LEAST-CONNECTIONS ROUTING (Simulating varying load)")
    print("=" * 70)
    servers[0].active_conns = 14  # srv-1: score 14/1 = 14
    servers[1].active_conns = 8   # srv-2: score 8/2 = 4 (Weight 2 allows 2x connections!)
    servers[2].active_conns = 10  # srv-3: score 10/1 = 10
    print("Current Server State:")
    for s in servers:
        print(" ", s)
    chosen = lb.route_least_connections()
    print(f"\n  🎯 Result: Routed to [{chosen.name}] because it has lowest normalized load ({chosen.active_conns}/{chosen.weight})!")

    print("\n" + "=" * 70)
    print(" 🔒 STEP 3: IP HASH ROUTING (Session Sticky by Client IP)")
    print("=" * 70)
    ips = ["192.168.1.10", "10.0.0.42", "192.168.1.10", "172.16.0.5", "192.168.1.10"]
    for ip in ips:
        target = lb.route_ip_hash(ip)
        print(f"  Client [{ip:<12}] -> Consistently routed to: [{target.name}]")

    print("\n" + "=" * 70)
    print(" 🚨 STEP 4: HEALTH CHECK FAILURE & AUTOMATIC EJECTION")
    print("=" * 70)
    print("⚠️  Simulating hardware crash: srv-3 runs out of memory!")
    servers[2].is_healthy = False
    lb.health_check()

    print("\nRouting 4 new requests after srv-3 failure:")
    for i in range(1, 5):
        target = lb.route_round_robin()
        print(f"  Request #{i} -> Routed to [{target.name}] (Dead server was safely skipped)")
    print("=" * 70)
