"""
Synthetic invoice data generator for testing and demo purposes.
"""
import random
import json
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional


VENDORS = [
    {"name": "Acme Corp", "avg_invoice": 1500, "std_dev": 500},
    {"name": "TechSupply Inc", "avg_invoice": 2800, "std_dev": 800},
    {"name": "CloudServices LLC", "avg_invoice": 3500, "std_dev": 1000},
    {"name": "Office Depot", "avg_invoice": 450, "std_dev": 200},
    {"name": "DataCorp", "avg_invoice": 2200, "std_dev": 600},
    {"name": "SecureIT Solutions", "avg_invoice": 1800, "std_dev": 400},
    {"name": "NetworkPro", "avg_invoice": 3100, "std_dev": 900},
    {"name": "SoftwareHub", "avg_invoice": 950, "std_dev": 300},
    {"name": "HardwareWorld", "avg_invoice": 4100, "std_dev": 1200},
    {"name": "ConsultingGroup", "avg_invoice": 5000, "std_dev": 1500},
]

LINE_ITEM_DESCRIPTIONS = [
    "Professional Services",
    "Software License",
    "Cloud Storage",
    "Technical Support",
    "Hardware Equipment",
    "Consulting Hours",
    "Training Session",
    "Maintenance Fee",
    "Domain Registration",
    "Security Subscription",
]

TAX_RATES = [0.0, 0.0625, 0.075, 0.08, 0.0825, 0.0875]


def generate_invoice_number(vendor: str, index: int) -> str:
    """Generate a unique invoice number."""
    vendor_code = "".join([c for c in vendor.split()[0] if c.isupper()])[:3]
    return f"INV-2026-{vendor_code}-{index:04d}"


def generate_line_items(num_items: int, total_budget: float) -> List[Dict[str, Any]]:
    """Generate random line items that sum to the total budget."""
    items = []
    remaining = total_budget

    for i in range(num_items - 1):
        max_item = remaining * 0.6
        item_total = random.uniform(50, max_item)
        remaining -= item_total

        quantity = random.randint(1, 10)
        unit_price = item_total / quantity

        items.append({
            "description": random.choice(LINE_ITEM_DESCRIPTIONS),
            "quantity": round(quantity, 2),
            "unit_price": round(unit_price, 2),
            "total": round(item_total, 2),
        })

    items.append({
        "description": random.choice(LINE_ITEM_DESCRIPTIONS),
        "quantity": 1,
        "unit_price": round(remaining, 2),
        "total": round(remaining, 2),
    })

    return items


def generate_base_invoice(
    index: int,
    vendor_override: Optional[str] = None,
    date_offset: int = 0
) -> Dict[str, Any]:
    """Generate a base invoice without anomalies."""
    vendor_data = random.choice(VENDORS) if not vendor_override else next(
        v for v in VENDORS if v["name"] == vendor_override
    )

    base_date = date(2026, 1, 1) + timedelta(days=random.randint(0, 45))
    invoice_date = base_date + timedelta(days=date_offset)
    due_date = invoice_date + timedelta(days=30)

    mean = vendor_data["avg_invoice"]
    std = vendor_data["std_dev"]
    total = max(100, random.gauss(mean, std))

    subtotal = total
    tax_rate = random.choice(TAX_RATES)
    tax = round(subtotal * tax_rate, 2)
    total_with_tax = subtotal + tax

    num_items = random.randint(2, 8)
    line_items = generate_line_items(num_items, subtotal)

    return {
        "document_id": f"doc_{index:05d}",
        "vendor_name": vendor_data["name"],
        "vendor_address": f"{random.randint(100, 9999)} Business Ave, Suite {random.randint(100, 500)}",
        "vendor_email": f"billing@{vendor_data['name'].lower().replace(' ', '')}.com",
        "vendor_phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
        "vendor_tax_id": f"XX-{random.randint(100000000, 999999999)}",
        "invoice_number": generate_invoice_number(vendor_data["name"], index),
        "invoice_date": invoice_date.isoformat(),
        "due_date": due_date.isoformat(),
        "customer_name": "Example Corporation",
        "customer_address": "123 Main Street, Anytown, ST 12345",
        "line_items": line_items,
        "subtotal": round(subtotal, 2),
        "tax": tax,
        "tax_rate": tax_rate,
        "total": round(total_with_tax, 2),
        "currency": "USD",
        "payment_terms": "Net 30",
    }


