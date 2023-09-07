from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import pandas as pd
from datetime import datetime
from selenium.webdriver.common.by import By
import yfinance as yf
import numpy as np
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import re 
import datetime

class Future_Scraper:
    def __init__(self):
        temp = 1
    
    def scrape_splits(self):
        service = Service()
        dates = []
        tickers = []
        ratios = []
        names = []
        driver = webdriver.Firefox(service = service)
        driver.implicitly_wait(20)
        driver.get("https://dilutiontracker.com/app/reverse-split?a=604e16")
        splits = driver.find_elements(By.XPATH, '//table[@class="table"]//tbody/tr')
        for s in splits:
            fields = s.find_elements(By.XPATH, "./*")
            date = fields[1].text
            ticker = fields[0].text
            ratio = fields[2].text
            status = fields[4].text
            if ticker == "Symbol":
                continue
            if date == "" or status == "Vote Approved":
                continue
            dates.append(date)
            tickers.append(ticker)
            if "to" in ratio:
                ratio = ratio.replace("to", "for")
            else:
                ratio = "1 for " + ratio
            ratios.append(ratio)
            print(ticker)
            name = ""
            try:
                name = yf.Ticker(ticker).info["longName"]
            except:
                name = np.nan
                print(f"No longName for {ticker}")
            names.append(name)
        driver.quit()
        return pd.DataFrame(data = {"date" : dates, "ticker" : tickers, "ratio" : ratios, "name" : names})

    def update_splits(self):
        service = Service()
        driver = webdriver.Firefox(service = service)
        driver.implicitly_wait(20)
        df = pd.read_csv("reverse_splits.csv")
        tickers = []
        dates = []
        names = []
        ratios = []
        df["date"] = pd.to_datetime(df["date"])
        name_date = set([(row["date"], row["ticker"]) for i, row in df.iterrows()]) #get all unique splits (all unique combos of date & ticker)
        df = df.dropna(axis = "rows", subset = "ticker") #drop null values since we might get to pick them back up
        driver.implicitly_wait(20)
        driver.get("https://dilutiontracker.com/app/reverse-split?a=604e16")
        splits = driver.find_elements(By.XPATH, '//table[@class="table"]//tbody/tr')
        earliest_split = datetime.datetime(2023, 6, 1)
        for s in splits:
            fields = s.find_elements(By.XPATH, "./*")
            date = fields[1].text
            ticker = fields[0].text
            status = fields[4].text
            if date == "" or status == "Vote Approved":
                continue
            if ticker == "Symbol":
                continue
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
            ratio = fields[2].text
            if date < earliest_split:
                print(f"{(date, ticker)} is before earliest known RSRU")
                break
            if ((date, ticker) not in name_date):
                dates.append(date)
                tickers.append(ticker)
                if "to" in ratio:
                    ratio = ratio.replace("to", "for")
                else:
                    ratio = "1 for " + ratio
                ratios.append(ratio)
                print(ticker)
                name = ""
                try:
                    name = yf.Ticker(ticker).info["longName"]
                except:
                    name = np.nan
                    print(f"No longName for {ticker}")
                names.append(name)
            else:
                print(f"{(date, ticker)} is already in the dataset")
                # break
        df2 = pd.DataFrame(data = {"date" : dates, "ticker": tickers, "name": names, "ratio" : ratios})
        df = pd.concat([df, df2], ignore_index = True)
        driver.quit()
        return df

            

#https://dilutiontracker.com/app/reverse-split?a=604e16