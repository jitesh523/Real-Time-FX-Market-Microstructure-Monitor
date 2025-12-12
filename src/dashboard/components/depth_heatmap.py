"""Market depth heatmap component."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import Dict


def render_depth_heatmap(orderbook: Dict, symbol: str):
    """
    Render market depth heatmap.
    
    Args:
        orderbook: Order book dictionary
        symbol: Currency pair symbol
    """
    if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
        st.warning("No order book data available for heatmap")
        return
    
    # Prepare data
    bids = orderbook['bids'][:10]
    asks = orderbook['asks'][:10]
    
    # Create price levels and sizes
    bid_prices = [b['price'] for b in bids]
    bid_sizes = [b['size'] for b in bids]
    
    ask_prices = [a['price'] for a in asks]
    ask_sizes = [a['size'] for a in asks]
    
    # Combine for heatmap
    all_prices = bid_prices + ask_prices
    all_sizes = bid_sizes + ask_sizes
    all_sides = ['Bid'] * len(bid_prices) + ['Ask'] * len(ask_prices)
    
    # Create DataFrame
    df = pd.DataFrame({
        'Price': all_prices,
        'Size': all_sizes,
        'Side': all_sides
    })
    
    # Depth heatmap
    st.markdown(f"### 🔥 Market Depth Heatmap - {symbol}")
    
    fig = go.Figure()
    
    # Bid side
    fig.add_trace(go.Bar(
        y=bid_prices,
        x=bid_sizes,
        orientation='h',
        name='Bids',
        marker=dict(
            color=bid_sizes,
            colorscale='Greens',
            showscale=False
        ),
        hovertemplate='Price: %{y:.5f}<br>Size: %{x:.2f}<extra></extra>'
    ))
    
    # Ask side
    fig.add_trace(go.Bar(
        y=ask_prices,
        x=[-s for s in ask_sizes],  # Negative for left side
        orientation='h',
        name='Asks',
        marker=dict(
            color=ask_sizes,
            colorscale='Reds',
            showscale=False
        ),
        hovertemplate='Price: %{y:.5f}<br>Size: %{x:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        barmode='overlay',
        xaxis_title="Size (Bids → | ← Asks)",
        yaxis_title="Price Level",
        height=500,
        showlegend=True,
        hovermode='y unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Cumulative depth chart
    st.markdown("### 📈 Cumulative Depth")
    
    # Calculate cumulative depths
    bid_cumulative = np.cumsum(bid_sizes)
    ask_cumulative = np.cumsum(ask_sizes)
    
    fig_cumulative = go.Figure()
    
    # Bid cumulative
    fig_cumulative.add_trace(go.Scatter(
        x=bid_prices,
        y=bid_cumulative,
        mode='lines+markers',
        name='Bid Cumulative',
        line=dict(color='green', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 0, 0.1)'
    ))
    
    # Ask cumulative
    fig_cumulative.add_trace(go.Scatter(
        x=ask_prices,
        y=ask_cumulative,
        mode='lines+markers',
        name='Ask Cumulative',
        line=dict(color='red', width=3),
        fill='tozeroy',
        fillcolor='rgba(255, 0, 0, 0.1)'
    ))
    
    fig_cumulative.update_layout(
        xaxis_title="Price",
        yaxis_title="Cumulative Size",
        height=350,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_cumulative, use_container_width=True)
    
    # Depth statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_bid = bid_prices[0] if bid_prices else 0
        best_ask = ask_prices[0] if ask_prices else 0
        mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0
        st.metric("Mid Price", f"{mid_price:.5f}")
    
    with col2:
        spread = best_ask - best_bid if best_bid and best_ask else 0
        spread_bps = (spread / mid_price * 10000) if mid_price > 0 else 0
        st.metric("Spread", f"{spread_bps:.2f} bps")
    
    with col3:
        total_bid_depth = sum(bid_sizes)
        total_ask_depth = sum(ask_sizes)
        depth_ratio = total_bid_depth / total_ask_depth if total_ask_depth > 0 else 0
        st.metric("Bid/Ask Ratio", f"{depth_ratio:.2f}")
