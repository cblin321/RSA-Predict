from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime
from selenium.webdriver.common.by import By
import yfinance as yf
import numpy as np
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
import time
from bs4 import BeautifulSoup
import requests
import configparser
import string
class SA_Scraper:
    
    def __init__(self):
        parser = configparser.ConfigParser()
        parser.read("config.ini")
        SA_KEY = parser["SA"]["api_key"]
        self.headers = {
            "X-RapidAPI-Key": SA_KEY,
            "X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com"
        }
            
    def clean_text(self, text):
        if pd.isnull(text):
            return text
        
        cleaned_name = ''.join(char for char in text if char.isalnum() or char.isspace() or char in string.punctuation)
        # text = re.sub('\s+', ' ', text)   
        # # Remove special characters
        # text = re.sub('[^A-Za-z0-9 ]+', '', text)
        
        return cleaned_name
        
    #fills in missing values that the selenium scraper didn't find    
    def scrape_filings(self, file_name):
        df = pd.read_csv(file_name, encoding='latin-1')
        # df["filings"] = df["filings"].astype(str)
        # df = df[df["filings"] == "nan"]
        url = "https://seeking-alpha.p.rapidapi.com/press-releases/v2/list"
        df["date"] = pd.to_datetime(df["date"])
        keywords = set(["combination", "split", "consolidation", "ratio change"])
        completed_words = set(["complete", "announce", "effect", "implement", "conduct"])
        filings = []
        unfinished = []
        for i, row in df.iterrows():
            if pd.isnull(row["filings"]):
                exec_date = pd.to_datetime(row["date"])
                until = int((exec_date + pd.DateOffset(months = 1)).timestamp()) #upper bound on the dates we search
                since = int((exec_date - pd.DateOffset(months = 3)).timestamp()) #lower bound on the dates we search
                querystring = {"id":row["ticker"], "since" : since, "unti" : until, "size" : 40}
                news = requests.get(url, params = querystring, headers = self.headers)
                count = 0
                while news.status_code != 200 and count < 10:
                    news = requests.get(url, params = querystring, headers = self.headers)
                    count += 1
                    time.sleep(15)
                if count == 9:
                    # filings.append(np.nan)
                    print("Failed to get a response from API, appending after missing value")
                    continue
                link = "https://seekingalpha.com"
                filing = ""
                flag = False
                # print(news.json())
                if len(news.json()["data"]) == 0:
                    # filings.append(np.nan)
                    print("No results found")
                    continue
                #loop thru all headlines in the post list
                news = news.json()["data"]
                for j, article in enumerate(news):
                    print(article["attributes"]["title"].strip().lower())
                    if article["attributes"]["title"] == "AnPac Bio Announces Plan to Implement ADS Ratio Change":
                        print("ratio change" in article["attributes"]["title"])
                        print("implement" in article["attributes"]["title"])
                    #loop thru both lists to see if any given combinations of keywords is in the headline
                    for word in keywords:
                        completed = False
                        if word in article["attributes"]["title"].strip().lower():
                            for word2 in completed_words:
                                if word2 in article["attributes"]["title"].strip().lower():
                                    #get the link and use bs4 to parse
                                    link += article["links"]["self"]
                                    completed = True
                                    break
                            if completed:
                                break
                    if completed:
                        break
                #if there's no headline that fits we skip
                if j == len(news) - 1 and link == "https://seekingalpha.com":
                    # filings.append(np.nan)
                    print("No filings found")
                    continue
                #parse article w/ bs4 and requests
                html = requests.get(link).text
                soup = BeautifulSoup(html, "lxml")
                paragraphs = soup.find_all("p")
                for p in paragraphs:
                    #seeing about and the company name should prevent getting some unecessary data
                    if "about " + yf.Ticker(row["ticker"]).info["longName"] in p.text.strip().lower():
                        break
                    #ideally we stop at "about," but it's difficult to find the 1st "about"
                    if "forward-looking" in p.text.strip().lower() or "forward looking" in p.text.strip().lower():
                        break
                    filing += p.text
                df.at[i, "filings"] = self.clean_text(filing)
                # filings.append(filing)
                print(f"ADDED TO DS: {article['attributes']['title']} {filing}")
                time.sleep(2)
            else:
                print(f"{row['ticker']} already has a filing")
                # filings.append(row["filings"])
        # df["filings"] = filings
        return df
                