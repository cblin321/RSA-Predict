from Future_Scraper import Future_Scraper
from model import Classifier
from Selenium_Scraper import Selenium_Scraper
from SA_Scraper import SA_Scraper

split_scraper = Future_Scraper()
df = split_scraper.update_splits()
df.to_csv("reverse_splits.csv", index = False)

filing_scraper = Selenium_Scraper()
df = filing_scraper.update_filings()
df.to_csv("full_data.csv", index = False)

# filing_scraper = SA_Scraper()
# df = filing_scraper.scrape_filings("full_data.csv")
# df.to_csv("temp.csv", index = False)


model = Classifier()
model.train_model()

# upcoming_df = model.transform_upcoming(retrain = True)
# current_df = model.transform_current(retrain = True) 

