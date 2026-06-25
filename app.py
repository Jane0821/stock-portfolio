from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import get_db_connection, init_db
from stock_fetcher import get_stock_data, get_stock_history, get_news
from quotes import get_random_quote
from datetime import datetime
import time

app = Flask(__name__)
init_db()

@app.route('/')
def index():
    start_time = time.time()
    
    conn = get_db_connection()
    holdings = conn.execute('SELECT * FROM holdings ORDER BY id DESC').fetchall()
    conn.close()
    
    # 合併同股票的多筆記錄
    merged = {}
    for stock in holdings:
        symbol = stock['symbol']
        if symbol not in merged:
            merged[symbol] = {
                'ids': [],
                'total_shares': 0,
                'total_cost': 0,
                'notes': [],
                'count': 0
            }
        merged[symbol]['ids'].append(stock['id'])
        merged[symbol]['total_shares'] += stock['shares']
        merged[symbol]['total_cost'] += stock['shares'] * stock['buy_price']
        if stock['note']:
            merged[symbol]['notes'].append(stock['note'])
        merged[symbol]['count'] += 1
    
    portfolio_data = []
    total_profit = 0
    
    for symbol, data in merged.items():
        avg_cost = data['total_cost'] / data['total_shares'] if data['total_shares'] > 0 else 0
        
        # 🔥 爬蟲 + 備援
        stock_data = get_stock_data(symbol)
        
        if stock_data:
            current_price = stock_data['price']
            change = ((current_price - avg_cost) / avg_cost) * 100 if avg_cost > 0 else 0
            profit = (current_price - avg_cost) * data['total_shares']
            total_profit += profit
            
            portfolio_data.append({
                'id': data['ids'][0],
                'symbol': symbol,
                'company_name': stock_data.get('company_name', symbol),
                'shares': data['total_shares'],
                'buy_price': round(avg_cost, 2),
                'avg_cost_count': data['count'],
                'current_price': current_price,
                'change': round(change, 2),
                'profit': round(profit, 2),
                'volume': stock_data.get('volume', 0),
                'error': False,
                'from_cache': stock_data.get('from_cache', False)
            })
        else:
            portfolio_data.append({
                'id': data['ids'][0],
                'symbol': symbol,
                'company_name': symbol,
                'shares': data['total_shares'],
                'buy_price': round(avg_cost, 2),
                'avg_cost_count': data['count'],
                'current_price': 0,
                'change': 0,
                'profit': 0,
                'volume': 0,
                'error': True,
                'from_cache': False
            })
    
    news = get_news()
    
    # 市場概況
    valid_stocks = [s for s in portfolio_data if not s['error']]
    total_volume = sum([s.get('volume', 0) for s in valid_stocks])
    total_value = sum([s.get('shares', 0) * s.get('current_price', 0) for s in valid_stocks])
    up_count = len([s for s in valid_stocks if s.get('change', 0) > 0])
    down_count = len([s for s in valid_stocks if s.get('change', 0) < 0])
    flat_count = len([s for s in valid_stocks if s.get('change', 0) == 0])
    
    if len(valid_stocks) > 0:
        avg_change = sum([s.get('change', 0) for s in valid_stocks]) / len(valid_stocks)
        if avg_change > 1:
            market_temp = "🔥 過熱"
            temp_color = "#e74c3c"
        elif avg_change > 0:
            market_temp = "🌤️ 偏多"
            temp_color = "#f39c12"
        elif avg_change > -1:
            market_temp = "🌥️ 偏空"
            temp_color = "#3498db"
        else:
            market_temp = "❄️ 低迷"
            temp_color = "#27ae60"
    else:
        market_temp = "⚪ 無資料"
        temp_color = "#999"
    
    market_data = {
        'total_volume': total_volume,
        'total_value': round(total_value, 2),
        'up_count': up_count,
        'down_count': down_count,
        'flat_count': flat_count,
        'market_temp': market_temp,
        'temp_color': temp_color,
        'stock_count': len(portfolio_data)
    }
    
    # 找出最賺和最賠
    sorted_stocks = sorted(portfolio_data, key=lambda x: x.get('profit', 0), reverse=True)
    best_stock = sorted_stocks[0] if sorted_stocks and sorted_stocks[0].get('profit', 0) > 0 else None
    worst_stock = sorted_stocks[-1] if sorted_stocks and sorted_stocks[-1].get('profit', 0) < 0 else None
    
    quote = get_random_quote()
    update_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    
    load_time = round((time.time() - start_time) * 1000, 0)
    print(f"⏱️ 頁面載入時間: {load_time}ms")
    
    return render_template('index.html', 
                         stocks=portfolio_data, 
                         news=news,
                         total_profit=round(total_profit, 2),
                         market_data=market_data,
                         best_stock=best_stock,
                         worst_stock=worst_stock,
                         quote=quote,
                         update_time=update_time,
                         load_time=load_time)

@app.route('/add', methods=['POST'])
def add_stock():
    symbol = request.form['symbol'].upper().strip()
    shares = int(request.form['shares'])
    buy_price = float(request.form['buy_price'])
    note = request.form.get('note', '')
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO holdings (symbol, shares, buy_price, note) VALUES (?, ?, ?, ?)',
        (symbol, shares, buy_price, note)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_stock(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM holdings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/refresh')
def refresh():
    return redirect(url_for('index'))

@app.route('/history/<symbol>')
def get_history(symbol):
    data = get_stock_history(symbol, period='5d')
    
    if data and 'closes' in data:
        return {
            'success': True,
            'symbol': symbol,
            'dates': data['dates'],
            'opens': data['opens'],
            'highs': data['highs'],
            'lows': data['lows'],
            'closes': data['closes']
        }
    else:
        return {'success': False, 'error': '無法獲取K線數據'}, 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)