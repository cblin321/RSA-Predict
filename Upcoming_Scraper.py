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
class Upcoming:
    def __init__(self):
        temp = 1
        
    def scrape_splits(self):
        service = Service()
        driver = webdriver.Firefox(service = service)
        driver.implicitly_wait(20)
        driver.get("https://www.nasdaqtrader.com/Trader.aspx?id=archiveheadlines&cat_id=105")
        df = pd.read_csv("reverse_splits.csv")
        companies = driver.find_elements(By.XPATH, '//div[@class="genTable"]/table/tbody//tr')
        tickers = []
        split_dates = []
        names = []
        ratios = []
        df["date"] = pd.to_datetime(df["date"])
        name_date = set([(row["date"], row["ticker"]) for i, row in df.iterrows()]) #get all unique splits (all unique combos of date & ticker)
        df = df.dropna(axis = "rows", subset = "ticker") #drop null values since we might get to pick them back up
        for c in companies:
            fields = c.find_elements(By.XPATH, "./*")
            date = fields[0].text
            headline = fields[3].text.lower()
            if ("reverse stock split" in headline): 
                ticker = re.search('\([a-z]+\)', headline)
                if not ticker:
                    print(f"No ticker found for {headline}")
                    continue
                split_dates.append(date)
                ticker = ticker.group().upper()
                tickers.append(ticker)
                # print(type(headline))
                driver.execute_script("arguments[0].scrollIntoView();", fields[3])
                time.sleep(5)
                headline.click()
                driver.switch_to.window(driver.window_handles[1])
                content = driver.find_element(By.XPATH, '//div[@class="genTableNews"]//p')
                ratio = re.search('\([0-9]+-[0-9]+\)')
                if not ratio:
                    print(f"No ratio for found {headline}")
                    ratios.append(np.nan)
                ratio = ratio.group()
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            else:
                print(f"Not a RS: {headline}")
            # print(date)
        driver.quit()
        
    #scrapes all upcoming splits
    def update_splits(self):
        service = Service()
        driver = webdriver.Firefox(service = service)
        driver.implicitly_wait(20)
        driver.get("https://hedgefollow.com/upcoming-stock-splits.php")
        df = pd.read_csv("reverse_splits.csv")
        companies = driver.find_elements(By.XPATH, '//*[@id="dg"]//tbody//tr')
        tickers = []
        split_dates = []
        names = []
        ratios = []
        df["date"] = pd.to_datetime(df["date"])
        name_date = set([(row["date"], row["ticker"]) for i, row in df.iterrows()]) #get all unique splits (all unique combos of date & ticker)
        df = df.dropna(axis = "rows", subset = "ticker") #drop null values since we might get to pick them back up
        for c in companies:
            fields = c.find_elements(By.XPATH, "./*")
            ticker = fields[0].get_attribute("data-val")
            ratio = fields[3].get_attribute("data-val")
            date = datetime.strptime(fields[4].get_attribute("data-val"), "%Y-%m-%d") 
            if ((date, ticker) not in name_date):
                if (float(ratio.split(":")[0]) < float(ratio.split(":")[1])):
                    tickers.append(ticker)
                    split_dates.append(date)
                    names.append(fields[2].get_attribute("data-val"))
                    ratios.append(ratio)
            else:
                print(f"{(date, ticker)} is already in the dataset")
                break
        df2 = pd.DataFrame(data = {"date" : split_dates, "ticker": tickers, "name": names, "ratio" : ratios})
        # df = df.drop(columns=["cik"])
        df = pd.concat([df, df2], ignore_index = True)
        driver.quit()
        return df
    
    # def test(self):
    #     service = Service()
    #     driver = webdriver.Firefox(service = service)
    #     driver.implicitly_wait(20)
    #     driver.get("https://hedgefollow.com/upcoming-stock-splits.php")
    #     companies = driver.find_elements(By.XPATH, '//*[@id="dg"]//tbody//tr')
    #     tickers = []
    #     split_dates = []
    #     names = []
    #     ratios = []
    #     for c in companies:
    #         fields = c.find_elements(By.XPATH, "./*")
    #         ratio = fields[3].get_attribute("data-val")
    #         if (float(ratio.split(":")[0]) < float(ratio.split(":")[1])):
    #             ticker = fields[0].get_attribute("data-val")
    #             date = datetime.strptime(fields[4].get_attribute("data-val"), "%Y-%m-%d") 
    #             print(f"company: {ticker} ratio: {ratio} date {date}")
        
        