"""Tutorial mode architecture placeholder."""

class TutorialMode:
    """Guided step-by-step tutorial mode (Planned for Phase 2)."""

    def __init__(self):
        self.mode_name: str = "Tutorial Mode"
        self.is_active: bool = False
        self.current_step: int = 0
        self.steps = [
            "Walk to Rack A and inspect empty U slots.",
            "Install a Router at U1-U2 and a Switch at U4.",
            "Patch an Ethernet cable from Router Gi0/0 to Switch Gi0/1.",
            "Open the CLI console and configure the interface IP address.",
            "Send an ICMP ping to verify end-to-end reachability."
        ]
