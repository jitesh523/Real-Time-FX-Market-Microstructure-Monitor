"""Enhanced dashboard with multi-symbol comparison."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.dashboard.utils import DataFetcher


def render_multi_symbol_comparison(symbols: list, minutes: int = 5):
    """
    Render multi-symbol comparison view.
    
    Args:
        symbols: List of currency pairs
        minutes: Time range in minutes
    """
    st.markdown("### 📊 Multi-Symbol Comparison")
    
    fetcher = DataFetcher()
    
    # Fetch data for all symbols
    all_data = {}
    for symbol in symbols:
        ticks = fetcher.get_recent_ticks(symbol, minutes=minutes)
        if ticks:
            all_data[symbol] = pd.DataFrame(ticks)
    
    if not all_data:
        st.warning("No data available for comparison")
        return
    
    # Price comparison
    fig_price = go.Figure()
    
    for symbol, df in all_data.items():
        fig_price.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['mid_price'],
            mode='lines',
            name=symbol,
            line=dict(width=2)
        ))
    
    fig_price.update_layout(
        title="Price Comparison",
        xaxis_title="Time",
        yaxis_title="Price",
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_price, use_container_width=True)
    
    # Spread comparison
    col1, col2 = st.columns(2)
    
    with col1:
        fig_spread = go.Figure()
        
        for symbol, df in all_data.items():
            fig_spread.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['spread_bps'],
                mode='lines',
                name=symbol
            ))
        
        fig_spread.update_layout(
            title="Spread Comparison (bps)",
            xaxis_title="Time",
            yaxis_title="Spread (bps)",
            height=300
        )
        
        st.plotly_chart(fig_spread, use_container_width=True)
    
    with col2:
        # Summary statistics
        st.markdown("#### Summary Statistics")
        
        summary_data = []
        for symbol, df in all_data.items():
            summary_data.append({
                'Symbol': symbol,
                'Avg Spread (bps)': df['spread_bps'].mean(),
                'Min Price': df['mid_price'].min(),
                'Max Price': df['mid_price'].max(),
                'Volatility': df['mid_price'].std()
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df.style.format({
            'Avg Spread (bps)': '{:.2f}',
            'Min Price': '{:.5f}',
            'Max Price': '{:.5f}',
            'Volatility': '{:.5f}'
        }), use_container_width=True)
