from abc import ABC, abstractmethod
from typing import List, Optional

class Payload(ABC):
    @property
    @abstractmethod
    def products(self) -> str:
        pass

class OnClickAction(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def payload(self) -> Payload:
        pass

class ChildChild(ABC):
    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @property
    @abstractmethod
    def label(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def required(self) -> Optional[bool]:
        pass

    @property
    @abstractmethod
    def data_source(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def on_click_action(self) -> Optional[OnClickAction]:
        pass

class LayoutChild(ABC):
    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def children(self) -> List[ChildChild]:
        pass

class Layout(ABC):
    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @property
    @abstractmethod
    def children(self) -> List[LayoutChild]:
        pass

class Description(ABC):
    @property
    @abstractmethod
    def type(self) -> str:
        pass

class Image(ABC):
    pass

class Properties(ABC):
    @property
    @abstractmethod
    def id(self) -> Description:
        pass

    @property
    @abstractmethod
    def title(self) -> Description:
        pass

    @property
    @abstractmethod
    def description(self) -> Description:
        pass

    @property
    @abstractmethod
    def image(self) -> Image:
        pass

class Items(ABC):
    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @property
    @abstractmethod
    def properties(self) -> Properties:
        pass

class Example(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def image(self) -> str:
        pass

class Products(ABC):
    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @property
    @abstractmethod
    def items(self) -> Items:
        pass

    @property
    @abstractmethod
    def example(self) -> List[Example]:
        pass

class CatalogHeading(ABC):
    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @property
    @abstractmethod
    def example(self) -> str:
        pass

class Data(ABC):
    @property
    @abstractmethod
    def catalog_heading(self) -> CatalogHeading:
        pass

    @property
    @abstractmethod
    def products(self) -> Products:
        pass

class Screen(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @property
    @abstractmethod
    def terminal(self) -> bool:
        pass

    @property
    @abstractmethod
    def data(self) -> Data:
        pass

    @property
    @abstractmethod
    def layout(self) -> Layout:
        pass

class CatalogJSON(ABC):
    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def screens(self) -> List[Screen]:
        pass