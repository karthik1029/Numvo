from abc import ABC, abstractmethod

from numvo.models import ProviderResult


class PhoneIntelligenceProvider(ABC):
    name: str

    @abstractmethod
    def lookup(self, phone_number: str) -> ProviderResult:
        raise NotImplementedError
