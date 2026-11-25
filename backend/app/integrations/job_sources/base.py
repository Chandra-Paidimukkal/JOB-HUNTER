"""
Base class for all job source connectors.
Each source implements this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class JobListing:
    """Normalized job listing from any source."""
    title: str
    company: str
    location: str
    description: str
    apply_url: str
    source: str
    external_id: Optional[str] = None
    company_logo: Optional[str] = None
    is_remote: bool = False
    is_hybrid: bool = False
    employment_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    skills_required: List[str] = field(default_factory=list)
    skills_preferred: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    posted_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    country: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None


class BaseJobSource(ABC):
    name: str = "base"
    requires_api_key: bool = False

    def is_configured(self) -> bool:
        """Return True if the connector is properly configured."""
        return True

    @abstractmethod
    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> List[JobListing]:
        """Search for jobs matching keywords."""
        ...

    def get_status(self) -> dict:
        return {
            "source": self.name,
            "configured": self.is_configured(),
            "requires_api_key": self.requires_api_key,
        }
