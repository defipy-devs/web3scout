from dataclasses import dataclass

@dataclass(frozen=True)
class PlatformsEnum:
    SUSHI: str = "sushi"
    UNIV3: str = "uniswap_v3"