def inject_price_spike(invoice: Dict[str, Any], spike_percent: float = 70.0) -> Dict[str, Any]:
    """Inject a price spike anomaly by significantly increasing the total."""
    original_total = invoice["total"]
    spike_multiplier = 1 + (spike_percent / 100)

    new_total = round(original_total * spike_multiplier, 2)
    difference = new_total - original_total

    invoice["total"] = new_total
    invoice["anomaly_type"] = "price_spike"
    invoice["anomaly_details"] = {
        "original_total": original_total,
        "new_total": new_total,
        "difference": difference,
        "spike_percent": spike_percent,
    }

    return invoice


def inject_duplicate_charge(invoice: Dict[str, Any], duplicate_invoice: Dict[str, Any]) -> Dict[str, Any]:
    """Inject duplicate charge anomaly."""
    invoice["anomaly_type"] = "duplicate_charge"
    invoice["anomaly_details"] = {
        "duplicate_of": duplicate_invoice["invoice_number"],
        "same_vendor": True,
        "same_amount": True,
        "same_date": True,
    }

    duplicate_invoice["anomaly_type"] = "duplicate_charge"
    duplicate_invoice["anomaly_details"] = {
        "duplicate_of": invoice["invoice_number"],
        "same_vendor": True,
        "same_amount": True,
        "same_date": True,
    }

    return invoice


def inject_tax_anomaly(invoice: Dict[str, Any]) -> Dict[str, Any]:
    """Inject a tax calculation anomaly."""
    original_tax = invoice["tax"]
    invoice["tax"] = round(original_tax * random.uniform(0.7, 0.9), 2)
    invoice["total"] = invoice["subtotal"] + invoice["tax"]

    invoice["anomaly_type"] = "tax_anomaly"
    invoice["anomaly_details"] = {
        "original_tax": original_tax,
        "modified_tax": invoice["tax"],
        "difference": original_tax - invoice["tax"],
        "description": "Tax amount does not match tax rate",
    }

    return invoice


def generate_invoices(count: int = 50, anomaly_rate: float = 0.15) -> List[Dict[str, Any]]:
    """
    Generate synthetic invoices with optional anomalies.

    Args:
        count: Number of invoices to generate
        anomaly_rate: Percentage of invoices with anomalies (0.0 to 1.0)

    Returns:
        List of invoice dictionaries
    """
    invoices = []

    for i in range(count):
        invoice = generate_base_invoice(i + 1, date_offset=random.randint(0, 30))
        invoices.append(invoice)

    num_anomalies = int(count * anomaly_rate)
    anomaly_indices = set(random.sample(range(count), min(num_anomalies, count)))

    duplicate_pairs = []
    used_indices = set()
    for idx in list(anomaly_indices):
        if idx in used_indices:
            continue
        if random.random() < 0.3 and idx + 1 < count and (idx + 1) not in used_indices:
            duplicate_pairs.append((idx, idx + 1))
            used_indices.add(idx)
            used_indices.add(idx + 1)

    for idx1, idx2 in duplicate_pairs:
        invoices[idx1] = inject_duplicate_charge(invoices[idx1], invoices[idx2])
        anomaly_indices.discard(idx2)

    for idx in anomaly_indices:
        anomaly_type = random.choice(["price_spike", "tax_anomaly"])

        if anomaly_type == "price_spike":
            invoices[idx] = inject_price_spike(invoices[idx], spike_percent=random.uniform(60, 100))
        elif anomaly_type == "tax_anomaly":
            invoices[idx] = inject_tax_anomaly(invoices[idx])

    return invoices


def save_invoices_to_json(invoices: List[Dict[str, Any]], filepath: str):
    """Save invoices to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(invoices, f, indent=2)


def load_invoices_from_json(filepath: str) -> List[Dict[str, Any]]:
    """Load invoices from a JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    invoices = generate_invoices(50, anomaly_rate=0.15)

    output_path = "/Users/patriciorequena/Documents/PersonalProjects/docops-agent/src/data/sample_invoices.json"
    save_invoices_to_json(invoices, output_path)

    print(f"Generated {len(invoices)} sample invoices")
    print(f"Saved to {output_path}")

    anomalies = [inv for inv in invoices if "anomaly_type" in inv]
    print(f"Injected {len(anomalies)} anomalies")
