"""
PDF 4-in-1 / N-up Slide Layout Converter
Converts slide-based PDFs (e.g., PowerPoint handouts) into multi-slide per page PDFs
(such as 4 slides on 1 A4 Landscape page in a clean 2x2 grid).

Author: Antigravity AI
"""

import os
import sys
import math
import argparse
import fitz  # PyMuPDF


def convert_pdf_to_4in1(
    input_pdf_path: str,
    output_pdf_path: str = None,
    layout: str = "4in1",
    draw_border: bool = True,
    draw_white_bg: bool = True,
    border_color=(0.8, 0.8, 0.8),
    border_width=0.5,
) -> str:
    """
    Converts input PDF into 4-in-1 (or 2-in-1 / 6-in-1) printable handout PDF.
    
    Default 4-in-1 Layout:
    - Page size: A4 Landscape (841.92 x 595.32 pt)
    - 2x2 grid with 25pt side margins, 20pt horizontal gap
    - Each slide retains its exact aspect ratio, centered in its cell
    - Clean white fill background and subtle light-gray borders
    - Vector text and original image fidelity 100% preserved
    """
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Input file not found: {input_pdf_path}")

    if not output_pdf_path:
        base, ext = os.path.splitext(input_pdf_path)
        output_pdf_path = f"{base}_{layout}{ext}"

    src_doc = fitz.open(input_pdf_path)
    total_slides = len(src_doc)
    if total_slides == 0:
        raise ValueError("Source PDF has 0 pages.")

    out_doc = fitz.open()

    if layout == "4in1":
        # A4 Landscape: 841.92 x 595.32
        page_w, page_h = 841.92, 595.32
        margin_x = 25.0
        gap_x = 20.0
        slide_w = (page_w - 2 * margin_x - gap_x) / 2  # 385.96 pt

        # Sample first slide aspect ratio to match standard slide proportion
        ref_page = src_doc[0]
        ref_rect = ref_page.rect
        aspect = ref_rect.height / ref_rect.width if ref_rect.width > 0 else (9 / 16)
        slide_h = slide_w * aspect

        # Standard vertical spacing: top/bottom margin ~52.78 pt, middle gap ~55.56 pt
        margin_y = 52.78
        gap_y = max(10.0, page_h - 2 * margin_y - 2 * slide_h)

        cells = [
            # Row 1 (Top-Left, Top-Right)
            fitz.Rect(margin_x, margin_y, margin_x + slide_w, margin_y + slide_h),
            fitz.Rect(margin_x + slide_w + gap_x, margin_y, margin_x + 2 * slide_w + gap_x, margin_y + slide_h),
            # Row 2 (Bottom-Left, Bottom-Right)
            fitz.Rect(margin_x, margin_y + slide_h + gap_y, margin_x + slide_w, margin_y + 2 * slide_h + gap_y),
            fitz.Rect(margin_x + slide_w + gap_x, margin_y + slide_h + gap_y, margin_x + 2 * slide_w + gap_x, margin_y + 2 * slide_h + gap_y),
        ]
        items_per_page = 4

    elif layout == "2in1":
        # A4 Portrait: 595.32 x 841.92 (2 slides stacked vertically)
        page_w, page_h = 595.32, 841.92
        margin_x = 35.0
        slide_w = page_w - 2 * margin_x
        ref_rect = src_doc[0].rect
        aspect = ref_rect.height / ref_rect.width if ref_rect.width > 0 else (9 / 16)
        slide_h = slide_w * aspect
        gap_y = 30.0
        margin_y = (page_h - 2 * slide_h - gap_y) / 2

        cells = [
            fitz.Rect(margin_x, margin_y, margin_x + slide_w, margin_y + slide_h),
            fitz.Rect(margin_x, margin_y + slide_h + gap_y, margin_x + slide_w, margin_y + 2 * slide_h + gap_y),
        ]
        items_per_page = 2

    elif layout == "6in1":
        # A4 Landscape: 3 columns x 2 rows
        page_w, page_h = 841.92, 595.32
        margin_x = 20.0
        gap_x = 15.0
        slide_w = (page_w - 2 * margin_x - 2 * gap_x) / 3
        ref_rect = src_doc[0].rect
        aspect = ref_rect.height / ref_rect.width if ref_rect.width > 0 else (9 / 16)
        slide_h = slide_w * aspect
        gap_y = 20.0
        margin_y = (page_h - 2 * slide_h - gap_y) / 2

        cells = []
        for r in range(2):
            for c in range(3):
                x = margin_x + c * (slide_w + gap_x)
                y = margin_y + r * (slide_h + gap_y)
                cells.append(fitz.Rect(x, y, x + slide_w, y + slide_h))
        items_per_page = 6

    else:
        raise ValueError(f"Unsupported layout: {layout}. Choose '4in1', '2in1', or '6in1'.")

    # Render pages
    for i in range(0, total_slides, items_per_page):
        page = out_doc.new_page(width=page_w, height=page_h)
        for slot in range(items_per_page):
            src_idx = i + slot
            if src_idx >= total_slides:
                break
            cell_rect = cells[slot]

            # Fit proportionally inside cell_rect
            src_page_rect = src_doc[src_idx].rect
            pw, ph = src_page_rect.width, src_page_rect.height
            if pw > 0 and ph > 0:
                p_ratio = pw / ph
                c_ratio = cell_rect.width / cell_rect.height
                if abs(p_ratio - c_ratio) < 0.05:
                    target_rect = cell_rect
                elif p_ratio > c_ratio:
                    tw = cell_rect.width
                    th = tw / p_ratio
                    tx = cell_rect.x0
                    ty = cell_rect.y0 + (cell_rect.height - th) / 2
                    target_rect = fitz.Rect(tx, ty, tx + tw, ty + th)
                else:
                    th = cell_rect.height
                    tw = th * p_ratio
                    ty = cell_rect.y0
                    tx = cell_rect.x0 + (cell_rect.width - tw) / 2
                    target_rect = fitz.Rect(tx, ty, tx + tw, ty + th)
            else:
                target_rect = cell_rect

            # Draw clean background & border
            fill_c = (1.0, 1.0, 1.0) if draw_white_bg else None
            border_c = border_color if draw_border else None

            if fill_c or border_c:
                page.draw_rect(
                    target_rect,
                    fill=fill_c,
                    color=border_c,
                    width=border_width,
                )

            # Embed original vector/raster content
            page.show_pdf_page(target_rect, src_doc, src_idx)

    # Save with compression
    out_doc.save(output_pdf_path, deflate=True, garbage=3)
    out_doc.close()
    src_doc.close()

    return output_pdf_path


