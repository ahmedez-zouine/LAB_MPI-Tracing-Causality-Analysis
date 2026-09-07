#!/usr/bin/env python3
"""
Generate publication-grade MPI Token Ring Topology & Measured Inter-Rank Latencies diagram.
Uses LaTeX / TikZ for vector-grade rendering, cropped tightly to bounding box.
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_topology_diagram():
    repo_root = Path(__file__).resolve().parent.parent
    figures_dir = repo_root / "report" / "figures"
    tex_path = figures_dir / "mpi_ring_topology.tex"
    pdf_path = figures_dir / "mpi_ring_topology.pdf"
    png_path = figures_dir / "mpi_ring_topology.png"

    if not tex_path.exists():
        print(f"Error: {tex_path} not found.")
        sys.exit(1)

    pdflatex_bin = "/Library/TeX/texbin/pdflatex"
    if not os.path.exists(pdflatex_bin):
        pdflatex_bin = "pdflatex"

    print("Compiling TikZ diagram with pdflatex...")
    cmd = [pdflatex_bin, "-interaction=nonstopmode", tex_path.name]
    res = subprocess.run(cmd, cwd=figures_dir, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"pdflatex warning/error: {res.stderr}")

    try:
        import fitz
        from PIL import Image
        import numpy as np

        doc = fitz.open(str(pdf_path))
        page = doc[0]
        pix = page.get_pixmap(dpi=300)
        raw_png = figures_dir / "mpi_ring_topology_raw.png"
        pix.save(str(raw_png))

        im = Image.open(str(raw_png)).convert("RGB")
        arr = np.array(im)
        mask = np.any(arr < 250, axis=2)
        coords = np.argwhere(mask)
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0) + 1

        pad = 35
        h, w, _ = arr.shape
        y0 = max(0, y0 - pad)
        x0 = max(0, x0 - pad)
        y1 = min(h, y1 + pad)
        x1 = min(w, x1 + pad)

        cropped = im.crop((x0, y0, x1, y1))
        cropped.save(str(png_path), "PNG", optimize=True)
        print(f"Successfully generated cropped PNG: {png_path} ({cropped.size[0]}x{cropped.size[1]})")
    except Exception as e:
        print(f"Error converting to cropped PNG: {e}")

if __name__ == "__main__":
    generate_topology_diagram()
