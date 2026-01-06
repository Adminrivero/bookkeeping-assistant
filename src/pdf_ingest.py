"""
PDF Ingestion Module for Credit Card Statements
-----------------------------------------------
This module discovers, normalizes, parses, and exports transactions
from credit card statement PDFs (e.g., Triangle MasterCard).
"""
import csv
import re
import pathlib
import pdfplumber
import time
import tempfile
import webbrowser, pathlib
from typing import List, Dict, Optional
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


def parse_section(table, section_config, source):
    """
    Parse a transaction table using bank profile config.

    Args:
        table (list[list[str]]): Extracted table rows.
        section_config (dict): Section config from bank profile JSON.
        source (str): Source identifier.

    Returns:
        list[dict]: Normalized transaction dictionaries.
    """
    transactions = []
    if not table or len(table) < 2:
        notify("Empty or malformed table in section %s" % section_config["section_name"], "warning")
        return transactions

    cols = section_config["columns"]
    for row in table[1:]:
        # Skip footer rows if flagged
        if section_config.get("skip_footer_rows", False) and any("total" in cell.lower() for cell in row if cell):
            continue
        
        tx = {
            "source": source,
            "section": section_config["section_name"]
        }
        
        try:
            for field, idx in cols.items():
                if idx < len(row):
                    value = row[idx].strip()
                    # Convert amount to float if field is "amount"
                    if field == "amount":
                        value = value.replace(",", "").replace("$", "").strip()
                        tx[field] = float(value) if value else 0.0
                    else:
                        tx[field] = value
            transactions.append(tx)
        except Exception as e:
            notify("Skipping malformed row in %s: %s | Error: %s" % (section_config["section_name"], row, e), "warning")
            
    notify("Parsed %d transactions from section %s" % (len(transactions), section_config["section_name"]), "info")
    return transactions


def validate_table_structure(table_rows: List[List[str | None]], section_config: Dict) -> bool:
    """
    Checks if a raw table matches the column structure AND header content
    defined in the config. Returns True if the table is a valid target.
    
    Args:
        table_rows (list[list[str]]): Extracted table rows.
        section_config (dict): Section config from bank profile JSON.
    Returns:
        bool: True if table matches expected structure and headers.
    """
    if not table_rows or len(table_rows) < 1:
        return False

    expected_labels = section_config.get("header_labels", [])
    expected_col_count = len(section_config["columns"])

    # --- CHECK 1: Column Count ---
    # Check the first row (the header)
    first_row = table_rows[0]
    
    # Clean the row to handle empty cells created by pdfplumber's heuristics
    clean_row = [str(c).strip() for c in first_row if c is not None and str(c).strip() != ""]
    
    if len(clean_row) < expected_col_count:
        # Fails if it doesn't have enough data columns
        return False
    
    if not expected_labels:
        # If no expected labels, assume structure check is sufficient (skip header check)
        return True

    # --- CHECK 2: Header Content (Semantic Validation) ---
    # Check if all required header labels are present in the first row.
    # Look for the labels in the *raw, full* first_row, cleaning them up for comparison.
    
    # 1. Prepare the extracted header for comparison
    header_str = " | ".join([str(c).replace("\n", " ").strip() for c in first_row if c is not None]).lower()
    
    # 2. Check for all expected labels
    for label in expected_labels:
        if label.lower() not in header_str:
            return False

    # If both checks pass, high confidence this is a transaction table
    return True


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


