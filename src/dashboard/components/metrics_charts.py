"""Metrics charts component."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict


def render_metrics_charts(metrics_data: List[Dict], tick_data: List[Dict] = None):
    """
    Render metrics charts.
    
    Args:
        metrics_data: List of metrics dictionaries
        tick_data: Optional list of tick dictionaries
    """
    if not metrics_data:
        st.warning("No metrics data available")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(metrics_data)
    
    # Spread chart
    st.markdown("### 📏 Bid-Ask Spread")
    fig_spread = go.Figure()
    
    fig_spread.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['spread_bps'],
        mode='lines',
        name='Spread (bps)',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 100, 200, 0.2)'
    ))
    
    fig_spread.update_layout(
        xaxis_title="Time",
        yaxis_title="Spread (basis points)",
        height=300,
        hovermode='x unified',
        showlegend=False
    )
    
    st.plotly_chart(fig_spread, use_container_width=True)
    
    # Depth and Imbalance
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Market Depth")
        fig_depth = go.Figure()
        
        fig_depth.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['bid_depth'],
            mode='lines',
            name='Bid Depth',
            line=dict(color='green', width=2),
            stackgroup='one'
        ))
        
        fig_depth.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['ask_depth'],
            mode='lines',
            name='Ask Depth',
            line=dict(color='red', width=2),
            stackgroup='one'
        ))
        
        fig_depth.update_layout(
            xaxis_title="Time",
            yaxis_title="Depth",
            height=300,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_depth, use_container_width=True)
    
    with col2:
        st.markdown("### ⚖️ Order Flow Imbalance")
        fig_imbalance = go.Figure()
        
        fig_imbalance.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['order_flow_imbalance'],
            mode='lines',
            name='Imbalance',
            line=dict(color='purple', width=2),
            fill='tozeroy'
        ))
        
        # Add zero line
        fig_imbalance.add_hline(y=0, line_dash="dash", line_color="gray")
        
        fig_imbalance.update_layout(
            xaxis_title="Time",
            yaxis_title="Imbalance",
            height=300,
            hovermode='x unified',
            showlegend=False
        )
        
        st.plotly_chart(fig_imbalance, use_container_width=True)
    
    # Volatility (if available)
    if 'volatility' in df.columns and df['volatility'].notna().any():
        st.markdown("### 📈 Volatility")
        fig_vol = go.Figure()
        
        # Filter out None values
        vol_df = df[df['volatility'].notna()].copy()
        
        fig_vol.add_trace(go.Scatter(
            x=vol_df['timestamp'],
            y=vol_df['volatility'],
            mode='lines',
            name='Volatility',
            line=dict(color='orange', width=2)
        ))
        
        fig_vol.update_layout(
            xaxis_title="Time",
            yaxis_title="Volatility",
            height=300,
            hovermode='x unified',
            showlegend=False
        ))
        
        st.plotly_chart(fig_vol, use_container_width=True)
    
    # Price chart (if tick data available)
    if tick_data:
        st.markdown("### 💹 Price Movement")
        tick_df = pd.DataFrame(tick_data)
        
        fig_price = go.Figure()
        
        fig_price.add_trace(go.Scatter(
            x=tick_df['timestamp'],
            y=tick_df['mid_price'],
            mode='lines',
            name='Mid Price',
            line=dict(color='darkblue', width=2)
        ))
        
        # Add bid/ask bands
        fig_price.add_trace(go.Scatter(
            x=tick_df['timestamp'],
            y=tick_df['bid'],
            mode='lines',
            name='Bid',
            line=dict(color='green', width=1, dash='dot'),
            opacity=0.5
        ))
        
        fig_price.add_trace(go.Scatter(
            x=tick_df['timestamp'],
            y=tick_df['ask'],
            mode='lines',
            name='Ask',
            line=dict(color='red', width=1, dash='dot'),
            opacity=0.5,
            fill='tonexty',
            fillcolor='rgba(200, 200, 200, 0.2)'
        ))
        
        fig_price.update_layout(
            xaxis_title="Time",
            yaxis_title="Price",
            height=350,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_price, use_container_width=True)
