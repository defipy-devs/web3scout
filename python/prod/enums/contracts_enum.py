from dataclasses import dataclass

@dataclass(frozen=True)
class JSONContractsEnum:
    IUniswapV2Pair: str = "IUniswapV2Pair"
    UniswapV2Pair: str = "UniswapV2Pair"
    UniswapV2Router02: str = "UniswapV2Router02"
    UniswapV2Factory: str = "UniswapV2Factory"
    UniswapV3Pool: str = "UniswapV3Pool"
    UniswapV3Factory: str = "UniswapV3Factory"
    UniV2IndexedYieldLinearExitPool: str = "UniV2IndexedYieldLinearExitPool"
    MintableRCIndexedYieldLinearExitPoolStudy: str = "MintableRCIndexedYieldLinearExitPoolStudy"



