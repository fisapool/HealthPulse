#!/usr/bin/env python3
"""
Verification script for Malaysian states and cities mapping
Checks that all 13 states + 3 federal territories are properly mapped
"""
import sys
sys.path.insert(0, '.')

from app.services.state_mapping import get_comprehensive_city_state_mapping, normalize_state_name

# Official Malaysian administrative divisions
OFFICIAL_STATES = [
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan",
    "Pahang", "Penang", "Perak", "Perlis", "Sabah", "Sarawak",
    "Selangor", "Terengganu"
]

OFFICIAL_FEDERAL_TERRITORIES = [
    "Kuala Lumpur", "Labuan", "Putrajaya"
]

# Key capital cities and major cities to verify
KEY_CITIES = {
    "Johor": ["Johor Bahru", "Muar", "Pasir Gudang", "Iskandar Puteri"],
    "Kedah": ["Alor Setar", "Sungai Petani", "Kulim", "Langkawi"],
    "Kelantan": ["Kota Bharu", "Kubang Kerian"],
    "Melaka": ["Melaka", "Malacca"],
    "Negeri Sembilan": ["Seremban", "Port Dickson", "Nilai", "Seri Menanti"],
    "Pahang": ["Kuantan", "Pekan", "Temerloh", "Cameron Highlands"],
    "Penang": ["George Town", "Butterworth", "Seberang Perai", "Bukit Mertajam"],
    "Perak": ["Ipoh", "Kuala Kangsar", "Taiping", "Teluk Intan"],
    "Perlis": ["Kangar", "Arau"],
    "Sabah": ["Kota Kinabalu", "Sandakan", "Tawau", "Lahad Datu"],
    "Sarawak": ["Kuching", "Miri", "Sibu", "Bintulu"],
    "Selangor": ["Shah Alam", "Klang", "Petaling Jaya", "Subang Jaya"],
    "Terengganu": ["Kuala Terengganu", "Dungun", "Kemaman"],
    "Kuala Lumpur": ["Kuala Lumpur"],
    "Labuan": ["Labuan"],
    "Putrajaya": ["Putrajaya"],
}

def verify_mapping():
    """Verify the state and city mapping is complete and accurate"""
    print("=" * 70)
    print("MALAYSIAN STATES AND CITIES MAPPING VERIFICATION")
    print("=" * 70)
    
    # Get the mapping
    mapping = get_comprehensive_city_state_mapping()
    
    # Check states
    print("\n1. VERIFYING 13 STATES + 3 FEDERAL TERRITORIES")
    print("-" * 70)
    all_divisions = OFFICIAL_STATES + OFFICIAL_FEDERAL_TERRITORIES
    state_values = set(mapping.values())
    
    verified_states = []
    missing_states = []
    
    for state in all_divisions:
        if state in state_values:
            verified_states.append(state)
            print(f"  ✓ {state}")
        else:
            missing_states.append(state)
            print(f"  ✗ {state} - MISSING")
    
    print(f"\n  Summary: {len(verified_states)}/{len(all_divisions)} verified")
    
    # Check key cities
    print("\n2. VERIFYING KEY CITIES AND CAPITALS")
    print("-" * 70)
    
    total_cities = 0
    verified_cities = 0
    
    for state, cities in KEY_CITIES.items():
        for city in cities:
            total_cities += 1
            city_lower = city.lower()
            
            # Check if city maps to correct state
            found_state = None
            for city_key, mapped_state in mapping.items():
                if city_lower in city_key or city_key in city_lower:
                    found_state = mapped_state
                    break
            
            if found_state == state:
                verified_cities += 1
                print(f"  ✓ {city} → {state}")
            else:
                print(f"  ✗ {city} → {found_state or 'NOT FOUND'} (expected {state})")
    
    print(f"\n  Summary: {verified_cities}/{total_cities} cities verified")
    
    # Check normalization
    print("\n3. VERIFYING STATE NAME NORMALIZATION")
    print("-" * 70)
    
    test_cases = [
        ("kl", "Kuala Lumpur"),
        ("KL", "Kuala Lumpur"),
        ("wp kuala lumpur", "Kuala Lumpur"),
        ("ns", "Negeri Sembilan"),
        ("pulau pinang", "Penang"),
        ("johor", "Johor"),
    ]
    
    for input_state, expected in test_cases:
        result = normalize_state_name(input_state)
        if result == expected:
            print(f"  ✓ '{input_state}' → '{result}'")
        else:
            print(f"  ✗ '{input_state}' → '{result}' (expected '{expected}')")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Total cities in mapping: {len(mapping)}")
    print(f"States/Federal Territories: {len(state_values)}")
    print(f"All administrative divisions present: {len(missing_states) == 0}")
    print("=" * 70)
    
    return len(missing_states) == 0

if __name__ == "__main__":
    success = verify_mapping()
    sys.exit(0 if success else 1)

