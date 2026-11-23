"""
Standalone Simulation of Distributed Web Crawler.
Demonstrates:
  1. URL Frontier with Host Politeness Queues and cooldown delays.
  2. Bloom Filter URL deduplication filter.
  3. URL Canonicalization & Normalization.
  4. Recursive mock HTML link parsing and discovery.
"""

import time
import hashlib
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Set, Optional

class SimpleBloomFilter:
    """Zero-dependency bit-array Bloom filter simulation."""
    def __init__(self, size: int = 1000):
        self.size = size
        self.bit_array = [0] * size

    def _hashes(self, item: str) -> List[int]:
        # Generate 3 independent hash offsets
        h1 = int(hashlib.md5(item.encode()).hexdigest(), 16) % self.size
        h2 = int(hashlib.sha1(item.encode()).hexdigest(), 16) % self.size
        h3 = int(hashlib.sha256(item.encode()).hexdigest(), 16) % self.size
        return [h1, h2, h3]

    def add(self, item: str):
        for h in self._hashes(item):
            self.bit_array[h] = 1

    def contains(self, item: str) -> bool:
        return all(self.bit_array[h] == 1 for h in self._hashes(item))

class URLNormalizer:
    @staticmethod
    def normalize(url: str) -> str:
        parsed = urlparse(url)
        # Lowercase scheme and domain
        scheme = parsed.scheme.lower() or "http"
        netloc = parsed.netloc.lower()
        # Strip default ports
        if netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif netloc.endswith(":443"):
            netloc = netloc[:-4]
        # Remove fragment (#section)
        path = parsed.path or "/"
        return f"{scheme}://{netloc}{path}"

class MockWebCrawler:
    def __init__(self, politeness_delay_secs: float = 0.1):
        self.politeness_delay = politeness_delay_secs
        # Host -> next allowed fetch timestamp
        self.host_cooldowns: Dict[str, float] = {}
        # Host -> FIFO queue of URLs
        self.host_queues: Dict[str, List[str]] = {}
        # Visited URL Bloom Filter
        self.bloom_filter = SimpleBloomFilter(size=5000)
        self.crawled_count = 0

        # Mock Internet Graph
        self.mock_web: Dict[str, List[str]] = {
            "http://example.com/": ["http://example.com/about", "http://wikipedia.org/wiki/Tech", "http://example.com/#fragment"],
            "http://example.com/about": ["http://example.com/team", "http://example.com/"],
            "http://example.com/team": [],
            "http://wikipedia.org/wiki/Tech": ["http://wikipedia.org/wiki/Computer", "http://example.com/about"],
            "http://wikipedia.org/wiki/Computer": []
        }

    def add_url(self, raw_url: str):
        clean_url = URLNormalizer.normalize(raw_url)
        if self.bloom_filter.contains(clean_url):
            # Already seen
            return

        self.bloom_filter.add(clean_url)
        host = urlparse(clean_url).netloc
        self.host_queues.setdefault(host, []).append(clean_url)
        print(f"  [FRONTIER] Enqueued URL for host '{host}': {clean_url}")

    def crawl_step(self) -> bool:
        """Finds a host queue ready for polite crawling."""
        now = time.time()

        for host, queue in list(self.host_queues.items()):
            if not queue:
                continue

            cooldown = self.host_cooldowns.get(host, 0.0)
            if now >= cooldown:
                # Host is ready for polite fetch
                target_url = queue.pop(0)
                self.host_cooldowns[host] = now + self.politeness_delay
                self._fetch_and_parse(target_url)
                return True

        return False

    def _fetch_and_parse(self, url: str):
        self.crawled_count += 1
        print(f"  [FETCHED #{self.crawled_count}] Downloading: {url}")
        
        # Simulate HTML parsing & link discovery
        outbound_links = self.mock_web.get(url, [])
        for link in outbound_links:
            self.add_url(link)

def run_simulation():
    print("=" * 65)
    print("DISTRIBUTED WEB CRAWLER SIMULATION")
    print("=" * 65)

    crawler = MockWebCrawler(politeness_delay_secs=0.08)

    print("Step 1: Seeding Crawler with Root URLs:\n")
    crawler.add_url("HTTP://Example.com:80/")
    crawler.add_url("http://example.com/#top")  # Tests normalization deduplication

    print("\nStep 2: Crawling web graph with politeness delays:")
    # Run crawl loop until queues are empty
    steps = 0
    while steps < 15:
        progress = crawler.crawl_step()
        if not progress:
            # Check if any queues still have pending items
            has_pending = any(len(q) > 0 for q in crawler.host_queues.values())
            if not has_pending:
                break
            time.sleep(0.02)  # Wait for politeness cooldown
        steps += 1

    print(f"\nCrawl complete! Total unique pages crawled: {crawler.crawled_count}")
    print("SUCCESS: Normalized URLs, adhered to per-host politeness, and deduplicated visits via Bloom filter!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
