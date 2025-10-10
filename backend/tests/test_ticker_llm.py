import os
import sys
import logging

# Ensure project root is on sys.path when running this file directly
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, os.pardir, os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend import profile_processor_agent as p

def test_llm_parse_specific_assets():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting test_llm_parse_specific_assets")
    tickers, asset_classes = p.llm_parse_specific_assets("appple, tesla, pear")
    logger.info("Result tickers=%s asset_classes=%s", tickers, asset_classes)
    print({"tickers": tickers, "asset_classes": asset_classes})

if __name__ == "__main__":
    # Allow running the test file directly for quick debugging
    test_llm_parse_specific_assets()