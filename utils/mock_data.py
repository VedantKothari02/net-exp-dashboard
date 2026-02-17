import random
from sqlalchemy.orm import Session
from database.db import SiteStatus, get_session, init_db
from analysis.scoring import calculate_score
from datetime import datetime

def generate_mock_data(num_sites=260):
    """Generates mock data for the specified number of sites."""
    session = get_session()

    # Clear existing data
    session.query(SiteStatus).delete()
    session.commit()

    sites = []
    for i in range(1, num_sites + 1):
        site_id = f"SITE-{i:03d}"
        site_name = f"Branch Office {i}"

        # Randomize Network Conditions
        rand = random.random()

        # 80% Healthy
        if rand < 0.8:
            wan_status = True
            latency = random.uniform(5, 45)
            packet_loss = 0.0
            jitter = random.uniform(1, 8)
            switch_status = True
            ap_status = True

        # 10% High Latency / Jitter
        elif rand < 0.9:
            wan_status = True
            latency = random.uniform(55, 150)
            packet_loss = random.uniform(0, 0.5)
            jitter = random.uniform(12, 30)
            switch_status = True
            ap_status = True

        # 5% Packet Loss
        elif rand < 0.95:
            wan_status = True
            latency = random.uniform(40, 80)
            packet_loss = random.uniform(1, 5)
            jitter = random.uniform(5, 15)
            switch_status = True
            ap_status = True

        # 3% Device Failure (LAN)
        elif rand < 0.98:
            wan_status = True
            latency = random.uniform(20, 50)
            packet_loss = 0.0
            jitter = random.uniform(2, 10)
            # Randomly fail switch or AP
            if random.random() < 0.5:
                switch_status = False
                ap_status = True # Often dependent, but let's keep simple
            else:
                switch_status = True
                ap_status = False

        # 2% Critical Failure (WAN Down)
        else:
            wan_status = False
            latency = 0.0
            packet_loss = 0.0
            jitter = 0.0
            switch_status = True # LAN might still be up locally
            ap_status = True

        metrics = {
            'wan_status': wan_status,
            'lan_switch_status': switch_status,
            'lan_ap_status': ap_status,
            'latency_ms': latency,
            'packet_loss_pct': packet_loss,
            'jitter_ms': jitter
        }

        score = calculate_score(metrics)

        site = SiteStatus(
            site_id=site_id,
            site_name=site_name,
            wan_status=wan_status,
            latency_ms=round(latency, 2),
            packet_loss_pct=round(packet_loss, 2),
            jitter_ms=round(jitter, 2),
            lan_switch_status=switch_status,
            lan_ap_status=ap_status,
            zdx_score=score,
            timestamp=datetime.utcnow()
        )
        sites.append(site)

    session.add_all(sites)
    session.commit()
    print(f"Generated data for {len(sites)} sites.")
    session.close()

if __name__ == "__main__":
    init_db()
    generate_mock_data()
