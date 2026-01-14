#!/usr/bin/env python3
"""
Next District Line Train to Upminster from Fulham Broadway

Fetches real-time departure information from the TfL Unified API.
No API key required for basic usage.

Usage:
    python next-train.py              # Show next trains to Upminster
    python next-train.py --all        # Show all eastbound trains
    python next-train.py --watch      # Auto-refresh every 30 seconds
"""

import urllib.request
import json
import sys
from datetime import datetime

# TfL API configuration
STATION_ID = "940GZZLUFBY"  # Fulham Broadway Naptan ID
LINE_ID = "district"
API_URL = f"https://api.tfl.gov.uk/StopPoint/{STATION_ID}/Arrivals"

# Eastbound destinations (towards Upminster direction)
EASTBOUND_DESTINATIONS = [
    "upminster",
    "barking",
    "dagenham east",
    "elm park",
    "hornchurch",
    "tower hill",
    "whitechapel",
    "mile end",
    "stepney green",
    "bow road",
    "bromley-by-bow",
    "west ham",
    "plaistow",
    "upton park",
    "east ham",
    "becontree",
    "dagenham heathway",
]


def fetch_arrivals():
    """Fetch live arrival data from TfL API."""
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": "NextTrain/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"Error connecting to TfL API: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error parsing TfL response")
        sys.exit(1)


def format_time(seconds):
    """Convert seconds to a human-readable time string."""
    if seconds < 60:
        return "Due"
    minutes = seconds // 60
    if minutes == 1:
        return "1 min"
    return f"{minutes} mins"


def get_arrival_time(arrival):
    """Parse expected arrival time from API response."""
    try:
        expected = datetime.fromisoformat(arrival["expectedArrival"].replace("Z", "+00:00"))
        return expected.strftime("%H:%M")
    except (KeyError, ValueError):
        return "--:--"


def filter_district_eastbound(arrivals, upminster_only=True):
    """Filter arrivals for District line eastbound trains."""
    filtered = []

    for arrival in arrivals:
        if arrival.get("lineId", "").lower() != "district":
            continue

        destination = arrival.get("destinationName", "").lower()
        towards = arrival.get("towards", "").lower()

        # Check if eastbound
        is_eastbound = any(dest in destination or dest in towards
                         for dest in EASTBOUND_DESTINATIONS)

        if not is_eastbound:
            continue

        # If upminster_only, filter strictly
        if upminster_only and "upminster" not in destination:
            continue

        filtered.append(arrival)

    # Sort by time to station
    filtered.sort(key=lambda x: x.get("timeToStation", 9999))
    return filtered


def display_arrivals(arrivals, show_all=False):
    """Display arrivals in a nice format."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n🚇 District Line from Fulham Broadway")
    print(f"   Updated: {now}")
    print("-" * 45)

    if not arrivals:
        destination = "eastbound" if show_all else "Upminster"
        print(f"   No {destination} trains currently showing")
        print("-" * 45)
        return

    for i, arr in enumerate(arrivals[:6]):  # Show next 6 trains
        destination = arr.get("destinationName", "Unknown")
        time_to = arr.get("timeToStation", 0)
        arrival_time = get_arrival_time(arr)
        platform = arr.get("platformName", "")

        time_str = format_time(time_to)

        # Highlight Upminster trains
        if "upminster" in destination.lower():
            marker = "→"
        else:
            marker = " "

        print(f" {marker} {time_str:>8}  {destination:<20} ({arrival_time})")

        if platform:
            print(f"            Platform: {platform}")

    print("-" * 45)
    print("  → = Upminster service")


def watch_mode(show_all=False):
    """Continuously refresh arrivals."""
    import time

    print("Watching for trains... (Ctrl+C to stop)\n")

    try:
        while True:
            # Clear screen (works on most terminals)
            print("\033[2J\033[H", end="")

            arrivals = fetch_arrivals()
            filtered = filter_district_eastbound(arrivals, upminster_only=not show_all)
            display_arrivals(filtered, show_all)

            print("\n  Refreshing in 30 seconds...")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\nStopped watching.")


def main():
    show_all = "--all" in sys.argv
    watch = "--watch" in sys.argv or "-w" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    if watch:
        watch_mode(show_all)
    else:
        arrivals = fetch_arrivals()
        filtered = filter_district_eastbound(arrivals, upminster_only=not show_all)
        display_arrivals(filtered, show_all)


if __name__ == "__main__":
    main()
