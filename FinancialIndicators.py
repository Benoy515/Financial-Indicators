import pandas as pd
import datetime
import pandas_datareader.data as web 
import requests
import numpy as np


class Stock:
    USER_AGENT = { 'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36') } 
    sesh = requests.Session() 
    sesh.headers.update(USER_AGENT)

    def __init__(self, ticker):
        self.ticker = ticker
        y, m, d = 2015, 1, 1
        self.infoDF = pd.DataFrame(web.DataReader(self.ticker, 'yahoo', start=datetime.datetime(y, m, d), end=datetime.date.today(), session=Stock.sesh))
    
    def __repr__(self):
        return (f'Stock object of {self.ticker.upper()}')
 
    def info(self, period):
        return self.infoDF[-period:]

    def priceHistory(self, period):
        df = self.info(period)
        priceList = []
        for i in df['Close']:
            priceList.append(round(i,2))
        return priceList

    def priceChanges(self, period):
        priceList = self.priceHistory(period)
        priceChanges = []
        for i in range(len(priceList)-1):
            priceChanges.append(round((priceList[i+1]/priceList[i]-1)*100,2))
        return priceChanges

    def SMA(self, period, n=10):
        prices = self.priceHistory(period+n)
        SMAlist = []
        for i in range(len(prices)-n+1):
            SMAlist.append(round(sum(prices[i:i+n])/n,2))
        return SMAlist[1:]

    def EMA(self, period, n=12):
        df = self.info(period+n+100)
        df.drop(['Open', 'Volume'], inplace=True,axis=1)
        EMAlist = []
        initialPeriod = []
        for i in range(n):
            initialPeriod.append(df['Close'][i])
        ema = sum(initialPeriod)/n
        for i in range(n, len(df['Close'])):
            ema = df['Close'][i]*(2/(1+n)) + ema*(1-(2/(1+n)))
            EMAlist.append(round(ema,2))
        return EMAlist[-period:]

    def RSI(self, period, n=14):
        RSIlist=[]
        changes = self.priceChanges(period+n+1+50)
        gainList=[]
        lossList=[]
        for i in changes[:n]:
            if i>=0:
                gainList.append(i)
                lossList.append(0)
            else:
                lossList.append(i)
                gainList.append(0)
        changes = changes[n:]
        averageGain = sum(gainList)/len(gainList)
        averageLoss = abs(sum(lossList)/len(lossList))
        for i in changes:
            if i>=0:
                averageGain = ((averageGain*(n-1)) + i)/n
                averageLoss = ((averageLoss*(n-1)) + 0)/n
            else:
                averageGain = ((averageGain*(n-1)) + 0)/n
                averageLoss = ((averageLoss*(n-1)) + abs(i))/n
            RS = averageGain/averageLoss
            cRSI = 100-(100/(1+RS))
            RSIlist.append(round(cRSI,2))
        return RSIlist[-period:]

    def stoch(self, period, fastkperiod=14, slowkperiod=3):
        fastklist = []
        slowklist = []
        df = self.info(period+fastkperiod+slowkperiod)
        highList = [round(i,2) for i in df['High']]
        lowList = [round(i,2) for i in df['Low']]
        currentList = [round(i,2) for i in df['Close']]
        for i in range(len(df)-fastkperiod):
            fastklist.append(round((currentList[i+fastkperiod]-min(lowList[i+1:i+fastkperiod+1]))/(max(highList[i+1:i+fastkperiod+1])-min(lowList[i+1:i+fastkperiod+1]))*100,2))
        for i in range(slowkperiod+1, len(fastklist)+1):
            slowklist.append(round(sum(fastklist[i-slowkperiod:i])/slowkperiod,2))
        return fastklist[-period:],slowklist

    def MACD(self, period, fastLength=12, slowLength=26, smoothingValue=9):
        MACDlist=[]
        fastEMA = self.EMA(period+smoothingValue+100, fastLength)
        slowEMA = self.EMA(period+smoothingValue+100, slowLength)
        for i,j in zip(fastEMA, slowEMA):
            MACDlist.append(round(i-j, 2))
        signalList = []
        signal = sum(MACDlist[:smoothingValue])/smoothingValue
        for i in MACDlist[smoothingValue:]:
            signal = i*(2/(1+smoothingValue)) + signal*(1-(2/(1+smoothingValue)))
            signalList.append(round(signal,2))
        divergence = []
        for i,j in zip(MACDlist[-period:],signalList[-period:]):
            divergence.append(round(i-j,2))
        return divergence

    def bollingerBands(self, period, n=20):
        prices = self.priceHistory(period+n)
        baseline = self.SMA(period+n,n)
        upperBand=[]
        lowerBand=[]
        for i in range(n, len(baseline)):
            standardDeviation = np.std(prices[i-n+1:i+1])
            upperBand.append(round(baseline[i]+standardDeviation*2,2))
            lowerBand.append(round(baseline[i]-standardDeviation*2,2))
        return upperBand,lowerBand

    def bollingerBandsDifference(self, period, n=20):
        prices = self.priceHistory(period)
        upperBand,lowerBand = self.bollingerBands(period,n)
        differences=[]
        for i,j,k in zip(prices,upperBand,lowerBand):
            if i>j:differences.append(round(((i-j)/i)*100,2))
            elif i<k:differences.append(round(((i-k)/i)*100,2))
            else:differences.append(0)
        return differences

    def heikenAshiValues(self, period):
        #NOTE returns in up(1)/down(2), open, high, low, close format
        info = self.info(period)
        finalList=[]
        highs = [round(i,2) for i in list(info["High"])]
        lows = [round(i,2) for i in list(info["Low"])]
        opens = [round(i,2) for i in list(info["Open"])]
        closes = [round(i,2) for i in list(info["Close"])]
        open1=opens[0]
        close1=closes[0]
        candleOpens=[open1]
        candleCloses=[close1]
        for i in range(1,period):
            currentCandleOpen=round((candleOpens[i-1]+candleCloses[i-1])/2,2)
            currentCandleClose=round((highs[i]+lows[i]+opens[i]+closes[i])/4,2)
            candleOpens.append(currentCandleOpen)
            candleCloses.append(currentCandleClose)
            finalList.append([int(currentCandleOpen<currentCandleClose),currentCandleOpen,max(highs[i],currentCandleOpen,currentCandleClose),min(lows[i],currentCandleOpen,currentCandleClose),currentCandleClose])
        return finalList[-period:]

    def heikenAshiTails(self, period):
        HAvalues = self.heikenAshiValues(period+1)
        tailsList=[]
        for i in HAvalues:
            if i[0]:
                bottomTail=i[1]-i[3]
                topTail=i[2]-i[4]
            else:
                bottomTail=i[4]-i[3]
                topTail=i[2]-i[1]
            tailsList.append(topTail/(topTail+bottomTail))
        return tailsList


#Testing for running module independently
if __name__ == "__main__":
    company = Stock("CCL")
    values = company.heikenAshiTails(20)
    for i in values:print(i)