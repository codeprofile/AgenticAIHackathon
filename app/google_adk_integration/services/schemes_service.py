# ============================================================================
# services/schemes_service.py
# ============================================================================
from typing import Dict, Any, List
from datetime import datetime
from ..utils.helpers import get_logger, load_json_data, normalize_location

logger = get_logger(__name__)


class SchemesService:
    """Government schemes and subsidies service"""

    def __init__(self):
        self.schemes_database = self._load_schemes_database()

    def _load_schemes_database(self) -> Dict[str, Any]:
        """Load schemes database from JSON file"""
        return load_json_data("data/schemes_db.json") or self._get_default_schemes_data()

    def get_schemes(self, state: str, category: str = "all", farmer_type: str = "all") -> Dict[str, Any]:
        """Get government schemes based on state and category"""
        try:
            state_normalized = normalize_location(state)
            applicable_schemes = []

            # Get national schemes (applicable everywhere)
            national_schemes = self.schemes_database.get("national", {})
            applicable_schemes.extend(self._filter_schemes(national_schemes, category, farmer_type, "national"))

            # Get state-specific schemes
            state_schemes = self.schemes_database.get(state_normalized, {})
            applicable_schemes.extend(self._filter_schemes(state_schemes, category, farmer_type, state))

            if not applicable_schemes:
                return {
                    "status": "not_found",
                    "message": f"No schemes found for {state} in category '{category}'",
                    "available_categories": self._get_available_categories(state_normalized),
                    "suggestion": "Try different category or check national schemes"
                }

            return {
                "status": "success",
                "state": state,
                "category": category,
                "total_schemes": len(applicable_schemes),
                "schemes": applicable_schemes,
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }

        except Exception as e:
            logger.error(f"Error fetching schemes for {state}: {e}")
            return {
                "status": "error",
                "message": "Unable to fetch schemes information at the moment"
            }

    def _filter_schemes(self, schemes_data: Dict, category: str, farmer_type: str, region: str) -> List[Dict]:
        """Filter schemes based on criteria"""
        filtered = []

        for scheme_category, schemes_list in schemes_data.items():
            # Category filter
            if category != "all" and category.lower() not in scheme_category.lower():
                continue

            for scheme in schemes_list:
                # Farmer type filter
                if farmer_type != "all":
                    eligible_types = scheme.get("eligible_farmer_types", ["all"])
                    if farmer_type not in eligible_types and "all" not in eligible_types:
                        continue

                # Add region info
                scheme_copy = scheme.copy()
                scheme_copy["region"] = region
                scheme_copy["category"] = scheme_category

                filtered.append(scheme_copy)

        return filtered

    def _get_available_categories(self, state: str) -> List[str]:
        """Get available scheme categories for a state"""
        categories = set()

        # National categories
        categories.update(self.schemes_database.get("national", {}).keys())

        # State categories
        categories.update(self.schemes_database.get(state, {}).keys())

        return list(categories)

    def get_scheme_details(self, scheme_name: str, state: str = None) -> Dict[str, Any]:
        """Get detailed information about a specific scheme"""
        try:
            # Search in national schemes first
            for category, schemes in self.schemes_database.get("national", {}).items():
                for scheme in schemes:
                    if scheme["name"].lower() == scheme_name.lower():
                        return {
                            "status": "success",
                            "scheme": scheme,
                            "category": category,
                            "region": "national"
                        }

            # Search in state schemes if state provided
            if state:
                state_normalized = normalize_location(state)
                state_schemes = self.schemes_database.get(state_normalized, {})
                for category, schemes in state_schemes.items():
                    for scheme in schemes:
                        if scheme["name"].lower() == scheme_name.lower():
                            return {
                                "status": "success",
                                "scheme": scheme,
                                "category": category,
                                "region": state
                            }

            return {
                "status": "not_found",
                "message": f"Scheme '{scheme_name}' not found",
                "suggestion": "Check scheme name spelling or browse available schemes"
            }

        except Exception as e:
            logger.error(f"Error getting scheme details for {scheme_name}: {e}")
            return {
                "status": "error",
                "message": "Unable to fetch scheme details"
            }

    def _get_default_schemes_data(self) -> Dict[str, Any]:
        """Default government schemes database"""
        return {
            "national": {
                "insurance": [
                    {
                        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                        "description": "Comprehensive crop insurance scheme covering all stages of crop cycle against various risks",
                        "benefits": [
                            "Coverage for pre-sowing to post-harvest losses",
                            "Premium rates: 2% for Kharif, 1.5% for Rabi crops",
                            "Claims settled through technology and satellite imagery",
                            "Coverage for natural calamities, pests, and diseases"
                        ],
                        "eligibility": [
                            "All farmers (landowner and tenant farmers)",
                            "Crop should be notified in the area",
                            "Coverage available for food grains, oilseeds, and horticultural crops"
                        ],
                        "how_to_apply": [
                            "Apply through banks where crop loan is availed",
                            "Non-loanee farmers can apply directly",
                            "Online application through PMFBY portal",
                            "Visit nearest Common Service Center (CSC)"
                        ],
                        "documents_required": [
                            "Land ownership documents or tenancy agreement",
                            "Bank account details",
                            "Aadhaar card",
                            "Sowing certificate (if applicable)"
                        ],
                        "contact_info": {
                            "website": "https://pmfby.gov.in",
                            "helpline": "14447"
                        },
                        "eligible_farmer_types": ["all"]
                    }
                ],
                "subsidy": [
                    {
                        "name": "PM-KISAN",
                        "description": "Direct income support scheme providing ₹6000 per year to eligible farmer families",
                        "benefits": [
                            "₹2000 per installment, 3 installments per year",
                            "Direct transfer to bank account",
                            "No requirement for any application or documentation by farmers"
                        ],
                        "eligibility": [
                            "Small and marginal farmer families",
                            "Families owning cultivable land up to 2 hectares",
                            "Land ownership as per land records"
                        ],
                        "how_to_apply": [
                            "Online registration at pmkisan.gov.in",
                            "Visit nearest CSC or village-level entrepreneur",
                            "Contact local agriculture officer",
                            "Through mobile app 'PM Kisan Mobile App'"
                        ],
                        "documents_required": [
                            "Aadhaar card",
                            "Bank account details",
                            "Land ownership certificate"
                        ],
                        "contact_info": {
                            "website": "https://pmkisan.gov.in",
                            "helpline": "155261"
                        },
                        "eligible_farmer_types": ["small", "marginal"]
                    }
                ],
                "credit": [
                    {
                        "name": "Kisan Credit Card (KCC)",
                        "description": "Credit facility for farmers to meet short-term credit requirements",
                        "benefits": [
                            "Credit limit based on operational land holding and cropping pattern",
                            "Flexible repayment schedule aligned with harvesting and income generation",
                            "Interest subvention for timely repayment",
                            "Insurance coverage for crops and farmer"
                        ],
                        "eligibility": [
                            "Farmers - individual/joint borrowers who are owner cultivators",
                            "Tenant farmers, oral lessees and share croppers",
                            "Self Help Group (SHG) members engaged in farming"
                        ],
                        "how_to_apply": [
                            "Visit nearest branch of scheduled commercial bank",
                            "Submit application with required documents",
                            "Bank will assess eligibility and credit limit"
                        ],
                        "documents_required": [
                            "Application form",
                            "Identity proof (Aadhaar/Voter ID)",
                            "Address proof",
                            "Land documents"
                        ],
                        "contact_info": {
                            "website": "https://pmkisan.gov.in/KCCStaticPage.aspx",
                            "helpline": "Contact your nearest bank branch"
                        },
                        "eligible_farmer_types": ["all"]
                    }
                ]
            },
            "punjab": {
                "subsidy": [
                    {
                        "name": "Punjab Farm Machinery Subsidy Scheme",
                        "description": "Subsidy on purchase of agricultural machinery and implements",
                        "benefits": [
                            "Up to 50% subsidy on machinery cost for small farmers",
                            "40% subsidy for other farmers",
                            "Special rates for SC/ST farmers",
                            "Coverage for tractors, combines, and other implements"
                        ],
                        "eligibility": [
                            "Farmers with valid land records in Punjab",
                            "Should not have availed subsidy for same implement in last 7 years",
                            "Minimum land holding requirements vary by implement"
                        ],
                        "how_to_apply": [
                            "Apply online through Punjab government portal",
                            "Visit district agriculture office",
                            "Submit application before purchasing machinery"
                        ],
                        "documents_required": [
                            "Land ownership documents",
                            "Identity and address proof",
                            "Bank account details",
                            "Quotation from authorized dealer"
                        ],
                        "contact_info": {
                            "website": "https://punjab.gov.in",
                            "helpline": "Contact district agriculture office"
                        },
                        "eligible_farmer_types": ["all"]
                    }
                ],
                "irrigation": [
                    {
                        "name": "Micro Irrigation Scheme Punjab",
                        "description": "Subsidy for drip and sprinkler irrigation systems",
                        "benefits": [
                            "Up to 85% subsidy for small and marginal farmers",
                            "75% subsidy for other farmers",
                            "Water saving up to 40-60%",
                            "Improved crop productivity"
                        ],
                        "eligibility": [
                            "Farmers with assured source of water",
                            "Minimum area of 0.5 acres",
                            "Should have electricity connection for pump"
                        ],
                        "how_to_apply": [
                            "Apply through authorized system providers",
                            "Technical feasibility assessment",
                            "Installation by certified technicians"
                        ],
                        "documents_required": [
                            "Land ownership proof",
                            "Water source certificate",
                            "Electricity connection proof"
                        ],
                        "contact_info": {
                            "website": "https://punjab.gov.in",
                            "helpline": "Contact irrigation department"
                        },
                        "eligible_farmer_types": ["all"]
                    }
                ]
            },
            "haryana": {
                "subsidy": [
                    {
                        "name": "Haryana Agricultural Machinery Grant Scheme",
                        "description": "Financial assistance for purchase of agricultural equipment",
                        "benefits": [
                            "50% subsidy for SC farmers",
                            "40% subsidy for general category",
                            "Custom hiring centers supported",
                            "Focus on modern farming equipment"
                        ],
                        "eligibility": [
                            "Farmers residing in Haryana",
                            "Valid land records",
                            "Should not have defaulted on previous loans"
                        ],
                        "how_to_apply": [
                            "Online application through Haryana government portal",
                            "Visit block agriculture office",
                            "Participate in equipment demonstrations"
                        ],
                        "contact_info": {
                            "website": "https://haryana.gov.in",
                            "helpline": "Contact agriculture department"
                        },
                        "eligible_farmer_types": ["all"]
                    }
                ]
            },
            "maharashtra": {
                "subsidy": [
                    {
                        "name": "Maharashtra Krishi Pump Scheme",
                        "description": "Subsidized electricity connection for agricultural pumps",
                        "benefits": [
                            "Free electricity connection up to 5 HP",
                            "Subsidized rates for higher capacity",
                            "Solar pump subsidy available",
                            "Separate feeder for agriculture"
                        ],
                        "eligibility": [
                            "Farmers with irrigated land",
                            "Should have legal land documents",
                            "Compliance with groundwater regulations"
                        ],
                        "how_to_apply": [
                            "Apply through MSEDCL offices",
                            "Submit land and identity documents",
                            "Technical survey by department"
                        ],
                        "contact_info": {
                            "website": "https://mahadiscom.in",
                            "helpline": "19122"
                        },
                        "eligible_farmer_types": ["all"]
                    }
                ],
                "insurance": [
                    {
                        "name": "Maharashtra State Crop Insurance",
                        "description": "Additional crop insurance coverage beyond PMFBY",
                        "benefits": [
                            "Coverage for local weather risks",
                            "Quick settlement process",
                            "Coverage for horticulture crops",
                            "Livestock insurance options"
                        ],
                        "eligibility": [
                            "Farmers already enrolled in PMFBY",
                            "Cultivation of notified crops",
                            "Regular premium payment"
                        ],
                        "how_to_apply": [
                            "Through cooperative banks",
                            "Agriculture insurance company offices",
                            "Online portal of state government"
                        ],
                        "contact_info": {
                            "website": "https://maharashtra.gov.in",
                            "helpline": "Contact district collector office"
                        },
                        "eligible_farmer_types": ["all"]
                    }
                ]
            }
        }
