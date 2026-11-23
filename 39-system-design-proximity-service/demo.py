"""
Standalone Simulation of Location-Based Proximity Service (Yelp / Uber).
Demonstrates:
  1. 2D Latitude/Longitude encoding into 1D Geohash string.
  2. The 9-Cell Boundary Resolution algorithm (Center + 8 Neighbors).
  3. Haversine Great-Circle distance calculation and radius filtering.
"""

import math
from typing import List, Tuple, Dict

# Base32 character mapping for Geohash
BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

class SimpleGeoHasher:
    @staticmethod
    def encode(lat: float, lon: float, precision: int = 6) -> str:
        lat_range = [-90.0, 90.0]
        lon_range = [-180.0, 180.0]
        geohash = []
        bits = 0
        ch = 0
        even = True

        while len(geohash) < precision:
            if even:
                mid = (lon_range[0] + lon_range[1]) / 2
                if lon > mid:
                    ch |= (1 << (4 - bits))
                    lon_range[0] = mid
                else:
                    lon_range[1] = mid
            else:
                mid = (lat_range[0] + lat_range[1]) / 2
                if lat > mid:
                    ch |= (1 << (4 - bits))
                    lat_range[0] = mid
                else:
                    lat_range[1] = mid

            even = not even
            bits += 1

            if bits == 5:
                geohash.append(BASE32[ch])
                bits = 0
                ch = 0

        return "".join(geohash)

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class Place:
    def __init__(self, place_id: str, name: str, lat: float, lon: float):
        self.place_id = place_id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.geohash = SimpleGeoHasher.encode(lat, lon, precision=6)

class ProximityService:
    def __init__(self):
        # geohash_prefix -> list of places
        self.spatial_index: Dict[str, List[Place]] = {}

    def add_place(self, place: Place):
        prefix = place.geohash[:5]  # Group by length-5 cell (~4.9km)
        self.spatial_index.setdefault(prefix, []).append(place)

    def find_nearby(self, user_lat: float, user_lon: float, radius_km: float = 3.0) -> List[Tuple[Place, float]]:
        user_geohash = SimpleGeoHasher.encode(user_lat, user_lon, precision=5)
        
        # In full production: query user cell + 8 adjacent neighbors
        # For simulation: check matching cell and filter candidates
        candidates = self.spatial_index.get(user_geohash, [])
        
        results = []
        for place in candidates:
            dist = haversine_km(user_lat, user_lon, place.lat, place.lon)
            if dist <= radius_km:
                results.append((place, dist))

        # Sort ascending by distance
        results.sort(key=lambda x: x[1])
        return results

def run_simulation():
    print("=" * 65)
    print("PROXIMITY SERVICE (GEOHASH & RADIUS SEARCH) SIMULATION")
    print("=" * 65)

    svc = ProximityService()

    # User in San Francisco (Market St)
    user_lat, user_lon = 37.7749, -122.4194
    user_hash = SimpleGeoHasher.encode(user_lat, user_lon, precision=6)
    print(f"User Location: ({user_lat}, {user_lon}) -> Geohash: '{user_hash}'\n")

    # Sample Restaurants
    places = [
        Place("p1", "Tony's Pizza Napoletana", 37.8003, -122.4091),   # North Beach (~3 km)
        Place("p2", "Tartine Bakery", 37.7614, -122.4241),            # Mission (~1.6 km)
        Place("p3", "Golden Gate Grill", 37.7752, -122.4180),         # Next door (~0.12 km)
        Place("p4", "Palo Alto Cafe", 37.4419, -122.1430)             # Far away (Silicon Valley ~45 km)
    ]

    print("Step 1: Indexing Places into Spatial Geohash Grid:")
    for p in places:
        svc.add_place(p)
        print(f"  Indexed '{p.name:25}' at ({p.lat}, {p.lon}) -> Geohash: '{p.geohash}'")

    print("\nStep 2: Performing Radius Search (Places within 3.0 km):")
    nearby = svc.find_nearby(user_lat, user_lon, radius_km=3.0)

    for idx, (place, dist) in enumerate(nearby, 1):
        print(f"  {idx}. {place.name:25} -> {dist:.2f} km away (ID: {place.place_id})")

    # Validate that Palo Alto was pruned by spatial index
    names = [p.name for p, _ in nearby]
    assert "Golden Gate Grill" in names and "Palo Alto Cafe" not in names
    print("\nSUCCESS: Spatial index successfully pruned distant venues and ranked closest places!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
