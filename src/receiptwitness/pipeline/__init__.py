"""Receipt & product matching pipeline — receipt normalization and product dedup."""

from receiptwitness.pipeline.matching import (
    ConfidenceLevel,
    ProductMatcher,
    match_purchase_item,
)
from receiptwitness.pipeline.normalization import (
    MatchMethod,
    MatchResult,
    clean_name,
    extract_size_info,
    jaccard_similarity,
    normalize_product,
)
from receiptwitness.pipeline.receipt import normalize_receipt, parse_meijer_item

__all__ = [
    "ConfidenceLevel",
    "MatchMethod",
    "MatchResult",
    "ProductMatcher",
    "clean_name",
    "extract_size_info",
    "jaccard_similarity",
    "match_purchase_item",
    "normalize_product",
    "normalize_receipt",
    "parse_meijer_item",
]
