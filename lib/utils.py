import io
import re
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
from openpyxl import Workbook
from werkzeug.security import generate_password_hash, check_password_hash


VALID_STATUSES = {"Active", "Broken", "Repair", "Retired"}


def hash_password(password: str) -> str:
    return generate_password_hash(password or "", method="pbkdf2:sha256", salt_length=16)


def verify_password(password: str, hashed: str) -> bool:
    return check_password_hash(hashed or "", password or "")


def is_valid_email(email: str) -> bool:
    return re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", email) is not None


def generate_excel_template() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Equipment"
    ws.append(["Equipment Name", "Code", "Category", "Location", "Status", "Description"])
    ws.append(["Laptop X", "EQ-001", "Computers", "London", "Active", "Dell Latitude 7420"])
    ws.append(["Forklift A", "EQ-002", "Vehicles", "Warehouse A", "Repair", "Hydraulic leak"])
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def parse_excel_to_rows(file_stream: io.BytesIO) -> pd.DataFrame:
    df = pd.read_excel(file_stream, dtype=str, header=0)
    df = df.fillna("")
    df.columns = [str(c).strip() for c in df.columns]

    first_row = df.iloc[0].astype(str).str.strip().str.lower().tolist() if len(df.index) else []
    alias_pool = {"equipment name", "name", "equipment", "item name", "asset name", "code", "equipment code", "asset code", "id", "sku", "status", "state", "category", "type", "location", "site", "place", "description", "notes"}
    if first_row and any(v in alias_pool for v in first_row):
        df.columns = [str(x).strip() for x in df.iloc[0].tolist()]
        df = df.iloc[1:].reset_index(drop=True)
        df = df.fillna("")
    return df


def validate_import_rows(df: pd.DataFrame, column_map: Dict[str, str]) -> Tuple[List[Dict], List[str]]:
    errors: List[str] = []
    normalized_cols = {str(c).strip().lower(): c for c in df.columns}

    aliases = {
        "equipment_name": {"equipment name", "name", "equipment", "item name", "asset name"},
        "equipment_code": {"code", "equipment code", "asset code", "id", "sku", "asset id"},
        "category": {"category", "type", "equipment type"},
        "location": {"location", "site", "place"},
        "status": {"status", "state"},
        "description": {"description", "notes", "note", "details"},
    }

    resolved: Dict[str, str | None] = {}
    for field, default_aliases in aliases.items():
        provided = (column_map or {}).get(field)
        if provided and provided in df.columns:
            resolved[field] = provided
            continue
        found = None
        for a in default_aliases:
            key = a.lower()
            if key in normalized_cols:
                found = normalized_cols[key]
                break
        resolved[field] = found

    if not resolved.get("equipment_name") and len(df.columns) >= 1:
        resolved["equipment_name"] = df.columns[0]
    if not resolved.get("equipment_code") and len(df.columns) >= 2:
        resolved["equipment_code"] = df.columns[1]
    if not resolved.get("status"):
        detected_status_col = None
        for col in df.columns:
            sample = set(str(v).strip() for v in df[col].head(20).tolist())
            sample = {s for s in sample if s}
            if sample and all(s in VALID_STATUSES for s in sample):
                detected_status_col = col
                break
        if detected_status_col:
            resolved["status"] = detected_status_col

    rows: List[Dict] = []
    seen_codes = set()

    for idx, row in df.iterrows():
        getv = lambda field: (str(row.get(resolved.get(field), "")).strip() if resolved.get(field) else "")
        extra_data = {str(col): str(row.get(col, "")).strip() for col in df.columns}

        mapped: Dict[str, str] = {
            "equipment_name": getv("equipment_name") or extra_data.get("Equipment Name") or extra_data.get("Name") or extra_data.get("Asset Name") or f"Item {idx+1}",
            "equipment_code": getv("equipment_code") or extra_data.get("Code") or extra_data.get("ID") or extra_data.get("Asset ID") or "",
            "category": getv("category") or extra_data.get("Category") or extra_data.get("Type") or "",
            "location": getv("location") or extra_data.get("Location") or "",
            "status": getv("status") or extra_data.get("Status") or "Active",
            "description": getv("description") or extra_data.get("Description") or extra_data.get("Notes") or "",
            "extra": extra_data,
        }

        if mapped["status"] and mapped["status"] not in VALID_STATUSES:
            errors.append(
                f"Row {idx+2}: invalid status '{mapped['status']}'. Allowed: {', '.join(sorted(VALID_STATUSES))}"
            )

        code = mapped["equipment_code"]
        if code in seen_codes:
            errors.append(f"Row {idx+2}: duplicate equipment_code '{code}' in file")
        elif code and code != "0":
            seen_codes.add(code)

        mapped["imported_at"] = datetime.utcnow()
        rows.append(mapped)

    return rows, errors

