import argparse
import os
import time
from database.db import init_db
from utils.mock_data import generate_mock_data

def run_mock_collection():
    print("Running Mock Data Collection...")
    generate_mock_data()
    print("Mock Data Collection Complete.")

def run_real_collection():
    print("Running Real Data Collection from Scrapers...")

    # Import Scrapers
    try:
        from collectors.fmg_proxy_collector import FMGProxyCollector
        from collectors.zdx_scraper import ZDXScraper
        from collectors.faz_scraper import FAZScraper

        # Configuration
        FMG_URL = os.getenv("FMG_URL", "https://fmg.example.com")
        FMG_USER = os.getenv("FMG_USER", "admin")
        FMG_PASS = os.getenv("FMG_PASS", "password")

        ZDX_URL = os.getenv("ZDX_URL", "https://admin.zdxcloud.net")
        ZDX_USER = os.getenv("ZDX_USER", "admin@example.com")
        ZDX_PASS = os.getenv("ZDX_PASS", "password")

        FAZ_URL = os.getenv("FAZ_URL", "https://faz.example.com")
        FAZ_USER = os.getenv("FAZ_USER", "admin")
        FAZ_PASS = os.getenv("FAZ_PASS", "password")

        # Run FMG Proxy Collector
        # fmg = FMGProxyCollector(FMG_URL, FMG_USER, FMG_PASS, headless=False)
        # fmg.run()

        # Run ZDX Scraper
        # zdx = ZDXScraper(ZDX_URL, ZDX_USER, ZDX_PASS, headless=False)
        # zdx.run()

        # Run FAZ Scraper
        # faz = FAZScraper(FAZ_URL, FAZ_USER, FAZ_PASS, headless=False)
        # faz.run()

        print("Real Data Collection logic is currently commented out. Please configure URLs and Credentials in main.py.")

    except ImportError as e:
        print(f"Error importing scrapers: {e}")

def main():
    parser = argparse.ArgumentParser(description="Network Experience Dashboard Data Collector")
    parser.add_argument("--mode", choices=["mock", "real"], default="mock", help="Data collection mode")
    parser.add_argument("--init-db", action="store_true", help="Initialize the database")

    args = parser.parse_args()

    if args.init_db:
        print("Initializing Database...")
        init_db()

    if args.mode == "mock":
        run_mock_collection()
    elif args.mode == "real":
        run_real_collection()

if __name__ == "__main__":
    main()
