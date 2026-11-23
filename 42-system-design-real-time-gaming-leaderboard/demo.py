"""
Standalone Simulation of Real-Time Gaming Leaderboard.
Demonstrates:
  1. In-memory sorted score ranking using compound fractional tie-breaking.
  2. Sub-millisecond player rank lookup.
  3. Top-K leaderboard retrieval.
  4. Surrounding player range queries (5 above, 5 below).
"""

import time
import bisect
from typing import Dict, List, Tuple

class LeaderboardPlayer:
    def __init__(self, user_id: str, username: str, points: int, timestamp: float):
        self.user_id = user_id
        self.username = username
        self.points = points
        self.timestamp = timestamp
        # Compound score: higher points = higher rank; earlier timestamp breaks ties!
        # Max future timestamp assumed 2,000,000,000
        self.composite_score = points + (1.0 - (timestamp / 2_000_000_000.0))

    def __lt__(self, other: 'LeaderboardPlayer'):
        # For reverse sorting: higher composite score comes first
        return self.composite_score > other.composite_score

class RealTimeLeaderboard:
    def __init__(self):
        # user_id -> LeaderboardPlayer
        self.players: Dict[str, LeaderboardPlayer] = {}
        # Sorted list of players maintained in descending order
        self.sorted_board: List[LeaderboardPlayer] = []

    def update_score(self, user_id: str, username: str, points: int) -> int:
        now = time.time()
        # Remove existing if present
        if user_id in self.players:
            old_player = self.players[user_id]
            self.sorted_board.remove(old_player)

        player = LeaderboardPlayer(user_id, username, points, now)
        self.players[user_id] = player
        
        # Binary insertion to maintain sorted order in O(log N)
        bisect.insort(self.sorted_board, player)
        
        # Return 1-based rank
        return self.sorted_board.index(player) + 1

    def get_rank(self, user_id: str) -> Tuple[int, int]:
        player = self.players.get(user_id)
        if not player:
            return -1, 0
        rank = self.sorted_board.index(player) + 1
        return rank, player.points

    def get_top_k(self, k: int = 5) -> List[Tuple[int, str, int]]:
        return [(idx + 1, p.username, p.points) for idx, p in enumerate(self.sorted_board[:k])]

    def get_surrounding(self, user_id: str, window: int = 2) -> List[Tuple[int, str, int, bool]]:
        player = self.players.get(user_id)
        if not player:
            return []
        
        center_idx = self.sorted_board.index(player)
        start = max(0, center_idx - window)
        end = min(len(self.sorted_board), center_idx + window + 1)
        
        results = []
        for idx in range(start, end):
            p = self.sorted_board[idx]
            is_me = (p.user_id == user_id)
            results.append((idx + 1, p.username, p.points, is_me))
        return results

def run_simulation():
    print("=" * 65)
    print("REAL-TIME GAMING LEADERBOARD SIMULATION")
    print("=" * 65)

    board = RealTimeLeaderboard()

    # 1. Populate initial players
    print("Step 1: Ingesting initial tournament scores...")
    sample_scores = [
        ("u1", "ShadowNinja", 2850),
        ("u2", "PixelQueen", 3420),
        ("u3", "VortexStorm", 1950),
        ("u4", "CyberKnight", 3100),
        ("u5", "IronGamer", 2400),
        ("u6", "AlphaWolf", 2850)  # Same score as ShadowNinja! Tests tie-breaker!
    ]

    for uid, name, pts in sample_scores:
        time.sleep(0.01)  # slight timestamp difference
        rank = board.update_score(uid, name, pts)
        print(f"  Player '{name:12}' scored {pts} pts -> Rank #{rank}")

    # 2. Check Top 3
    print("\nStep 2: Fetching Top 3 Global Champions:")
    top3 = board.get_top_k(3)
    for rank, name, pts in top3:
        print(f"  #{rank}: {name:12} with {pts} pts")

    # 3. Verify Tie-Breaking
    print("\nStep 3: Verifying Deterministic Tie-Breaking (ShadowNinja vs AlphaWolf):")
    ninja_rank, _ = board.get_rank("u1")
    wolf_rank, _ = board.get_rank("u6")
    print(f"  ShadowNinja Rank: #{ninja_rank} (Scored 2850 earlier)")
    print(f"  AlphaWolf Rank:   #{wolf_rank} (Scored 2850 later)")
    assert ninja_rank < wolf_rank
    print("  SUCCESS: Earlier timestamp broke the tie deterministically!")

    # 4. Player earns points mid-tournament and jumps in rank
    print("\nStep 4: VortexStorm earns +1500 points in a match!")
    new_rank = board.update_score("u3", "VortexStorm", 1950 + 1500)
    print(f"  VortexStorm updated score: 3450 pts -> JUMPED to Rank #{new_rank}!")
    assert new_rank == 1

    # 5. Fetch Surrounding Players for ShadowNinja
    print("\nStep 5: Showing surrounding competitors for ShadowNinja:")
    surrounding = board.get_surrounding("u1", window=2)
    for rank, name, pts, is_me in surrounding:
        marker = " <--- (YOU)" if is_me else ""
        print(f"  Rank #{rank:2}: {name:12} ({pts} pts){marker}")

    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
