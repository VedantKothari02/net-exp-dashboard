from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Create the SQLite database file
DB_FILE = 'network_dashboard.db'
if os.path.exists(DB_FILE):
    # For now, we don't want to wipe the db every time, but for dev it's okay if needed.
    pass

engine = create_engine(f'sqlite:///{DB_FILE}', echo=False)
Base = declarative_base()

class SiteStatus(Base):
    __tablename__ = 'site_status'

    id = Column(Integer, primary_key=True)
    site_id = Column(String, unique=True, nullable=False)
    site_name = Column(String, nullable=False)

    # WAN Metrics (from FortiManager/FortiGate)
    wan_status = Column(Boolean, default=True) # True = UP, False = DOWN
    latency_ms = Column(Float, default=0.0)
    packet_loss_pct = Column(Float, default=0.0)
    jitter_ms = Column(Float, default=0.0)

    # LAN Metrics (from FortiManager/Switch/AP)
    lan_switch_status = Column(Boolean, default=True) # True = UP
    lan_ap_status = Column(Boolean, default=True) # True = UP

    # ZDX / Experience Metrics
    zdx_score = Column(Float, default=0.0) # Calculated or scraped score

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'site_id': self.site_id,
            'site_name': self.site_name,
            'wan_status': 'UP' if self.wan_status else 'DOWN',
            'latency_ms': self.latency_ms,
            'packet_loss_pct': self.packet_loss_pct,
            'jitter_ms': self.jitter_ms,
            'lan_switch_status': 'UP' if self.lan_switch_status else 'DOWN',
            'lan_ap_status': 'UP' if self.lan_ap_status else 'DOWN',
            'zdx_score': self.zdx_score,
            'timestamp': self.timestamp
        }

def init_db():
    """Initializes the database, creating tables if they don't exist."""
    Base.metadata.create_all(engine)

def get_session():
    """Returns a new SQLAlchemy session."""
    Session = sessionmaker(bind=engine)
    return Session()
