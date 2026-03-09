import streamlit as st
import akshare as ak
import pandas as pd
import datetime

# 设置网页标题和布局
st.set_page_config(page_title="我的量化摔杯雷达", page_icon="📡", layout="centered")

st.title("📡 核心标的摔杯信号雷达")
st.markdown("随时输入A股代码，一键透视主力资金与高位风险形态。")

# 默认填入你的10只核心关注股票
default_stocks = "600875, 600478, 601801, 000537, 600178, 000825, 600170, 600008, 601118, 600026"
stock_input = st.text_input("📝 请输入股票代码（多个代码用纯英文逗号隔开）：", default_stocks)

def analyze_stock(stock):
    try:
        df = ak.stock_zh_a_hist(symbol=stock, period="daily", adjust="qfq")
        if df.empty or len(df) < 30:
            return f"⚪ **{stock}**：数据获取失败或不足"
            
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
        
        # 高敏度模式：只要满足1个条件就报警
        if (today['收盘'] < today['开盘'] and body/total_len > 0.7) or (upper_shadow > body * 2):
            reasons.append("K线见顶(大阴/长上影)")
        if today['MFI'] > 80: 
            reasons.append(f"资金过热(MFI:{today['MFI']:.1f})")
        if today['最高'] > today['UPPER'] and today['收盘'] < today['UPPER']:
            reasons.append("布林带上轨压制")
            
        if len(reasons) >= 1:
            return f"🔴 **{stock}** 触发风险：{' | '.join(reasons)}"
        else:
            return f"🟢 **{stock}** 状态安全，未见明显抛压"
            
    except Exception as e:
        return f"⚪ **{stock}**：查询出错，请检查代码"

if st.button("🚀 立即全盘扫描"):
    stocks = [s.strip() for s in stock_input.split(",")]
    with st.spinner('正在云端连接交易所数据，请稍候...'):
        st.markdown("---")
        for stock in stocks:
            result = analyze_stock(stock)
            if "🔴" in result:
                st.error(result)
            elif "🟢" in result:
                st.success(result)
            else:
                st.warning(result)
        st.markdown(f"*扫描完成时间：{datetime.datetime.now().strftime('%H:%M:%S')}*")
