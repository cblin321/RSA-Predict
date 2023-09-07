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
import timedelta
import re
import string
class Selenium_Scraper:
    #constructor, initializes webdriver
    def __init__(self):
        temp = 1
        
    #scrapes all reverse splits on stockanalysis.com has a comprehensive list going 1 year back
    #returns a pandas df of all reverse splits going a year back
    def scrape_splits(self):
        tickers = []
        split_dates = []
        names = []
        ratio = []
        service = Service()
        driver = webdriver.Firefox(service = service)
        driver.get("https://stockanalysis.com/actions/splits")
        companies = self.driver.find_elements(By.XPATH, '//tbody[@class = "svelte-1jtwn20"]/*') #finds all companies that have split in the table 
        for company in companies:
            type = company.find_elements(By.XPATH, "./*")[3].text #what kind of split
            if type == "Reverse":
                try:
                    tickers.append(company.find_element(By.XPATH, ".//a").text)
                    names.append(yf.Ticker(company.find_element(By.XPATH, ".//a").text).info["longName"]) #use the ticker to lookup the official name of the company thru yf api
                except:
                    for element in company.find_elements(By.XPATH, "./*"): #if something went wrong we print the name of the company for logging
                        print(element.text)
                    continue
                split_dates.append(company.find_elements(By.XPATH, "./*")[0].text) #appends the date to the list
                ratio.append(company.find_elements(By.XPATH, "./*")[-1].text) #appends the split ratio, like a 1:17, etc
        return pd.DataFrame(data = {"name": names, "ticker" : tickers, "date" : split_dates, "ratio" : ratio}) 
    
    #appends splits to an already existing csv
    #returns the old splits + updated ones
    def update_splits(self):
        tickers = []
        split_dates = []
        names = []
        ratio = []
        service = Service()
        driver = webdriver.Firefox(service = service)
        df = pd.read_csv("reverse_splits.csv")
        df = df.drop(columns= ["filings2", "cik", "Unnamed: 0"])
        df["date"] = pd.to_datetime(df["date"], format="mixed")
        name_date = set([(row["date"], row["ticker"]) for i, row in df.iterrows()]) #get all unique splits (all unique combos of date & ticker)
        df = df.dropna(axis = "rows", subset = "ticker") #drop null values since we might get to pick them back up
        driver.get("https://stockanalysis.com/actions/splits")
        companies = driver.find_elements(By.XPATH, '//tbody[@class = "svelte-1jtwn20"]/*') #gets a table of all companiues that have gone thru splits
        for company in companies:
            type = company.find_elements(By.XPATH, "./*")[3].text #type of split
            try: 
                if (datetime.strptime(company.find_elements(By.XPATH, "./*")[0].text, "%b %d, %Y"),  company.find_element(By.XPATH, ".//a").text) not in name_date: #we check to see if we have this combo of ticker and date in the ds already
                    if type == "Reverse":
                        tickers.append(company.find_element(By.XPATH, ".//a").text)
                        names.append(yf.Ticker(company.find_element(By.XPATH, ".//a").text).info["longName"])
                        split_dates.append(company.find_elements(By.XPATH, "./*")[0].text)
                        ratio.append(company.find_elements(By.XPATH, "./*")[-1].text)
                else:
                    print(f"{company.find_element(By.XPATH, './/a').text} {datetime.strptime(company.find_elements(By.XPATH, './*')[0].text, '%b %d, %Y')} already in DS")
                    break
            except:
                for element in company.find_elements(By.XPATH, "./*"): #print the element that caused the error
                    print(element.text)
        driver.quit()
        df2 = pd.DataFrame(data = {"name": names, "ticker" : tickers, "date" : split_dates, "ratio" : ratio}) #a df of all the new splits
        df = pd.concat([df, df2], ignore_index = True) #combine the previous splits with new ones
        return df
        
    #takes in a csv of tickers and dates, and finds the filings associated with them
    #returns the original df with a column of filings included
    def scrape_filings(self):
        df = pd.read_csv("reverse_splits.csv", encoding='latin-1') #this will be whatever is returned by scrape_splits
        service = Service()
        driver = webdriver.Firefox(service = service)
        driver.implicitly_wait(8)
        df["date"] = pd.to_datetime(df["date"], format= "mixed")
        keywords = set(["combination", "split", "consolidation"]) #these are some words that indicate a reverse split
        completed_words = set(["complete", "announce", "effect", "implement"]) #these are some words that indicate the company is executing the split
        filings = []
        unfinished = []
        curr_date = ""
        for i, row in df.iterrows():
            try:
                driver.get(f"https://finviz.com/quote.ashx?t={row['ticker']}&p=d")
            except: #this means that there was some issue with the driver or site, we try the next ticker in that case
                filings.append(np.nan) 
                unfinished.append((row, i))
                continue
            new = ""
            try:
                news = driver.find_element(By.ID, "news-table") #this is a table of headlines
            except:
                print(f"No results found for {row['ticker']}") #typically this means that finviz doesn't have this ticker available
                filings.append(np.nan)
                continue
            curr_date = ""
            print(len(news.find_elements(By.XPATH, ".//tr"))) #prints the # of headlines associated with this compnay
            for j, headline in enumerate(news.find_elements(By.XPATH, ".//tr")): #look thru the table of headlines
                driver.implicitly_wait(20)
                filing = ""
                date = headline.find_elements(By.XPATH, "./*")[0]
                title = ""
                try:
                    title = headline.find_element(By.XPATH, './/a').text.strip()
                except:
                    continue
                if len(date.text.split()) > 1: #when this is not the case the date will just be a time, like 10:30 AM this means that the article was posted in the same day
                    curr_date = datetime.strptime(date.text.split()[0], "%b-%d-%y") #since the date is more thant just a time, we know to update the date
                    #print(curr_date)
                for word in keywords:
                    completed = False
                    #print(headline.find_element(By.XPATH, './/a').text)
                    #we try all combinations of the keywords and completed words to identify reverse splits only
                    if row["date"] >= curr_date and word in headline.find_element(By.XPATH, './/a').text.lower().strip():
                        for word2 in completed_words:
                            if word2 in headline.find_element(By.XPATH, './/a').text.lower().strip():
                                #time.sleep(5)
                                driver.execute_script("arguments[0].scrollIntoView();", headline) 
                                driver.execute_script("arguments[0].click();", headline.find_element(By.XPATH, './/a'))  
                                completed = True 
                                break 
                        if completed:
                            break
                time.sleep(5)
                if len(driver.window_handles) < 2: #this means that we were unable to find a valid split 
                    print("Unable to find RS for: " + row["ticker"] + " " + headline.find_element(By.XPATH, './/a').text.lower().strip()) #print for logging
                    if j ==  len(news.find_elements(By.XPATH, ".//tr")) - 1: #if we're on the last headline append nan and move on
                        filings.append(np.nan)
                    continue
                driver.switch_to.window(driver.window_handles[1]) #switch to the YF page
                if "yahoo" not in driver.current_url: #in the rare case this is not YF link we record it and close the tab
                    print(driver.current_url)
                    filings.append(np.nan)
                    unfinished.append((row, i))
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    break
                try:
                    #click the story continues button to reveal the whole article
                    read_more = driver.find_element(By.XPATH, '//button[text()="Story continues"]') 
                    driver.execute_script('arguments[0].scrollIntoView();', read_more)
                    driver.execute_script('arguments[0].click();', read_more)
                except:
                    print("Read more not found on yf, continuing as per usual")
                article = driver.find_elements(By.XPATH, '//div[@class="caas-body"]/p') #all p tags make up the whole article
                for paragraph in article:
                    driver.implicitly_wait(5)
                    #look for bold text within any paragraph, this will typically indicate the end of the article (forward looking statements or info abt the company)
                    bold_text = paragraph.find_elements(By.XPATH, './/b') 
                    strong_text = paragraph.find_elements(By.XPATH, ".//strong")
                    flag = False
                    if bold_text:
                        curr = ""
                        for bold in bold_text:
                            curr += bold.text
                            if "About" in curr or "Forward-looking" in curr:
                                print(curr)
                                flag = True #indicate we found the end of the article
                    if strong_text:
                        curr = ""
                        for bold in strong_text:
                            curr += bold.text
                            if "About" in curr or "Forward-looking" in curr:
                                print(curr)
                                flag = True #indicate we found the end of the article
                    if flag:
                        break
                    filing += paragraph.text #add the current paragraph's text to the filing
                filings.append(filing)
                print(f"ADDED TO DS: {title} {filing}")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                break
        driver.quit()
        df["filings"] = filings
        return df
    
    def clean_text(self, text):
        if pd.isnull(text):
            return text
        
        cleaned_name = ''.join(char for char in text if char.isalnum() or char.isspace() or char in string.punctuation)
        # text = re.sub('\s+', ' ', text)
        
        # # Remove special characters
        # text = re.sub('[^A-Za-z0-9 ]+', '', text)
        
        return cleaned_name
    
    #updates the current dataset with all filings up to now
    #returns the updated df
    def update_filings(self):
        df = pd.read_csv("full_data.csv", encoding='latin-1') #this is a set of reverse splits (we assume it's the unupdated dataset)
        service = Service()
        driver = webdriver.Firefox(service = service)
        driver.implicitly_wait(8)
        # data = self.update_splits() #this should be all reverse splits not in the dataset
        data = pd.read_csv("reverse_splits.csv") 
        # data["date"] = pd.to_datetime(data["date"], format = "mixed")
        data["date"] = pd.to_datetime(data["date"])
        # df["date"] = pd.to_datetime(df["date"], format = "mixed")
        df["date"] = pd.to_datetime(df["date"])
        df["filings"] = df["filings"].apply(lambda x : self.clean_text(x))
        keywords = set(["combination", "split", "consolidation", "ratio change"])
        completed_words = set(["complete", "announce", "effect", "implement", "conduct"])
        filings = []
        unfinished = []
        curr_date = ""
        new_data = data[~(data["ticker"].isin(df["ticker"]) & data["date"].isin(df["date"]))]
        for i, row in new_data.iterrows():
            try:
                driver.get(f"https://finviz.com/quote.ashx?t={row['ticker']}&p=d")
            except:
                filings.append(np.nan)
                unfinished.append((row, i))
                continue
            new = ""
            try:
                news = driver.find_element(By.ID, "news-table")
            except:
                print(f"No results found for {row['ticker']}")
                filings.append(np.nan)
                continue
            curr_date = ""
            print(len(news.find_elements(By.XPATH, ".//tr")))
            for j, headline in enumerate(news.find_elements(By.XPATH, ".//tr")):
                driver.implicitly_wait(20)
                filing = ""
                date = headline.find_elements(By.XPATH, "./*")[0]
                title = ""
                try:
                    title = headline.find_element(By.XPATH, './/a').text.strip()
                except:
                    continue
                if len(date.text.split()) > 1:
                    curr_date = datetime.strptime(date.text.split()[0], "%b-%d-%y")
                    #print(curr_date)
                for word in keywords:
                    completed = False
                    #print(headline.find_element(By.XPATH, './/a').text)
                    #19th row[date] 21st curr_date
                    #
                    if (row["date"] - timedelta.Timedelta(days = 14) <= curr_date and row["date"] + timedelta.Timedelta(days = 14) >= curr_date)  and word in headline.find_element(By.XPATH, './/a').text.lower().strip():
                        for word2 in completed_words:
                            if word2 in headline.find_element(By.XPATH, './/a').text.lower().strip():
                                #time.sleep(5)
                                driver.execute_script("arguments[0].scrollIntoView();", headline)
                                driver.execute_script("arguments[0].click();", headline.find_element(By.XPATH, './/a'))
                                completed = True
                                break
                        if completed:
                            break
                time.sleep(5)
                if len(driver.window_handles) < 2:
                    print(row["ticker"] + " " + headline.find_element(By.XPATH, './/a').text.lower().strip())
                    if j ==  len(news.find_elements(By.XPATH, ".//tr")) - 1:
                        filings.append(np.nan)
                    continue
                driver.switch_to.window(driver.window_handles[1])
                if "yahoo" not in driver.current_url:
                    print(driver.current_url)
                    filings.append(np.nan)
                    unfinished.append((row, i))
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    break
                try:
                    read_more = driver.find_element(By.XPATH, '//button[text()="Story continues"]')
                    driver.execute_script('arguments[0].scrollIntoView();', read_more)
                    driver.execute_script('arguments[0].click();', read_more)
                except:
                    print("Read more not found on yf, continuing as per usual")
                article = driver.find_elements(By.XPATH, '//div[@class="caas-body"]/p')
                for paragraph in article:
                    driver.implicitly_wait(5)
                    bold_text = paragraph.find_elements(By.XPATH, './/b')
                    strong_text = paragraph.find_elements(By.XPATH, ".//strong")
                    flag = False
                    if bold_text:
                        curr = ""
                        for bold in bold_text:
                            curr += bold.text
                            if "About" in curr or "Forward-looking" in curr:
                                print(curr)
                                flag = True
                    if strong_text:
                        curr = ""
                        for bold in strong_text:
                            curr += bold.text
                            if "About" in curr or "Forward-looking" in curr:
                                print(curr)
                                flag = True
                    if flag:
                        break
                    filing += paragraph.text
                filings.append(filing)
                print(f"ADDED TO DS: {title} {filing}")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                break    
        driver.quit()
        new_data["filings"] = filings
        df = pd.concat([df, new_data], ignore_index = True)
        return df  