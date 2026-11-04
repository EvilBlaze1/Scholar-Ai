import os
import re
import math

class SimplePDFBuilder:
    def __init__(self, output_path):
        self.output_path = output_path
        self.objects = []
        self.pages = [] # list of stream byte-strings
        self.width = 595.28
        self.height = 841.89
        self.margin_left = 45.0
        self.margin_right = 45.0
        self.margin_top = 45.0
        self.margin_bottom = 45.0
        self.printable_width = self.width - self.margin_left - self.margin_right
        
        # State during building
        self.current_page_ops = []
        self.cursor_y = self.height - self.margin_top - 20.0
        self.page_number = 0

    def add_object(self, obj_str):
        self.objects.append(obj_str)
        return len(self.objects)

    def new_page(self, is_cover=False):
        if self.current_page_ops:
            self.pages.append("\n".join(self.current_page_ops))
            self.current_page_ops = []
        
        self.page_number += 1
        self.cursor_y = self.height - self.margin_top - 25.0

        if not is_cover:
            # Add running header
            self.current_page_ops.append("q")
            self.current_page_ops.append("0.85 0.88 0.92 RG 0.5 w")
            self.current_page_ops.append(f"{self.margin_left} 805 m {self.width - self.margin_right} 805 l S")
            self.current_page_ops.append("BT /F2 7.5 Tf 0.35 0.40 0.50 rg")
            self.current_page_ops.append(f"{self.margin_left} 810 Td (SCHOLAR AI -- ARCHITECTURE & IMPLEMENTATION GUIDE) Tj ET")
            self.current_page_ops.append("BT /F1 7.5 Tf 0.50 0.55 0.65 rg")
            self.current_page_ops.append(f"{self.width - self.margin_right - 60} 810 Td (VERSION 2.1.0) Tj ET")
            self.current_page_ops.append("Q")

            # Add running footer placeholder (will be finalized)
            self.current_page_ops.append("q")
            self.current_page_ops.append("0.85 0.88 0.92 RG 0.5 w")
            self.current_page_ops.append(f"{self.margin_left} 35 m {self.width - self.margin_right} 35 l S")
            self.current_page_ops.append("BT /F1 7.0 Tf 0.50 0.55 0.65 rg")
            self.current_page_ops.append(f"{self.margin_left} 24 Td (Scholar AI Technical Documentation -- Proprietary & Confidential) Tj ET")
            self.current_page_ops.append("BT /F2 7.5 Tf 0.30 0.35 0.45 rg")
            self.current_page_ops.append(f"{self.width - self.margin_right - 55} 24 Td (Page {self.page_number}) Tj ET")
            self.current_page_ops.append("Q")

    def ensure_space(self, needed_pt):
        if self.cursor_y - needed_pt < self.margin_bottom + 15.0:
            self.new_page()

    def sanitize(self, text):
        replacements = [
            ("₹", "Rs. "),
            ("→", "->"),
            ("•", "-"),
            ("–", "-"),
            ("—", " -- "),
            ("“", '"'),
            ("”", '"'),
            ("‘", "'"),
            ("’", "'"),
            ("≤", "<="),
            ("≥", ">="),
            ("×", "x"),
            ("…", "..."),
            (" ", " "),
            (" ", " "),
            ("±", "+/-"),
            ("≠", "!="),
            ("≈", "~="),
            ("’", "'"),
            ("↔", "<->"),
        ]
        t = text
        for orig, rep in replacements:
            t = t.replace(orig, rep)
        # Retain only ascii / latin-1 characters
        t = re.sub(r'[^\x20-\x7E]', ' ', t)
        # Escape PDF special chars
        t = t.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        return t

    def wrap_text(self, text, max_chars):
        words = text.split()
        if not words:
            return []
        lines = []
        cur = []
        cur_len = 0
        for w in words:
            w_len = len(w)
            if cur_len + w_len + 1 > max_chars and cur:
                lines.append(" ".join(cur))
                cur = [w]
                cur_len = w_len
            else:
                cur.append(w)
                cur_len += w_len + 1
        if cur:
            lines.append(" ".join(cur))
        return lines

    def add_cover_page(self):
        self.new_page(is_cover=True)
        ops = self.current_page_ops

        # Top dark hero box
        hero_height = 420.0
        hero_y = self.height - hero_height
        ops.append("q")
        ops.append(f"0.04 0.07 0.12 rg 0 {hero_y} {self.width} {hero_height} re f")

        # Subtle decorative gradient band
        ops.append(f"0.39 0.40 0.95 rg 0 {hero_y - 4} {self.width} 4 re f")

        # Title
        ops.append("BT /F2 36 Tf 1.0 1.0 1.0 rg")
        ops.append(f"50 {hero_y + 320} Td (SCHOLAR AI) Tj ET")

        # Subtitle
        ops.append("BT /F2 13 Tf 0.55 0.58 0.98 rg")
        ops.append(f"50 {hero_y + 290} Td (Full-Stack AI-Assisted Scholarship Discovery & Matching Platform) Tj ET")

        # Mission overview
        ops.append("BT /F1 9.5 Tf 0.80 0.85 0.92 rg")
        ops.append(f"50 {hero_y + 250} Td (An intelligent engineering system combining real-time Google Serper search,) Tj ET")
        ops.append(f"50 {hero_y + 236} Td (automated BeautifulSoup web extraction, deterministic 9-rule evaluation, and) Tj ET")
        ops.append(f"50 {hero_y + 222} Td (application lifecycle tracking for Indian higher education students.) Tj ET")

        # Key badge metrics inside hero
        badges = [
            ("53 Tests Passing", "Pytest Suite"),
            ("FastAPI + React 18", "Decoupled Architecture"),
            ("Argon2id + JWT", "Multi-Hasher Security"),
            ("Serper + BS4", "Live Web Extraction"),
        ]
        badge_x = 50.0
        badge_y = hero_y + 120.0
        for title, subtitle in badges:
            ops.append("0.10 0.15 0.25 rg 0.22 0.30 0.45 RG 0.5 w")
            ops.append(f"{badge_x} {badge_y} 115 55 re B")
            ops.append("BT /F2 8.5 Tf 0.45 0.85 0.65 rg")
            ops.append(f"{badge_x + 8} {badge_y + 34} Td ({self.sanitize(title)}) Tj ET")
            ops.append("BT /F1 7.5 Tf 0.70 0.75 0.85 rg")
            ops.append(f"{badge_x + 8} {badge_y + 16} Td ({self.sanitize(subtitle)}) Tj ET")
            badge_x += 125.0

        ops.append("Q") # End hero

        # Bottom Metadata Card
        card_y = 70.0
        card_h = 300.0
        ops.append("q")
        ops.append(f"0.98 0.99 1.0 rg 0.85 0.88 0.93 RG 1.0 w")
        ops.append(f"50 {card_y} {self.printable_width} {card_h} re B")

        # Card Title
        ops.append("BT /F2 13 Tf 0.10 0.14 0.22 rg")
        ops.append(f"70 {card_y + card_h - 35} Td (SYSTEM SPECIFICATION & ARCHITECTURAL AUDIT) Tj ET")
        ops.append("0.39 0.40 0.95 RG 1.5 w")
        ops.append(f"70 {card_y + card_h - 42} m 360 {card_y + card_h - 42} l S")

        specs = [
            ("Platform Name:", "Scholar AI (Production Milestone 2.1.0)"),
            ("Target Demographics:", "Indian College & University Students (B.Tech, MBBS, B.Sc, B.Com, etc.)"),
            ("Frontend Stack:", "React 18 Single Page Application, Vite 5, React Router v6, Pure CSS"),
            ("UI Design System:", "Modern Clean Dark SaaS (Linear & Stripe Design Tokens)"),
            ("Backend Framework:", "FastAPI 0.115+, Python 3.11+, Pydantic v2, Uvicorn ASGI Server"),
            ("Database Engine:", "MongoDB Atlas (Cloud M0 Replica Set), PyMongo 4.6+, TLS CA Handshake"),
            ("Authentication:", "Argon2id Multi-Hasher, Legacy Bcrypt Auto-Upgrade, 7-Day JWT (HS256)"),
            ("Discovery Pipeline:", "Serper Google Search API, BS4 Scraper, Rupee Heuristic with Rs.500 Floor"),
            ("Rule Evaluation:", "Deterministic 9-Rule Engine (Income, Category, Domicile, Cutoff, Synonyms)"),
            ("Test Coverage:", "53 Passing Pytest Unit & Integration Tests (100% Core Regression Pass)"),
            ("Generated Date:", "November 2026"),
        ]

        row_y = card_y + card_h - 70.0
        for label, val in specs:
            ops.append("BT /F2 8.0 Tf 0.25 0.30 0.40 rg")
            ops.append(f"70 {row_y} Td ({self.sanitize(label)}) Tj ET")
            ops.append("BT /F1 8.0 Tf 0.15 0.20 0.28 rg")
            ops.append(f"195 {row_y} Td ({self.sanitize(val)}) Tj ET")
            row_y -= 19.5

        ops.append("Q")

    def add_chapter_header(self, title):
        # Force a new page for major chapters if not already at the top
        if self.cursor_y < self.height - self.margin_top - 60.0:
            self.new_page()
        
        self.ensure_space(50.0)
        ops = self.current_page_ops
        clean = self.sanitize(title)

        ops.append("q")
        ops.append("BT /F2 16 Tf 0.06 0.09 0.16 rg")
        ops.append(f"{self.margin_left} {self.cursor_y} Td ({clean}) Tj ET")
        # Indigo underline
        ops.append("0.39 0.40 0.95 RG 2.0 w")
        ops.append(f"{self.margin_left} {self.cursor_y - 6} m {self.width - self.margin_right} {self.cursor_y - 6} l S")
        ops.append("Q")
        self.cursor_y -= 26.0

    def add_section_header(self, title):
        self.ensure_space(35.0)
        ops = self.current_page_ops
        clean = self.sanitize(title)

        ops.append("q")
        ops.append("BT /F2 11.5 Tf 0.12 0.16 0.28 rg")
        ops.append(f"{self.margin_left} {self.cursor_y} Td ({clean}) Tj ET")
        ops.append("0.85 0.88 0.92 RG 0.75 w")
        ops.append(f"{self.margin_left} {self.cursor_y - 4} m {self.width - self.margin_right} {self.cursor_y - 4} l S")
        ops.append("Q")
        self.cursor_y -= 18.0

    def add_subsection_header(self, title):
        self.ensure_space(25.0)
        ops = self.current_page_ops
        clean = self.sanitize(title)

        ops.append("q")
        ops.append("BT /F2 9.5 Tf 0.18 0.24 0.38 rg")
        ops.append(f"{self.margin_left} {self.cursor_y} Td ({clean}) Tj ET")
        ops.append("Q")
        self.cursor_y -= 14.0

    def add_paragraph(self, text):
        clean = self.sanitize(text)
        lines = self.wrap_text(clean, max_chars=92)
        if not lines:
            return
        
        needed = len(lines) * 11.5 + 4.0
        self.ensure_space(needed)
        
        ops = self.current_page_ops
        ops.append("q BT /F1 8.5 Tf 0.15 0.18 0.24 rg")
        for i, l in enumerate(lines):
            y = self.cursor_y - (i * 11.5)
            ops.append(f"{self.margin_left} {y} Td ({l}) Tj")
        ops.append("ET Q")
        self.cursor_y -= needed

    def add_bullet(self, text, is_ordered=False, num=1):
        clean = self.sanitize(text)
        lines = self.wrap_text(clean, max_chars=86)
        if not lines:
            return
        
        needed = len(lines) * 11.5 + 3.0
        self.ensure_space(needed)
        
        ops = self.current_page_ops
        bullet_symbol = f"{num}." if is_ordered else "-"
        
        ops.append("q")
        ops.append("BT /F2 8.5 Tf 0.39 0.40 0.95 rg")
        ops.append(f"{self.margin_left + 6} {self.cursor_y} Td ({bullet_symbol}) Tj ET")
        
        ops.append("BT /F1 8.5 Tf 0.15 0.18 0.24 rg")
        for i, l in enumerate(lines):
            y = self.cursor_y - (i * 11.5)
            ops.append(f"{self.margin_left + 22} {y} Td ({l}) Tj")
        ops.append("ET Q")
        self.cursor_y -= needed

    def add_callout(self, text):
        clean = self.sanitize(text)
        lines = self.wrap_text(clean, max_chars=82)
        if not lines:
            return
        
        box_h = len(lines) * 11.5 + 14.0
        self.ensure_space(box_h + 8.0)
        
        ops = self.current_page_ops
        box_y = self.cursor_y - box_h + 4.0
        
        ops.append("q")
        # Light background
        ops.append(f"0.96 0.97 0.99 rg 0.88 0.91 0.96 RG 0.5 w")
        ops.append(f"{self.margin_left} {box_y} {self.printable_width} {box_h} re B")
        # Accent left border
        ops.append("0.39 0.40 0.95 rg")
        ops.append(f"{self.margin_left} {box_y} 3.5 {box_h} re f")
        
        # Text
        ops.append("BT /F3 8.0 Tf 0.22 0.28 0.38 rg")
        for i, l in enumerate(lines):
            y = self.cursor_y - 6.0 - (i * 11.5)
            ops.append(f"{self.margin_left + 14} {y} Td ({l}) Tj")
        ops.append("ET Q")
        self.cursor_y -= box_h + 8.0

    def add_code_block(self, lines_raw):
        if not lines_raw:
            return
        
        sanitized_lines = []
        for l in lines_raw:
            clean = self.sanitize(l)
            # Truncate lines exceeding 85 chars to prevent overflow
            if len(clean) > 85:
                clean = clean[:82] + "..."
            sanitized_lines.append(clean)

        line_h = 9.5
        box_h = len(sanitized_lines) * line_h + 12.0
        
        # If code block is huge, split across pages
        if box_h > 400.0:
            chunk_size = 35
            for chunk_idx in range(0, len(sanitized_lines), chunk_size):
                self.add_code_block(sanitized_lines[chunk_idx:chunk_idx + chunk_size])
            return

        self.ensure_space(box_h + 6.0)
        ops = self.current_page_ops
        box_y = self.cursor_y - box_h + 4.0

        ops.append("q")
        # Dark slate box
        ops.append("0.05 0.08 0.13 rg 0.18 0.22 0.30 RG 0.5 w")
        ops.append(f"{self.margin_left} {box_y} {self.printable_width} {box_h} re B")

        # Code text
        ops.append("BT /F4 7.2 Tf 0.90 0.94 0.98 rg")
        for i, l in enumerate(sanitized_lines):
            y = self.cursor_y - 7.0 - (i * line_h)
            ops.append(f"{self.margin_left + 10} {y} Td ({l}) Tj")
        ops.append("ET Q")
        self.cursor_y -= box_h + 8.0

    def add_table(self, headers, rows):
        if not headers:
            return
        
        cols = len(headers)
        col_w = self.printable_width / cols
        row_h = 16.0
        table_h = (len(rows) + 1) * row_h + 6.0

        if table_h > 450.0:
            # Chunk rows if large
            chunk_size = 20
            for r_idx in range(0, len(rows), chunk_size):
                self.add_table(headers, rows[r_idx:r_idx + chunk_size])
            return

        self.ensure_space(table_h + 6.0)
        ops = self.current_page_ops

        # Header Row
        header_y = self.cursor_y - row_h
        ops.append("q")
        ops.append(f"0.93 0.95 0.98 rg 0.78 0.82 0.88 RG 0.5 w")
        ops.append(f"{self.margin_left} {header_y} {self.printable_width} {row_h} re B")
        for c_idx, h in enumerate(headers):
            clean_h = self.sanitize(h.strip())
            if len(clean_h) > int(col_w / 5.5):
                clean_h = clean_h[:int(col_w / 5.5) - 2] + ".."
            cell_x = self.margin_left + (c_idx * col_w) + 6.0
            ops.append("BT /F2 7.5 Tf 0.10 0.15 0.25 rg")
            ops.append(f"{cell_x} {header_y + 4.5} Td ({clean_h}) Tj ET")
        ops.append("Q")

        # Data Rows
        cur_y = header_y
        for r_idx, r in enumerate(rows):
            cur_y -= row_h
            bg = "1.0 1.0 1.0" if r_idx % 2 == 0 else "0.97 0.98 0.99"
            ops.append("q")
            ops.append(f"{bg} rg 0.85 0.88 0.92 RG 0.5 w")
            ops.append(f"{self.margin_left} {cur_y} {self.printable_width} {row_h} re B")
            for c_idx in range(cols):
                val = r[c_idx] if c_idx < len(r) else ""
                clean_val = self.sanitize(val.strip())
                max_chars = int(col_w / 5.2)
                if len(clean_val) > max_chars:
                    clean_val = clean_val[:max_chars - 2] + ".."
                cell_x = self.margin_left + (c_idx * col_w) + 6.0
                ops.append("BT /F1 7.0 Tf 0.18 0.22 0.28 rg")
                ops.append(f"{cell_x} {cur_y + 4.5} Td ({clean_val}) Tj ET")
            ops.append("Q")

        self.cursor_y = cur_y - 10.0

    def finalize(self):
        # Flush last page
        if self.current_page_ops:
            self.pages.append("\n".join(self.current_page_ops))
            self.current_page_ops = []

        total_pages = len(self.pages)
        print(f"Total pages rendered: {total_pages}")

        # Catalog & Pages objects
        # 1: Catalog
        self.add_object("<< /Type /Catalog /Pages 2 0 R >>")
        # 2: Pages (placeholder, will be updated)
        self.add_object("")
        # 3: Helvetica
        self.add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        # 4: Helvetica-Bold
        self.add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
        # 5: Helvetica-Oblique
        self.add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>")
        # 6: Courier
        self.add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
        # 7: Courier-Bold
        self.add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold >>")

        page_ids = []
        for p_idx, page_content in enumerate(self.pages, 1):
            # Patch running footer with correct total pages
            final_content = page_content.replace(f"Page {p_idx}) Tj ET", f"Page {p_idx} of {total_pages}) Tj ET")
            
            stream_bytes = final_content.encode("latin-1")
            stream_obj = (
                f"<< /Length {len(stream_bytes)} >>\n"
                f"stream\n"
                f"{final_content}\n"
                f"endstream"
            )
            content_id = self.add_object(stream_obj)

            page_obj = (
                f"<< /Type /Page /Parent 2 0 R\n"
                f"   /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R /F4 6 0 R /F5 7 0 R >> >>\n"
                f"   /MediaBox [0 0 {self.width:.2f} {self.height:.2f}]\n"
                f"   /Contents {content_id} 0 R >>"
            )
            page_id = self.add_object(page_obj)
            page_ids.append(f"{page_id} 0 R")

        # Update Pages (obj 2)
        kids_str = " ".join(page_ids)
        self.objects[1] = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_ids)} >>"

        # Build xref table and assemble binary output
        out = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
        offsets = []
        current_offset = len(out[0])

        for i, obj in enumerate(self.objects, 1):
            offsets.append(current_offset)
            obj_bytes = f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1")
            out.append(obj_bytes)
            current_offset += len(obj_bytes)

        xref_offset = current_offset
        xref = [f"xref\n0 {len(self.objects) + 1}\n0000000000 65535 f \n"]
        for off in offsets:
            xref.append(f"{off:010d} 00000 n \n")
        trailer = (
            f"trailer\n"
            f"<< /Size {len(self.objects) + 1}\n"
            f"   /Root 1 0 R\n"
            f"   /Info << /Title (Scholar AI Complete Documentation)\n"
            f"            /Author (Scholar AI Engineering Team)\n"
            f"            /Subject (Scholarship Discovery Architecture & Implementation)\n"
            f"            /Creator (Scholar AI Doc Engine)\n"
            f"         >>\n"
            f">>\n"
            f"startxref\n"
            f"{xref_offset}\n"
            f"%%EOF\n"
        )

        out.append("".join(xref).encode("latin-1"))
        out.append(trailer.encode("latin-1"))

        with open(self.output_path, "wb") as f:
            f.write(b"".join(out))

        size_kb = len(b"".join(out)) / 1024
        print(f"SUCCESS: Generated PDF '{self.output_path}' ({size_kb:.1f} KB, {total_pages} pages)")


