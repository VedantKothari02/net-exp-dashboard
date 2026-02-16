def calculate_score(metrics):
    """
    Calculates a Network Experience Score (0-100) based on raw metrics.

    metrics: dict containing:
        - wan_status: bool
        - lan_switch_status: bool
        - lan_ap_status: bool
        - latency_ms: float
        - packet_loss_pct: float
        - jitter_ms: float
    """

    # Critical Failure Check
    if not metrics.get('wan_status', False):
        return 0.0

    score = 100.0

    # Device Availability Penalties
    if not metrics.get('lan_switch_status', True):
        score -= 20

    if not metrics.get('lan_ap_status', True):
        score -= 20

    # Performance Penalties

    # Latency: Penalty starts if > 50ms.
    # Max penalty 30 points (at 350ms+).
    latency = metrics.get('latency_ms', 0)
    if latency > 50:
        penalty = (latency - 50) / 10
        score -= min(penalty, 30)

    # Packet Loss: Huge penalty.
    # Max penalty 40 points (at 8% loss).
    loss = metrics.get('packet_loss_pct', 0)
    if loss > 0:
        penalty = loss * 5
        score -= min(penalty, 40)

    # Jitter: Penalty starts if > 10ms.
    # Max penalty 10 points (at 60ms+).
    jitter = metrics.get('jitter_ms', 0)
    if jitter > 10:
        penalty = (jitter - 10) / 5
        score -= min(penalty, 10)

    return max(0.0, round(score, 1))

def get_health_status(score):
    """Returns a string status based on the score."""
    if score >= 90:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Fair"
    elif score > 0:
        return "Poor"
    else:
        return "Critical"
