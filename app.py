"""
TransUnion CRA Report Analyzer
A Streamlit application for analyzing Credit Reference Agency report data.
"""

import streamlit as st
import pandas as pd
import re
from typing import List, Optional, Tuple

# Page configuration
st.set_page_config(
    page_title="TransUnion CRA Report Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constants
DEFAULT_COLUMN_NAMES = [
    "Account_ID",
    "Column_2",
    "Column_3",
    "Column_4",
    "Column_5",
    "Column_6",
    "Status_Title",
    "First_Name",
    "Last_Name",
    "Address_Line_1",
    "Address_Line_2",
    "City",
    "County",
    "Postcode_1",
    "Postcode_2",
    "Date_Field",
    "Column_17",
    "Column_18",
]

STATUS_CODES = ["A", "M", "P", "V"]
FIXED_LEADING_COLUMNS = 9
FIXED_TRAILING_COLUMNS = 5
VARIABLE_MIDDLE_COLUMNS = 4


# -----------------------------
# Helper Functions
# -----------------------------

def assign_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Apply stable column names, expanding with Column_N names when needed."""
    if len(df.columns) <= len(DEFAULT_COLUMN_NAMES):
        df.columns = DEFAULT_COLUMN_NAMES[: len(df.columns)]
        return df

    column_names = DEFAULT_COLUMN_NAMES.copy()
    for i in range(len(DEFAULT_COLUMN_NAMES), len(df.columns)):
        column_names.append(f"Column_{i + 1}")
    df.columns = column_names
    return df


def split_embedded_date_token(tokens: List[str]) -> List[str]:
    """Split tokens like `6EB19051979` into postcode/date when the separator is missing."""
    if len(tokens) < 3:
        return tokens

    candidate = tokens[-3]
    if re.fullmatch(r"\d{8}", candidate):
        return tokens

    match = re.fullmatch(r"(.+?)(\d{8})", candidate)
    if not match:
        return tokens

    prefix, date_part = match.groups()
    if not prefix:
        return tokens

    updated = tokens.copy()
    updated[-3] = prefix
    updated.insert(len(updated) - 2, date_part)
    return updated


def collapse_middle_tokens(tokens: List[str]) -> List[str]:
    """Collapse variable-width address tokens back into the four expected middle fields."""
    if len(tokens) <= VARIABLE_MIDDLE_COLUMNS:
        return tokens + [""] * (VARIABLE_MIDDLE_COLUMNS - len(tokens))

    county = tokens[-1]
    city = tokens[-2]
    address_tokens = tokens[:-2]

    if len(address_tokens) == 1:
        address_1, address_2 = address_tokens[0], ""
    else:
        split_at = max(1, len(address_tokens) // 2)
        address_1 = " ".join(address_tokens[:split_at])
        address_2 = " ".join(address_tokens[split_at:])

    return [address_1, address_2, city, county]


def normalize_row_width(parts: List[str]) -> List[str]:
    """Normalize one parsed CRA row so core trailing fields stay aligned."""
    expected_columns = len(DEFAULT_COLUMN_NAMES)
    clean_parts = [part.strip() for part in parts if part.strip()]

    if len(clean_parts) > FIXED_LEADING_COLUMNS:
        leading = clean_parts[:FIXED_LEADING_COLUMNS]
        remainder = split_embedded_date_token(clean_parts[FIXED_LEADING_COLUMNS:])
        clean_parts = leading + remainder

    if len(clean_parts) > FIXED_LEADING_COLUMNS + FIXED_TRAILING_COLUMNS:
        leading = clean_parts[:FIXED_LEADING_COLUMNS]
        remainder = clean_parts[FIXED_LEADING_COLUMNS:]
        trailing = remainder[-FIXED_TRAILING_COLUMNS:]
        middle = collapse_middle_tokens(remainder[:-FIXED_TRAILING_COLUMNS])
        normalized = leading + middle + trailing
        if len(normalized) <= expected_columns:
            return normalized + [""] * (expected_columns - len(normalized))

    if len(clean_parts) <= expected_columns:
        return clean_parts + [""] * (expected_columns - len(clean_parts))

    leading = clean_parts[:FIXED_LEADING_COLUMNS]
    remainder = clean_parts[FIXED_LEADING_COLUMNS:]

    if len(remainder) <= expected_columns - FIXED_LEADING_COLUMNS:
        normalized = leading + remainder
        return normalized + [""] * (expected_columns - len(normalized))

    trailing = remainder[-FIXED_TRAILING_COLUMNS:]
    middle = collapse_middle_tokens(remainder[:-FIXED_TRAILING_COLUMNS])
    return leading + middle + trailing


def parse_text_content(text_content: str) -> pd.DataFrame:
    """Parse raw CRA text into a normalized DataFrame."""
    lines = [line for line in text_content.splitlines() if line.strip()]
    if not lines:
        return pd.DataFrame()

    data_rows = []
    for line in lines:
        parts = line.replace("\t", " ").split()
        data_rows.append(normalize_row_width(parts))

    return assign_column_names(pd.DataFrame(data_rows))


@st.cache_data(show_spinner=False)
def parse_file_content(file_name: str, content: bytes) -> Tuple[pd.DataFrame, bool]:
    """Parse uploaded file bytes with cache keys tied to the file content."""
    try:
        text_content = content.decode("utf-8", errors="ignore")
        df = parse_text_content(text_content)
        return df, not df.empty
    except Exception as e:
        st.error(f"Error parsing file: {str(e)}")
        return pd.DataFrame(), False


def parse_data_file(uploaded_file) -> Tuple[pd.DataFrame, bool]:
    """Read a Streamlit upload and parse it without reusing stale cached uploads."""
    uploaded_file.seek(0)
    content = uploaded_file.read()
    return parse_file_content(uploaded_file.name, content)


def extract_status_code(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract status code from the Status_Title column (column 7).

    Tagged values look like: AMiss, VMr, PMrs, MMr etc.
    Untagged values like Mr/Mrs/Miss should NOT be treated as status code M.
    """
    if "Status_Title" not in df.columns:
        return df

    s = df["Status_Title"].astype(str).fillna("").str.strip()

    tagged = (
        (s.str.len() >= 2)
        & (s.str[0].isin(STATUS_CODES))
        & (s.str[1].str.match(r"[A-Z]"))
    )

    df["Status_Code"] = ""
    df.loc[tagged, "Status_Code"] = s.loc[tagged].str[0]

    df["Title"] = s
    df.loc[tagged, "Title"] = s.loc[tagged].str[1:]

    cols = df.columns.tolist()
    status_title_idx = cols.index("Status_Title")

    cols.remove("Status_Code")
    cols.remove("Title")

    cols.insert(status_title_idx + 1, "Status_Code")
    cols.insert(status_title_idx + 2, "Title")

    return df[cols]


def filter_dataframe(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply filters to the DataFrame."""
    filtered_df = df.copy()

    # Account ID filter
    if filters.get("account_id"):
        account_search = str(filters["account_id"]).strip()
        if filters.get("exact_match"):
            filtered_df = filtered_df[filtered_df["Account_ID"] == account_search]
        else:
            filtered_df = filtered_df[
                filtered_df["Account_ID"].astype(str).str.contains(
                    account_search, case=False, na=False
                )
            ]

    # Status code filter
    if filters.get("status_codes"):
        filtered_df = filtered_df[filtered_df["Status_Code"].isin(filters["status_codes"])]

    # Name filters
    if filters.get("first_name"):
        filtered_df = filtered_df[
            filtered_df["First_Name"].astype(str).str.contains(
                filters["first_name"], case=False, na=False
            )
        ]

    if filters.get("last_name"):
        filtered_df = filtered_df[
            filtered_df["Last_Name"].astype(str).str.contains(
                filters["last_name"], case=False, na=False
            )
        ]

    # Postcode filter
    if filters.get("postcode"):
        postcode_mask = (
            filtered_df["Postcode_1"].astype(str).str.contains(filters["postcode"], case=False, na=False)
            | filtered_df["Postcode_2"].astype(str).str.contains(filters["postcode"], case=False, na=False)
        )
        filtered_df = filtered_df[postcode_mask]

    # Generic column search (supports optional regex)
    if filters.get("search_column") and filters.get("search_value"):
        col = filters["search_column"]
        val = filters["search_value"]
        if col in filtered_df.columns:
            regex_mode = bool(filters.get("regex_mode", False))
            try:
                filtered_df = filtered_df[
                    filtered_df[col].astype(str).str.contains(
                        val, case=False, na=False, regex=regex_mode
                    )
                ]
            except Exception as exc:
                # pandas may surface invalid regex patterns via re.error or backend-specific errors.
                if regex_mode:
                    return filtered_df.iloc[0:0]
                raise exc

    return filtered_df


def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")


def load_match_file(uploaded_file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Load an optional reconciliation file and return either data or an error message."""
    if uploaded_file is None:
        return None, None

    try:
        file_name = uploaded_file.name.lower()
        if file_name.endswith(".csv"):
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file), None
        if file_name.endswith(".xlsx"):
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file), None
        return None, "Unsupported file type. Please upload a CSV or XLSX file."
    except Exception as exc:
        return None, f"Unable to read match file: {exc}"


