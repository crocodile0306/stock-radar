import streamlit as st
import akshare as ak
import pandas as pd
import datetime

# 设置网页标题和布局
st.set_page_config(page_title="A股主力形态雷达", page_icon="📡", layout="centered")

st.title("📡 A股通用摔杯信号雷达")
st.markdown("输入任意 A 股代码，一键透视高位风险与主力出货形态。")

# 干净的输入框，没有任何默认股票，你可以随便填任意 A 股代码
stock_input = st.text_input("📝 请输入你要检测的股票代码（例如：600519, 000001）：", "")

def analyze_stock(stock):
    try:
        # 获取任意股票的日线数据
        df = ak.stock_zh_a_hist(symbol=stock, period="daily", adjust="qfq")
        if df.empty or len(df) < 30:
            return f"⚪ **{stock}**：数据获取失败，请检查代码是否是标准的 6 位数字"
            
        df['MA20'] = df['收盘'].rolling(20).mean()
        df['UPPER'] = df['MA20'] + 2 * df['收盘'].rolling(20).std()
        
        tp = (df['最高'] + df['最低'] + df['收盘']) / 3
        rmf = tp * df['成交量']
        pos_mf = rmf.where(tp > tp.shift(1), 0).rolling(14).sum()
        neg_mf = rmf.where(tp < tp.shift(1), 0).rolling(14).sum()
        df['MFI'] = 100 - (100 / (1 + pos_mf / (neg_mf + 1e-9)))
        
        today = df.iloc[-1]
        reasons = []
        
        # ================= 核心判定区 =================
        body = abs(today['收盘'] - today['开盘'])
        total_len = today['最高'] - today['最低'] + 0.00001 
        upper_shadow = today['最高'] - max(today['收盘'], today['开盘'])
        
        # 改进1：真正的大阴线（实体占全天振幅70%以上，且全天振幅大于1%）
        is_big_drop = (today['收盘'] < today['开盘']) and (body / total_len > 0.7) and (total_len / today['开盘'] > 0.01)
        
        # 改进2：真正的致命长上影（上影线大于实体2倍，且上影线长度必须大于股价的 1.5%）
        is_long_shadow = (upper_shadow > body * 2) and (upper_shadow / today['开盘'] > 0.015)
        
        if is_big_drop or is_long_shadow:
            reasons.append("K线破位(大阴线/长上影)")
            
        if today['MFI'] > 80: 
            reasons.append(f"资金过热(MFI:{today['MFI']:.1f})")
            
        if today['最高'] > today['UPPER'] and today['收盘'] < today['UPPER']:
            reasons.append("布林带上轨压制")
            
        # 综合判定：只要满足上面真正的风险条件之一，就报警
        if len(reasons) >= 1:
            return f"🔴 **{stock}** 触发风险：{' | '.join(reasons)}"
        else:
            return f"🟢 **{stock}** 形态健康，未见明显出货信号"
            
    except Exception as e:
        return f"⚪ **{stock}**：查询出错，请确保输入了正确的 6 位股票代码"

# 点击按钮后开始全网查询
if st.button("🚀 立即深度扫描"):
    if not stock_input.strip():
        st.warning("⚠️ 请先在上方输入股票代码！")
    else:
        # 支持用逗号、空格分隔的多个任意代码
        stocks = [s.strip() for s in stock_input.replace('，', ',').split(",") if s.strip()]
        
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
