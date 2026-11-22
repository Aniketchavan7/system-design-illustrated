"""
Interactive Demo: API Gateway & Reverse Proxy Simulator
Run this script to observe JWT token validation, rate limit verification,
route dispatching, and Backend-For-Frontend (BFF) request aggregation.
"""

import time

# --- Simulated Internal Microservices (Private Network) ---
def internal_user_service(user_id: str):
    return {"user_id": user_id, "name": "Alice Johnson", "tier": "gold"}

def internal_order_service(user_id: str):
    return {"orders": [{"id": "ord_101", "total": 89.50, "status": "shipped"}]}

def internal_recommendations_service(user_id: str):
    return {"recommended_items": ["Wireless Headphones", "Ergonomic Keyboard"]}

# --- API Gateway Core Engine ---
class APIGatewayEngine:
    def __init__(self):
        # In-memory session store of valid tokens
        self.valid_tokens = {
            "token_alice_valid": "usr_4201",
            "token_bob_valid": "usr_7812"
        }
        # In-memory rate limits: token -> requests in window
        self.rate_limits = {}

    def handle_request(self, method: str, path: str, auth_token: str = None):
        print(f"\n🌐 INCOMING REQUEST: {method} {path}")

        # 1. Edge Security Check: Authentication
        if not auth_token or auth_token not in self.valid_tokens:
            print("  ❌ [401 UNAUTHORIZED] Missing or invalid Bearer token. Rejected at edge!")
            return {"status": 401, "error": "Unauthorized"}

        user_id = self.valid_tokens[auth_token]
        print(f"  🔑 [AUTH PASSED] Token verified for User ID: {user_id}")

        # 2. Rate Limit Check
        current_count = self.rate_limits.get(auth_token, 0)
        if current_count >= 3:
            print(f"  ⏱️ [429 TOO MANY REQUESTS] Quota exceeded ({current_count}/3). Request throttled!")
            return {"status": 429, "error": "Rate limit exceeded"}
        self.rate_limits[auth_token] = current_count + 1
        print(f"  ✅ [RATE LIMIT OK] Current quota: {self.rate_limits[auth_token]}/3")

        # 3. BFF Request Aggregation Route: /api/v1/mobile/home-dashboard
        if path == "/api/v1/mobile/home-dashboard":
            print("  🚀 [BFF AGGREGATION] Mobile client requested composite dashboard!")
            print("     -> Concurrently dispatching internal RPCs: UserSvc, OrderSvc, RecomSvc...")
            user_data = internal_user_service(user_id)
            orders_data = internal_order_service(user_id)
            recom_data = internal_recommendations_service(user_id)

            composite_response = {
                "status": 200,
                "profile": user_data,
                "recent_orders": orders_data["orders"],
                "recommendations": recom_data["recommended_items"]
            }
            print("  📦 [200 OK] Stitched 3 microservice responses into 1 clean mobile payload!")
            return composite_response

        # 4. Standard Single Route Dispatching
        if path.startswith("/api/v1/users"):
            print("  🧭 [ROUTED] Dispatched to internal User Microservice (Port 8081)")
            return {"status": 200, "data": internal_user_service(user_id)}
        elif path.startswith("/api/v1/orders"):
            print("  🧭 [ROUTED] Dispatched to internal Order Microservice (Port 8082)")
            return {"status": 200, "data": internal_order_service(user_id)}

        print(f"  ❌ [404 NOT FOUND] No route matches {path}")
        return {"status": 404, "error": "Route not found"}

if __name__ == "__main__":
    gw = APIGatewayEngine()

    print("=" * 70)
    print(" 🚪 SCENARIO 1: Unauthenticated request rejected at perimeter")
    print("=" * 70)
    gw.handle_request("GET", "/api/v1/orders")

    print("\n" + "=" * 70)
    print(" 🚪 SCENARIO 2: Authenticated single route request")
    print("=" * 70)
    gw.handle_request("GET", "/api/v1/orders", auth_token="token_alice_valid")

    print("\n" + "=" * 70)
    print(" 🚀 SCENARIO 3: BFF Aggregation (1 mobile call replaces 3 API calls)")
    print("=" * 70)
    dashboard = gw.handle_request("GET", "/api/v1/mobile/home-dashboard", auth_token="token_alice_valid")
    print("\nResult Payload received by Mobile App:")
    print(dashboard)

    print("\n" + "=" * 70)
    print(" ⏱️ SCENARIO 4: Rate limit protection kicks in")
    print("=" * 70)
    gw.handle_request("GET", "/api/v1/orders", auth_token="token_alice_valid") # 3rd request (allowed)
    gw.handle_request("GET", "/api/v1/orders", auth_token="token_alice_valid") # 4th request (rejected 429)
    print("=" * 70)
