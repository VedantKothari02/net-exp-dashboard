import streamlit as st
import pandas as pd
from database.db import get_session, SiteStatus, init_db
from analysis.scoring import get_health_status

st.set_page_config(page_title="Network Experience Dashboard", layout="wide")

@st.cache_data
def load_data():
    session = get_session()
    # Check if table exists
    try:
        sites = session.query(SiteStatus).all()
        data = [s.to_dict() for s in sites]
    except Exception as e:
        data = []
    finally:
        session.close()
    return pd.DataFrame(data)

def main():
    st.title("Network Experience Dashboard")

    # Load Data
    df = load_data()

    if df.empty:
        st.warning("No data found. Please generate mock data or run collectors.")
        if st.button("Generate Mock Data"):
            from utils.mock_data import generate_mock_data
            init_db()
            generate_mock_data()
            st.rerun()
        return

    # Calculate Status if not present
    if 'health_status' not in df.columns:
        df['health_status'] = df['zdx_score'].apply(get_health_status)

    # Summary Metrics
    total_sites = len(df)
    critical_sites = len(df[df['health_status'] == 'Critical'])
    poor_sites = len(df[df['health_status'] == 'Poor'])
    good_sites = len(df[df['health_status'].isin(['Good', 'Excellent'])])
    avg_score = df['zdx_score'].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sites", total_sites)
    col2.metric("Avg Experience Score", f"{avg_score:.1f}")
    col3.metric("Critical Issues", critical_sites, delta_color="inverse")
    col4.metric("Healthy Sites", good_sites)

    st.markdown("---")

    # Filters
    st.sidebar.header("Filters")
    status_filter = st.sidebar.multiselect(
        "Filter by Status",
        options=['Excellent', 'Good', 'Fair', 'Poor', 'Critical'],
        default=['Excellent', 'Good', 'Fair', 'Poor', 'Critical']
    )

    search_term = st.sidebar.text_input("Search Site ID or Name")

    # Apply Filters
    filtered_df = df[df['health_status'].isin(status_filter)]
    if search_term:
        filtered_df = filtered_df[
            filtered_df['site_id'].str.contains(search_term, case=False) |
            filtered_df['site_name'].str.contains(search_term, case=False)
        ]

    # Main Table
    st.subheader("Site Overview")

    if filtered_df.empty:
        if search_term:
            st.info(f"No sites found matching \"{search_term}\" with the selected filters.")
        else:
            st.info("No sites found with the selected filters.")
        st.markdown("Try adjusting your filters or search term.")
        return

    st.dataframe(
        filtered_df[['site_id', 'site_name', 'health_status', 'zdx_score', 'wan_status', 'lan_switch_status', 'lan_ap_status']],
        column_config={
            "site_id": st.column_config.TextColumn("Site ID", help="Unique identifier for the site"),
            "site_name": st.column_config.TextColumn("Site Name", help="Name of the branch or location"),
            "health_status": st.column_config.TextColumn("Health", help="Overall calculated health status"),
            "zdx_score": st.column_config.ProgressColumn(
                "Experience Score",
                help="Network Experience Score (0-100)",
                format="%d",
                min_value=0,
                max_value=100,
            ),
            "wan_status": st.column_config.TextColumn("WAN", help="Wide Area Network connection status"),
            "lan_switch_status": st.column_config.TextColumn("Switch", help="Local Area Network switch status"),
            "lan_ap_status": st.column_config.TextColumn("Access Point", help="Wireless Access Point status"),
        },
        use_container_width=True,
        hide_index=True
    )

    # Detail View
    st.markdown("---")
    st.subheader("Site Diagnostics")

    # Dropdown to select site
    site_options = filtered_df['site_id'].unique()
    selected_site_id = st.selectbox("Select Site for Details", site_options) if len(site_options) > 0 else None

    if selected_site_id:
        # Get the row for the selected site
        site_row = filtered_df[filtered_df['site_id'] == selected_site_id].iloc[0]

        c1, c2 = st.columns([1, 2])

        with c1:
            st.metric("Experience Score", f"{site_row['zdx_score']}", delta=site_row['health_status'])
            st.write(f"**Status:** {site_row['health_status']}")
            st.write(f"**Last Updated:** {site_row['timestamp']}")

        with c2:
            st.write("#### Metrics Breakdown")

            # WAN Health
            wan_status_str = "UP" if site_row['wan_status'] == 'UP' or site_row['wan_status'] is True else "DOWN"
            if wan_status_str == 'UP':
                st.success(f"WAN Link UP | Latency: {site_row['latency_ms']}ms | Loss: {site_row['packet_loss_pct']}% | Jitter: {site_row['jitter_ms']}ms")
            else:
                st.error("WAN Link DOWN")

            # LAN Health
            col_a, col_b = st.columns(2)
            with col_a:
                sw_status = "UP" if site_row['lan_switch_status'] == 'UP' or site_row['lan_switch_status'] is True else "DOWN"
                if sw_status == 'UP':
                    st.success("Switch: UP")
                else:
                    st.error("Switch: DOWN")
            with col_b:
                ap_status = "UP" if site_row['lan_ap_status'] == 'UP' or site_row['lan_ap_status'] is True else "DOWN"
                if ap_status == 'UP':
                    st.success("Access Point: UP")
                else:
                    st.error("Access Point: DOWN")

            # Diagnostic Logic
            st.write("#### Automated Root Cause Analysis")
            issues = []
            if wan_status_str == 'DOWN':
                st.error("🔴 **CRITICAL**: WAN Link is down. Check ISP or FortiGate interface.")
                issues.append("WAN Down")
            elif site_row['packet_loss_pct'] > 1.0:
                st.warning(f"🟠 **Performance**: High Packet Loss ({site_row['packet_loss_pct']}%). Check ISP quality or congestion.")
                issues.append("High Packet Loss")
            elif site_row['latency_ms'] > 100:
                st.warning(f"🟡 **Performance**: High Latency ({site_row['latency_ms']}ms). Possible congestion or routing issue.")
                issues.append("High Latency")

            if sw_status == 'DOWN':
                st.error("🔴 **LAN**: Core Switch is unreachable. Check power or uplink.")
                issues.append("Switch Down")
            if ap_status == 'DOWN':
                st.error("🔴 **WIFI**: Access Point is unreachable. Check PoE or switch port.")
                issues.append("AP Down")

            if not issues:
                st.info("✅ No significant issues detected.")

if __name__ == "__main__":
    main()
