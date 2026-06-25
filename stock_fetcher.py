import twstock
import yfinance as yf
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

def get_stock_data(symbol):
    """使用 twstock 抓取台股最新收盤價及成交量"""
    try:
        if symbol.isdigit():
            print(f"🔍 從 twstock 抓取: {symbol}")
            stock = twstock.Stock(symbol)
            
            if len(stock.price) == 0:
                print(f"⚠️ 沒有 {symbol} 的資料")
                return None
            
            latest_price = stock.price[-1]
            
            # 抓取成交量
            volume = 0
            if hasattr(stock, 'volume') and len(stock.volume) > 0:
                volume = stock.volume[-1]
            elif hasattr(stock, 'capacity') and len(stock.capacity) > 0:
                volume = stock.capacity[-1]
            
            if len(stock.price) > 1:
                prev_price = stock.price[-2]
                change = ((latest_price - prev_price) / prev_price) * 100
            else:
                change = 0.0
            
            company_name = symbol
            
            print(f"✅ {company_name} ({symbol}) 收盤價: {latest_price}, 成交量: {volume}")
            return {
                'price': round(latest_price, 2),
                'change': round(change, 2),
                'volume': volume,
                'company_name': company_name
            }
        return None
    except Exception as e:
        print(f"❌ twstock 抓取失敗 ({symbol}): {e}")
        return None

def get_stock_history(symbol, period='5d'):
    """使用 twstock 抓取歷史 K 線數據"""
    try:
        if symbol.isdigit():
            print(f"🔍 從 twstock 抓取歷史資料: {symbol}")
            stock = twstock.Stock(symbol)
            
            days = 5
            if len(stock.price) < days:
                days = len(stock.price)
            
            if days == 0:
                print(f"⚠️ 沒有 {symbol} 的歷史資料")
                return None
            
            closes = stock.price[-days:]
            dates = stock.date[-days:]
            
            opens = stock.open[-days:] if hasattr(stock, 'open') and len(stock.open) >= days else closes
            highs = stock.high[-days:] if hasattr(stock, 'high') and len(stock.high) >= days else closes
            lows = stock.low[-days:] if hasattr(stock, 'low') and len(stock.low) >= days else closes
            
            date_strs = [d.strftime('%Y-%m-%d') for d in dates]
            
            print(f"✅ 取得 {days} 筆歷史資料")
            return {
                'dates': date_strs,
                'opens': [round(o, 2) for o in opens],
                'highs': [round(h, 2) for h in highs],
                'lows': [round(l, 2) for l in lows],
                'closes': [round(c, 2) for c in closes]
            }
        return None
    except Exception as e:
        print(f"❌ twstock 歷史資料抓取失敗 ({symbol}): {e}")
        return None

def get_twse_index():
    """抓取台股加權指數（大盤）- 使用 Yahoo Finance"""
    try:
        import yfinance as yf
        print("🔍 從 Yahoo Finance 抓取大盤指數: ^TWSE")
        
        # 下載大盤指數資料
        data = yf.download('^TWSE', period='1d', progress=False)
        
        if data.empty:
            print("⚠️ 無法取得大盤指數")
            return {
                'price': '--',
                'change': 0,
                'change_percent': 0,
                'volume': 0,
                'turnover': 0
            }
        
        # 最新收盤價
        price = data['Close'].iloc[-1]
        
        # 計算漲跌
        change = 0
        if len(data) > 1:
            prev_close = data['Close'].iloc[-2]
            change = price - prev_close
        
        # 成交量（股數）
        volume = 0
        if 'Volume' in data.columns and not data['Volume'].empty:
            volume = data['Volume'].iloc[-1]
        
        # 成交值
        turnover = 0
        if 'Volume' in data.columns and not data['Volume'].empty:
            turnover = volume * price
        
        print(f"✅ 大盤指數: {price:.2f}, 漲跌: {change:.2f}, 成交量: {volume}, 成交值: {turnover:.0f}")
        
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