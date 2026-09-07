#!/usr/bin/env python3
"""
Plot causality & topology diagrams for MPI Ring trace analysis.
"""

import sys
from pathlib import Path
from plot_ring_topology import generate_topology_diagram

def generate_causality_diagram(events=None):
    """
    Generate ring topology and causality visualizers.
    """
    generate_topology_diagram()

if __name__ == "__main__":
    generate_causality_diagram()