def get_section_footer_bbox(page, footer_text, search_area_bbox, header_x_range=None):
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
    # if debug_mode:
    #     debug_visualize_search_area(page, search_area, action="save")
    # End debug section
    
    search_strip = page.crop(search_area_bbox)
    matches = search_strip.search(footer_text)
    
    if not matches:
        return None
    
    # Get all horizontal lines in the search area once to avoid repeated calls
    all_lines = [l for l in search_strip.lines if abs(l["y0"] - l["y1"]) == 0 and (l["x1"] - l["x0"]) > 1]
    
    # Group line segments by y0 coord to find distinct lines that belong to the same horizontal divider (y-coordinate)
    y0_groups = defaultdict(list)
    for line in all_lines:
        y0_groups[line["y0"]].append(line)
        
    # Create a sorted list of horizontal line segments (grouped by their y0 coordinate)
    horizontal_lines = [group for _, group in sorted(y0_groups.items(), key=lambda kv: kv[0])]
    
    valid_matches = []
    for match in matches:
        text_top = match["top"]
        text_bottom = match["bottom"]
        footer_bbox: Dict[str, Optional[dict]] = {"text_bbox": None, "line_bbox": None}
        
        # Check Gate 2: Line Proximity and Horizontal Coverage
        line_above = False
        for l in horizontal_lines:
            line_top= l[0]["top"]
            line_x0 = l[0]["x0"]
            line_x1 = l[-1]["x1"]
            
            # 1. Vertical Proximity Gate
            # Allow the line to be up to 15 points above the text and up to 2 points 'inside' the text box
            is_vertically_aligned = (text_top - 15) <= line_top <= (text_top + 2)
            
            # Ensure the line is physically above the text midline (restrict it to a 15-points range)
            # text_midline = (text_top + text_bottom) / 2
            # is_vertically_aligned = (text_midline - 15) <= line_top < text_midline
            
            # 2. Horizontal Coverage Gate
            # Check if the line starts before and ends after the text box horizontally
            is_horizontally_covering = (line_x0 <= match["x0"]) and (line_x1 >= match["x1"])
            
            if is_vertically_aligned and is_horizontally_covering:
                line_above = True
                footer_bbox["line_bbox"] = {"x0": line_x0, "top": line_top, "x1": line_x1, "bottom": line_top}
                break
        
        # Check Gate 3: Horizontal Overlap (if header bounds are provided)
        overlaps_header = True
        if header_x_range:
            # Check if the footer text is roughly within the same horizontal corridor
            header_x0, header_x1 = header_x_range
            overlaps_header = (match["x0"] > header_x0 and (match["x1"] <= header_x1 or match["x1"] <= (page.width * 0.5)))

        if line_above and overlaps_header:
            footer_bbox["text_bbox"] = {"x0": match["x0"], "top": match["top"], "x1": match["x1"], "bottom": match["bottom"]}
            valid_matches.append(footer_bbox)

    if valid_matches:
        # Return the top_most valid match's dict
        return min(valid_matches, key=lambda r: r["text_bbox"]["top"])
    
    return None


def validate_table_presence(page, strip_bbox, section, bank_name, footer_bbox=None) -> bool:
    """
    Validates table presence using Structural Validation and Regex-based 
    Content Validation to handle multi-line headers and encoding artifacts.
    
    Logic:
    1. If footer_bbox is provided, assume the structural "bottom" is valid.
    2. If not, fall back to searching for at least one significant horizontal line.
    3. In both cases, verify that a minimum percentage of column headers exist.
    
    args:
        page: pdfplumber Page object
        strip_bbox: (left, top, right, bottom) tuple defining the area to check
        section: dict containing expected table section info, including columns
        footer_bbox: Optional dict defining the footer bounding box, if available
        
    Returns:
        bool: True if a valid table is detected, False otherwise
    """
    # Debug section: visualize search area
    if debug_mode:
        debug_visualize_search_area(page, strip_bbox, action="save")
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
        # Fallback: Manual search for horizontal lines (common in tables)
        segments = [l for l in crop.lines if abs(l["y0"] - l["y1"]) == 0 and (l["x1"] - l["x0"]) > 1]
        # Group line segments by y0 coord to find distinct lines that belong to the same horizontal divider (y-coordinate)
        y0_groups = defaultdict(list)
        for line in segments:
            y0_groups[line["y0"]].append(line)
        lines = [group for _, group in sorted(y0_groups.items(), key=lambda kv: kv[0])]
        # Also check for rectangles (TD headers are often in boxes)
        rects = [r for r in crop.rects if (r["x1"] - r["x0"]) > 1]
        has_structure = len(lines) >= 1 or len(rects) >= 1

    # --- 2. Content Validation (Header Regex Match) ---
    header_labels = section.get("header_labels", [])
    if not header_labels:
        return has_structure  # If no header labels defined, rely solely on structural validation.

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
                td_header_rect["bottom"] + 5  # small buffer below the rect
            )
    
    header_crop = page.crop(header_zone_bbox)
    text = header_crop.extract_text() or ""
    
    found_count = 0
    for label in header_labels:
        # Generate a flexible regex pattern for each header label (for potential OCR issues, multi-line headers, or extra whitespace)
        # Base pattern: Replace spaces in label with multi-line space/newline bridge
        pattern_content = re.escape(label).replace(r'\ ', r'\s*[\n\r]?\s*')
        
        # Special Case: Amount, optional space and encoding symbols
        if "AMOUNT" in label.upper():
            # Matches 'AMOUNT', optional space, then '(' + anything + ')'
            pattern_content = r'AMOUNT\s*(\([^\)]*\))?'
        
        # Special Case: Description variations
        if "DESCRIPTION" in label.upper():
            # Allow for "TRANS" "TRANSACTION", "ACTIVITY" prefix
            # pattern_content = r'(TRANS|ACTIVITY|TRANSACTION)?\s*[\n\r]?\s*DESCRIPTION'
            # Allow up to 2 arbitrary prefix tokens before "DESCRIPTION" (letters, digits, &, -, /, .)
            pattern_content = r'(?:[A-Z0-9&\-/\.]+(?:\s+[A-Z0-9&\-/\.]+){0,2}\s*)?DESCRIPTION\b'
        
        # Special Case: The "Interleaved Bridge" strategy for multi-line headers
        if "\n" in label:
            # For labels expected to be multi-line, allow for an interleaved line of up to 3 words between them
            parts = label.split("\n")
            if len(parts) == 2:
                part1, part2 = map(re.escape, parts)
                # Allow either whitespace/newline or a single short interleaved line (up to ~60 chars)
                joiner = r'(?:\s+|[^\n]{1,60}\n[^\n]{1,60})'
                pattern_content = rf'{part1}\s*(?:{joiner})?\s*{part2}'
            else:
                # For more than 2 lines, allow for flexible whitespace/newlines between all parts
                escaped_parts = [re.escape(p) for p in parts]
                pattern_content = r'\s*[\n\r]?\s*'.join(escaped_parts)
        
        # Compile with IGNORECASE for flexibility
        pattern = re.compile(pattern_content, re.IGNORECASE)
        
        # Search for the header lable pattern
        if pattern.search(text):
            found_count += 1
            
    # --- 3. Threshold Validation ---
    # Require at least 75% of headers for high-confidence sections
    # but can fallback to 50% for noisier statements.
    threshold = 0.75 if len(header_labels) > 2 else 0.5
    has_headers = (found_count / len(header_labels)) >= threshold if header_labels else True

    return has_structure and has_headers


