import streamlit as st
import yfinance as yf
import plotly.express as px
import asyncio
from dotenv import load_dotenv

from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core.models import UserMessage

load_dotenv()

# ----------------------------
# Initialize Ollama client
# ----------------------------
ollama_client = OllamaChatCompletionClient(model="qwen2.5:latest")

# ----------------------------
# Chat memory
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

# ----------------------------
# Streamlit layout
# ----------------------------
st.set_page_config(page_title="Stock Analyze Agent", page_icon="📈")
st.title("📈 Stock Analysis & Recommendation Agent")

stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT):")

if st.button("Analyze") and stock_symbol:
    add_message("user", stock_symbol)

    try:
        # ----------------------------
        # Fetch stock info
        # ----------------------------
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        df = stock.history(period="1y")

        # ----------------------------
        # Plot closing price
        # ----------------------------
        fig = px.line(df, x=df.index, y="Close",
                      title=f"{stock_symbol} Closing Price (1Y)")
        st.plotly_chart(fig)

        # ----------------------------
        # Build prompt for LLM
        # ----------------------------
        context = f"""
Analyze the following stock:
- Stock Symbol: {stock_symbol}
- Company Name: {info.get('shortName','N/A')}
- Current Price: {info.get('currentPrice','N/A')}
- Market Cap: {info.get('marketCap','N/A')}
- PE Ratio: {info.get('trailingPE','N/A')}
- 52w High/Low: {info.get('fiftyTwoWeekHigh','N/A')} / {info.get('fiftyTwoWeekLow','N/A')}
- Business Summary: {info.get('longBusinessSummary','N/A')}

Provide a buy, hold, or sell recommendation with reasoning.
"""

        # Clean prompt
        context_clean = "\n".join([line.strip() for line in context.splitlines() if line.strip()])

        # Create UserMessage
        user_msg = UserMessage(content=context_clean, source="user")

        # ----------------------------
        # Call Ollama LLM (async)
        # ----------------------------
        response = asyncio.run(ollama_client.create([user_msg]))

        # ✅ Access LLM response correctly
        add_message("assistant", response.content)

    except Exception as e:
        add_message("assistant", f"Error fetching stock data: {e}")

# ----------------------------
# Display chat history
# ----------------------------
st.subheader("💬 Chat History")
for msg in st.session_state.messages:
    role = "You" if msg["role"] == "user" else "Agent"
    st.markdown(f"**{role}:** {msg['content']}")

# ----------------------------
# Clear chat button
# ----------------------------
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.success("Chat cleared!")
