from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class ProductCategory(str, Enum):
    food = "food"
    textile = "textile"
    electronics = "electronics"
    personal_care = "personal_care"
    household = "household"
    sport = "sport"
    industrial = "industrial"


class ProductOverview(BaseModel):
    name: str
    category: ProductCategory
    description: str
    origin_in_india: str
    key_organisations: Optional[List[str]] = None
    historical_note: Optional[str] = None


class RawMaterial(BaseModel):
    name: str
    source_region: str
    percentage_share: Optional[float] = None
    cost_per_unit: Optional[str] = None
    notes: Optional[str] = None


class SupplyChainStage(BaseModel):
    stage: str
    location: str
    workers_involved: Optional[List[str]] = None
    description: str
    key_equipment: Optional[List[str]] = None
    cost_added_inr: Optional[str] = None


class GeographyInfo(BaseModel):
    producing_states: List[str]
    major_clusters: Optional[List[str]] = None
    trade_routes: Optional[List[str]] = None


from typing import Union

class CostBreakdownItem(BaseModel):
    stage: str
    cost_inr: Optional[str] = None
    percentage_of_retail: Optional[Union[str, float]] = None


class Economics(BaseModel):
    farm_gate_price_inr: Optional[str] = None
    retail_price_inr: Optional[str] = None
    cost_breakdown: Optional[List[CostBreakdownItem]] = None
    gst_rate: Optional[str] = None
    gst_notes: Optional[str] = None
    market_size_india: Optional[str] = None


class RetailPrice(BaseModel):
    brand: str
    product_name: str
    pack_size: str
    price_inr: float
    retailer: str
    location: str
    date: str


class Sustainability(BaseModel):
    carbon_footprint: Optional[str] = None
    water_usage: Optional[str] = None
    key_concerns: Optional[List[str]] = None
    certifications_schemes: Optional[List[str]] = None


class GovernmentPolicy(BaseModel):
    key_schemes: Optional[List[str]] = None
    regulatory_body: Optional[str] = None
    import_export_policy: Optional[str] = None


class SourceType(str, Enum):
    academic = "academic"
    government = "government"
    ngo = "ngo"
    news = "news"
    industry = "industry"


class Source(BaseModel):
    title: str
    url: Optional[str] = None
    source_type: SourceType
    year: Optional[int] = None


class ProductKnowledge(BaseModel):
    product: str
    overview: ProductOverview
    raw_materials: List[RawMaterial]
    supply_chain: List[SupplyChainStage]
    geography: GeographyInfo
    economics: Economics
    retail_prices: List[RetailPrice]
    sustainability: Sustainability
    government_policy: GovernmentPolicy
    sources: List[Source]