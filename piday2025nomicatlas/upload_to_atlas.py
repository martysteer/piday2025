#!/usr/bin/env python3
"""
Minimal Nomic Atlas Map Creator

Creates an empty Nomic Atlas map with the given name.

Usage:
    python create_empty_map.py --map-name MyMapName
"""

import argparse
from nomic import atlas

def main():
    parser = argparse.ArgumentParser(description="Create an empty Nomic Atlas map")
    parser.add_argument("--map-name", "-n", required=True, help="Name for the Atlas map")
    args = parser.parse_args()
    
    print(f"Creating empty Atlas map: {args.map_name}")
    
    # Create empty map with just a single placeholder item
    atlas_map = atlas.map_data(
        data=[{"id": "1", "placeholder": "empty map"}],
        identifier=args.map_name,
        description=f"{args.map_name} - Empty Map"
    )
    
    print(f"\nCreated map successfully!")
    print(f"Map ID: {atlas_map.id}")
    print(f"View at: https://atlas.nomic.ai/map/{atlas_map.id}")

if __name__ == "__main__":
    main()