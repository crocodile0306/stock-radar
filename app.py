import streamlit as st
import akshare as ak
import pandas as pd
import datetime
import requests

# 设置网页标题和布局
st.set_page_config(page_title="AI 驱动版 A股主力雷达", page_icon="🧠", layout="centered")

st.title("🧠 摔杯信号雷达 (AI 深度诊断版)")
st.markdown("不仅透视主力出货形态，更有 DeepSeek 盘中实战策略推演。")

stock_input = st.text_input("📝 请输入你要检测的股票代码（例如：600875, 600026）：", "")

# 你的硅基流动 API 钥匙
API_KEY = "sk-lnkomejdqoodgqhxayoazvwwneemazcgovbzjaiyspsyerai"

def get_ai_advice(stock, price, mfi, risk_signals):
    """调用硅基流动的 DeepSeek-V3 模型进行实战分析"""
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    if risk_signals:
        prompt = f"你是一个资深A股短线游资操盘手。我的股票代码是 {stock}，当前收盘价 {price:.2f}。资金流入热度MFI为 {mfi:.1f}。目前量化系统抓取到了极其恶劣的风险信号：【{risk_signals}】。请直接给出最犀利、无废话的实战操作建议，告诉我是减仓、清仓还是防守，限 100 字以内。"
    else:
        prompt = f"你是一个资深A股短线游资操盘手。我的股票代码是 {stock}，当前收盘价 {price:.2f}。资金流入热度MFI为 {mfi:.1f}。目前量化系统显示该股形态健康，未见明显抛压和见顶信号。请给我一句简短有力的持仓定心丸和后续盯盘建议，限 100 字以内。"

    payload = {
        "model": "deepseek-ai/DeepSeek-V3", 
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return "⚠️ AI 大脑连接超时，请直接参考量化信号。"

def analyze_stock(stock):
    try:
        df = ak.stock_zh_a_hist(symbol=stock, period="daily", adjust="qfq")
        if df.empty or len(df) < 30:
            return "error", f"⚪ **{stock}**：数据获取失败，请检查代码"
            
        df['MA20'] = df['收盘'].rolling(20).mean()
        df['UPPER'] = df['MA20'] + 2 * df['收盘'].rolling(20).std()
        
        tp = (df['最高'] + df['最低'] + df['收盘']) / 3
        rmf = tp * df['成交量']
        pos_mf = rmf.where(tp > tp.shift(1), 0).rolling(14).sum()
        neg_mf = rmf.where(tp < tp.shift(1), 0).rolling(14).sum()
        df['MFI'] = 100 - (100 / (1 + pos_mf / (neg_mf + 1e-9)))
        
        today = df.iloc[-1]
        reasons = []
        
        body = abs(today['收盘'] - today['开盘'])
        total_len = today['最高'] - today['最低'] + 0.00001 
        upper_shadow = today['最高'] - max(today['收盘'], today['开盘'])
        
        is_big_drop = (today['收盘'] < today['开盘']) and (body / total_len > 0.7) and (total_len / today['开盘'] > 0.01)
        is_long_shadow = (upper_shadow > body * 2) and (upper_shadow / today['开盘'] > 0.015)
        
        if is_big_drop or is_long_shadow:
            reasons.append("K线破位(大阴线/长上影)")
        if today['MFI'] > 80: 
            reasons.append(f"资金过热(MFI:{today['MFI']:.1f})")
        if today['最高'] > today['UPPER'] and today['收盘'] < today['UPPER']:
            reasons.append("布林带上轨压制")
            
        risk_str = " | ".join(reasons)
        
        # 让 AI 思考
        ai_advice = get_ai_advice(stock, today['收盘'], today['MFI'], risk_str)
        
        if len(reasons) >= 1:
            return "danger", f"🔴 **{stock}** 触发风险：{risk_str}\n\n💡 **AI 操盘建议**：\n> {ai_advice}"
        else:
            return "success", f"🟢 **{stock}** 形态健康，未见明显出货信号\n\n💡 **AI 操盘建议**：\n> {ai_advice}"
            
    except Exception as e:
        return "error", f"⚪ **{stock}**：查询出错，请重试。"

if st.button("🚀 立即深度扫描"):
    if not stock_input.strip():
        st.warning("⚠️ 请先在上方输入股票代码！")
    else:
        stocks = [s.strip() for s in stock_input.replace('，', ',').split(",") if s.strip()]
        
        with st.spinner('🤖 AI 正在云端推演主力意图，请稍候 (约 3-5 秒)...'):
            st.markdown("---")
            for stock in stocks:
                status, result = analyze_stock(stock)
                if status == "danger":
                    st.error(result)
                elif status == "success":
                    st.success(result)
                else:
                    st.warning(result)
            st.markdown(f"*扫描完成时间：{datetime.datetime.now().strftime('%H:%M:%S')}*")
