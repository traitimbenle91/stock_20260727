import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

class StockDataManager:

    def __init__(self):
        # symbols: dict[int, list[str]] -> {code: [syb1, syb2, ...]}
        self.symbols: dict = {}

    def load_symbols(self, filepath="backup/syb_scan.csv", default=None, sybs=None):
        """Load danh sách symbols từ CSV, trả về dict {code: [sybs]}."""
        if sybs is not None:
            return

        try:
            df = pd.read_csv(filepath)
            df["syb"] = df["syb"].astype(str).str.strip().str.upper()
            if "code" in df.columns:
                df["code"] = df["code"].astype(int)
                grouped: dict = {}
                for _, row in df.iterrows():
                    code = int(row["code"])
                    grouped.setdefault(code, []).append(row["syb"])
                self.symbols = grouped
            else:
                self.symbols = {0: df["syb"].tolist()}
        except Exception as e:
            logger.error(f"Error loading symbols from {filepath}: {e}")
            self.symbols = {0: (default if default is not None else ["CTG", "PFL", "VCT"])}


def flatten_symbols(symbol_groups: dict[int, list[str]]) -> list[tuple[int, str]]:
    """Flatten {code: [symbol]} thành [(code, symbol), ...] theo đúng thứ tự file CSV."""
    return [(code, symbol) for code, symbols in symbol_groups.items() for symbol in symbols]