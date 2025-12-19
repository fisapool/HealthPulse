# Malaysia States and Cities Mapping

This document lists the verified states and cities used in the HealthPulse system, extracted from official Wikipedia sources.

## Source References

- **States and Federal Territories**: [Wikipedia - States and federal territories of Malaysia](https://en.wikipedia.org/wiki/States_and_federal_territories_of_Malaysia)
- **Official Cities**: [Wikipedia - List of cities in Malaysia](https://en.wikipedia.org/wiki/List_of_cities_in_Malaysia)

## Administrative Divisions

### 13 States
1. Johor
2. Kedah
3. Kelantan
4. Melaka (Malacca)
5. Negeri Sembilan
6. Pahang
7. Penang (Pulau Pinang)
8. Perak
9. Perlis
10. Sabah
11. Sarawak
12. Selangor
13. Terengganu

### 3 Federal Territories
1. Kuala Lumpur
2. Labuan
3. Putrajaya

**Total: 16 administrative divisions**

## Official Cities (Bandaraya) - 20 Cities (2024)

As of 2024, Malaysia has 20 areas officially designated as cities by law:

| # | City | State/Federal Territory | Status |
|---|------|------------------------|--------|
| 1 | George Town | Penang | Capital city |
| 2 | Kuala Lumpur | Federal Territory | National capital |
| 3 | Ipoh | Perak | Capital city |
| 4 | Johor Bahru | Johor | Capital city |
| 5 | Kuching | Sarawak | Capital city |
| 6 | Shah Alam | Selangor | Capital city |
| 7 | Malacca City | Melaka | Capital city |
| 8 | Alor Setar | Kedah | Capital city |
| 9 | Miri | Sarawak | - |
| 10 | Petaling Jaya | Selangor | - |
| 11 | Kuala Terengganu | Terengganu | Capital city |
| 12 | Iskandar Puteri | Johor | - |
| 13 | Seberang Perai | Penang | - |
| 14 | Seremban | Negeri Sembilan | Capital city |
| 15 | Subang Jaya | Selangor | - |
| 16 | Pasir Gudang | Johor | - |
| 17 | Kuantan | Pahang | Capital city |
| 18 | Klang | Selangor | - |
| 19 | Kota Kinabalu | Sabah | Capital city |
| 20 | Putrajaya | Federal Territory | Administrative capital |

**Note**: The list includes 16 from Peninsular Malaysia and 3 from East Malaysia (Sarawak and Sabah), plus 1 Federal Territory (Putrajaya).

## Implementation

All states, federal territories, and official cities are mapped in:
- `backend/app/services/state_mapping.py`

The mapping system:
- Includes all 20 official cities
- Includes additional major towns and districts
- Supports common abbreviations (KL, JB, NS, etc.)
- Integrates with DOSM datasets for dynamic updates
- Normalizes state names for consistency

## Verification Status

✅ **All 13 states verified**  
✅ **All 3 federal territories verified**  
✅ **All 20 official cities (2024) verified**  
✅ **150+ additional cities/towns mapped**

Last verified: 2024

