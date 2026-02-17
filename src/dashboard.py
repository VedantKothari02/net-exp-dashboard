import streamlit as st
import pandas as pd
import logging
import sys
import os

# Add src to sys.path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from collector import DataCollector
except ImportError:
    st.error("Could not import DataCollector. Make sure you are running from the project root or 'src' directory.")
    DataCollector = None

# Configure logging to capture output
logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Network Experience Dashboard", layout="wide")

st.title("Network Experience Dashboard")

st.sidebar.header("Configuration")
fmg_url = st.sidebar.text_input("FMG URL", value="https://fmg.example.com")
fmg_user = st.sidebar.text_input("Username", value="admin")
fmg_pass = st.sidebar.text_input("Password", type="password")
fmg_adom = st.sidebar.text_input("ADOM", value="root")

# Initialize session state for dataframe
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

if st.sidebar.button("Fetch Data"):
    if not fmg_url or not fmg_user or not fmg_pass:
        st.error("Please provide all credentials.")
    elif DataCollector is None:
        st.error("DataCollector module is missing. Cannot fetch data.")
    else:
        with st.spinner("Connecting to FMG and fetching data from 260+ sites... This may take a moment."):
            try:
                collector = DataCollector(fmg_url, fmg_user, fmg_pass, verify_ssl=False, adom=fmg_adom)
                fetched_df = collector.fetch_all_data()

                if fetched_df.empty:
                    st.warning("No data found or login failed.")
                else:
                    st.success(f"Successfully fetched data for {len(fetched_df)} sites.")
                    st.session_state.df = fetched_df

            except Exception as e:
                st.error(f"An error occurred: {e}")
                logger.exception("Error in dashboard")

# Display Data if available
if not st.session_state.df.empty:
    df = st.session_state.df

    # Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    total_sites = len(df)
    up_sites = len(df[df['status'] == 'UP'])
    down_sites = total_sites - up_sites

    switches_total = df['switches_total'].sum()
    switches_up = df['switches_up'].sum()
    aps_total = df['aps_total'].sum()
    aps_up = df['aps_up'].sum()

    col1.metric("Total Sites", total_sites)
    col2.metric("Sites UP", up_sites)
    col3.metric("Sites DOWN", down_sites, delta_color="inverse")
    col4.metric("Switches UP", f"{switches_up}/{switches_total}")
    col5.metric("APs UP", f"{aps_up}/{aps_total}")

    # Search
    search_term = st.text_input("Search by Site Name or Serial", "")
    if search_term:
        df_display = df[df['name'].str.contains(search_term, case=False) | df['serial'].str.contains(search_term, case=False)]
    else:
        df_display = df

    # Main Table
    st.dataframe(df_display.style.map(lambda x: 'color: red' if x == 'DOWN' or x == 'Unreachable' else 'color: green', subset=['status']))

    # Detailed View
    st.subheader("Granular Data Analysis")
    # Dropdown for selecting site, keep state if possible
    site_options = df_display['name'].unique()
    selected_site = st.selectbox("Select a site for details", site_options)

    if selected_site:
        site_data = df[df['name'] == selected_site].iloc[0]

        col_d1, col_d2 = st.columns(2)
        with col_d1:
             st.info(f"Site Status: {site_data['status']}")
             st.write(f"CPU: {site_data['cpu']}% | Memory: {site_data['mem']}%")
        with col_d2:
             st.write(f"Switches: {site_data['switches_up']}/{site_data['switches_total']} Online")
             if 'switches_down_list' in site_data and site_data['switches_down_list']:
                 st.error(f"Down Switches: {', '.join(site_data['switches_down_list'])}")

             st.write(f"APs: {site_data['aps_up']}/{site_data['aps_total']} Online")
             if 'aps_down_list' in site_data and site_data['aps_down_list']:
                 st.error(f"Down APs: {', '.join(site_data['aps_down_list'])}")

        with st.expander("Raw Data"):
            st.json(site_data.to_dict())

        st.info("ZDX Data Integration: Pending API Access or Report Parsing implementation.")

st.sidebar.markdown("---")
st.sidebar.info("Note: This dashboard uses FMG Proxy to fetch live data from devices without direct access.")
