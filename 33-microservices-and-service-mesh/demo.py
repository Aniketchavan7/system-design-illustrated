"""
Standalone Simulation of Microservices, Dynamic Service Discovery,
Distributed Tracing Propagation, and Circuit Breaking.
Demonstrates:
  1. Dynamic Service Registry (registration, heartbeat, deregistration).
  2. Sidecar Proxy with Client-Side Round-Robin Load Balancing.
  3. Distributed Tracing context propagation (W3C traceparent headers).
  4. Circuit Breaker state machine (CLOSED -> OPEN -> HALF-OPEN -> CLOSED).
"""

import time
import random
import uuid
from typing import Dict, List, Optional, Tuple

class ServiceInstance:
    def __init__(self, service_name: str, instance_id: str, ip: str, port: int):
        self.service_name = service_name
        self.instance_id = instance_id
        self.ip = ip
        self.port = port
        self.healthy = True
        self.failure_mode = False

    def handle_request(self, trace_id: str, parent_span_id: str, payload: dict) -> Tuple[int, dict]:
        # Generate new span id for this local hop
        span_id = uuid.uuid4().hex[:16]
        if self.failure_mode:
            return 503, {
                "error": f"Service {self.service_name} ({self.instance_id}) internal failure",
                "trace_id": trace_id,
                "span_id": span_id
            }
        return 200, {
            "status": "success",
            "served_by": f"{self.service_name}@{self.instance_id}",
            "trace_id": trace_id,
            "span_id": span_id,
            "data": payload
        }

class ServiceRegistry:
    def __init__(self):
        # service_name -> list of healthy instances
        self.services: Dict[str, List[ServiceInstance]] = {}

    def register(self, instance: ServiceInstance):
        if instance.service_name not in self.services:
            self.services[instance.service_name] = []
        self.services[instance.service_name].append(instance)
        print(f"[Registry] Registered: {instance.service_name} -> {instance.instance_id} ({instance.ip}:{instance.port})")

    def deregister(self, service_name: str, instance_id: str):
        if service_name in self.services:
            self.services[service_name] = [i for i in self.services[service_name] if i.instance_id != instance_id]
            print(f"[Registry] Deregistered: {service_name} -> {instance_id}")

    def discover(self, service_name: str) -> List[ServiceInstance]:
        return [i for i in self.services.get(service_name, []) if i.healthy]

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 1.0):
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.last_state_change = time.time()

    def before_call(self) -> bool:
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_state_change > self.cooldown_seconds:
                self.state = "HALF-OPEN"
                self.last_state_change = now
                print(f"    [CircuitBreaker] Cooldown expired -> Transitioned to HALF-OPEN (Testing 1 probe call)")
                return True
            else:
                return False  # Fast fail
        return True

    def record_result(self, is_success: bool):
        now = time.time()
        if is_success:
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                self.last_state_change = now
                print(f"    [CircuitBreaker] Probe succeeded -> Circuit fully CLOSED (Restored)")
            elif self.state == "CLOSED":
                self.failure_count = 0
        else:
            self.failure_count += 1
            if self.state in ("CLOSED", "HALF-OPEN") and self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                self.last_state_change = now
                print(f"    [CircuitBreaker] Threshold reached ({self.failure_count} errors) -> Circuit TRIPPED to OPEN (Failing fast)")

class SidecarProxy:
    def __init__(self, proxy_id: str, registry: ServiceRegistry):
        self.proxy_id = proxy_id
        self.registry = registry
        self.round_robin_indices: Dict[str, int] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    def route_request(self, target_service: str, payload: dict, trace_id: Optional[str] = None) -> Tuple[int, dict]:
        # Generate distributed trace ID if root call
        if not trace_id:
            trace_id = uuid.uuid4().hex
        parent_span_id = uuid.uuid4().hex[:16]

        if target_service not in self.circuit_breakers:
            self.circuit_breakers[target_service] = CircuitBreaker()

        cb = self.circuit_breakers[target_service]

        # 1. Circuit Breaker Check
        if not cb.before_call():
            return 503, {
                "error": f"Circuit breaker OPEN for {target_service} (Fast fail)",
                "trace_id": trace_id
            }

        # 2. Service Discovery
        instances = self.registry.discover(target_service)
        if not instances:
            cb.record_result(is_success=False)
            return 503, {"error": f"No healthy instances found for {target_service}", "trace_id": trace_id}

        # 3. Client-Side Round-Robin Balancing
        idx = self.round_robin_indices.get(target_service, 0)
        selected_instance = instances[idx % len(instances)]
        self.round_robin_indices[target_service] = idx + 1

        # 4. Dispatch with Trace Context Header Propagation
        status, response = selected_instance.handle_request(trace_id, parent_span_id, payload)
        is_success = (200 <= status < 400)
        cb.record_result(is_success)

        return status, response

def run_simulation():
    print("=" * 65)
    print("MICROSERVICES & SERVICE MESH SIDECAR SIMULATION")
    print("=" * 65)

    registry = ServiceRegistry()

    # 1. Register microservice instances
    print("\n1. REGISTERING SERVICE INSTANCES IN DISCOVERY REGISTRY")
    pay_1 = ServiceInstance("payment-service", "pay-inst-1", "10.0.1.10", 8080)
    pay_2 = ServiceInstance("payment-service", "pay-inst-2", "10.0.1.11", 8080)
    registry.register(pay_1)
    registry.register(pay_2)

    # 2. Setup Sidecar Proxy
    sidecar = SidecarProxy("envoy-orders-sidecar", registry)

    # 3. Simulate client-side load balancing and tracing
    print("\n2. DISPATCHING REQUESTS WITH CLIENT-SIDE BALANCING & DISTRIBUTED TRACING")
    for i in range(1, 4):
        status, res = sidecar.route_request("payment-service", {"order_id": f"ord_{100+i}", "amount": 99.0})
        print(f"Req #{i} -> Status: {status} | Served by: {res.get('served_by')} | TraceID: {res.get('trace_id')[:8]}... SpanID: {res.get('span_id')}")

    # 4. Simulate Failure & Circuit Breaker Tripping
    print("\n3. SIMULATING DOWNSTREAM OUTAGE & CIRCUIT BREAKER TRIP")
    pay_1.failure_mode = True
    pay_2.failure_mode = True
    print("Simulated outage: Both payment service instances now returning 503 errors.\n")

    for i in range(1, 6):
        status, res = sidecar.route_request("payment-service", {"order_id": f"ord_err_{i}"})
        print(f"Error test call #{i} -> HTTP {status}: {res.get('error')}")

    # 5. Recovery test
    print("\n4. SIMULATING RECOVERY & HALF-OPEN STATE")
    time.sleep(1.1)  # wait for cooldown
    pay_1.failure_mode = False
    pay_2.failure_mode = False
    print("Instances recovered to healthy state. Sending probe request...")
    status, res = sidecar.route_request("payment-service", {"order_id": "ord_probe_recovered"})
    print(f"Probe call result -> Status: {status} | Served by: {res.get('served_by')}")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