def batch_convert_directory(dir_path: str, layout: str = "4in1") -> list:
    """Batch convert all eligible PDFs in a directory."""
    converted = []
    if not os.path.isdir(dir_path):
        print(f"Directory not found: {dir_path}")
        return converted

    for fname in sorted(os.listdir(dir_path)):
        if fname.lower().endswith(".pdf") and not fname.lower().endswith(f"_{layout}.pdf"):
            full_path = os.path.join(dir_path, fname)
            out_path = os.path.join(dir_path, f"{os.path.splitext(fname)[0]}_{layout}.pdf")
            if os.path.exists(out_path):
                print(f"[SKIP] Already exists: {out_path}")
                continue
            try:
                print(f"[CONVERTING] {fname}...")
                convert_pdf_to_4in1(full_path, out_path, layout=layout)
                print(f"[OK] -> {os.path.basename(out_path)}")
                converted.append(out_path)
            except Exception as e:
                print(f"[ERROR] Failed {fname}: {e}")
    return converted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PDF slides into 4-in-1 handout format.")
    parser.add_argument("path", help="PDF file path or folder path to convert")
    parser.add_argument("-o", "--output", help="Output PDF file path (optional)", default=None)
    parser.add_argument("-l", "--layout", help="Layout: 4in1 (default), 2in1, 6in1", default="4in1")

    args = parser.parse_args()

    target = args.path
    if os.path.isdir(target):
        print(f"Batch converting folder: {target}")
        res = batch_convert_directory(target, layout=args.layout)
        print(f"Finished! Total converted: {len(res)}")
    elif os.path.isfile(target):
        out = convert_pdf_to_4in1(target, args.output, layout=args.layout)
        print(f"Success! Converted file saved at: {out}")
    else:
        print(f"Error: Target path does not exist: {target}")
        sys.exit(1)