def normalize_match_keys(series: pd.Series) -> pd.Series:
    """Trim values and discard blanks so reconciliation counts are meaningful."""
    normalized = series.fillna("").astype(str).str.strip()
    return normalized[normalized != ""]


def apply_dark_theme() -> None:
    """Apply a restrained dark theme to the Streamlit app."""
    st.markdown(
        """
<style>
  :root {
    --cra-bg: #0b1017;
    --cra-panel: #121a24;
    --cra-panel-strong: #172231;
    --cra-border: rgba(154, 172, 194, 0.18);
    --cra-text: #eef4fb;
    --cra-muted: #9aacc2;
    --cra-primary: #5fb3ff;
    --cra-primary-strong: #2f87d5;
    --cra-success: #44c29a;
    --cra-warning: #f4bd50;
  }

  .stApp {
    background: linear-gradient(180deg, #0b1017 0%, #0f1722 58%, #0b1017 100%);
    color: var(--cra-text);
  }

  [data-testid="stHeader"],
  [data-testid="stToolbar"] {
    background: transparent;
  }

  section[data-testid="stSidebar"] {
    background: #0f1722;
    border-right: 1px solid var(--cra-border);
  }

  h1, h2, h3, h4, p, label, span {
    letter-spacing: 0;
  }

  h1 {
    font-size: 2.35rem;
    font-weight: 750;
  }

  [data-testid="stMetric"],
  [data-testid="stDataFrame"],
  div[data-testid="stAlert"],
  div[data-testid="stExpander"] {
    border: 1px solid var(--cra-border);
    border-radius: 8px;
    background: rgba(18, 26, 36, 0.82);
    box-shadow: 0 14px 34px rgba(0, 0, 0, 0.22);
  }

  [data-testid="stMetric"] {
    padding: 1rem;
  }

  .stButton > button,
  .stDownloadButton > button,
  [data-testid="stFileUploader"] button {
    border-radius: 6px;
    border: 1px solid rgba(95, 179, 255, 0.42);
    background: linear-gradient(180deg, #256fae 0%, #1f5f97 100%);
    color: white;
    font-weight: 650;
    box-shadow: 0 10px 22px rgba(31, 95, 151, 0.24);
  }

  .stButton > button:hover,
  .stDownloadButton > button:hover,
  [data-testid="stFileUploader"] button:hover {
    border-color: rgba(95, 179, 255, 0.78);
    background: linear-gradient(180deg, #2d83c8 0%, #22679f 100%);
  }

  input,
  textarea,
  div[data-baseweb="select"] > div {
    border-radius: 6px !important;
    border-color: var(--cra-border) !important;
    background-color: #101925 !important;
  }

  hr {
    border-color: var(--cra-border);
  }
</style>
""",
        unsafe_allow_html=True,
    )


