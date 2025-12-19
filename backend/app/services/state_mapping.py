"""
State and City Mapping Service
Builds comprehensive state-city mappings from DOSM datasets and hardcoded data
"""
import logging
from typing import Dict, Set, Optional
from sqlalchemy.orm import Session
from app.models.dosm_record import DOSMRecord

logger = logging.getLogger(__name__)


def load_dosm_state_mappings(db: Session) -> Dict[str, str]:
    """
    Load state-city mappings from DOSM records in database
    
    Attempts to extract state/city relationships from DOSM datasets.
    Looks for fields like: state, negeri, state_name, city, bandar, city_name, location
    
    Returns:
        Dictionary mapping lowercase city names to state names
    """
    dosm_mappings = {}
    
    try:
        # Query DOSM records that might contain location data
        # Look for records with common location-related fields
        records = db.query(DOSMRecord).limit(1000).all()
        
        for record in records:
            if not record.data:
                continue
            
            data = record.data
            
            # Try to extract state and city from various possible field names
            state = None
            city = None
            
            # Common DOSM field names for state
            state_fields = ["state", "negeri", "state_name", "negeri_name", "region", "wilayah"]
            for field in state_fields:
                if field in data and data[field]:
                    state = str(data[field]).strip()
                    break
            
            # Common DOSM field names for city
            city_fields = ["city", "bandar", "city_name", "bandar_name", "location", "daerah", "district"]
            for field in city_fields:
                if field in data and data[field]:
                    city = str(data[field]).strip()
                    break
            
            # If we found both state and city, add to mapping
            if state and city:
                city_lower = city.lower()
                # Normalize state name (capitalize properly)
                state_normalized = state.title()
                dosm_mappings[city_lower] = state_normalized
        
        if dosm_mappings:
            logger.info(f"Loaded {len(dosm_mappings)} state-city mappings from DOSM records")
        else:
            logger.debug("No state-city mappings found in DOSM records")
            
    except Exception as e:
        logger.warning(f"Error loading DOSM state mappings: {e}")
    
    return dosm_mappings


