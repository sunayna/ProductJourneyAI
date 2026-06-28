from pydantic import BaseModel, HttpUrl, Field
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
    origin_country: str
    year_invented: Optional[int] = None
    fun_fact: Optional[str] = None

class RawMaterial(BaseModel):
    name: str
    source_region: str
    percentage_share: Optional[float] = None
    notes: Optional[str] = None

class ManufacturingStep(BaseModel):
    step_number: int
    title: str
    description: str
    energy_intensity: Optional[str] = None
    by_products: Optional[List[str]] = None

class GeographyInfo(BaseModel):
    producing_countries: List[str]
    major_trade_routes: Optional[List[str]] = None
    consuming_countries: Optional[List[str]] = None

class Economics(BaseModel):
    farm_gate_pct: Optional[float] = None
    processing_pct: Optional[float] = None
    transport_pct: Optional[float] = None
    retail_pct: Optional[float] = None
    avg_retail_price_usd: Optional[float] = None
    market_size_usd_bn: Optional[float] = None

class Sustainability(BaseModel):
    carbon_kg_per_unit: Optional[float] = None
    water_liters_per_unit: Optional[float] = None
    certifications: Optional[List[str]] = None
    key_concerns: Optional[List[str]] = None

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
    manufacturing: List[ManufacturingStep]
    geography: GeographyInfo
    economics: Economics
    sustainability: Sustainability
    sources: List[Source]