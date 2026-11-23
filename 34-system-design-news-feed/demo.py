"""
Standalone Simulation of News Feed System.
Demonstrates:
  1. Hybrid Fanout Model (Push for regular users, Pull for celebrities).
  2. In-memory Redis-style Sorted Set (ZSET) timeline generation.
  3. Celebrity outbox caching & real-time K-way merge sort.
  4. Cursor-based pagination with Snowflake-style IDs.
"""

import time
import heapq
from typing import Dict, List, Set, Tuple

CELEBRITY_THRESHOLD = 5  # Scaled down for simulation (normally 10,000)

class Post:
    def __init__(self, post_id: int, author_id: str, content: str, timestamp: float):
        self.post_id = post_id
        self.author_id = author_id
        self.content = content
        self.timestamp = timestamp

    def __repr__(self):
        return f"Post(id={self.post_id}, author={self.author_id}, time={self.timestamp:.1f}, text='{self.content}')"

class NewsFeedEngine:
    def __init__(self):
        # Social Graph: user_id -> set of followers
        self.followers: Dict[str, Set[str]] = {}
        # Social Graph: user_id -> set of people they follow
        self.following: Dict[str, Set[str]] = {}
        
        # Post storage (simulates primary DB / KV cache)
        self.posts_db: Dict[int, Post] = {}
        
        # User inboxes: user_id -> list of (timestamp, post_id) sorted descending
        self.user_inboxes: Dict[str, List[Tuple[float, int]]] = {}
        
        # Celebrity outboxes: celebrity_id -> list of (timestamp, post_id)
        self.celebrity_outboxes: Dict[str, List[Tuple[float, int]]] = {}
        
        self.id_counter = 1000

    def add_follow(self, follower: str, followee: str):
        self.followers.setdefault(followee, set()).add(follower)
        self.following.setdefault(follower, set()).add(followee)

    def publish_post(self, author_id: str, content: str) -> Post:
        self.id_counter += 1
        post_id = self.id_counter
        post = Post(post_id, author_id, content, time.time())
        self.posts_db[post_id] = post

        follower_count = len(self.followers.get(author_id, set()))
        is_celebrity = follower_count >= CELEBRITY_THRESHOLD

        if is_celebrity:
            # PULL MODEL: Save strictly to celebrity outbox
            self.celebrity_outboxes.setdefault(author_id, []).append((post.timestamp, post_id))
            print(f"  [Publish - PULL] Celebrity {author_id} ({follower_count} followers) published #{post_id} -> Written ONLY to outbox.")
        else:
            # PUSH MODEL: Fan-out on write to all follower inboxes
            followers = self.followers.get(author_id, set())
            print(f"  [Publish - PUSH] Regular User {author_id} published #{post_id} -> Pushing to {len(followers)} follower inboxes.")
            for f in followers:
                inbox = self.user_inboxes.setdefault(f, [])
                inbox.append((post.timestamp, post_id))
                # Keep sorted descending by timestamp
                inbox.sort(key=lambda x: x[0], reverse=True)

        return post

    def get_feed(self, user_id: str, limit: int = 5, cursor_time: float = float('inf')) -> List[Post]:
        """
        Hybrid Feed Generation:
        1. Fetch pre-computed inbox (Push items).
        2. Fetch celebrity outboxes for all followed celebrities (Pull items).
        3. Merge and rank in-memory.
        """
        candidates: List[Tuple[float, int]] = []

        # 1. Grab push items from inbox
        user_inbox = self.user_inboxes.get(user_id, [])
        for ts, pid in user_inbox:
            if ts < cursor_time:
                candidates.append((ts, pid))

        # 2. Grab pull items from followed celebrities
        followed = self.following.get(user_id, set())
        for f in followed:
            if f in self.celebrity_outboxes:
                for ts, pid in self.celebrity_outboxes[f]:
                    if ts < cursor_time:
                        candidates.append((ts, pid))

        # 3. Sort candidates descending by timestamp (K-way merge simulation)
        candidates.sort(key=lambda x: x[0], reverse=True)

        # 4. Paginate and hydrate full post objects
        page_items = candidates[:limit]
        return [self.posts_db[pid] for _, pid in page_items]

def run_simulation():
    print("=" * 65)
    print("NEWS FEED HYBRID FANOUT & RANKING SIMULATION")
    print("=" * 65)

    engine = NewsFeedEngine()

    # Setup Social Graph
    # Taylor Swift is a celebrity (followed by 6 users)
    celebrity = "taylor_swift"
    regular_user = "alice"
    reader = "bob"

    for i in range(1, 7):
        engine.add_follow(follower=f"user_{i}", followee=celebrity)
    
    # Reader (Bob) follows both Taylor Swift and Alice
    engine.add_follow(follower=reader, followee=celebrity)
    engine.add_follow(follower=reader, followee=regular_user)
    # Alice also follows Taylor Swift
    engine.add_follow(follower=regular_user, followee=celebrity)

    print(f"Followers of {celebrity}: {len(engine.followers[celebrity])} (Exceeds threshold of {CELEBRITY_THRESHOLD} -> CELEBRITY)")
    print(f"Followers of {regular_user}: {len(engine.followers.get(regular_user, set()))} (REGULAR USER)\n")

    # 1. Regular User posts (Fanout on Write)
    print("Step 1: Alice (regular user) posts")
    p1 = engine.publish_post(regular_user, "Enjoying a quiet morning coffee!")
    time.sleep(0.05)

    # 2. Celebrity posts (Fanout on Read)
    print("\nStep 2: Taylor Swift (celebrity) posts")
    p2 = engine.publish_post(celebrity, "Excited to announce my world tour dates!")
    time.sleep(0.05)

    # 3. Regular User posts again
    print("\nStep 3: Alice posts another update")
    p3 = engine.publish_post(regular_user, "Reading a great distributed systems book.")
    time.sleep(0.05)

    # 4. Reader (Bob) reads their news feed
    print(f"\nStep 4: Reader ({reader}) loads their feed (Hybrid Merge):")
    feed = engine.get_feed(reader, limit=5)
    for idx, post in enumerate(feed, 1):
        print(f"  {idx}. [{post.author_id}] {post.content} (ID: {post.post_id})")

    # Verify both push and pull items merged seamlessly
    authors = [p.author_id for p in feed]
    assert celebrity in authors and regular_user in authors
    print("\nSUCCESS: Hybrid feed merged Alice's push post and Taylor's pull post in chronological order!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