# -----------------------------
# Main Application
# -----------------------------

def main():
    apply_dark_theme()

    st.title("TransUnion CRA Report Analyzer")
    st.markdown(
        """
Upload your TransUnion CRA report file to analyze and filter the data.
Supports large files (up to 500MB) with tab or space-delimited format.
"""
    )

    # File upload
    st.sidebar.header("File Upload")
    uploaded_file = st.sidebar.file_uploader(
        "Choose a CRA report file",
        type=["txt"],
        help="Upload a tab or space-delimited text file (max 500MB)",
    )

    if uploaded_file is None:
        st.info("Please upload a CRA report file to begin analysis.")

        st.subheader("Expected File Format")
        st.markdown(
            """
The application expects a tab or space-delimited text file with the following structure:

- **Column 1**: Account ID
- **Column 7**: Status Code + Title (e.g., 'AMiss', 'VMr', 'PMiss', 'MMiss')
    - First character is the status code: **A**, **M**, **P**, or **V**
- **Columns 8-9**: First Name, Last Name
- **Remaining columns**: Address fields, dates, and numeric codes

**Sample data:**
            
"""
        )

        st.subheader("Features")
        st.markdown(
            """
- **Quick Status Code Filters**: One-click filtering by A, M, P, or V (stateful toggles)
- **Account ID Search**: Fast lookup with exact or partial matching
- **Name Search**: Filter by first name, last name, or both
- **Postcode Search**: Search across postcode fields
- **Advanced Search**: Filter any column with text search (optional regex)
- **Export Results**: Download filtered data as CSV
- **Large File Support**: Efficiently handles files up to 500MB
- **Pagination + Freeze Columns**: Browse large datasets with a split-view freeze
- **Copy / Export a Single Row**: Quick extraction for CRM notes/attachments
- **Cross-File Matching**: Optional reconciliation against internal extract (CSV/XLSX)
"""
        )
        return

    # Show file info
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.sidebar.success(f"File uploaded: {uploaded_file.name}")
    st.sidebar.info(f"Size: {file_size_mb:.2f} MB")

    # Parse file
    with st.spinner("Loading and parsing file..."):
        df, success = parse_data_file(uploaded_file)

    if not success or df.empty:
        st.error("Failed to parse the file. Please check the file format.")
        st.info(
            """
**Expected format:**
- Tab or space-delimited text file
- Each row should contain account information
- Column 7 should contain status code + title (e.g., 'AMiss', 'VMr')
"""
        )
        return

    # Extract status codes
    df = extract_status_code(df)

    # Status Code Distribution
    st.subheader("Status Code Distribution")
    status_counts = df["Status_Code"].replace("", pd.NA).dropna().value_counts()
    if len(status_counts) > 0:
        st.bar_chart(status_counts)
    else:
        st.info("No tagged status codes found to chart.")

    st.success(f"Successfully loaded {len(df):,} records")

    # -----------------------------
    # Cross-File Matching (Optional)
    # -----------------------------
    st.divider()
    st.subheader("Cross-File Matching (Optional)")

    match_file = st.file_uploader(
        "Upload an internal extract to match against (CSV or XLSX)",
        type=["csv", "xlsx"],
        help="Optional: upload your internal extract to reconcile against CRA file",
    )

    match_df, match_error = load_match_file(match_file)

    if match_error:
        st.error(match_error)

    if match_df is not None and not match_df.empty:
        c1, c2 = st.columns(2)
        with c1:
            cra_key = st.selectbox(
                "CRA match column",
                options=list(df.columns),
                index=list(df.columns).index("Account_ID") if "Account_ID" in df.columns else 0,
            )
        with c2:
            internal_key = st.selectbox(
                "Internal match column",
                options=list(match_df.columns),
                index=list(match_df.columns).index("Account_ID") if "Account_ID" in match_df.columns else 0,
            )

        cra_keys = normalize_match_keys(df[cra_key])
        int_keys = normalize_match_keys(match_df[internal_key])

        cra_set = set(cra_keys)
        int_set = set(int_keys)

        matched = len(cra_set & int_set)
        cra_only = len(cra_set - int_set)
        internal_only = len(int_set - cra_set)

        m1, m2, m3 = st.columns(3)
        m1.metric("Matched (unique keys)", f"{matched:,}")
        m2.metric("In CRA only", f"{cra_only:,}")
        m3.metric("In internal only", f"{internal_only:,}")

        cra_unmatched_df = df[
            df[cra_key].fillna("").astype(str).str.strip().ne("")
            & ~df[cra_key].fillna("").astype(str).str.strip().isin(int_set)
        ]
        internal_unmatched_df = match_df[
            match_df[internal_key].fillna("").astype(str).str.strip().ne("")
            & ~match_df[internal_key].fillna("").astype(str).str.strip().isin(cra_set)
        ]

        if len(cra_unmatched_df) > 0:
            st.caption("CRA records not found in internal extract (preview 200):")
            st.dataframe(cra_unmatched_df.head(200), use_container_width=True, height=300)
            st.download_button(
                "Download CRA-Unmatched (CSV)",
                data=cra_unmatched_df.to_csv(index=False).encode("utf-8"),
                file_name=f"cra_unmatched_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        if len(internal_unmatched_df) > 0:
            st.caption("Internal records not found in CRA file (preview 200):")
            st.dataframe(internal_unmatched_df.head(200), use_container_width=True, height=300)
            st.download_button(
                "Download Internal-Unmatched (CSV)",
                data=internal_unmatched_df.to_csv(index=False).encode("utf-8"),
                file_name=f"internal_unmatched_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # -----------------------------
    # Sidebar Filters
    # -----------------------------
    st.sidebar.header("Filters")
    filters = {}

    # Session state init
    if "status_codes_selected" not in st.session_state:
        st.session_state.status_codes_selected = []

    # Status Code Filter (stateful)
    st.sidebar.subheader("Status Code")
    c1, c2, c3, c4 = st.sidebar.columns(4)

    def _toggle_status(code: str):
        cur = st.session_state.status_codes_selected
        if code in cur:
            st.session_state.status_codes_selected = [x for x in cur if x != code]
        else:
            st.session_state.status_codes_selected = cur + [code]

    with c1:
        if st.button("A", use_container_width=True, help="Toggle Status Code A"):
            _toggle_status("A")
    with c2:
        if st.button("M", use_container_width=True, help="Toggle Status Code M"):
            _toggle_status("M")
    with c3:
        if st.button("P", use_container_width=True, help="Toggle Status Code P"):
            _toggle_status("P")
    with c4:
        if st.button("V", use_container_width=True, help="Toggle Status Code V"):
            _toggle_status("V")

    status_multiselect = st.sidebar.multiselect(
        "Or select multiple:",
        options=STATUS_CODES,
        default=st.session_state.status_codes_selected,
        help="Select one or more status codes to filter",
    )
    st.session_state.status_codes_selected = status_multiselect

    if st.session_state.status_codes_selected:
        filters["status_codes"] = st.session_state.status_codes_selected

    st.sidebar.divider()

    # Account ID Filter
    st.sidebar.subheader("Account ID")
    account_id = st.sidebar.text_input("Search Account ID", help="Search by account ID (Column 1)")
    exact_match = st.sidebar.checkbox("Exact match", value=False)
    if account_id:
        filters["account_id"] = account_id
        filters["exact_match"] = exact_match

    st.sidebar.divider()

    # Name filters
    st.sidebar.subheader("Name Search")
    first_name = st.sidebar.text_input("First Name")
    last_name = st.sidebar.text_input("Last Name")
    if first_name:
        filters["first_name"] = first_name
    if last_name:
        filters["last_name"] = last_name

    st.sidebar.divider()

    # Postcode filter
    st.sidebar.subheader("Address")
    postcode = st.sidebar.text_input("Postcode", help="Search in postcode fields")
    if postcode:
        filters["postcode"] = postcode

    st.sidebar.divider()

    # Advanced Search - any column
    st.sidebar.subheader("Advanced Search")
    search_column = st.sidebar.selectbox(
        "Select Column",
        options=[""] + list(df.columns),
        help="Search in any column",
    )
    search_value = st.sidebar.text_input("Search Value")
    regex_mode = st.sidebar.checkbox("Regex mode", value=False)
    if search_column and search_value:
        filters["search_column"] = search_column
        filters["search_value"] = search_value
        filters["regex_mode"] = regex_mode

    # Reset filters
    if st.sidebar.button("Reset All Filters", use_container_width=True):
        st.session_state.status_codes_selected = []
        st.rerun()

    # Apply filters
    filtered_df = filter_dataframe(df, filters)

    # -----------------------------
    # Results
    # -----------------------------
    st.header("Results")

    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("Total Records", f"{len(df):,}")
    with r2:
        st.metric("Filtered Records", f"{len(filtered_df):,}")
    with r3:
        pct = (len(filtered_df) / len(df) * 100) if len(df) else 0.0
        st.metric("Showing", f"{pct:.1f}%")

    if len(filtered_df) > 0:
        csv_data = convert_df_to_csv(filtered_df)
        st.download_button(
            label="Download Filtered Results (CSV)",
            data=csv_data,
            file_name=f"cra_report_filtered_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()

    # -----------------------------
    # Pagination + Freeze Columns + Copy Row
    # -----------------------------
    st.subheader("Data Preview")

    rows_per_page = st.selectbox("Rows per page:", options=[50, 100, 250, 500, 1000], index=1)

    total_rows = len(filtered_df)
    total_pages = (total_rows - 1) // rows_per_page + 1 if total_rows > 0 else 0

    if total_pages <= 0:
        st.info("No records match the current filters.")
        return

    page = st.number_input(
        f"Page (1-{total_pages})",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1,
    )

    start_idx = (page - 1) * rows_per_page
    end_idx = min(start_idx + rows_per_page, total_rows)

    page_df = filtered_df.iloc[start_idx:end_idx].copy()

    # Freeze columns option (split view)
    freeze_cols = st.checkbox("Freeze first columns (split view)", value=True)
    freeze_n = st.number_input(
        "How many columns to freeze?",
        min_value=1,
        max_value=min(10, len(page_df.columns)),
        value=min(3, len(page_df.columns)),
        step=1,
    )

    if freeze_cols and len(page_df.columns) > freeze_n:
        left_cols = list(page_df.columns[:freeze_n])
        right_cols = list(page_df.columns[freeze_n:])

        left, right = st.columns([1, 3])
        with left:
            st.dataframe(page_df[left_cols], use_container_width=True, height=600)
        with right:
            st.dataframe(page_df[right_cols], use_container_width=True, height=600)
    else:
        st.dataframe(page_df, use_container_width=True, height=600)

    st.caption(f"Showing rows {start_idx + 1} to {end_idx} of {total_rows:,}")

    # Copy / Export a Single Row (uses current page_df)
    st.divider()
    st.subheader("Copy / Export a Single Row")

    if len(page_df) > 0:
        pick = st.number_input(
            "Pick a row number from the table above (within this page):",
            min_value=1,
            max_value=len(page_df),
            value=1,
            step=1,
        )

        selected_row = page_df.iloc[int(pick) - 1]

        st.caption("Selected row (JSON-style) - copy/paste into notes or CRM:")
        st.code(selected_row.to_json(), language="json")

        st.caption("Selected row (CSV) - download for attachments:")
        one_row_csv = selected_row.to_frame().T.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Selected Row (CSV)",
            data=one_row_csv,
            file_name=f"cra_selected_row_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
