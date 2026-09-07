#!/usr/bin/env python3
"""
Plot causality & topology diagrams for MPI Ring trace analysis.

Generates:
  - report/figures/mpi_ring_topology.pdf/.png
  - report/figures/mpi_ring_causality_timeline.pdf/.png
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from plot_ring_topology import generate_causality_timeline, generate_topology_diagram


def generate_causality_diagram(events=None):
    """Generate ring topology and causality timeline diagrams."""
    generate_topology_diagram()
    generate_causality_timeline()


if __name__ == "__main__":
    generate_causality_diagram()
