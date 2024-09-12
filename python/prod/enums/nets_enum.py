from dataclasses import dataclass

@dataclass(frozen=True)
class NetsEnum:
    ROLLUX: str = "rollux"
    ETH: str = "ethereum"
    ARB: str = "arbitrum"
    OP: str = "optimism"
    POLYGON: str = "polygon"
    LOCALHOST: str = "localhost"