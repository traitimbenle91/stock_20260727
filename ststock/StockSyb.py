from pathlib import Path

import pandas as pd
import requests

from utils.logger import get_logger

URL = "https://api-finfo.vndirect.com.vn/v4/stocks?q=type:IFC,ETF,STOCK~status:LISTED&fields=code,companyName,companyNameEng,shortName,floor,industryName&size=3000"
CSV_PATH = Path(__file__).resolve().parent.parent / "backup" / "sybs.csv"
logger = get_logger(__name__)

class StockSyb:
    def __init__(self):
        self.total_sybs = 0
        self.sybs = pd.DataFrame(
            columns=["syb", "companyName", "floor", "shortName", "companyNameEng"]
        )

    def _build_dataframe(self, data):
        return pd.DataFrame(
            [
                {
                    "syb": item.get("code", ""),
                    "companyName": item.get("companyName", ""),
                    "floor": item.get("floor", ""),
                    "shortName": item.get("shortName", ""),
                    "companyNameEng": item.get("companyNameEng", ""),
                }
                for item in data
            ]
        )

    def _load_from_local_csv(self):
        if not CSV_PATH.exists():
            return False

        self.sybs = pd.read_csv(CSV_PATH)
        self.total_sybs = len(self.sybs)
        logger.debug(f"Đọc dữ liệu local thành công! total_sybs = {self.total_sybs}")
        logger.debug(f"sybs(local) rows = {len(self.sybs)}")
        if not self.sybs.empty:
            logger.debug(f"sybs(local) preview:\n{self.sybs.head(5).to_string(index=False)}")
        return True

    def _fetch_from_web_and_save_csv(self):
        response = requests.get(URL, timeout=30)

        if response.status_code != 200:
            logger.debug(f"Lỗi hệ thống: Status code {response.status_code}")
            return False

        payload = response.json()
        data = payload.get("data", [])

        self.sybs = self._build_dataframe(data)
        self.total_sybs = payload.get("totalElements", len(self.sybs))
        logger.debug(f"sybs(web) rows = {len(self.sybs)}")
        if not self.sybs.empty:
            logger.debug(f"sybs(web) preview:\n{self.sybs.head(15).to_string(index=False)}")

        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.sybs.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

        logger.debug(f"Lấy dữ liệu web thành công! total_sybs = {self.total_sybs}")
        return True

    def get_list_sybs(self, force_web=False):
        try:
            logger.debug(f"get_list_sybs(force_web={force_web})")
            if not force_web:
                if self._load_from_local_csv():
                    logger.debug("get_list_sybs -> return sybs từ local csv")
                    return self.sybs

            if self._fetch_from_web_and_save_csv():
                logger.debug("get_list_sybs -> return sybs từ web")
                return self.sybs
        except Exception as e:
            logger.debug(f"Lỗi: {e}")

        return self.sybs
