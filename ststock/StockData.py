
import requests
import ast
import pandas as pd
import datetime as datetime
import numpy as np
import json
import re
import time
import os

from utils.logger import get_logger

MAIN_URL = "https://dchart-api.vndirect.com.vn/dchart/history"
TIME_DELTA = 900
TIME_FROM = '2024-1-1'
TIME_TO = '2026-3-24'
logger = get_logger(__name__)

class StockData:
    def __init__(self):
        # 2. KIỂM TRA VÀ TỰ ĐỘNG TẠO THƯ MỤC (Nếu chưa có)
        # Tham số exist_ok=True giúp code không bị lỗi nếu thư mục đã tồn tại từ trước
        os.makedirs(".//backup//1D", exist_ok=True)
        # os.makedirs(".//backup//1H", exist_ok=True)
        # os.makedirs(".//backup//5", exist_ok=True)
        self.allData = {}

    def _pull_data_from_web(self, syb, resl = '1D', timefrom = 0, timeTo = int(round(datetime.datetime.timestamp(datetime.datetime.now())))):
        try:
            url = MAIN_URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Referer': 'https://dchart.vndirect.com.vn/'
            }
            
            parameters = {
                'resolution': resl,
                'symbol': syb,
                'from' : timefrom,
                'to' : timeTo
                }
            response = requests.get(url, params = parameters, headers=headers)
            # Kiểm tra xem request có thành công không (Status code 200)
            if response.status_code == 200:
                content = response.content
                stock_data = ast.literal_eval(content.decode('utf-8'))
                
                if resl == '1D':
                    formatStrTime = "%Y/%m/%d"
                else:
                    formatStrTime = "%Y/%m/%d %H:%M"
                datestr = [datetime.datetime.fromtimestamp(i).strftime(formatStrTime) for i in stock_data['t']]
                data = pd.DataFrame({#'Index': np.arange(1, len(stock_data['o']) + 1),
                                            'Date': pd.to_datetime(datestr),
                                            'Open': stock_data['o'],
                                            'High': stock_data['h'],
                                            'Low': stock_data['l'],
                                            'Close': stock_data['c'],
                                            'Volume': stock_data['v']})
                data.index = [i for i in range(len(data))]
                logger.debug(f"{syb} Lấy dữ liệu thành công from web!")
                return data
            else:
                logger.debug(f"Lỗi hệ thống: Status code {response.status_code}")
                logger.debug(response.text)
            
        except:
            logger.debug(syb + ' Error connection')
            return pd.DataFrame()

    def _pull_data(self, syb, iResl, dTimeFrom):
        data = pd.DataFrame()
        today = int(round(datetime.datetime.timestamp(datetime.datetime.now())))
        # today = int(datetime.datetime.strptime(TIME_TO, '%Y-%m-%d').timestamp())
        
        dTimeTo = dTimeFrom + datetime.timedelta(TIME_DELTA)

        iTimeFrom = int(round(datetime.datetime.timestamp(dTimeFrom)))
        iTimeTo = int(round(datetime.datetime.timestamp(dTimeTo)))

        while True:
            if iTimeTo > today:
                iTimeTo = today
            dataSeason = pd.DataFrame()

            # while(dataSeason.empty):
            dataSeason = self._pull_data_from_web(syb, resl = iResl, timefrom = iTimeFrom, timeTo = iTimeTo)
            
            if data.empty:
                data = dataSeason
            else:
                # data = data.append(dataSeason)
                data = pd.concat([data, dataSeason], ignore_index=True)

            if iTimeTo == today:
                break
            
            dTimeFrom = dTimeTo
            dTimeTo = dTimeFrom + datetime.timedelta(TIME_DELTA)
            iTimeFrom = int(round(datetime.datetime.timestamp(dTimeFrom)))
            iTimeTo = int(round(datetime.datetime.timestamp(dTimeTo)))
        return data

    def get_data(self, syb, resl = '1D'):
        dTimeFrom = datetime.datetime.strptime(TIME_FROM, "%Y-%m-%d")

        try:
            data = pd.read_csv('.//backup//' + resl + '//' + '//' + syb + '.csv', index_col = 0, parse_dates = ['Date'], date_format='%Y-%m-%d')
            data.index = [i for i in range(len(data))]
        except:
            data = pd.DataFrame()
        
        if data.empty:
            print("Data empty, pulling from web...")
            data = self._pull_data(syb, resl, dTimeFrom)
            data.to_csv('.//backup//' + resl + '//' + '//' + syb + '.csv', index=True, encoding='utf-8')
            data.index = [i for i in range(len(data))]

        self.allData[syb] = data

    def update_data(self, syb, resl = '1D'):
        index = self.allData[syb].index[-1]

        dTimeFrom = pd.Timestamp(self.allData[syb].at[index, 'Date']).to_pydatetime()
        dataNew = self._pull_data(syb, resl, dTimeFrom)

        for dd in dataNew['Date'].to_numpy(): 
            d = pd.to_datetime(str(dd)).strftime('%Y-%m-%d')
            self.allData[syb].drop(self.allData[syb].loc[self.allData[syb]['Date'] == d].index, inplace=True)

        self.allData[syb] = pd.concat([self.allData[syb], dataNew], ignore_index=True)
        self.allData[syb]['Date'] =  [pd.to_datetime(i).strftime('%Y-%m-%d') for i in self.allData[syb]['Date'].to_numpy()]

        self.allData[syb].index = [i for i in range(len(self.allData[syb]))]
        
        # Lưu dữ liệu cập nhật vào CSV
        # self.allData[syb].to_csv('.//backup//' + resl + '//' + '//' + syb + '.csv', index=True, encoding='utf-8')