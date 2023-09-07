import pandas as pd
import nltk
from sklearn.model_selection import GridSearchCV, cross_val_score
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
from nltk.corpus import wordnet
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import GradientBoostingClassifier
from datetime import date
from joblib import dump, load
import string

class Classifier:
    
    def __init__(self):
        curr_date = date.today()
        nltk.download("stopwords")
        nltk.download('punkt')
        self.ru = pd.read_csv("Roundups.csv")
        self.df = pd.read_csv("full_data.csv", encoding='latin-1')
        self.display = self.df.copy()
        self.df["date"] = pd.to_datetime(self.df["date"])
        self.df["round_up"] = self.df.apply(lambda x : 1 if x["ticker"] in self.ru["ticker"].unique() else 0, axis = 1)
        self.ru = self.ru.dropna()
        self.clean_data()
        self.current = self.df[self.df["date"].apply(lambda x : x.day == curr_date.day and x.month == curr_date.month and x.year == curr_date.year)]
        self.upcoming = self.df[self.df["date"].apply(lambda x : pd.Timestamp(x) > pd.Timestamp(curr_date))]
        
    def clean_text(self, text):
        # Normalize whitespace
        text = re.sub('\s+', ' ', text)
        # Remove special characters
        text = re.sub('[^A-Za-z0-9 ]+', '', text)
        return text
    
    def clean(self, text):
        if pd.isnull(text):
            return text
    
        cleaned_name = ''.join(char for char in text if char.isalnum() or char.isspace() or char in string.punctuation)
        # text = re.sub('\s+', ' ', text)
        
        # # Remove special characters
        # text = re.sub('[^A-Za-z0-9 ]+', '', text)
        
        return cleaned_name
            
    def clean_data(self):
        self.df["filings"] = self.df["filings"].astype(str)
        # print(self.df.head(5))
        self.df.drop(columns=["filings2", "cik", "Unnamed: 0"], inplace = True)
        correct = self.df.apply(lambda x :  "fraction" in x["filings"].strip().lower() and x["filings"] != "nan", axis = 1)
        self.df = self.df.iloc[correct[correct == True].index]
        stop = set(stopwords.words("english"))
        stop.remove("up")
        stop.remove("down")
        financial_stop_words = [
            'company', 'companies', 'corporation', 'corporations', 'incorporated', 'limited',
            'ltd', 'llc', 'group', 'holdings', 'plc', 'bank', 'banks', 'financial', 'finance',
            'investment', 'investments', 'asset', 'assets', 'equity', 'capital', 'stock', 'stocks',
            'share', 'shares', 'bond', 'bonds', 'derivative', 'derivatives', 'option', 'options',
            'futures', 'commodity', 'commodities', 'forex', 'exchange', 'market', 'markets',
            'trading', 'trade', 'broker', 'brokers', 'portfolio', 'fund', 'funds', 'mutual',
            'mutuals', 'index', 'indices', 'dividend', 'dividends', 'earnings', 'revenue', 'profit',
            'loss', 'income', 'liquidity', 'valuation', 'rating', 'credit', 'debit', 'loan', 'loans',
            'mortgage', 'securities', 'insurance', 'insurer', 'underwriter', 'policy', 'policies',
            'premium', 'premiums', 'claim', 'claims', 'coverage', 'deductible', 'underwriting',
            'reinsurance', 'pension', 'retirement', 'annuity', 'annuities', '401k', 'stockholder',
            'shareholder', 'investor', 'trader', 'analyst', 'analysts', 'financials', 'audit',
            'accounting', 'tax', 'taxes', 'revenue', 'expenditure', 'assets', 'liabilities', 'debt',
            'equities', 'interest', 'rate', 'credit', 'score', 'lending', 'leverage', 'volatility',
            'liquidity', 'yield', 'inflation', 'deflation', 'gdp', 'inflation', 'purchasing',
            'managers', 'cpi', 'index', 'deficit', 'balance', 'sheet', 'income', 'statement',
            'cash', 'flow', 'hedge', 'hedging', 'risk', 'return', 'asset', 'allocation',
            'portfolio', 'diversification', 'option', 'pricing', 'swap', 'arbitrage', 'securitization',
            'bond', 'yield', 'duration', 'coupon', 'spread', 'equity', 'valuation', 'payout',
            'cost', 'average', 'earnings', 'per', 'price', 'earnings', 'ratio', 'market', 'cap',
            'beta', 'volatility', 'liquidity', 'dividend', 'yield', 'retained', 'earnings', 'earnings',
            'per', 'share', 'growth', 'rate', 'return', 'on', 'equity', 'return', 'on', 'assets',
            'return', 'on', 'investment', 'price', 'to', 'earnings', 'price', 'to', 'sales',
            'price', 'to', 'book', 'value', 'return', 'on', 'capital', 'expenditure', 'depreciation',
            'amortization', 'operating', 'income', 'net', 'income', 'gross', 'income', 'net', 'profit',
            'net', 'loss', 'operating', 'margin', 'net', 'margin', 'gross', 'margin', 'working', 'capital',
            'current', 'ratio', 'quick', 'ratio', 'debt', 'ratio', 'leverage', 'ratio', 'interest',
            'coverage', 'ratio', 'acid', 'test', 'ratio', 'inventory', 'turnover', 'receivables',
            'turnover', 'payables', 'turnover', 'working', 'capital', 'turnover', 'asset', 'turnover',
            'inventory', 'days', 'sales', 'outstanding', 'days', 'payable', 'outstanding',
            'days', 'receivable', 'outstanding', 'cash', 'conversion', 'cycle', 'dupont', 'analysis',
            'ebitda', 'marginal', 'cost', 'of', 'capital', 'wacc', 'risk', 'free', 'rate', 'beta',
            'capital', 'asset', 'pricing', 'model', 'dividend', 'discount', 'model', 'black',
            'scholes', 'model', 'monte', 'carlo', 'simulation', 'bull', 'bear', 'market', 'long',
            'short', 'position', 'buy', 'sell', 'hold', 'quarterly', 'annual', 'fiscal', 'year',
            'balance', 'sheet', 'income', 'statement', 'cash', 'flow', 'statement', 'financial',
            'statement', 'statement', 'of', 'operations', 'footnote', 'footnotes', 'auditor', 'audited',
            'unaudited', 'interim', 'statement', 'of', 'financial', 'position', 'consolidated',
            'financial', 'statements', 'notes', 'to', 'the', 'financial', 'statements',
            'management', 'discussion', 'and', 'analysis', 'risk', 'factor', '10k', '10q', '8k',
            'prospectus', 'proxy', 'statement', 'registration', 'statement', 'sec', 'filings',
            'form', '10k', 'form', '10q', 'form', '8k', 'form', '20f', 'form', '40f', 'form', '6k'
        ]
        stop_words = set(stopwords.words('english')).union(set(financial_stop_words))
        self.df["filings"] = self.df["filings"].str.lower()
        self.df["filings"] = self.df["filings"].str.replace(r'[^\w\s]', ' ', regex = True)
        self.df["filings"] = self.df["filings"].apply(lambda x : " ".join([word for word in word_tokenize(x) if word not in stop]))
        self.df['filings'] = self.df['filings'].apply(lambda x: self.clean_text(x))
        
    def train_model(self):
        # print(self.current.head())
        training = self.df.drop(self.current.index)
        training = self.df.drop(self.upcoming.index)
        X = training["filings"]
        y = training["round_up"]
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(X)
        parameters = {
        'n_estimators': [100, 200, 300],
        'learning_rate': [0.1, 0.05, 0.01],
        'max_depth': [3, 5, 10]
        }   
        gb = GradientBoostingClassifier()
        grid_search_gb = GridSearchCV(gb, parameters, scoring="recall")
        grid_search_gb.fit(X, y)
        best_gb = grid_search_gb.best_estimator_
        dump(best_gb, "model.joblib")
        dump(vectorizer, "vectorizer.joblib")
        return gb
    
    
    def transform_current(self, retrain = False):
        if retrain:
            self.train_model()
        if self.current.shape[0] == 0:
            return self.current 
        self.df["date"] = pd.to_datetime(self.df["date"])
        model = load("model.joblib")
        X_test = self.current["filings"]
        vectorizer = load("vectorizer.joblib")
        X_test = vectorizer.transform(X_test)
        # self.current["rounding up?"] = model.predict(X_test)
        temp = self.display.copy().loc[self.current.index].drop(columns=["Unnamed: 0", "filings2", "cik"])
        temp["round up?"] = model.predict(X_test) 
        return temp
    
    def transform_upcoming(self, retrain = False):
        if retrain:
            self.train_model()
        if self.upcoming.shape[0] == 0:
            return self.current
        self.df["date"] = pd.to_datetime(self.df["date"])
        model = load("model.joblib")
        X_test = self.upcoming["filings"]
        vectorizer = load("vectorizer.joblib")
        X_test = vectorizer.transform(X_test)
        # self.upcoming["rounding up?"] = model.predict(X_test)
        temp = self.display.copy().loc[self.upcoming.index].drop(columns=["Unnamed: 0", "filings2", "cik"])
        temp["round up?"] = model.predict(X_test) 
        return temp