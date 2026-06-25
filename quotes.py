import random
import json
import os

# 預設股市語錄（至少 30 句）
DEFAULT_QUOTES = [
    "別把雞蛋放在同一個籃子裡。",
    "市場永遠是對的。",
    "貪婪和恐懼是市場的兩大驅動力。",
    "買在謠言時，賣在事實時。",
    "趨勢是你的朋友。",
    "投資有風險，請謹慎評估。",
    "不要把短線交易當成投資。",
    "在別人貪婪時恐懼，在別人恐懼時貪婪。",
    "股市是財富重分配的場所。",
    "長期投資是散戶的最佳策略。",
    "不要試圖預測市場，要準備好應對市場。",
    "投資要像種樹，需要時間成長。",
    "風險來自於你不知道自己在做什麼。",
    "市場總是有理由，但理由總是事後才出現。",
    "股票市場是唯一一個商品越漲越多人買的地方。",
    "紀律比判斷力更重要。",
    "保本永遠是第一要務。",
    "不要借錢買股票。",
    "投資是藝術，不是科學。",
    "專注於企業價值，而不是股價波動。",
    "恐慌時買進，貪婪時賣出。",
    "耐心是投資者最重要的美德。",
    "投資成功的關鍵是時間，不是時機。",
    "了解自己比了解市場更重要。",
    "偉大的投資來自於簡單的觀念。",
    "市場會給你機會，但不會給你時間。",
    "每一次下跌都是機會的開始。",
    "累積財富需要時間，失去財富只需要一個錯誤。",
    "股市中最貴的一句話是「這次不一樣」。",
    "紀律是散戶對抗法人的唯一武器。",
    "投資不是賭博，是機率的遊戲。",
    "財富是耐心的副產品。",
]

QUOTES_FILE = "quotes_data.json"

def load_quotes():
    """從檔案載入語錄，如果檔案不存在則建立預設資料庫"""
    if os.path.exists(QUOTES_FILE):
        try:
            with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data and len(data) > 0:
                    return data
        except:
            pass
    # 如果檔案不存在或讀取失敗，建立預設資料庫
    save_quotes(DEFAULT_QUOTES)
    return DEFAULT_QUOTES

def save_quotes(quotes):
    """儲存語錄到檔案"""
    with open(QUOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)

def get_random_quote():
    """隨機回傳一句語錄"""
    quotes = load_quotes()
    return random.choice(quotes) if quotes else "投資有風險，請謹慎評估。"

def add_quote(quote):
    """新增一句語錄到資料庫"""
    quotes = load_quotes()
    quotes.append(quote)
    save_quotes(quotes)
    return True