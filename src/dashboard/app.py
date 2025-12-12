"""Main Streamlit dashboard application for FX Market Microstructure Monitor."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

from config import settings
from src.dashboard.components.orderbook_viz import render_orderbook
from src.dashboard.components.metrics_charts import render_metrics_charts
from src.dashboard.components.anomaly_alerts import render_anomaly_alerts
from src.dashboard.components.depth_heatmap import render_depth_heatmap
from src.dashboard.utils.data_fetcher import DataFetcher


# Page configuration
st.set_page_config(
    page_title="FX Market Microstructure Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .anomaly-alert {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .status-good {
        color: #4caf50;
        font-weight: bold;
    }
    .status-warning {
        color: #ff9800;
        font-weight: bold;
    }
    .status-bad {
        color: #f44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main dashboard application."""
    
    # Header
    st.markdown('<div class="main-header">📊 FX Market Microstructure Monitor</div>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Symbol selection
        selected_symbol = st.selectbox(
            "Currency Pair",
            settings.currency_pairs_list,
            index=0
        )
        
        # Refresh interval
        refresh_interval = st.slider(
            "Refresh Interval (seconds)",
            min_value=1,
            max_value=10,
            value=settings.refresh_interval_seconds
        )
        
        # Time range
        time_range = st.selectbox(
            "Time Range",
            ["Last 1 minute", "Last 5 minutes", "Last 15 minutes", "Last 1 hour"],
            index=1
        )
        
        # Anomaly detection settings
        st.subheader("🔍 Anomaly Detection")
        enable_anomaly_detection = st.checkbox("Enable Anomaly Detection", value=True)
        anomaly_threshold = st.slider(
            "Anomaly Threshold",
            min_value=0.5,
            max_value=1.0,
            value=0.7,
            step=0.05
        )
        
        # Database connection status
        st.subheader("📡 Status")
        data_fetcher = DataFetcher()
        
        if data_fetcher.is_connected():
            st.success("✅ Connected to ClickHouse")
        else:
            st.error("❌ Database connection failed")
    
    # Main content
    try:
        # Convert time range to minutes
        time_range_map = {
            "Last 1 minute": 1,
            "Last 5 minutes": 5,
            "Last 15 minutes": 15,
            "Last 1 hour": 60
        }
        minutes = time_range_map[time_range]
        
        # Fetch data
        with st.spinner("Loading data..."):
            tick_data = data_fetcher.get_recent_ticks(selected_symbol, minutes=minutes)
            orderbook_data = data_fetcher.get_recent_orderbook(selected_symbol)
            metrics_data = data_fetcher.get_recent_metrics(selected_symbol, minutes=minutes)
        
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        if tick_data and len(tick_data) > 0:
            latest_tick = tick_data[-1]
            
            with col1:
                st.metric(
                    label="Mid Price",
                    value=f"{latest_tick['mid_price']:.5f}",
                    delta=f"{latest_tick['spread_bps']:.2f} bps"
                )
            
            with col2:
                st.metric(
                    label="Spread (bps)",
                    value=f"{latest_tick['spread_bps']:.2f}",
                    delta=None
                )
            
            with col3:
                if metrics_data and len(metrics_data) > 0:
                    latest_metrics = metrics_data[-1]
                    st.metric(
                        label="Total Depth",
                        value=f"{latest_metrics['total_depth']:.2f}",
                        delta=None
                    )
            
            with col4:
                if metrics_data and len(metrics_data) > 0:
                    quality_score = 85.0  # Placeholder
                    st.metric(
                        label="Market Quality",
                        value=f"{quality_score:.0f}/100",
                        delta=None
                    )
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Live Metrics",
            "📚 Order Book",
            "🚨 Anomaly Detection",
            "🔥 Market Depth"
        ])
        
        with tab1:
            st.subheader(f"Real-Time Metrics - {selected_symbol}")
            if metrics_data and len(metrics_data) > 0:
                render_metrics_charts(metrics_data, tick_data)
            else:
                st.info("No metrics data available. Start the data pipeline to see real-time metrics.")
        
        with tab2:
            st.subheader(f"Order Book - {selected_symbol}")
            if orderbook_data:
                render_orderbook(orderbook_data)
            else:
                st.info("No order book data available.")
        
        with tab3:
            st.subheader("Anomaly Detection & Alerts")
            if enable_anomaly_detection and metrics_data:
                render_anomaly_alerts(metrics_data, anomaly_threshold)
            else:
                st.info("Enable anomaly detection in the sidebar to see alerts.")
        
        with tab4:
            st.subheader("Market Depth Heatmap")
            if orderbook_data:
                render_depth_heatmap(orderbook_data, selected_symbol)
            else:
                st.info("No order book data available for heatmap.")
        
        # Auto-refresh
        st.empty()
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        st.error(f"An error occurred: {str(e)}")
        st.info("Make sure the data pipeline is running and ClickHouse is accessible.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Refresh interval: {refresh_interval}s"
    )


if __name__ == "__main__":
    main()
