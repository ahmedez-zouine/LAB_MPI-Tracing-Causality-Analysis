#!/usr/bin/env python3
"""
Generate publication-grade MPI Token Ring diagrams (topology + causality timeline).
Compiles the TikZ sources under report/figures/ and crops them to tight PNGs.
"""

import os
import subprocess
import sys
from pathlib import Path


def compile_tex(tex_path: Path) -> Path:
    pdflatex_bin = "/Library/TeX/texbin/pdflatex"
    if not os.path.exists(pdflatex_bin):
        pdflatex_bin = "pdflatex"

    print(f"Compiling {tex_path.name} with pdflatex...")
    res = subprocess.run(
        [pdflatex_bin, "-interaction=nonstopmode", tex_path.name],
        cwd=tex_path.parent,
        capture_output=True,
        text=True,
    )
    pdf_path = tex_path.with_suffix(".pdf")
    if res.returncode != 0 or not pdf_path.exists():
        print(f"pdflatex warning/error: {res.stderr}")
        print(res.stdout[-2000:])
        sys.exit(1)
    return pdf_path


def pdf_to_cropped_png(pdf_path: Path, png_path: Path) -> None:
    import fitz
    from PIL import Image
    import numpy as np

    doc = fitz.open(str(pdf_path))
    page = doc[0]
    pix = page.get_pixmap(dpi=300)
    raw_png = pdf_path.with_name(pdf_path.stem + "_raw.png")
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
    raw_png.unlink(missing_ok=True)
    print(f"Generated {png_path.name} ({cropped.size[0]}x{cropped.size[1]})")


def generate_diagram(stem: str) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    figures_dir = repo_root / "report" / "figures"
    tex_path = figures_dir / f"{stem}.tex"

    if not tex_path.exists():
        print(f"Error: {tex_path} not found.")
        sys.exit(1)

    pdf_path = compile_tex(tex_path)
    pdf_path = tex_path.with_suffix(".pdf")
    try:
        pdf_to_cropped_png(pdf_path, figures_dir / f"{stem}.png")
    except Exception as e:
        print(f"Error converting {stem} to cropped PNG: {e}")


def generate_topology_diagram():
    generate_diagram("mpi_ring_topology")


def generate_causality_timeline():
    generate_diagram("mpi_ring_causality_timeline")


if __name__ == "__main__":
    generate_topology_diagram()
    generate_causality_timeline()