def get_table_edges(page, search_area_bbox, vertical=False):
    """
    Finds horizontal lines within a vertical area to determine table edges.
    If vertical=True, returns (left_x, right_x, top_y, bottom_y).
    
    Args:
        page: pdfplumber Page object
        search_area_bbox: (left, top, right, bottom) tuple defining search area
        vertical: bool, if True returns full bbox (left, right, top, bottom)
        
    Returns:
        dict or None: Dictionary with table edges info or None if not found.
    """
    # Debug section: visualize search area
    if debug_mode:
        debug_visualize_search_area(page, search_area_bbox, action="save")
    # End debug section
    
    table_edges = {"coords": (), "headers_bbox": (), "rows_bbox": (), "explicit_vertical_lines": []}
    
    # all_lines = page.within_bbox(search_area_bbox).lines
    all_lines = page.crop(search_area_bbox).lines
    # Filter for horizontal lines that are long enough to be a table separator
    clean_lines = [l for l in all_lines if abs(l["y0"] - l["y1"]) == 0 and (l["x1"] - l["x0"]) > 1]
    # Group lines by y0 prop to find distinct line segments that belong to the same horizontal divider (y-coordinate)
    horizontal_lines = []
    # Loop through clean_lines to group lines and create an ordered list of lists
    y0_groups = {}
    for line in clean_lines:
        y0 = line["y0"]
        if y0 not in y0_groups:
            y0_groups[y0] = []
        y0_groups[y0].append(line)
    # Save grouped lines as a list of lists
    horizontal_lines = [lines for lines in y0_groups.values() if len(lines) > 0]
    # Sort horizontal lines by their y-coordinate (top)
    horizontal_lines.sort(key=lambda lines: lines[0]["top"])
    
    if not horizontal_lines:
        return None
    
    # Assume the first horizontal line group defines the table width
    left_x = horizontal_lines[0][0]["x0"]
    right_x = horizontal_lines[0][-1]["x1"]
    table_edges["coords"] = (left_x, right_x)
    
    if vertical:
        # Determine top and bottom y-coordinates
        top_y = horizontal_lines[0][0]["top"]
        bottom_y = search_area_bbox[3]
        if len(horizontal_lines) > 1:
            bottom_y = horizontal_lines[-1][0]["top"]
        table_edges["coords"] = (left_x, right_x, top_y, bottom_y)
    
    # Find explicit vertical lines in the first horizontal line group
    if len(horizontal_lines[0]) == 5:
        first_group = horizontal_lines[0]
        table_edges["explicit_vertical_lines"] = [line["x1"] for line in first_group]
        table_edges["explicit_vertical_lines"][0] = first_group[0]["x0"]  # Replace first edge with left edge
    
    return table_edges

