from flask import Flask, render_template, url_for
import pandas as pd
import re
from datetime import date
import string
from datetime import datetime
from Future_Scraper import Future_Scraper
from model import Classifier
from Selenium_Scraper import Selenium_Scraper
from SA_Scraper import SA_Scraper
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
# Set the SERVER_NAME and APPLICATION_ROOT
# SERVER_NAME = '127.0.0.1:5000'
app.config['SERVER_NAME'] = '127.0.0.1:5000'  # Change this to your server's address
app.config['APPLICATION_ROOT'] = '/'

# # PREFERRED_URL_SCHEME should match your deployment (http or https)
app.config['PREFERRED_URL_SCHEME'] = 'http'  # Change to 'https' if using HTTPS

#TODO add links for all filings, make a navbar, split current/upcoming and past into seperate pages
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upcoming")
def upcoming():
    return render_template("upcoming.html", table = upcoming_df)

@app.route("/current")
def current():
    return render_template("current.html", table = current_df)

@app.route("/past")
def past():
    return render_template("past.html", table = training)

#id is in the form "ticker:date"
@app.route('/filing/<id>')
def get_filing(id):
    return render_template("filing.html", ticker = id.split(":")[0], content = fetch_filings(id), date = id.split(":")[1])
    
    
def fetch_filings(id):
    ticker = id.split(":")[0]
    date = pd.to_datetime(id.split(":")[1])
    temp = df[(df["date"] == date) & (df["ticker"] == ticker)]
    return temp.iloc[0]["filings"]

def create_link(row):
    return f'<a href="{app.config["PREFERRED_URL_SCHEME"]}://{app.config["SERVER_NAME"]}{app.config["APPLICATION_ROOT"]}filing/{row["ticker"]}:{row["date"].strftime("%Y-%m-%d")}">{row["ticker"]} RS Filing</a>'
    
curr_date = date.today()
df = pd.read_csv("full_data.csv", encoding='latin-1')
ru = pd.read_csv("Roundups.csv")
ru = ru.dropna()
df = df.drop(columns=["filings2", "cik", "Unnamed: 0"])
df["filings"] = df["filings"].astype(str)
df["filings"] = df["filings"].apply(lambda x : re.sub('[^A-Za-z0-9\s]+', '', x))
df["round_up"] = df.apply(lambda x : 1 if x["ticker"] in ru["ticker"].unique() else 0, axis = 1)
df["date"] = pd.to_datetime(df["date"])
current = df[df["date"].apply(lambda x : x.day == curr_date.day and x.month == curr_date.month and x.year == curr_date.year)]
upcoming = df[df["date"].apply(lambda x : pd.Timestamp(x) > pd.Timestamp(curr_date))]
training = df.drop(current.index)
training = df.drop(upcoming.index)
training["links"] = training.apply(create_link, axis = 1)
model = Classifier()

upcoming_df = model.transform_upcoming()
current_df = model.transform_current() 

# print(upcoming_df.dtypes)
print(current.columns)

if upcoming_df.shape[0] > 0:
    upcoming_df["links"] = df.apply(create_link, axis = 1)
    upcoming_df["round up?"] = upcoming_df["round up?"].astype(int)
else:
    upcoming_df["round up?"] = ""

if current_df.shape[0] > 0:
    current_df["round up?"] = current_df["round up?"].astype(int)
    current_df["links"] = current_df.apply(create_link, axis = 1)
else:
    current_df["round up?"] = ""
    current_df = current_df.drop(columns = ["round_up"])
    
training["round_up"] = training["round_up"].astype(int)

upcoming_df["round up?"] = upcoming_df["round up?"].replace({0 : "No", 1 : "Yes"})
current_df["round up?"] = current_df["round up?"].replace({0 : "No", 1 : "Yes"})
training["round_up"] = training["round_up"].replace({0 : "No", 1 : "Yes"})
training = training.rename({"round_up" : "round up?"})

upcoming_df = upcoming_df.drop(columns = ["filings"])
upcoming_df = upcoming_df.rename({"links" : "filing"})
training = training.drop(columns = ["filings"])
training = training.rename({"links" : "filing"})
current_df = current_df.drop(columns = ["filings"])
current_df = current_df.rename({"links" : "filing"})


upcoming_df = upcoming_df.to_html(index = False, classes = "", escape = False)
current_df = current_df.to_html(index = False, classes = "", escape = False)
training = training.to_html(index = False, classes = "", escape = False)

if __name__ == "__main__":
    app.run(debug = True)
