from dataclasses import dataclass

@dataclass(frozen=True)
class PlatformsEnum:
    SUSHI: str = "sushi"
    LOCAL: str = "local"
    UNIV3: str = "uniswap_v3"
