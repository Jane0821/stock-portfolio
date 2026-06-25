from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import get_db_connection, init_db
from stock_fetcher import get_stock_data, get_stock_history, get_news
from quotes import get_random_quote
from datetime import datetime
import json
import os

app = Flask(__name__)
init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    holdings = conn.execute('SELECT * FROM holdings ORDER BY id DESC').fetchall()
    conn.close()
    
    # 合併同股票的多筆記錄（計算平均成本）
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
    
    # 🔥 先建立基本資料（不含股價），讓頁面快速顯示
    portfolio_data = []
    for symbol, data in merged.items():
        avg_cost = data['total_cost'] / data['total_shares'] if data['total_shares'] > 0 else 0
        
        # 先顯示基本資訊，股價稍後透過 AJAX 載入
        portfolio_data.append({
            'id': data['ids'][0],
            'symbol': symbol,
            'company_name': symbol,  # 稍後更新
            'shares': data['total_shares'],
            'buy_price': round(avg_cost, 2),
            'avg_cost_count': data['count'],
            'current_price': 0,
            'change': 0,
            'profit': 0,
            'volume': 0,
            'error': True,
            'loading': True  # 🔥 標記為載入中
        })
    
    news = get_news()
    
    # 市場概況（從持股計算）
    market_data = {
        'total_volume': 0,
        'total_value': 0,
        'up_count': 0,
        'down_count': 0,
        'flat_count': len(portfolio_data),
        'market_temp': '⏳ 載入中...',
        'temp_color': '#999',
        'stock_count': len(portfolio_data)
    }
    
    quote = get_random_quote()
    update_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    
    return render_template('index.html', 
                         stocks=portfolio_data, 
                         news=news,
                         total_profit=0,
                         market_data=market_data,
                         best_stock=None,
                         worst_stock=None,
                         quote=quote,
                         update_time=update_time,
                         loading=True)  # 🔥 傳入 loading 狀態

@app.route('/api/stocks')
def api_stocks():
    """API：回傳所有持股的即時股價"""
    conn = get_db_connection()
    holdings = conn.execute('SELECT * FROM holdings ORDER BY id DESC').fetchall()
    conn.close()
    
    merged = {}
    for stock in holdings:
        symbol = stock['symbol']
        if symbol not in merged:
            merged[symbol] = {
                'ids': [],
                'total_shares': 0,
                'total_cost': 0,
                'count': 0
            }
        merged[symbol]['ids'].append(stock['id'])
        merged[symbol]['total_shares'] += stock['shares']
        merged[symbol]['total_cost'] += stock['shares'] * stock['buy_price']
        merged[symbol]['count'] += 1
    
    result = []
    total_profit = 0
    
    for symbol, data in merged.items():
        avg_cost = data['total_cost'] / data['total_shares'] if data['total_shares'] > 0 else 0
        stock_data = get_stock_data(symbol)
        
        if stock_data:
            current_price = stock_data['price']
            change = ((current_price - avg_cost) / avg_cost) * 100 if avg_cost > 0 else 0
            profit = (current_price - avg_cost) * data['total_shares']
            total_profit += profit
            
            result.append({
                'symbol': symbol,
                'company_name': stock_data.get('company_name', symbol),
                'current_price': current_price,
                'change': round(change, 2),
                'profit': round(profit, 2),
                'volume': stock_data.get('volume', 0),
                'error': False
            })
        else:
            result.append({
                'symbol': symbol,
                'company_name': symbol,
                'current_price': 0,
                'change': 0,
                'profit': 0,
                'volume': 0,
                'error': True
            })
    
    # 找出最賺和最賠
    sorted_stocks = sorted(result, key=lambda x: x.get('profit', 0), reverse=True)
    best = sorted_stocks[0] if sorted_stocks and sorted_stocks[0]['profit'] > 0 else None
    worst = sorted_stocks[-1] if sorted_stocks and sorted_stocks[-1]['profit'] < 0 else None
    
    return jsonify({
        'stocks': result,
        'total_profit': round(total_profit, 2),
        'best_stock': best,
        'worst_stock': worst
    })

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