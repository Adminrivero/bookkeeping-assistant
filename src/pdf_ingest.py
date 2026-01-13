"""
PDF Ingestion Module for Credit Card Statements
-----------------------------------------------
This module discovers, normalizes, parses, and exports transactions
from credit card statement PDFs (e.g., Triangle MasterCard, TD Visa).
"""
import csv
import re
import pathlib
import pdfplumber
import time
import tempfile
import webbrowser, pathlib
from typing import List, Dict, Optional, Literal
from datetime import datetime
from src.utils import load_bank_profile, notify, debug_mode, time_it
from collections import defaultdict


def discover_pdfs(year_dir: str):
    """
    Recursively find all PDF files under ./data/<year>/.

    Args:
        year_dir (str): Path to the tax year directory.

    Returns:
        list[pathlib.Path]: Sorted list of PDF file paths.
    """
    pdfs = sorted(pathlib.Path(year_dir).rglob("*.pdf"))
    notify("Discovered %d PDF files in %s" % (len(pdfs), year_dir), "info")
    
    return pdfs


def normalize_filename(pdf_path: pathlib.Path, bank: str):
    """
    Ensure filename follows <bank>-<month>.pdf convention by reading statement date.

    Args:
        pdf_path (Path): Path to the PDF file.
        bank (str): Bank identifier (e.g., 'triangle').

    Returns:
        Path: Normalized file path.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text() or ""
            match = re.search(r"Statement date:\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
            if match:
                date_obj = datetime.strptime(match.group(1), "%B %d, %Y")
                month_str = date_obj.strftime("%b").lower()
                new_name = f"{bank}-{month_str}.pdf"
                new_path = pdf_path.with_name(new_name)
                if pdf_path.name != new_name:
                    pdf_path.rename(new_path)
                    notify("Renamed %s → %s" % (pdf_path.name, new_name), "info")
                return new_path
    except Exception as e:
        notify("Failed to normalize filename for %s: %s" % (pdf_path, e), "warning")
    
    return pdf_path


def debug_visualize_search_area(page, crop_bbox, action: str = "save", filename: Optional[str] = None):
    """
    Visualize a cropped area of a PDF page by drawing a red rectangle.
    
    Args:
        page: pdfplumber Page object.
        crop_bbox: (x0, top, x1, bottom) tuple defining the crop area.
        action: "save", "show", or "both". Defaults to "save".
        filename: Optional filename when action includes "save".
        
    Returns:
        str|None: Path to saved file if saved, otherwise None.
    """
    # Crop and render
    search_strip = page.crop(crop_bbox)
    im = search_strip.to_image()
    im.draw_rects([search_strip.bbox], stroke="red", fill=None)

    action = action.lower()
    base_path = pathlib.Path.cwd() / ".pydebug"
    saved_path = None

    if "save" in action:
        if not filename:
            filename = f"debug_search_strip_{int(time.time())}.png"
        if not base_path.exists():
            base_path.mkdir(parents=True)
        im.save(base_path / filename)
        saved_path = base_path / filename

    if "show" in action:
        # Try to show via PIL; fallback to opening saved file in the default viewer
        try:
            im.original.show()
        except Exception:
            if saved_path is None:
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                im.save(tmp.name)
                saved_path = tmp.name
            webbrowser.open(pathlib.Path(saved_path).as_uri())

    return saved_path


def debug_visualize_column_zones(page, crop_bbox: tuple, break_points: List[float], action: str = "save", filename: Optional[str] = None) -> Optional[pathlib.Path]:
    """
    Visualizes estimated column zones by drawing rectangles between vertical breakpoints.
    Useful for tuning fallback logic in tables without explicit horizontal lines.
    
    Args:
        page: pdfplumber.Page object
        crop_bbox: (left, top, right, bottom) of the header area to visualize
        break_points: List of X-coordinates (e.g., [x0, x1, x2, x3, x4] for 4 columns)
        action: "save", "show", or "save_show"
        filename: Optional custom filename for the debug image
        
    Returns:
        Optional[Path]: Path to saved debug image if saved, otherwise None
    """
    # 1. Prepare the crop and the image
    search_strip = page.crop(crop_bbox)
    im = search_strip.to_image(resolution=150) # usually enough for debug
    
    # 2. Draw the column rectangles
    # Breakpoints: [bp0, bp1, bp2, bp3, bp4] defines 4 columns
    for i in range(len(break_points) - 1):
        col_x0 = break_points[i]
        col_x1 = break_points[i+1]
        
        # Define rectangle for the current column
        column_rect = (col_x0, crop_bbox[1], col_x1, crop_bbox[3])
        
        # Alternating colors can help distinguish edges
        stroke_color = "#FF0000" if i % 2 == 0 else "#0000FF"
        im.draw_rect(column_rect, stroke=stroke_color, stroke_width=2, fill=None)
        
        # Optional: Label the column index for even better debugging
        # im.draw_text(str(i), (col_x0 + 2, crop_bbox[1] + 2), font_size=10)

    # 3. Handle Saving/Showing the debug image
    action = action.lower()
    base_path = pathlib.Path.cwd() / ".pydebug"
    saved_path = None

    if "save" in action:
        if not filename:
            filename = f"debug_cols_{int(time.time())}.png"
        if not base_path.exists():
            base_path.mkdir(parents=True)
        
        final_file = base_path / filename
        im.save(final_file)
        saved_path = final_file

    if "show" in action:
        try:
            # Using the internal PIL image object to show
            im.original.show()
        except Exception:
            if saved_path is None:
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                im.save(tmp.name)
                saved_path = pathlib.Path(tmp.name)
            webbrowser.open(saved_path.as_uri())

    return saved_path


def _build_header_pattern(label: str) -> re.Pattern:
    """
    Return a compiled, case-insensitive regex that robustly matches a header label
    in PDF/OCR-extracted text, allowing flexible whitespace and line breaks and
    handling special cases (e.g., 'AMOUNT' variants and 'DESCRIPTION' prefixes).
    
    Args:
        label (str): The header label to build a pattern for (e.g., "TRANSACTION\nDATE").

    Returns:
        re.Pattern: Compiled regex pattern for matching the header label in extracted text.
    """
    # Base pattern: Replace spaces in label with multi-line space/newline bridge
    pattern_content = re.escape(label).replace(r"\ ", r"\s*[\n\r]?\s*")

    # SPECIAL CASE: Amount, optional space and encoding symbols
    if "AMOUNT" in label.upper():
        # Matches 'AMOUNT', optional space, then '(' + anything + ')'
        pattern_content = r'AMOUNT\s*(\([^\)]*\))?'

    # SPECIAL CASE: Description variations
    if "DESCRIPTION" in label.upper():
        # Allow for "TRANS" "TRANSACTION", "ACTIVITY" prefix
        # pattern_content = r'(TRANS|ACTIVITY|TRANSACTION)?\s*[\n\r]?\s*DESCRIPTION'
        # Allow up to 2 arbitrary prefix tokens before "DESCRIPTION" (letters, digits, &, -, /, .)
        pattern_content = r'(?:[A-Z0-9&\-/\.]+(?:\s+[A-Z0-9&\-/\.]+){0,2}\s*)?DESCRIPTION\b'

    # SPECIAL CASE: The "Interleaved Bridge" strategy for multi-line headers
    if "\n" in label:
        parts = label.split("\n")
        if len(parts) == 2:
            part1, part2 = map(re.escape, parts)
            joiner = r'(?:\s+|[^\n]{1,60}\n[^\n]{1,60})'
            pattern_content = rf'{part1}\s*(?:{joiner})?\s*{part2}'
        else:
            escaped_parts = [re.escape(p) for p in parts]
            pattern_content = r'\s*[\n\r]?\s*'.join(escaped_parts)

    return re.compile(pattern_content, re.IGNORECASE)


def _normalize_segment(seg):
    """Normalize segment to a consistent bbox dict with floats."""
    return {
        "x0": float(seg.get("x0", 0.0)),
        "x1": float(seg.get("x1", 0.0)),
        "top": float(seg.get("top", seg.get("y0", 0.0))),
        "bottom": float(seg.get("bottom", seg.get("y1", 0.0))),
    }


def _extract_horizontal_lines(cropped_search_area, ascending=True, consolidate_segments=True, min_seg_length=1, min_width=10, max_gap=3) -> List[List[Dict[str, float]]]:
    """
    Extract horizontal lines from a cropped search area, with options to consolidate segments.

    Args:
        cropped_search_area: pdfplumber cropped page object
        ascending: bool indicating sort order by Y-coordinate (default: True)
        consolidate_segments: bool to merge nearby line segments into single lines (default: True)
        min_seg_length: minimum length of line segments to consider (default: 1)
        max_gap: maximum gap between segments to be consolidated into a single line (default: 3)

    Returns:
        list[list[dict]]: List of horizontal lines, each line is a list of segment dicts with keys 'x0', 'x1', 'top', 'bottom'
    """
    # Normalize horizontal lines & thin rectangles into segments
    combined_segments = (
        [_normalize_segment(l) for l in cropped_search_area.lines if abs(l["y0"] - l["y1"]) == 0 and (l["x1"] - l["x0"]) > min_seg_length] + 
        [_normalize_segment(r) for r in cropped_search_area.rects if (r["x1"] - r["x0"]) > min_seg_length and abs(r["bottom"] - r["top"]) < max_gap]
    )
    
    if consolidate_segments:
        # Group segments by Y-coordinate to form horizontal lines
        y_groups = defaultdict(list)
        for seg in combined_segments:
            y_key = round(seg["top"], 1)  # Group by rounded top coordinate
            y_groups[y_key].append(seg)
        
        # Create a sorted (desc) list of horizontal lines (each is a list of segments)
        horizontal_lines = [
            g_sorted for _, group in sorted(y_groups.items())
            if (g_sorted := sorted(group, key=lambda s: s["x0"])) and (g_sorted[-1]["x1"] - g_sorted[0]["x0"] > min_width)
        ]
        
        # Sort lines by Y-coordinate
        horizontal_lines.sort(key=lambda l: l[0]["top"], reverse=not ascending)
        return horizontal_lines
    
    # If not consolidating, return each normalized segment as a single-element list so the return type is consistent
    normalized = sorted([_normalize_segment(s) for s in combined_segments], key=lambda s: s["top"], reverse=not ascending)
    return [[seg] for seg in normalized]


# @time_it
def get_page_left_margin(page, top_fraction: float = 1.0, left_fraction: float = 1.0) -> float:
    """Find the leftmost x0 coordinate of text in the top portion of the page.

    Args:
        page: pdfplumber Page object
        top_fraction: float between 0.0 and 1.0 indicating portion of page height to consider.
        left_fraction: float between 0.0 and 1.0 indicating portion of page width to consider.
        
    Returns:
        float: The leftmost x0 coordinate of text in the specified top portion of the page.
    """
    # Debug section: visualize search area
    # if debug_mode:
    #     debug_visualize_search_area(page, (0, 0, page.width * left_fraction, page.height * top_fraction), action="save")
    # End debug section
    
    search_area = (0, 0, page.width * left_fraction, page.height * top_fraction)
    crop_area = page.crop(search_area)
    words_found = crop_area.extract_words()

    try:
        page_left_margin = min(w.get("x0", 0) for w in words_found)
    except ValueError:
        page_left_margin = 0
        
    return page_left_margin


def find_header_label_x_coordinate(page, search_area_bbox, label_text, edge="left", margin=0):
    """
    Find the x-coordinate of a table header label edge by searching for the label text.

    Args:
        page: pdfplumber Page object
        search_area_bbox: (left, top, right, bottom) tuple defining search area
        label_text: text label to search for
        edge: "left" or "right" indicating which edge to return
        margin: int margin to add/subtract from found edge

    Returns:
        float|None: x-coordinate of the edge or None if not found
    """
    search_strip = page.crop(search_area_bbox)

    # Tokenize and try the most significant (longest) tokens first to avoid noisy matches
    tokens = [t for t in re.split(r"\s+", label_text.strip()) if t]
    tokens.sort(key=len, reverse=True)

    for token in tokens:
        matches = search_strip.search(token)
        if matches:
            m = matches[0]
            if edge == "left":
                return max(0.0, float(m.get("x0", 0.0)) - margin)
            else:
                return min(float(page.width), float(m.get("x1", page.width)) + margin)

    return None


def get_section_header_bbox(page, match_text, crop_bbox = None, left_margin: Optional[float] = None, tolerance: float = 0.5):
    """
    Finds the bounding box of a section header by searching for match_text.
    
    Args:
        page: pdfplumber Page object
        match_text: text to search for
        crop_bbox: optional (x0, top, x1, bottom) tuple to limit search area
        left_margin: optional float to filter matches by left alignment
        tolerance: float tolerance for left alignment filtering
        
    Returns:
        dict|None: Bounding box dict or None if not found
    """
    results = (page.crop(crop_bbox) if crop_bbox else page).search(match_text)
    
    if not results:
        return None
    
    if left_margin is not None:
        # Filter for matches that are left-aligned within tolerance
        results = [r for r in results if abs(r["x0"] - left_margin) <= tolerance]
    
    if results:
        # Return the top_most match's dict (x0, top, x1, bottom)
        return min(results, key=lambda r: r["top"])
    
    return None


def get_table_footer_bbox(page, footer_text, search_area_bbox, header_x_range=None):
    """
    Finds the bounding box of a section footer by searching for footer_text
    within a defined search area and validating its position relative to the header.
    Implements a three-gate validation process (1-Vertical Slice Gate, 2-Line Proximity Gate, 3-Horizontal Overlap Gate).

    Args:
        page: pdfplumber Page object
        footer_text: text to search for
        search_area_bbox: (left, top, right, bottom) tuple defining search area
        header_x_range: (x0, x1) of the section header for horizontal validation
        
    Returns:
        dict|None: Bounding box dict or None if not found
    """
    # Debug section: visualize search area
    if debug_mode:
        debug_visualize_search_area(page, search_area_bbox, action="save", filename=f"get_table_footer_bbox-debug_search_area.png")
    # End debug section
    
    search_strip = page.crop(search_area_bbox)
    # Gate 1: Vertical Slice Gate - Only consider matches that fall within the vertical bounds of the search area
    matches = search_strip.search(footer_text)
    
    if not matches:
        return None
    
    # Get horizontal lines in the search area to validate proximity to footer text
    horizontal_lines = _extract_horizontal_lines(search_strip, ascending=False)
    
    valid_matches = []
    for match in matches:
        text_top = match["top"]
        text_bottom = match["bottom"]
        footer_bbox: Dict[str, Optional[dict]] = {
            "text_bbox": None, 
            "line_bbox": None
        }
        
        # Check Gate 2: Line Proximity and Horizontal Coverage
        line_above = False
        for l in horizontal_lines:
            line_top= l[0]["top"]
            line_bottom = l[0]["bottom"]
            line_x0 = l[0]["x0"]
            line_x1 = l[-1]["x1"]
            
            # 1. Vertical Proximity Gate
            # Allow the line to be up to 5 points above the text and up to 2 points 'inside' the text box
            is_vertically_aligned = (text_top - 5) <= line_top <= (text_top + 2)
            
            # Ensure the line is physically above the text midline (restrict it to a 5-points range)
            # text_midline = (text_top + text_bottom) / 2
            # is_vertically_aligned = (text_midline - 5) <= line_top < text_midline
            
            # 2. Horizontal Coverage Gate
            # Check if the line starts before and ends after the text box horizontally
            is_horizontally_covering = (line_x0 <= match["x0"]) and (line_x1 >= match["x1"])
            
            if is_vertically_aligned and is_horizontally_covering:
                line_above = True
                footer_bbox["line_bbox"] = {"x0": line_x0, "top": line_top, "x1": line_x1, "bottom": line_bottom}
                break
        
        # Check Gate 3: Horizontal Overlap (if header bounds are provided)
        overlaps_header = True
        if header_x_range:
            # Check if the footer text is roughly within the same horizontal corridor
            header_x0, header_x1 = header_x_range
            overlaps_header = (match["x0"] >= header_x0 and (match["x1"] <= header_x1 or match["x1"] <= (page.width * 0.5)))

        if line_above and overlaps_header:
            footer_bbox["text_bbox"] = {"x0": match["x0"], "top": text_top, "x1": match["x1"], "bottom": text_bottom}
            valid_matches.append(footer_bbox)

    if valid_matches:
        # Return the top_most valid match's dict
        return min(valid_matches, key=lambda r: r["text_bbox"]["top"])
    
    return None


def validate_table_presence(page, strip_bbox, section, bank_name, footer_bbox=None) -> bool:
    """
    Validates table presence using Structural Validation and Regex-based 
    Content Validation to handle multi-line headers and encoding artifacts.
    
    args:
        page: pdfplumber Page object
        strip_bbox: (left, top, right, bottom) tuple defining the area to check
        section: dict containing expected table section info, including columns
        bank_name: str name of the bank (for any bank-specific logic)
        footer_bbox: Optional dict defining the footer bounding box, if available
        
    Returns:
        bool: True if a valid table is detected, False otherwise
    """
    # Debug section: visualize search area
    # if debug_mode:
    #     debug_visualize_search_area(page, strip_bbox, action="save")
    # End debug section
    
    crop = page.crop(strip_bbox)
    
    # --- 1. Structural Validation ---
    has_structure = False
    if footer_bbox and footer_bbox.get("line_bbox"):
        # A footer horizontal line within strip_bbox is strong evidence of a table.
        line = footer_bbox["line_bbox"]
        if strip_bbox[1] <= line["top"] <= strip_bbox[3]:
            has_structure = True
    
    if not has_structure:
        # Fallback: Manual search for horizontal separator (common in tables)
        lines = _extract_horizontal_lines(crop, ascending=True)
        # Also check for actual rectangles (TD table headers are often enclosed in a box)
        rects = [r for r in crop.rects if (r["x1"] - r["x0"]) > 1]
        has_structure = len(lines) >= 1 or len(rects) >= 1

    # --- 2. Content Validation (Header Regex Match) ---
    header_labels = section.get("header_labels", [])
    if not header_labels:
        return has_structure

    # Dynamic header zone estimation
    header_buffer = 60
    header_zone_bbox = (
        strip_bbox[0],
        strip_bbox[1],
        strip_bbox[2],
        min(strip_bbox[1] + header_buffer, strip_bbox[3])
    )
    
    if bank_name == "TD Visa":
        # Find significant rectangle that could be enclosing the header and adjust the header zone accordingly
        td_rects = [r for r in crop.rects if (r["x1"] - r["x0"]) > 100 and (r["y1"] - r["y0"]) > 20]
        if td_rects:
            # Assume the top-most large rectangle is the header box
            td_header_rect = min(td_rects, key=lambda r: r["top"])
            header_zone_bbox = (
                strip_bbox[0],
                td_header_rect["top"] - 2,  # small buffer above the rect
                strip_bbox[2],
                td_header_rect["bottom"] + 2  # small buffer below the rect
            )
    
    header_crop = page.crop(header_zone_bbox)
    text = header_crop.extract_text() or ""
    
    found_count = 0
    for label in header_labels:
        # Build a regex pattern for the label
        pattern = _build_header_pattern(label)
        # Search for the header lable pattern
        if pattern.search(text):
            found_count += 1
            
    # --- 3. Threshold Validation ---
    # Require at least 75% of headers for high-confidence sections
    # but can fallback to 50% for noisier statements.
    threshold = 0.75 if len(header_labels) > 2 else 0.5
    has_headers = (found_count / len(header_labels)) >= threshold if header_labels else True

    return has_structure and has_headers


def get_table_header_bbox(page, search_area_bbox, section, bank_name, padding: float = 2.0):
    """
    Locate and extract bounding boxes for table headers within a specified search area on a PDF page.
    This function searches for header labels defined in the section configuration, using regex patterns
    to handle OCR artifacts and flexible whitespace. It dynamically estimates the header zone and adjusts
    based on the bank name for specialized handling (e.g., detecting horizontal lines for Triangle MasterCard
    or enclosing rectangles for TD Visa). If matches are found, it computes a padded bounding box for the
    headers and estimates vertical line breakpoints for column boundaries.
    
    Args:
        page: The PDF page object to search on.
        search_area_bbox (tuple): Bounding box (left, top, right, bottom) defining the search area.
        section (dict): Configuration dictionary containing 'header_labels' list of strings to match.
        bank_name (str): Name of the bank (e.g., "Triangle MasterCard", "TD Visa") to apply specific logic.
        padding (float, optional): Padding value to expand the matched bounding box. Defaults to 2.0.
        
    Returns:
        dict or None: A dictionary containing:
            - "text_bbox": Bounding box of the matched header text after padding and clamping.
            - "line_bbox": Bounding box of the horizontal line (if found for Triangle MasterCard).
            - "vertical_lines_bp": List of x-coordinates for vertical line breakpoints (column boundaries).
        Returns None if no header labels are provided, the search area is invalid, or no matches are found.
        
    Notes:
        - For "Triangle MasterCard", it extracts horizontal lines to define the header zone and captures
          vertical breakpoints if exactly 5 line segments are detected.
        - For "TD Visa", it identifies large rectangles to adjust the header zone.
        - Vertical breakpoints are estimated from matches if not captured from lines.
    """
    header_labels = section.get("header_labels", [])
    if not header_labels:
        return None

    left, top, right, bottom = map(float, search_area_bbox)
    if max(0.0, bottom - top) <= 0:
        return None
    
    header_bbox: Dict[str, Optional[dict] | tuple | list] = {
        "coords": (),
        "text_bbox": None,
        "line_bbox": None,
        "vertical_lines_bp": []
    }

    # Dynamic Header Zone Estimation
    header_buffer = 50
    header_bottom = min(bottom, top + header_buffer)
    header_zone_bbox = (left, top, right, header_bottom)
    
    if bank_name == "Triangle MasterCard":
        # For Triangle MC, look for top horizontal line to define the header zone
        crop = page.crop(search_area_bbox)
        horizontal_lines = _extract_horizontal_lines(crop, ascending=True)
        if horizontal_lines:
            # Assume the first horizontal line is the bottom boundary of the header zone
            first_line = horizontal_lines[0]
            header_zone_bbox = (left, top, right, first_line[0]["top"])
            header_bbox["line_bbox"] = {
                "x0": first_line[0]["x0"],
                "top": first_line[0]["top"],
                "x1": first_line[-1]["x1"],
                "bottom": first_line[0]["bottom"]
            }
            # Store vertical line breakpoints if there are exactly 5 segments (indicating 4 columns)
            if first_line and len(first_line) == 5:
                header_bbox["vertical_lines_bp"] = [(seg["x1"] if i else seg["x0"]) for i, seg in enumerate(first_line)]
        
    elif bank_name == "TD Visa":
        # For TD Visa, find rectangle that encloses the header labels and adjust the header zone accordingly
        td_crop = page.crop(search_area_bbox)
        # all_rects = [r for r in td_crop.rects if (r["x1"] - r["x0"]) > 1] 
        td_rects = [r for r in td_crop.rects if (r["x1"] - r["x0"]) > 100 and (r["y1"] - r["y0"]) > 10]
        if td_rects:
            # Assume the top-most large rectangle is the header box
            td_header_rect = min(td_rects, key=lambda r: r["top"])
            header_zone_bbox = (
                left,
                td_header_rect["top"] - padding,  # small buffer above the rect
                right,
                td_header_rect["bottom"] + padding  # small buffer below the rect
            )
    
    header_crop = page.crop(header_zone_bbox)
    
    # Vertical Boundaries Refinement (top, bottom)
    vertical_boundary: dict[str, float] = {"top": float("inf"), "bottom": float("-inf")}
    for label in header_labels:
        pattern = _build_header_pattern(label)
        matches = header_crop.search(pattern)
        for m in matches:
            vertical_boundary["top"] = min(vertical_boundary["top"], float(m.get("top", float("inf"))))
            vertical_boundary["bottom"] = max(vertical_boundary["bottom"], float(m.get("bottom", float("-inf"))))

    t = max(top, vertical_boundary["top"] - padding) if vertical_boundary["top"] < float("inf") else top
    b = min(bottom, vertical_boundary["bottom"] + padding) if vertical_boundary["bottom"] > float("-inf") else bottom

    header_bbox["text_bbox"] = {"x0": left, "top": t, "x1": right, "bottom": b}
    line_bottom = header_bbox["line_bbox"] if header_bbox["line_bbox"] else None
    line_bottom_y = line_bottom.get("bottom", 0) if isinstance(line_bottom, dict) else 0
    header_bbox["coords"] = (left, t, right, max(b, line_bottom_y))
    
    if debug_mode:
        debug_visualize_search_area(page, header_bbox["coords"], action="save", filename=f"get_table_header_bbox-debug_final_header_outter_bbox.png")
    
    if not header_bbox["vertical_lines_bp"]:
        # Fallback: Word-Aware Refinement for Horizontal Breakpoints
        header_text_crop = page.crop(tuple(header_bbox["text_bbox"].values()))
        # Extract all individual word objects in the header zone
        all_words = header_text_crop.extract_words()
        
        matches = []
        current_cursor_x0 = left    # Start searching from the left edge
        for label in header_labels:
            # Clean the label and get the first word as an anchor for matching
            clean_label = label.strip().upper()
            first_token = clean_label.split()[0] if clean_label else ""
            
            found_word = None
            for word in all_words:
                word_text = word.get("text", "").strip().upper()
                if first_token in word_text and word["x0"] >= (current_cursor_x0 - 1):
                    found_word = word
                    break
            
            if found_word:
                matches.append(found_word)
                # Move cursor to the end of the found word for next search
                current_cursor_x0 = found_word["x1"]
            else:
                # Fallback: If literal match fails, try fuzzy pattern
                segment_crop = header_crop.crop((current_cursor_x0, header_bbox["text_bbox"]["top"], right, header_bbox["text_bbox"]["bottom"]))
                pattern = _build_header_pattern(label)
                seg_matches = segment_crop.search(pattern)
                if seg_matches:
                    matches.append(seg_matches[0])
                    current_cursor_x0 = seg_matches[0]["x1"]
        
        if len(matches) == len(header_labels):
            sorted_matches = sorted(matches, key=lambda m: m["x0"])
            # Use x0 for the breakpoints
            header_bbox["vertical_lines_bp"] = [m["x0"] for m in sorted_matches]
            # Apply overrides
            header_bbox["vertical_lines_bp"][0] = min(sorted_matches[0]["x0"], left)
            # Shift last column start left by 80% of the header label width
            header_bbox["vertical_lines_bp"][-1] = sorted_matches[-1]["x0"] - round(sorted_matches[-1].get("width", 0) * 0.8, 2)
            # Add the final edge
            header_bbox["vertical_lines_bp"].append(max(sorted_matches[-1]["x1"], right))
            
            if debug_mode:
                debug_visualize_column_zones(page, header_bbox["coords"], header_bbox["vertical_lines_bp"], action="save", filename=f"get_table_header_bbox-debug_column_zones-{bank_name}.png")

    if not header_bbox["text_bbox"] and not header_bbox["line_bbox"] and not header_bbox["vertical_lines_bp"]:
        return None
    return header_bbox


def get_table_edges(page, search_area_bbox, section, bank_name, footer_bbox=None):
    """
    Determines table boundaries by combining text-header detection and geometric line analysis.
    """
    # Debug section: visualize search area
    if debug_mode:
        debug_visualize_search_area(page, search_area_bbox, action="save", filename=f"get_table_edges-debug_search_area.png")
        # test_area_bbox = (0, 0, page.width, search_area_bbox[1])
        # debug_visualize_search_area(page, test_area_bbox, action="save", filename=f"get_table_edges-debug_test_area.png")
    # End debug section

    table_edges = {
        "coords": (),
        "headers_bbox": None,
        "rows_bbox": None,
        "footer_bbox": None,
        "explicit_vertical_lines": []
    }

    # 1. Find the Textual Header Area including horizontal header lines (if any) and vertical lines that may define column boundaries
    h_bbox = get_table_header_bbox(page, search_area_bbox, section, bank_name, padding=2.0)
    if not h_bbox:
        return None
    
    header_coords = h_bbox.get("coords", search_area_bbox)
    if not isinstance(header_coords, (tuple, list)):
        header_coords = search_area_bbox # Fallback to search area coords
    header_left, header_top, header_right, header_bottom = map(float, header_coords)
    
    # Determine table horizontal edges: the leftmost and rightmost x-coordinates from available lines, or fallback to header coords
    table_left = float('inf')
    table_right = float('-inf')
    if h_bbox.get("line_bbox"):
        line_bbox = h_bbox["line_bbox"]
        if not isinstance(line_bbox, dict):
            line_bbox = {}
        table_left = min(table_left, line_bbox.get("x0", float('inf')))
        table_right = max(table_right, line_bbox.get("x1", float('-inf')))
    if footer_bbox and footer_bbox.get("line_bbox"):
        table_left = min(table_left, footer_bbox["line_bbox"]["x0"])
        table_right = max(table_right, footer_bbox["line_bbox"]["x1"])
    if table_left == float('inf'):
        table_left = header_left
    if table_right == float('-inf'):
        table_right = header_right
    
    # Set table top edge
    table_top = float(header_top)
    # Set table_header_bottom to the header bottom coordinate
    table_header_bottom = float(header_bottom)
    
    # Set table_footer_top to the footer line top if footer line exist, otherwise use the footer text top if footer text exist, otherwise use the search area bottom
    # table_footer_top = float(footer_bbox["line_bbox"]["top"]) if footer_bbox and footer_bbox["line_bbox"] else (float(footer_bbox["text_bbox"]["top"]) if footer_bbox and footer_bbox["text_bbox"] else float(search_area_bbox[3]))
    table_footer_top = search_area_bbox[3]  # Default to search area bottom
    if footer_bbox:
        if footer_bbox.get("line_bbox"):
            table_footer_top = footer_bbox["line_bbox"]["top"]
        elif footer_bbox.get("text_bbox"):
            table_footer_top = footer_bbox["text_bbox"]["top"]

    table_edges["headers_bbox"] = h_bbox
    table_edges["coords"] = (table_left, table_top, table_right, table_footer_top)
    table_edges["rows_bbox"] = (table_left, table_header_bottom, table_right, table_footer_top)
    table_edges["footer_bbox"] = footer_bbox or None
    table_edges["explicit_vertical_lines"] = h_bbox.get("vertical_lines_bp", [])

    return table_edges


def validate_extracted_table(table_rows: List[List[str | None]], section_config: Dict, *, type_check: Literal["rows_only", "header_only", "both"] = "both", max_header_rows: int = 2, header_match_threshold: float = 0.6) -> bool:
    """
    Post-extraction validation (fast, rows-only/content-based) for extracted tables.

    Modes:
      1) type_check="rows_only"  -> validates that the extracted data "looks like rows" (no header required).
      2) type_check="header_only" -> validates header presence (supports 1-2 header rows) + basic structure.
      3) type_check="both" -> validates both rows and header (if header_labels are defined in section_config).

    This validator:
      - Verifies row/column shape (when applicable)
      - Validates header labels fuzzy-match (when applicable)

    Args:
        table_rows: Extracted table rows (list of rows, each row list of cells).
        section_config: Section config from bank profile JSON.
        type_check: Validation mode ("rows_only", "header_only", or "both").
        max_header_rows: When type_check includes header validation, number of leading rows to consider as header (1 or 2).
        header_match_threshold: Fraction of expected header labels that must be found in the header text.

    Returns:
        bool: True if the extracted table is plausible for this section; otherwise False.
    """
    if not table_rows or not isinstance(table_rows, list):
        return False

    expected_cols = section_config.get("columns", {})
    if not expected_cols:
        return False
    
    expected_count = len(expected_cols)

    # Internal cleaning helper
    def _clean(v: object) -> str:
        return str(v).replace("\n", " ").strip().lower() if v is not None else ""

    # --- 1. Structural Validation (Rows) ---
    if type_check in ("rows_only", "both"):
        good_rows = 0
        # Check a sample of rows for performance
        sample_size = min(len(table_rows), 20)
        
        for row in table_rows[:sample_size]:
            if not isinstance(row, list): continue
            
            # Use a generator to count non-empty cells (faster than list creation)
            nonempty_count = sum(1 for cell in row if _clean(cell))
            
            # Tolerance: Accept rows that are off by 1 to handle merged/split PDF columns
            if nonempty_count >= (expected_count - 1):
                good_rows += 1

        # Logic: Require at least one valid data row
        if good_rows == 0:
            return False
            
        # Ratio check: At least 40% of the sample must look like valid data
        if sample_size >= 4 and (good_rows / sample_size) < 0.4:
            return False

    # --- 2. Content Validation (Headers) ---
    if type_check in ("header_only", "both"):
        expected_labels = section_config.get("header_labels", [])
        if not expected_labels:
            # If "both" was requested but no labels defined, structure is enough
            return True if type_check == "both" else False
        
        # Flatten the first N rows into a single search string
        header_n = max(1, min(int(max_header_rows), 3))
        header_text = " ".join(
            " ".join(_clean(cell) for cell in row if cell)
            for row in table_rows[:header_n] if isinstance(row, list)
        )

        # Count how many expected keywords appear in the extracted header area
        hits = sum(1 for label in expected_labels if _clean(label) in header_text)

        required_hits = max(1, int(len(expected_labels) * header_match_threshold))
        if hits < required_hits:
            return False

    return True


def parse_rows(table_rows: List[List[str | None]], section_config: Dict, source: str, tax_year: str, *, rows_only: bool = True, max_header_rows: int = 2,) -> List[Dict]:
    """
    Parse extracted PDF table rows into normalized transaction dicts.

    This function is designed to be resilient to common PDF table extraction anomalies:
      - Header rows included/excluded depending on extraction strategy
      - Multi-line descriptions (continuation rows)
      - Noise/total/footer rows
      - Amount formats: $1,234.56, (123.45), 123.45 CR/DR, unicode minus

    Args:
        table_rows: Raw extracted rows (list of rows, each row list of cells)
        section_config: Section config from bank profile JSON (must include "columns")
        source: Bank/source name (e.g., "TD Visa", "CIBC", "Triangle MasterCard")
        tax_year: Tax year string (e.g., "2025") used to resolve partial dates (no year in statement rows)
        rows_only: If True, assume table_rows contain only data rows; if False, drop up to max_header_rows
        max_header_rows: Number of leading rows to drop when rows_only=False

    Returns:
        List[Dict]: Normalized transactions with keys:
            transaction_date (YYYY-MM-DD), posting_date (YYYY-MM-DD or None),
            description, amount (float), source, section
    """
    if not table_rows:
        return []

    section_name = section_config.get("section_name") or section_config.get("name") or "Transactions"

    cols = section_config.get("columns") or {}
    tx_date_idx = cols.get("transaction_date")
    post_date_idx = cols.get("posting_date")
    desc_idx = cols.get("description")
    amt_idx = cols.get("amount")

    # Minimum required to produce a transaction
    if desc_idx is None or amt_idx is None:
        return []

    # ---- Pre-clean once (performance + consistent downstream logic) ----
    clean_rows: List[List[str]] = []
    for r in table_rows:
        if not r or not any(r):
            continue
        clean_rows.append([str(c).replace("\n", " ").strip() if c is not None else "" for c in r])

    if not clean_rows:
        return []

    # Skip headers if caller says header rows are present
    if not rows_only:
        drop_n = min(max(0, int(max_header_rows)), len(clean_rows))
        clean_rows = clean_rows[drop_n:]

    if not clean_rows:
        return []

    year_int = int(tax_year)

    def _cell(row: List[str], idx: Optional[int]) -> str:
        if idx is None:
            return ""
        return row[idx] if 0 <= idx < len(row) else ""

    _AMT_TOKEN = re.compile(r"-?\d+(?:\.\d+)?")

    def _parse_amount(s: str) -> Optional[float]:
        """
        Parse an amount cell into float.
        Supports:
          - "$1,234.56"
          - "(123.45)" -> -123.45
          - "123.45 CR" -> -123.45 (credit reduces balance / payment)
          - "123.45 DR" ->  123.45
          - unicode minus "−"
        Returns None if no numeric token found.
        """
        if not s:
            return None

        s_upper = (
            s.upper()
            .replace("$", "")
            .replace(",", "")
            .replace("−", "-")
            .strip()
        )

        is_credit = "CR" in s_upper
        s_clean = s_upper.replace("CR", "").replace("DR", "").strip()

        if s_clean.startswith("(") and s_clean.endswith(")"):
            inner = s_clean[1:-1].strip()
            m = _AMT_TOKEN.search(inner)
            if not m:
                return None
            try:
                return -abs(float(m.group(0)))
            except ValueError:
                return None

        m = _AMT_TOKEN.search(s_clean)
        if not m:
            return None
        try:
            val = float(m.group(0))
        except ValueError:
            return None

        if is_credit:
            return -abs(val)
        return val

    def _looks_like_date(s: str) -> bool:
        s = (s or "").upper().strip()
        if not s:
            return False
        patterns = [
            r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b",
            r"\b(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\.?\s+\d{1,2}\b",
        ]
        return any(re.search(p, s) for p in patterns)

    def _is_total_or_noise_row(row: List[str]) -> bool:
        """
        Reject obvious totals/footers/noise.
        Keep this conservative: only skip when highly likely non-transaction.
        """
        joined = " ".join(c for c in row if c).strip().upper()
        if not joined:
            return True

        # Common statement footers/totals
        noise_markers = (
            "TOTAL",
            "TOTALS",
            "SUBTOTAL",
            "NEW BALANCE",
            "PREVIOUS STATEMENT BALANCE",
            "STATEMENT BALANCE",
            "BALANCE FORWARD",
            "TOTAL INTEREST",
            "TOTAL PAYMENTS",
            "TOTAL CREDITS",
            "TOTAL CHARGES",
            "TOTAL FEES",
            "ACCOUNT NUMBER",
            "PAGE ",
        )
        if any(m in joined for m in noise_markers):
            # Avoid false positives: "TOTAL" inside merchant names is rare; still treat as noise
            return True

        # Very short single-cell fragments are usually OCR artifacts
        nonempty = [c for c in row if c and c.strip()]
        if len(nonempty) == 1 and len(nonempty[0]) <= 2:
            return True

        return False

    def _is_desc_only_continuation(row: List[str]) -> bool:
        """
        Continuation row heuristic: has description text but lacks amount and date-like tokens.
        """
        desc = _cell(row, desc_idx)
        amt = _parse_amount(_cell(row, amt_idx))

        tx_raw = _cell(row, tx_date_idx)
        post_raw = _cell(row, post_date_idx)

        has_any_date = _looks_like_date(tx_raw) or _looks_like_date(post_raw)
        has_desc = bool(desc and desc.strip())
        has_amount = amt is not None

        return has_desc and (not has_amount) and (not has_any_date)

    def _parse_date(raw: str, *, default_year: int) -> Optional[str]:
        """
        Convert a raw date token to ISO YYYY-MM-DD.
        Supports:
          - 12/31, 12/31/2024, 12/31/24
          - DEC 31, DEC. 31
        Uses default_year when year is missing.
        """
        s = (raw or "").strip().upper()
        if not s:
            return None

        # Numeric date: M/D[/YY|YYYY]
        m = re.search(r"\b(?P<m>\d{1,2})/(?P<d>\d{1,2})(?:/(?P<y>\d{2,4}))?\b", s)
        if m:
            mm = int(m.group("m"))
            dd = int(m.group("d"))
            yy = m.group("y")
            if yy:
                y = int(yy)
                if y < 100:
                    # Interpret 2-digit year as 20xx (reasonable for modern statements)
                    y += 2000
            else:
                y = default_year
            try:
                return datetime(y, mm, dd).strftime("%Y-%m-%d")
            except ValueError:
                return None

        # Alpha date: "DEC 31" or "DEC. 31"
        m = re.search(r"\b(?P<mon>JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\.?\s+(?P<d>\d{1,2})\b", s)
        if m:
            mon_map = {
                "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
                "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
            }
            mm = mon_map.get(m.group("mon"), 0)
            dd = int(m.group("d"))
            if mm <= 0:
                return None
            try:
                return datetime(default_year, mm, dd).strftime("%Y-%m-%d")
            except ValueError:
                return None

        return None

    out: List[Dict] = []
    last_tx: Optional[Dict] = None

    for row in clean_rows:
        if _is_total_or_noise_row(row):
            continue

        # Continuation rows (multi-line descriptions)
        if _is_desc_only_continuation(row):
            if last_tx:
                extra = _cell(row, desc_idx).strip()
                if extra:
                    last_tx["description"] = (last_tx.get("description", "") + " " + extra).strip()
            continue

        desc = _cell(row, desc_idx).strip()
        if not desc:
            # If no description, it's rarely a valid transaction row
            continue

        amt_val = _parse_amount(_cell(row, amt_idx))
        if amt_val is None:
            # If it isn't a continuation row (handled above) and amount is missing, skip
            continue

        tx_date_raw = _cell(row, tx_date_idx)
        post_date_raw = _cell(row, post_date_idx)

        tx_date_iso = _parse_date(tx_date_raw, default_year=year_int) if tx_date_idx is not None else None
        post_date_iso = _parse_date(post_date_raw, default_year=year_int) if post_date_idx is not None else None

        # If we expect a transaction date column but couldn't parse it, skip (prevents garbage rows)
        if tx_date_idx is not None and not tx_date_iso:
            continue

        tx: Dict[str, object] = {
            "transaction_date": tx_date_iso,
            "posting_date": post_date_iso,
            "description": desc,
            "amount": float(amt_val),
            "source": source,
            "section": section_name,
        }

        out.append(tx)
        last_tx = tx

    return out


# @time_it
def debug_parse_pdf(pdf_path: pathlib.Path, bank: str, tax_year: Optional[int] = None):
    profile = load_bank_profile(bank)
    bank_name = profile.get("bank_name", bank)
    table_settings = profile.get("table_settings", {})
    skip_pages = profile.get('skip_pages_by_index', [])
    sections = profile.get("sections", [])
    
    all_data = {section['section_name']: [] for section in sections}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            if page_num in skip_pages:
                print(f"Skipping page {page_num + 1} (Configured skip)")
                continue
            
            print(f"Processing page {page_num + 1}")
            
            # --- Prepare: Get page left margin for alignment checks ---
            left_margin = get_page_left_margin(page, top_fraction=0.20, left_fraction=0.30)

            # 1. Identify where every section starts on this page (if present)
            page_section_positions = []
            for sec in sections:
                bbox = get_section_header_bbox(page, sec["match_text"], left_margin=left_margin)
                if bbox:
                    page_section_positions.append({
                        "section": sec,
                        "top": bbox["top"],
                        "bottom": bbox["bottom"],
                        "left": bbox["x0"],
                        "right": bbox["x1"]
                    })
            
            # Sort sections by their vertical position (top to bottom)
            page_section_positions.sort(key=lambda x: x["top"])

            # 2. Iterate through sections found on this page
            for i, item in enumerate(page_section_positions):
                section = item["section"]
                start_y = item["bottom"]
                left_x, right_x = item["left"], page.width
                header_x_range = (left_x, item["right"])
                
                # Vertical Boundaries: Define the search ceiling (start_y) and floor (end_y) for the table
                max_y = page_section_positions[i+1]["top"] if i + 1 < len(page_section_positions) else page.height
                end_y = max_y # Default to next section top or page bottom
                
                # Check for footer row to refine end_y
                footer_marker = section.get("footer_row_text")
                footer_bbox = None
                if footer_marker:
                    # Define search area for footer: from start_y to max_y
                    search_area_bbox = (left_x, start_y, right_x, max_y)
                    footer_bbox = get_table_footer_bbox(page, footer_marker, search_area_bbox, header_x_range=header_x_range)
                    if footer_bbox:
                        end_y = footer_bbox["text_bbox"]["bottom"] + 5 # Slight padding below footer
                    
                # Table Boundaries: Adjust horizontal and vertical boundaries based on table horizontal lines
                search_strip_bbox = (0, start_y, page.width, end_y)
                table_edges = get_table_edges(page, search_strip_bbox, section, bank_name, footer_bbox=footer_bbox)
                if table_edges is not None:
                    left_x = table_edges["coords"][0]
                    right_x = table_edges["coords"][1]
                    start_y = table_edges["coords"][2]
                    end_y = table_edges["coords"][3]

                # Define Crop Box: (left, top, right, bottom)
                # crop_box = (left_x - 2, start_y, right_x + 2, end_y)
                crop_box = (left_x, start_y, right_x, end_y)
                
                try:
                    cropped_page = page.crop(crop_box)
                except ValueError:
                    print(f"  [Warn] Invalid crop for {section['section_name']}")
                    continue

                # 3. Extract Tables
                if table_edges is not None:
                    if table_settings["vertical_strategy"] == "explicit":
                        table_settings["explicit_vertical_lines"] = table_edges["explicit_vertical_lines"]
                tables = cropped_page.find_tables(table_settings=table_settings)
                
                print(f"  Section '{section['section_name']}': Found {len(tables)} tables.")

                for table in tables:
                    raw_data = table.extract()
                    if not raw_data: continue

                    # 4. Filter & Validate Rows
                    valid_rows = []
                    header_found = False
                    
                    # Get expected columns from config
                    expected_cols = len(section['columns'])

                    for row in raw_data:
                        # Clean row: remove None and empty strings
                        clean_row = [str(c).strip() for c in row if c and str(c).strip()]
                        
                        # A. Header Validation
                        if not header_found:
                            # Check if this row looks like the header defined in JSON
                            # We join to string to be fuzzy-match friendly
                            row_str = " ".join(clean_row).upper()
                            required_labels = [l.upper() for l in section.get("header_labels", [])]
                            
                            # If most labels match, assume it's the header
                            matches = sum(1 for label in required_labels if label in row_str)
                            if matches >= 2: # Loose threshold (2 out of 4)
                                header_found = True
                                continue # Skip the header row itself
                        
                        # B. Data Extraction
                        # Must have enough columns and look like a transaction
                        if len(clean_row) >= expected_cols:
                            # Basic heuristic: Date often in col 0, Amount in last col
                            # You can add regex for date checking here for extra safety
                            
                            # Handle empty cells if strategy="text" creates gaps
                            # We map by index defined in JSON
                            try:
                                tx = {
                                    "transaction_date": row[section['columns']['transaction_date']],
                                    "posting_date": row[section['columns']['posting_date']],
                                    "description": row[section['columns']['description']],
                                    "amount": row[section['columns']['amount']]
                                }
                                valid_rows.append(tx)
                            except IndexError:
                                continue

                    if valid_rows:
                        all_data[section['section_name']].extend(valid_rows)
                        print(f"    -> Extracted {len(valid_rows)} valid transactions.")

    # Final Summary
    total_tx = sum(len(x) for x in all_data.values())
    print(f"\nTotal Transactions Extracted: {total_tx}")
    return all_data


def parse_pdf(pdf_path: pathlib.Path, bank: str, tax_year: Optional[int] = None):
    """
    Extract transactions from a PDF using bank profile config.

    Args:
        pdf_path (Path): Path to the PDF file.
        bank (str): Bank identifier.
        
    Returns:
        list[dict]: All transactions parsed from the PDF.
    """
    # If debug_mode — invoke debug parser to finetune extraction:
    # if debug_mode:
    #     notify(f"Debug parsing enabled for {pdf_path.name} — invoking debug_parse_pdf()", "info")
    #     all_transactions = debug_parse_pdf(pdf_path, bank)
    #     return [tx for section_rows in all_transactions.values() for tx in section_rows]
    # End debug section

    transactions = []
    profile = load_bank_profile(bank)

    # ---- Validate profile structure (fail fast) ----
    sections = profile.get("sections")
    if not isinstance(sections, list) or not sections:
        notify(f"Bank profile for {bank} is missing 'sections' or it is malformed/empty.", "error")
        return transactions

    for s in sections:
        if not isinstance(s, dict) or "section_name" not in s or "match_text" not in s or "columns" not in s:
            notify(f"Bank profile for {bank} has malformed section entries (needs section_name/match_text/columns).", "error")
            return transactions
        if not isinstance(s.get("columns"), dict) or not s["columns"]:
            notify(f"Bank profile for {bank} section '{s.get('section_name')}' has missing/malformed columns.", "error")
            return transactions

    table_settings = profile.get("table_settings", {}) or {}
    skip_indices = set(profile.get("skip_pages_by_index", []) or [])
    header_anchor = profile.get("page_header_anchor", None)
    source_name = profile.get("bank_name", bank)

    # Track sections found on this statement (kept for potential future validation)
    sections_map = {section["section_name"]: [] for section in sections}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Skip pages as per profile config
                if page_num in skip_indices:
                    continue

                # 1) Content-aware page skipping based on header anchor (cheap top-strip scan)
                left_margin = 0.0
                if header_anchor:
                    try:
                        header_area = page.crop((0, 0, page.width, page.height * 0.15))
                        pattern = r'\s+'.join(re.escape(word) for word in header_anchor.split())
                        anchors = header_area.search(pattern, flags=re.IGNORECASE)
                        if not anchors:
                            continue
                        left_margin = float(anchors[0].get("x0", 0.0) or 0.0)
                    except Exception:
                        anchors = []

                # Fallback: if no header anchor or failed, compute left margin from top portion
                if not left_margin:
                    left_margin = float(get_page_left_margin(page, top_fraction=0.20, left_fraction=0.30) or 0.0)

                # 2) Identify all section headers on this page
                page_section_positions = []
                for sec in sections:
                    bbox = get_section_header_bbox(page, sec["match_text"], left_margin=left_margin)
                    if not bbox:
                        continue
                    page_section_positions.append(
                        {
                            "section": sec,
                            "top": bbox["top"],
                            "bottom": bbox["bottom"],
                            "left": bbox["x0"],
                            "right": bbox["x1"],
                        }
                    )
                    sections_map[sec["section_name"]].append(page_num)

                if not page_section_positions:
                    continue

                page_section_positions.sort(key=lambda x: x["top"])

                # 3) For each found section, compute bounds, crop, extract, validate, parse
                for i, item in enumerate(page_section_positions):
                    section = item["section"]

                    # --- Vertical bounds (start after header, end at next section or page bottom) ---
                    start_y = float(item["bottom"])
                    max_y = (
                        float(page_section_positions[i + 1]["top"])
                        if (i + 1) < len(page_section_positions)
                        else float(page.height)
                    )
                    end_y = max_y

                    # --- Optional footer tightening ---
                    footer_marker = section.get("footer_row_text")
                    footer_bbox = None
                    if footer_marker:
                        search_area_bbox = (0.0, start_y, float(page.width), max_y)
                        header_x_range = (float(item["left"]), float(item["right"]))
                        footer_bbox = get_table_footer_bbox(page, footer_marker, search_area_bbox, header_x_range=header_x_range)
                        if footer_bbox and float(footer_bbox["text_bbox"]["top"]) > start_y:
                            # end_y = float(footer_bbox["text_bbox"]["top"])
                            end_y = float(footer_bbox["text_bbox"]["bottom"]) + 5  # small padding below footer

                    # Guard: invalid vertical window
                    if end_y <= start_y + 2:
                        continue
                    
                    # --- Table: validation & refined edge detection ---
                    strip_bbox = (
                        float(footer_bbox["line_bbox"]["x0"]) if footer_bbox and footer_bbox.get("line_bbox") else 0.0,
                        float(start_y),
                        float(footer_bbox["line_bbox"]["x1"]) if footer_bbox and footer_bbox.get("line_bbox") else float(page.width),
                        float(end_y),
                    )
                    
                    # Gate 1: Ensure the area actually looks like a table for this bank statement
                    if not validate_table_presence(page, strip_bbox, section, source_name, footer_bbox=footer_bbox):
                        continue
                    
                    # Gate 2: Get precise table bounds based on text anchors and lines
                    table_edges = get_table_edges(page, strip_bbox, section, source_name, footer_bbox=footer_bbox)
                    
                    if table_edges and table_edges.get("coords"):
                        left_x, top_y, right_x, bottom_y = table_edges["coords"]
                        # Use the refined row_bbox for data extraction (if available)
                        rows_bbox = table_edges.get("rows_bbox", None)
                    else:
                        # Fallback: reasonable corridor based on section header and footer (if any)
                        left_x, top_y, right_x, bottom_y = (max(0.0, float(item["left"]) - 1.0), start_y, min(float(page.width), strip_bbox[2]), end_y)
                        rows_bbox = None

                    # Guard: invalid crop
                    min_w_threshold, min_h_threshold = 50.0, 10.0
                    if rows_bbox and (rows_bbox[2] - rows_bbox[0] < min_w_threshold or rows_bbox[3] - rows_bbox[1] < min_h_threshold):
                        continue
                    if right_x - left_x < min_w_threshold or bottom_y - top_y < min_h_threshold:
                        continue

                    # Create crop box for table extraction: prefer rows_bbox if available, otherwise use the broader header/footer-based bounds
                    crop_box = rows_bbox or (left_x, top_y, right_x, bottom_y)
                    try:
                        cropped_page = page.crop(crop_box)
                    except Exception:
                        continue

                    # --- Extraction settings: inject explicit verticals when available/configured ---
                    effective_table_settings = dict(table_settings)
                    if (
                        table_edges
                        and effective_table_settings.get("vertical_strategy") == "explicit"
                        and table_edges.get("explicit_vertical_lines")
                    ):
                        effective_table_settings["explicit_vertical_lines"] = table_edges["explicit_vertical_lines"]

                    # Prefer single-table extraction for performance; fallback to find_tables when needed
                    table_rows = None
                    try:
                        table_rows = cropped_page.extract_table(table_settings=effective_table_settings)
                    except Exception:
                        table_rows = None

                    if not table_rows:
                        try:
                            tables = cropped_page.find_tables(table_settings=effective_table_settings) or []
                            if tables:
                                # Choose the biggest extracted table (most rows) as best candidate
                                extracted = [t.extract() for t in tables]
                                extracted = [t for t in extracted if t]
                                if extracted:
                                    table_rows = max(extracted, key=lambda t: len(t))
                            elif rows_bbox:
                                cropped_page = page.crop((left_x, top_y, right_x, bottom_y))
                                table_rows = cropped_page.extract_table(table_settings=effective_table_settings)
                        except Exception:
                            table_rows = None

                    # Guard: no table extracted
                    if not table_rows:
                        continue

                    # --- Post-extraction validation ---
                    if not rows_bbox:
                        # Validate header only; row-level integrity is deferred to the parsing stage.
                        if not validate_extracted_table(table_rows, section, type_check="header_only"):
                            continue

                    # --- Parse & normalize rows ---
                    try:
                        new_txs = parse_rows(table_rows, section, source=source_name, tax_year=str(tax_year or datetime.now().year), rows_only=not bool(rows_bbox))
                    except Exception as e:
                        notify(
                            "Failed parsing section %s in %s (page %d): %s"
                            % (section.get("section_name"), pdf_path.name, page_num + 1, e),
                            "error",
                        )
                        continue

                    if new_txs:
                        transactions.extend(new_txs)

    except Exception as e:
        notify("Failed to parse PDF %s: %s" % (pdf_path, e), "error")

    notify("Extracted %d transactions from %s" % (len(transactions), pdf_path.name), "info")
    return transactions


def parse_csv(file_path: pathlib.Path, profile: dict):
    """
    Parse TD Visa CSV statement into normalized transactions.
    """
    transactions = []
    
    with open(file_path, "r") as f:
        for line in f:
            row = line.strip().split(",")
            if not row or len(row) < 5:
                continue

            tx_date = datetime.strptime(row[0], "%m/%d/%Y").strftime("%Y-%m-%d")
            desc = row[1].strip()
            debit = float(row[2]) if row[2] else 0.0
            credit = float(row[3]) if row[3] else 0.0
            amount = debit - credit  # normalize: charges positive, payments negative
            balance = float(row[4]) if row[4] else None

            # Skip footer rows
            if desc in ["PREVIOUS STATEMENT BALANCE", "TOTAL NEW BALANCE"]:
                continue

            transactions.append({
                "transaction_date": tx_date,
                "description": desc,
                "amount": amount,
                "balance": balance,
                "source": profile["bank_name"],
                "section": "Transactions"
            })
    
    return transactions


def export_csv(transactions, out_path: pathlib.Path):
    """
    Write transactions to CSV.

    Args:
        transactions (list[dict]): List of transaction dicts.
        out_path (Path): Output CSV path.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["transaction_date","posting_date","description","amount","source","section"])
            writer.writeheader()
            for tx in transactions:
                writer.writerow(tx)
        notify("Exported %d transactions to %s" % (len(transactions), out_path), "info")
    except Exception as e:
        notify("Failed to export CSV %s: %s" % (out_path, e), "error")


def ingest_year(year: str, bank: str = "triangle"):
    """
    Main entrypoint: discover, normalize, parse, and export all PDFs for a tax year.

    Args:
        year (str): Tax year (e.g., '2024').
        bank (str): Bank identifier (default 'triangle').
    """
    pdfs = discover_pdfs(f"./data/{year}/")
    all_tx = []
    tax_year = int(year)
    
    for pdf in pdfs:
        normalized_pdf = normalize_filename(pdf, bank)
        tx = parse_pdf(normalized_pdf, bank, tax_year=tax_year)
        export_csv(tx, pathlib.Path(f"./output/{year}/{bank}/{normalized_pdf.stem}.csv"))
        all_tx.extend(tx)
        
    # unified CSV
    export_csv(sorted(all_tx, key=lambda x: x["transaction_date"]), pathlib.Path(f"./output/{year}/credit_cards.csv"))