# @time_it
def debug_parse_pdf(pdf_path: pathlib.Path, bank: str):
    profile = load_bank_profile(bank)
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
                
                # labels = section.get("header_labels", [])
                # if labels:
                #     # Refine Horizontal Boundaries using header labels
                #     end_y = item["bottom"] + 60 # Approx height of header area
                #     # Determine Search Strip (a small vertical area containing the table headers)
                #     search_strip_bbox = (left_x, start_y, right_x, end_y)
                #     # Horizontal Boundaries: Find leftmost and rightmost text in the header row
                #     left_edge = find_header_label_x_coordinate(page, search_strip_bbox, labels[0], edge="left")
                #     right_edge = find_header_label_x_coordinate(page, search_strip_bbox, labels[-1], edge="right")
                #     if left_edge is not None:
                #         left_x = left_edge
                #     if right_edge is not None:
                #         right_x = right_edge
                
                # Vertical Boundaries: Define the search ceiling (start_y) and floor (end_y) for the table
                max_y = page_section_positions[i+1]["top"] if i + 1 < len(page_section_positions) else page.height
                end_y = max_y # Default to next section top or page bottom
                
                # Check for footer row to refine end_y
                footer_marker = section.get("footer_row_text")
                
                if footer_marker:
                    # Define search area for footer: from start_y to max_y
                    search_area_bbox = (left_x, start_y, right_x, max_y)
                    footer_bbox = get_section_footer_bbox(page, footer_marker, search_area_bbox, header_x_range=header_x_range)
                    if footer_bbox:
                        end_y = footer_bbox["text_bbox"]["bottom"] + 5 # Slight padding below footer
                    
                # Table Boundaries: Adjust horizontal and vertical boundaries based on table horizontal lines
                search_strip_bbox = (0, start_y, page.width, end_y)
                table_edges = get_table_edges(page, search_strip_bbox, vertical=True)
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


def parse_pdf(pdf_path: pathlib.Path, bank: str):
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
                        # Debug section: visualize search area
                        # debug_visualize_search_area(page, (0, 0, page.width, page.height * 0.15), action="save")
                        # text = header_area.extract_text() or ""
                        # found = header_anchor in text
                        # End debug section
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
                        footer_bbox = get_section_footer_bbox(page, footer_marker, search_area_bbox, header_x_range=header_x_range)
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
                    
                    # Gate 2: Get precise coordinates based on text anchors and lines
                    table_edges = get_table_edges(page, strip_bbox, vertical=True)
                    
                    if table_edges and "coords" in table_edges:
                        left_x, right_x, top_y, bottom_y = table_edges["coords"]
                        # Keep within page bounds
                        left_x = max(0.0, float(left_x))
                        right_x = min(float(page.width), float(right_x))
                        top_y = max(0.0, float(top_y))
                        bottom_y = min(float(page.height), float(bottom_y))
                    else:
                        # Fallback: reasonable corridor from left margin to page width
                        left_x, right_x, top_y, bottom_y = (max(0.0, float(item["left"]) - 1.0), float(page.width), start_y, end_y)

                    # Guard: invalid crop
                    if right_x <= left_x + 2 or bottom_y <= top_y + 2:
                        continue

                    crop_box = (left_x, top_y, right_x, bottom_y)
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
                        except Exception:
                            table_rows = None

                    if not table_rows:
                        continue

                    # --- Validate target table structure/headers before parsing ---
                    if not validate_table_structure(table_rows, section):
                        continue

                    # --- Parse & normalize ---
                    try:
                        new_txs = parse_section(table_rows, section, source_name)
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
    
    for pdf in pdfs:
        normalized_pdf = normalize_filename(pdf, bank)
        tx = parse_pdf(normalized_pdf, bank)
        export_csv(tx, pathlib.Path(f"./output/{year}/{bank}/{normalized_pdf.stem}.csv"))
        all_tx.extend(tx)
        
    # unified CSV
    export_csv(sorted(all_tx, key=lambda x: x["transaction_date"]), pathlib.Path(f"./output/{year}/credit_cards.csv"))
