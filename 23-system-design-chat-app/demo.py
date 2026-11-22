"""
Interactive Demo: System Design — Real-Time Distributed Chat Application (WhatsApp / Discord)
Run this script to observe:
1. Full-Duplex WebSocket connections distributed across multiple chat gateway servers.
2. Cross-server message routing via simulated Redis Pub/Sub message broker.
3. Distributed Presence Service tracking Online / Offline status with heartbeats.
4. Offline message storage and APNs/FCM Push Notification simulation.
5. Wide-Column (Cassandra-style) message history queries.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass

# ==============================================================
# 1. Message Data Model & Persistent Store (Cassandra Model)
# ==============================================================
@dataclass
class ChatMessage:
    message_id: str
    channel_id: str
    sender_id: str
    receiver_id: str
    content: str
    timestamp: float

class CassandraMessageStore:
    def __init__(self):
        # channel_id -> list of ChatMessages sorted by timestamp
        self.tables: Dict[str, List[ChatMessage]] = {}

    def insert(self, msg: ChatMessage):
        if msg.channel_id not in self.tables:
            self.tables[msg.channel_id] = []
        self.tables[msg.channel_id].append(msg)

    def fetch_history(self, channel_id: str, limit: int = 10) -> List[ChatMessage]:
        msgs = self.tables.get(channel_id, [])
        return msgs[-limit:]


# ==============================================================
# 2. Presence Service (Redis Sorted Sets Simulation)
# ==============================================================
class PresenceService:
    def __init__(self, timeout_s: float = 2.0):
        self.timeout_s = timeout_s
        self.heartbeats: Dict[str, float] = {}
        self.user_to_gateway: Dict[str, str] = {}

    def heartbeat(self, user_id: str, gateway_id: str):
        now = time.time()
        self.heartbeats[user_id] = now
        self.user_to_gateway[user_id] = gateway_id

    def is_online(self, user_id: str) -> bool:
        if user_id in self.heartbeats:
            return (time.time() - self.heartbeats[user_id]) <= self.timeout_s
        return False

    def get_gateway(self, user_id: str) -> Optional[str]:
        if self.is_online(user_id):
            return self.user_to_gateway.get(user_id)
        return None

    def disconnect(self, user_id: str):
        self.heartbeats.pop(user_id, None)
        self.user_to_gateway.pop(user_id, None)


# ==============================================================
# 3. Chat Gateway (WebSocket Connection Manager)
# ==============================================================
class ChatGateway:
    def __init__(self, gateway_id: str, presence: PresenceService, db: CassandraMessageStore, broker: 'MessageBroker'):
        self.gateway_id = gateway_id
        self.presence = presence
        self.db = db
        self.broker = broker
        # user_id -> active simulated client callback
        self.active_connections: Dict[str, List[str]] = {}

    def connect_user(self, user_id: str):
        self.active_connections[user_id] = []
        self.presence.heartbeat(user_id, self.gateway_id)

    def disconnect_user(self, user_id: str):
        self.active_connections.pop(user_id, None)
        self.presence.disconnect(user_id)

    def send_message(self, sender_id: str, receiver_id: str, content: str):
        channel_id = f"dm:{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
        msg = ChatMessage(
            message_id=f"msg_{int(time.time()*1000)}",
            channel_id=channel_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            timestamp=time.time()
        )
        # 1. Persist to Cassandra Store
        self.db.insert(msg)

        # 2. Check recipient presence
        target_gw = self.presence.get_gateway(receiver_id)
        if target_gw:
            # Recipient is online on a gateway -> route via broker!
            self.broker.publish(target_gw, receiver_id, msg)
        else:
            # Recipient is offline -> push notification & offline queue
            self.broker.simulate_push_notification(receiver_id, msg)

    def deliver_to_socket(self, user_id: str, msg: ChatMessage):
        """Pushes frame down active client WebSocket."""
        if user_id in self.active_connections:
            self.active_connections[user_id].append(f"[{msg.sender_id}]: {msg.content}")


# ==============================================================
# 4. Message Broker (Redis Pub/Sub Simulation)
# ==============================================================
class MessageBroker:
    def __init__(self):
        self.gateways: Dict[str, ChatGateway] = {}
        self.offline_inboxes: Dict[str, List[ChatMessage]] = {}

    def register_gateway(self, gw: ChatGateway):
        self.gateways[gw.gateway_id] = gw

    def publish(self, target_gateway_id: str, user_id: str, msg: ChatMessage):
        if target_gateway_id in self.gateways:
            gw = self.gateways[target_gateway_id]
            gw.deliver_to_socket(user_id, msg)

    def simulate_push_notification(self, user_id: str, msg: ChatMessage):
        if user_id not in self.offline_inboxes:
            self.offline_inboxes[user_id] = []
        self.offline_inboxes[user_id].append(msg)
        print(f"  🔔 [APNs/FCM Push Alert] Sent to {user_id}: New message from {msg.sender_id}: '{msg.content}'")


def main():
    print("=" * 70)
    print("REAL-TIME DISTRIBUTED CHAT APPLICATION SIMULATION")
    print("=" * 70)

    db = CassandraMessageStore()
    presence = PresenceService(timeout_s=1.0)
    broker = MessageBroker()

    # Launch two independent Chat Gateways (e.g. Gateway-Tokyo and Gateway-London)
    gw_tokyo = ChatGateway("GW-Tokyo-01", presence, db, broker)
    gw_london = ChatGateway("GW-London-02", presence, db, broker)
    broker.register_gateway(gw_tokyo)
    broker.register_gateway(gw_london)

    # 1. Connect Users to different gateways
    print("\n--- Phase 1: WebSocket Client Connections ---")
    gw_tokyo.connect_user("Alice")
    gw_london.connect_user("Bob")
    print(f"Alice connected to: {presence.get_gateway('Alice')} (Online: {presence.is_online('Alice')})")
    print(f"Bob connected to:   {presence.get_gateway('Bob')} (Online: {presence.is_online('Bob')})")

    # 2. Real-Time Cross-Gateway Messaging
    print("\n--- Phase 2: Cross-Gateway Messaging via Redis Pub/Sub ---")
    print("Alice sends: 'Hey Bob, how is London?'")
    t0 = time.perf_counter()
    gw_tokyo.send_message(sender_id="Alice", receiver_id="Bob", content="Hey Bob, how is London?")
    dur_ms = (time.perf_counter() - t0) * 1000

    print(f"Latency to deliver cross-gateway: {dur_ms:.3f} ms")
    print(f"Bob's WebSocket Screen: {gw_london.active_connections['Bob']}")

    print("\nBob replies: 'Raining as usual! Working on System Design.'")
    gw_london.send_message(sender_id="Bob", receiver_id="Alice", content="Raining as usual! Working on System Design.")
    print(f"Alice's WebSocket Screen: {gw_tokyo.active_connections['Alice']}")

    # 3. Offline Messaging & Push Notifications
    print("\n--- Phase 3: Offline Messaging & Push Notifications ---")
    print("Charlie is offline (no WebSocket connection)...")
    print("Alice sends to Charlie: 'Are you joining the meeting?'")
    gw_tokyo.send_message(sender_id="Alice", receiver_id="Charlie", content="Are you joining the meeting?")

    # Charlie reconnects later
    print("\nCharlie wakes up and connects to GW-Tokyo-01...")
    gw_tokyo.connect_user("Charlie")
    if "Charlie" in broker.offline_inboxes:
        pending = broker.offline_inboxes.pop("Charlie")
        for m in pending:
            gw_tokyo.deliver_to_socket("Charlie", m)
        print(f"Charlie synced {len(pending)} offline message(s) upon login!")
    print(f"Charlie's WebSocket Screen: {gw_tokyo.active_connections['Charlie']}")

    # 4. Message History from Cassandra
    print("\n--- Phase 4: Fetching Channel History from Cassandra ---")
    history = db.fetch_history("dm:Alice_Bob")
    print(f"Fetched {len(history)} messages for channel 'dm:Alice_Bob':")
    for m in history:
        print(f"  [{m.sender_id} -> {m.receiver_id}]: {m.content}")

    print("=" * 70)
    print("Chat Application simulation completed successfully!")

if __name__ == "__main__":
    main()
