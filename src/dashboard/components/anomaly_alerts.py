"""Anomaly alerts component."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict


def render_anomaly_alerts(metrics_data: List[Dict], threshold: float = 0.7):
    """
    Render anomaly detection alerts.
    
    Args:
        metrics_data: List of metrics dictionaries
        threshold: Anomaly score threshold
    """
    if not metrics_data:
        st.warning("No metrics data available")
        return
    
    df = pd.DataFrame(metrics_data)
    
    # Filter anomalies
    anomalies = df[df['is_anomaly'] == 1].copy()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_records = len(df)
        st.metric("Total Records", total_records)
    
    with col2:
        anomaly_count = len(anomalies)
        st.metric("Anomalies Detected", anomaly_count)
    
    with col3:
        if total_records > 0:
            anomaly_rate = (anomaly_count / total_records) * 100
            st.metric("Anomaly Rate", f"{anomaly_rate:.1f}%")
        else:
            st.metric("Anomaly Rate", "N/A")
    
    with col4:
        if not anomalies.empty and 'anomaly_score' in anomalies.columns:
            avg_score = anomalies['anomaly_score'].mean()
            st.metric("Avg Anomaly Score", f"{avg_score:.3f}")
        else:
            st.metric("Avg Anomaly Score", "N/A")
    
    # Recent anomalies
    st.markdown("### 🚨 Recent Anomalies")
    
    if anomalies.empty:
        st.success("✅ No anomalies detected in the selected time range")
    else:
        # Show most recent anomalies
        recent_anomalies = anomalies.tail(10).sort_values('timestamp', ascending=False)
        
        for _, anomaly in recent_anomalies.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    timestamp = anomaly['timestamp']
                    if isinstance(timestamp, str):
                        timestamp = pd.to_datetime(timestamp)
                    st.markdown(f"**{timestamp.strftime('%H:%M:%S')}**")
                
                with col2:
                    anomaly_type = anomaly.get('anomaly_type', 'Unknown')
                    if anomaly_type:
                        st.markdown(f"Type: `{anomaly_type}`")
                    else:
                        st.markdown("Type: `General Anomaly`")
                
                with col3:
                    score = anomaly.get('anomaly_score', 0)
                    if score:
                        st.markdown(f"Score: **{score:.3f}**")
                
                # Details expander
                with st.expander("Details"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.metric("Spread (bps)", f"{anomaly['spread_bps']:.2f}")
                        st.metric("Bid Depth", f"{anomaly['bid_depth']:.2f}")
                    
                    with col_b:
                        st.metric("Total Depth", f"{anomaly['total_depth']:.2f}")
                        st.metric("Flow Imbalance", f"{anomaly['order_flow_imbalance']:.3f}")
                
                st.markdown("---")
    
    # Anomaly timeline
    if not anomalies.empty:
        st.markdown("### 📅 Anomaly Timeline")
        
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Add all data points
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df.get('anomaly_score', [0] * len(df)),
            mode='markers',
            name='Normal',
            marker=dict(color='lightblue', size=5),
            opacity=0.5
        ))
        
        # Highlight anomalies
        fig.add_trace(go.Scatter(
            x=anomalies['timestamp'],
            y=anomalies.get('anomaly_score', [threshold] * len(anomalies)),
            mode='markers',
            name='Anomaly',
            marker=dict(color='red', size=10, symbol='x'),
        ))
        
        # Add threshold line
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Threshold ({threshold})"
        )
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Anomaly Score",
            height=300,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Anomaly type distribution
    if not anomalies.empty and 'anomaly_type' in anomalies.columns:
        st.markdown("### 📊 Anomaly Type Distribution")
        
        # Filter out None values
        type_counts = anomalies[anomalies['anomaly_type'].notna()]['anomaly_type'].value_counts()
        
        if not type_counts.empty:
            import plotly.express as px
            
            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Anomaly Types"
            )
            
            fig.update_layout(height=300)
            
            st.plotly_chart(fig, use_container_width=True)
