import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from trading_strategy import (
    calculate_moving_averages,
    get_stock_data,
    identify_golden_cross,
    implement_strategy,
)


st.set_page_config(page_title="Trading Strategy Dashboard", layout="wide")


@st.cache_data
def load_strategy_data():
    data = get_stock_data("MSFT")
    data = calculate_moving_averages(data)
    data = identify_golden_cross(data)
    positions = implement_strategy(data)
    return data, positions


def compute_summary(positions):
    if positions.empty:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "average_profit": 0.0,
            "average_holding_days": 0.0,
        }

    total_trades = len(positions)
    winning_trades = int((positions["ProfitPct"] > 0).sum())
    losing_trades = total_trades - winning_trades
    win_rate = (winning_trades / total_trades) * 100 if total_trades else 0
    average_profit = positions["ProfitPct"].mean()
    average_holding = positions["HoldingDays"].mean()

    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "average_profit": average_profit,
        "average_holding_days": average_holding,
    }


def draw_price_chart(data, positions):
    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(data.index, data["Close"], label="Close Price", color="black", linewidth=2)
    ax.plot(data.index, data["MA50"], label="50-day MA", color="tab:blue", linewidth=1.5)
    ax.plot(data.index, data["MA200"], label="200-day MA", color="tab:red", linewidth=1.5)

    if not positions.empty:
        buy_points = positions[["BuyDate", "BuyPrice"]].rename(columns={"BuyDate": "Date", "BuyPrice": "Price"})
        sell_points = positions[["SellDate", "SellPrice"]].rename(columns={"SellDate": "Date", "SellPrice": "Price"})

        ax.scatter(buy_points["Date"], buy_points["Price"], color="green", s=80, marker="o", label="Buy")
        ax.scatter(sell_points["Date"], sell_points["Price"], color="red", s=80, marker="o", label="Sell")

    ax.set_title("MSFT Price with Moving Averages")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.xticks(rotation=45)

    st.pyplot(fig)


page = st.sidebar.radio("Navigation", ["Price Chart", "Trade Statistics", "Detailed Trades"])


data, positions = load_strategy_data()

if page == "Price Chart":
    st.title("Price Chart")
    st.caption("Whole-period stock price with 50-day MA, 200-day MA, and trade entry/exit markers.")
    draw_price_chart(data, positions)

elif page == "Trade Statistics":
    st.title("Trade Statistics")
    summary = compute_summary(positions)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trades", summary["total_trades"])
    col2.metric("Winning Trades", summary["winning_trades"])
    col3.metric("Losing Trades", summary["losing_trades"])
    col4.metric("Win Rate", f"{summary['win_rate']:.2f}%")

    col5, col6 = st.columns(2)
    col5.metric("Average Profit", f"{summary['average_profit']:.2f}%")
    col6.metric("Average Holding Days", f"{summary['average_holding_days']:.1f} days")

    if not positions.empty:
        st.subheader("Summary Table")
        summary_table = pd.DataFrame(
            [
                {
                    "Total Trades": summary["total_trades"],
                    "Winning Trades": summary["winning_trades"],
                    "Losing Trades": summary["losing_trades"],
                    "Win Rate (%)": round(summary["win_rate"], 2),
                    "Average Profit (%)": round(summary["average_profit"], 2),
                    "Average Holding Days": round(summary["average_holding_days"], 2),
                }
            ]
        )
        st.dataframe(summary_table, use_container_width=True)

else:
    st.title("Detailed Trades")
    if positions.empty:
        st.info("No trade signals were detected for the selected stock.")
    else:
        display_df = positions.copy()
        display_df["BuyDate"] = pd.to_datetime(display_df["BuyDate"]).dt.strftime("%Y-%m-%d")
        display_df["SellDate"] = pd.to_datetime(display_df["SellDate"]).dt.strftime("%Y-%m-%d")
        display_df["ProfitPct"] = display_df["ProfitPct"].map(lambda x: f"{x:.2f}%")
        st.dataframe(display_df, use_container_width=True)