def get_comprehensive_city_state_mapping(db: Optional[Session] = None) -> Dict[str, str]:
    """
    Get comprehensive city-to-state mapping combining hardcoded data and DOSM records
    
    Args:
        db: Optional database session to load DOSM mappings
        
    Returns:
        Dictionary mapping lowercase city names to state names
    """
    # Base mapping with comprehensive Malaysian cities
    # Includes all 20 official cities (bandaraya) as of 2024 according to Wikipedia:
    # https://en.wikipedia.org/wiki/List_of_cities_in_Malaysia
    # 1. George Town, 2. Kuala Lumpur, 3. Ipoh, 4. Johor Bahru, 5. Kuching,
    # 6. Shah Alam, 7. Malacca City, 8. Alor Setar, 9. Miri, 10. Petaling Jaya,
    # 11. Kuala Terengganu, 12. Iskandar Puteri, 13. Seberang Perai, 14. Seremban,
    # 15. Subang Jaya, 16. Pasir Gudang, 17. Kuantan, 18. Klang, 19. Kota Kinabalu, 20. Putrajaya (if counted separately)
    base_mapping = {
        # Sarawak
        "miri": "Sarawak", "kuching": "Sarawak", "sibu": "Sarawak", "bintulu": "Sarawak",
        "sri aman": "Sarawak", "sarikei": "Sarawak", "kapit": "Sarawak", "limbang": "Sarawak",
        "lawas": "Sarawak", "mukah": "Sarawak", "betong": "Sarawak", "marudi": "Sarawak",
        
        # Sabah
        "kota kinabalu": "Sabah", "kk": "Sabah", "sandakan": "Sabah", "tawau": "Sabah",
        "lahad datu": "Sabah", "keningau": "Sabah", "semporna": "Sabah", "kudat": "Sabah",
        "ranau": "Sabah", "beaufort": "Sabah", "tuaran": "Sabah", "pap": "Sabah",
        "putatan": "Sabah", "papar": "Sabah",
        
        # Selangor
        "shah alam": "Selangor", "petaling jaya": "Selangor", "pj": "Selangor",
        "subang jaya": "Selangor", "klang": "Selangor", "kajang": "Selangor",
        "ampang": "Selangor", "rawang": "Selangor", "sepang": "Selangor",
        "balakong": "Selangor", "puchong": "Selangor", "cyberjaya": "Selangor",
        "bandar baru bangi": "Selangor", "seri kembangan": "Selangor",
        "bandar sunway": "Selangor", "kota damansara": "Selangor",
        "putra heights": "Selangor", "sungai buloh": "Selangor", "puncak alam": "Selangor",
        "selayang": "Selangor", "bangi": "Selangor", "serdang": "Selangor",
        "semenyih": "Selangor", "taman universiti": "Selangor",
        
        # Johor
        "johor bahru": "Johor", "jb": "Johor", "skudai": "Johor", "pasir gudang": "Johor",
        "batu pahat": "Johor", "muar": "Johor", "segamat": "Johor", "kluang": "Johor",
        "kota tinggi": "Johor", "pontian": "Johor", "mersing": "Johor",
        "simpang renggam": "Johor", "ulu tiram": "Johor", "senai": "Johor",
        "kulai": "Johor", "nusajaya": "Johor", "iskandar puteri": "Johor",
        "masai": "Johor", "tangkak": "Johor", "yong peng": "Johor", "parit raja": "Johor",
        
        # Perak
        "ipoh": "Perak", "taiping": "Perak", "teluk intan": "Perak", "sitiawan": "Perak",
        "kampar": "Perak", "batu gajah": "Perak", "lumut": "Perak", "tronoh": "Perak",
        "tambun": "Perak", "simpang pulai": "Perak", "parit": "Perak", "parit buntar": "Perak",
        "beruas": "Perak", "bota": "Perak", "seri manjung": "Perak", "kuala kangsar": "Perak",
        
        # Penang (Pulau Pinang)
        "george town": "Penang", "butterworth": "Penang", "bayan lepas": "Penang",
        "air itam": "Penang", "jelutong": "Penang", "balik pulau": "Penang",
        "bukit mertajam": "Penang", "nibong tebal": "Penang", "perai": "Penang",
        "seberang perai": "Penang", "tanggung bungah": "Penang", "batu ferringhi": "Penang",
        "pulau pinang": "Penang",
        
        # Kedah
        "alor setar": "Kedah", "sungai petani": "Kedah", "kulim": "Kedah",
        "langkawi": "Kedah", "kuala kedah": "Kedah", "yan": "Kedah",
        "kubang pasu": "Kedah", "pendang": "Kedah", "anak bukit": "Kedah",
        
        # Kelantan
        "kota bharu": "Kelantan", "pasir mas": "Kelantan", "tanah merah": "Kelantan",
        "tumpat": "Kelantan", "gua musang": "Kelantan", "ketereh": "Kelantan", "kubang kerian": "Kelantan",
        
        # Terengganu
        "kuala terengganu": "Terengganu", "dungun": "Terengganu", "kemaman": "Terengganu",
        "jerteh": "Terengganu", "besut": "Terengganu", "marang": "Terengganu",
        "hulu nerus": "Terengganu",
        
        # Pahang
        "kuantan": "Pahang", "temerloh": "Pahang", "bentong": "Pahang", "raub": "Pahang",
        "kuala lipis": "Pahang", "pekan": "Pahang", "rompin": "Pahang",
        "jerantut": "Pahang", "cameron highlands": "Pahang", "fraser's hill": "Pahang", "fraser hill": "Pahang",
        
        # Melaka
        "melaka": "Melaka", "malacca": "Melaka", "malacca city": "Melaka",
        "ayer keroh": "Melaka", "alor gajah": "Melaka", "jasin": "Melaka",
        
        # Negeri Sembilan
        "seremban": "Negeri Sembilan", "port dickson": "Negeri Sembilan",
        "nilai": "Negeri Sembilan", "kuala pilah": "Negeri Sembilan",
        "rembau": "Negeri Sembilan", "tampin": "Negeri Sembilan", "seri menanti": "Negeri Sembilan",
        
        # Perlis
        "kangar": "Perlis", "arau": "Perlis",
        
        # Federal Territories
        "kuala lumpur": "Kuala Lumpur", "kl": "Kuala Lumpur",
        "putrajaya": "Putrajaya", "labuan": "Labuan",
        
        # Common abbreviations
        "sarawak": "Sarawak", "sabah": "Sabah", "selangor": "Selangor",
        "johor": "Johor", "perak": "Perak", "penang": "Penang",
        "kedah": "Kedah", "kelantan": "Kelantan", "terengganu": "Terengganu",
        "pahang": "Pahang", "melaka": "Melaka", "perlis": "Perlis",
    }
    
    # If database session provided, load DOSM mappings and merge
    if db:
        dosm_mappings = load_dosm_state_mappings(db)
        # DOSM mappings take priority (they're more authoritative)
        # Merge: base mapping first, then DOSM overrides
        combined = {**base_mapping, **dosm_mappings}
        return combined
    
    return base_mapping


def normalize_state_name(state: str) -> str:
    """
    Normalize state name to standard format
    
    Args:
        state: Raw state name from various sources
        
    Returns:
        Normalized state name
    """
    if not state:
        return "Unknown"
    
    state_lower = state.lower().strip()
    
    # Map common variations to standard names
    state_variations = {
        "kl": "Kuala Lumpur",
        "wp kuala lumpur": "Kuala Lumpur",
        "wilayah persekutuan kuala lumpur": "Kuala Lumpur",
        "wp putrajaya": "Putrajaya",
        "wilayah persekutuan putrajaya": "Putrajaya",
        "wp labuan": "Labuan",
        "wilayah persekutuan labuan": "Labuan",
        "ns": "Negeri Sembilan",
        "n.sembilan": "Negeri Sembilan",
        "n.s": "Negeri Sembilan",
        "pulau pinang": "Penang",
    }
    
    if state_lower in state_variations:
        return state_variations[state_lower]
    
    # Title case for standard formatting
    return state.title()

