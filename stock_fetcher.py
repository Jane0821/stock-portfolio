import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def get_stock_data(symbol):
    """使用 yfinance 抓取台股最新收盤價及成交量"""
    try:
        # 如果是台股（純數字），加上 .TW
        if symbol.isdigit():
            symbol_tw = symbol + '.TW'
            print(f"🔍 從 Yahoo Finance 抓取: {symbol_tw}")
            
            data = yf.download(symbol_tw, period='1d', progress=False)
            
            if data.empty:
                print(f"⚠️ 找不到 {symbol} 的資料")
                return None
            
            latest_price = data['Close'].iloc[-1]
            
            # 計算漲跌幅（與昨日比）
            if len(data) > 1:
                prev_price = data['Close'].iloc[-2]
                change = ((latest_price - prev_price) / prev_price) * 100
            else:
                change = 0.0
            
            # 抓取成交量
            volume = 0
            if 'Volume' in data.columns and not data['Volume'].empty:
                volume = int(data['Volume'].iloc[-1])
            
            # 抓取公司名稱
            company_name = symbol
            try:
                ticker = yf.Ticker(symbol_tw)
                info = ticker.info
                name = info.get('longName', info.get('shortName', symbol))
                if name:
                    company_name = name
            except:
                pass
            
            print(f"✅ {company_name} ({symbol}) 收盤價: {latest_price:.2f}, 成交量: {volume}")
            return {
                'price': round(latest_price, 2),
                'change': round(change, 2),
                'volume': volume,
                'company_name': company_name
            }
        else:
            # 美股直接用原代號
            print(f"🔍 從 Yahoo Finance 抓取: {symbol}")
            data = yf.download(symbol, period='1d', progress=False)
            
            if data.empty:
                return None
            
            latest_price = data['Close'].iloc[-1]
            
            if len(data) > 1:
                prev_price = data['Close'].iloc[-2]
                change = ((latest_price - prev_price) / prev_price) * 100
            else:
                change = 0.0
            
            volume = 0
            if 'Volume' in data.columns and not data['Volume'].empty:
                volume = int(data['Volume'].iloc[-1])
            
            company_name = symbol
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                name = info.get('longName', info.get('shortName', symbol))
                if name:
                    company_name = name
            except:
                pass
            
            return {
                'price': round(latest_price, 2),
                'change': round(change, 2),
                'volume': volume,
                'company_name': company_name
            }
    except Exception as e:
        print(f"❌ yfinance 抓取失敗 ({symbol}): {e}")
        return None

def get_stock_history(symbol, period='5d'):
    """使用 yfinance 抓取歷史 K 線數據"""
    try:
        if symbol.isdigit():
            symbol = symbol + '.TW'
        
        print(f"🔍 從 Yahoo Finance 抓取歷史資料: {symbol}")
        data = yf.download(symbol, period=period, progress=False)
        
        if data.empty:
            print(f"⚠️ 找不到 {symbol} 的歷史資料")
            return None
        
        # 回傳 OHLC 數據
        return {
            'dates': data.index.strftime('%Y-%m-%d').tolist(),
            'opens': data['Open'].round(2).tolist(),
            'highs': data['High'].round(2).tolist(),
            'lows': data['Low'].round(2).tolist(),
            'closes': data['Close'].round(2).tolist()
        }
    except Exception as e:
        print(f"❌ yfinance 歷史資料抓取失敗 ({symbol}): {e}")
        return None

def get_twse_index():
    """抓取台股加權指數（大盤）- 使用 Yahoo Finance"""
    try:
        print("🔍 從 Yahoo Finance 抓取大盤指數: ^TWII")
        
        data = yf.download('^TWII', period='1d', progress=False)
        
        if data.empty:
            print("⚠️ 無法取得大盤指數")
            return {
                'price': '--',
                'change': 0,
                'change_percent': 0,
                'volume': 0,
                'turnover': 0
            }
        
        price = data['Close'].iloc[-1]
        
        change = 0
        if len(data) > 1:
            prev_close = data['Close'].iloc[-2]
            change = price - prev_close
        
        volume = 0
        if 'Volume' in data.columns and not data['Volume'].empty:
            volume = int(data['Volume'].iloc[-1])
        
        turnover = 0
        if 'Volume' in data.columns and not data['Volume'].empty:
            turnover = volume * price
        
        print(f"✅ 大盤指數: {price:.2f}, 漲跌: {change:.2f}")
        
        return {
            'price': round(price, 2),
            'change': round(change, 2),
            'change_percent': round((change / (price - change)) * 100 if (price - change) > 0 else 0, 2),
            'volume': int(volume),
            'turnover': int(turnover)
        }
    except Exception as e:
        print(f"❌ 抓取大盤指數失敗: {e}")
        return {
            'price': '--',
            'change': 0,
            'change_percent': 0,
            'volume': 0,
            'turnover': 0
        }

def get_news():
    """從 Google News 抓取財經新聞標題"""
    try:
        url = 'https://news.google.com/rss/search?q=stock+market&hl=zh-TW&gl=TW&ceid=TW:zh'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        news_items = []
        for item in soup.find_all('item')[:5]:
            news_items.append({
                'title': item.title.text if item.title else '無標題',
                'link': item.link.text if item.link else '#',
                'pub_date': item.pubDate.text[:16] if item.pubDate else ''
            })
        return news_items
    except Exception as e:
        print(f"❌ 抓取新聞錯誤: {e}")
        return [
            {'title': '📊 台積電宣布3奈米製程量產', 'link': '#'},
            {'title': '📈 美股四大指數全面上漲', 'link': '#'},
            {'title': '🏦 央行宣布利率維持不變', 'link': '#'}
        ]