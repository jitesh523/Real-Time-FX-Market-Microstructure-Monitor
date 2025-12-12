"""Order book visualization component."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Optional


def render_orderbook(orderbook: Dict):
    """
    Render order book visualization.
    
    Args:
        orderbook: Order book dictionary with bids and asks
    """
    if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
        st.warning("No order book data available")
        return
    
    col1, col2 = st.columns(2)
    
    # Bids table
    with col1:
        st.markdown("### 🟢 Bids")
        bids_df = pd.DataFrame(orderbook['bids'][:10])
        if not bids_df.empty:
            bids_df = bids_df[['price', 'size']]
            bids_df.columns = ['Price', 'Size']
            bids_df['Cumulative'] = bids_df['Size'].cumsum()
            st.dataframe(
                bids_df.style.format({'Price': '{:.5f}', 'Size': '{:.2f}', 'Cumulative': '{:.2f}'}),
                use_container_width=True,
                hide_index=True
            )
    
    # Asks table
    with col2:
        st.markdown("### 🔴 Asks")
        asks_df = pd.DataFrame(orderbook['asks'][:10])
        if not asks_df.empty:
            asks_df = asks_df[['price', 'size']]
            asks_df.columns = ['Price', 'Size']
            asks_df['Cumulative'] = asks_df['Size'].cumsum()
            st.dataframe(
                asks_df.style.format({'Price': '{:.5f}', 'Size': '{:.2f}', 'Cumulative': '{:.2f}'}),
                use_container_width=True,
                hide_index=True
            )
    
    # Depth chart
    st.markdown("### 📊 Order Book Depth")
    
    fig = go.Figure()
    
    # Bids
    if not bids_df.empty:
        fig.add_trace(go.Bar(
            x=bids_df['Price'],
            y=bids_df['Size'],
            name='Bids',
            marker_color='green',
            opacity=0.7
        ))
    
    # Asks
    if not asks_df.empty:
        fig.add_trace(go.Bar(
            x=asks_df['Price'],
            y=asks_df['Size'],
            name='Asks',
            marker_color='red',
            opacity=0.7
        ))
    
    fig.update_layout(
        title="Order Book Depth",
        xaxis_title="Price",
        yaxis_title="Size",
        barmode='group',
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Order book metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bid_depth = sum(b['size'] for b in orderbook['bids'])
        st.metric("Total Bid Depth", f"{bid_depth:.2f}")
    
    with col2:
        ask_depth = sum(a['size'] for a in orderbook['asks'])
        st.metric("Total Ask Depth", f"{ask_depth:.2f}")
    
    with col3:
        total_depth = bid_depth + ask_depth
        if total_depth > 0:
            imbalance = (bid_depth - ask_depth) / total_depth
            st.metric("Imbalance", f"{imbalance:.3f}")
        else:
            st.metric("Imbalance", "N/A")
