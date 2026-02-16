import pytest
from analysis.scoring import calculate_score

def test_perfect_score():
    metrics = {
        'wan_status': True,
        'lan_switch_status': True,
        'lan_ap_status': True,
        'latency_ms': 20,
        'packet_loss_pct': 0,
        'jitter_ms': 5
    }
    assert calculate_score(metrics) == 100.0

def test_high_latency_penalty():
    # Latency 150ms -> (150-50)/10 = 10 pts penalty
    metrics = {
        'wan_status': True,
        'lan_switch_status': True,
        'lan_ap_status': True,
        'latency_ms': 150,
        'packet_loss_pct': 0,
        'jitter_ms': 5
    }
    assert calculate_score(metrics) == 90.0

def test_packet_loss_penalty():
    # Packet Loss 2% -> 2 * 5 = 10 pts penalty
    metrics = {
        'wan_status': True,
        'lan_switch_status': True,
        'lan_ap_status': True,
        'latency_ms': 20,
        'packet_loss_pct': 2,
        'jitter_ms': 5
    }
    assert calculate_score(metrics) == 90.0

def test_device_down_penalty():
    # Switch Down -> -20 pts
    metrics = {
        'wan_status': True,
        'lan_switch_status': False,
        'lan_ap_status': True,
        'latency_ms': 20,
        'packet_loss_pct': 0,
        'jitter_ms': 5
    }
    assert calculate_score(metrics) == 80.0

def test_wan_down_critical():
    metrics = {
        'wan_status': False,
        'lan_switch_status': True,
        'lan_ap_status': True,
        'latency_ms': 0,
        'packet_loss_pct': 0,
        'jitter_ms': 0
    }
    assert calculate_score(metrics) == 0.0

def test_score_floor():
    # Massive penalties -> Score should not be negative
    metrics = {
        'wan_status': True,
        'lan_switch_status': False, # -20
        'lan_ap_status': False,     # -20
        'latency_ms': 500,          # -30 (cap)
        'packet_loss_pct': 20,      # -40 (cap)
        'jitter_ms': 100            # -10 (cap)
    }
    # Total deduction: 120 -> Score 0
    assert calculate_score(metrics) == 0.0