def compile_md_to_pdf():
    md_path = r"d:\Scholar AI\docs\SCHOLAR_AI_COMPLETE_DOCUMENTATION.md"
    pdf_path = r"d:\Scholar AI\docs\SCHOLAR_AI_COMPLETE_DOCUMENTATION.pdf"
    
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    lines = md_text.splitlines()
    builder = SimplePDFBuilder(pdf_path)
    
    # 1. Add Cover Page
    builder.add_cover_page()

    # 2. Parse Markdown
    in_code = False
    code_lines = []
    
    in_table = False
    table_headers = []
    table_rows = []

    def flush_table():
        nonlocal in_table, table_headers, table_rows
        if in_table:
            builder.add_table(table_headers, table_rows)
            in_table = False
            table_headers = []
            table_rows = []

    for line in lines:
        stripped = line.strip()

        # Fenced code blocks
        if stripped.startswith("```"):
            flush_table()
            if in_code:
                builder.add_code_block(code_lines)
                in_code = False
                code_lines = []
            else:
                in_code = True
                code_lines = []
            continue

        if in_code:
            code_lines.append(line)
            continue

        # Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not in_table:
                in_table = True
                table_headers = cells
            elif re.match(r'^\s*[:\-]+\s*$', cells[0]):
                # Delimiter line
                pass
            else:
                table_rows.append(cells)
            continue
        elif in_table:
            flush_table()

        # Horizontal Rule
        if re.match(r'^(---|___|\*\*\*)$', stripped):
            continue

        # Chapter Headers (# Chapter ...)
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            builder.add_chapter_header(title)
            continue

        # Section Headers (## ...)
        if stripped.startswith("## "):
            title = stripped[3:].strip()
            builder.add_section_header(title)
            continue

        # Subsection Headers (### ...)
        if stripped.startswith("### "):
            title = stripped[4:].strip()
            builder.add_subsection_header(title)
            continue

        # Blockquote / Callout
        if stripped.startswith(">"):
            text = stripped[1:].strip()
            builder.add_callout(text)
            continue

        # Bullets
        bullet_match = re.match(r'^[-*]\s+(.+)$', stripped)
        if bullet_match:
            builder.add_bullet(bullet_match.group(1), is_ordered=False)
            continue

        num_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if num_match:
            builder.add_bullet(num_match.group(2), is_ordered=True, num=int(num_match.group(1)))
            continue

        # Blank line
        if not stripped:
            continue

        # Regular Paragraph
        builder.add_paragraph(stripped)

    if in_code and code_lines:
        builder.add_code_block(code_lines)
    if in_table:
        flush_table()

    builder.finalize()

if __name__ == "__main__":
    compile_md_to_pdf()
