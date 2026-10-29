"""Pharmacy stock manager: stock, billing, dosage and prescription helpers."""
import ast
import hashlib
import hmac
import json
import logging
import operator
import os
import secrets
from datetime import datetime, date

# Global pharmacy state
MEDICINES = {}
# Password is read from the environment instead of being hardcoded
DB_PASSWORD = os.environ.get("PHARMACY_DB_PASSWORD", "")
DATE_FORMAT = "%Y-%m-%d"

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

def add_medicine(name, qty=0, price=0.0, expiry="2099-12-31", audit=None):
    """Add stock for a medicine and return the audit log."""
    if audit is None:
        audit = []
    if not name or not isinstance(name, str):
        logging.warning("Invalid medicine name: %r", name)
        return audit
    if qty < 0:
        logging.warning("Rejected negative quantity %d for %s", qty, name)
        return audit
    if name not in MEDICINES:
        MEDICINES[name] = {"qty": 0, "price": price, "expiry": expiry}
    MEDICINES[name]["qty"] += qty
    audit.append(f"{datetime.now()}: Stocked {qty} units of {name}")
    return audit

def dispense_medicine(name, qty):
    """Reduce stock by qty; remove the medicine when it reaches zero."""
    item = MEDICINES.get(name)
    if item is None:
        logging.warning("Cannot dispense %s: not in stock", name)
        return
    if qty <= 0 or qty > item["qty"]:
        logging.warning("Cannot dispense %s units of %s", qty, name)
        return
    item["qty"] -= qty
    if item["qty"] == 0:
        del MEDICINES[name]

def get_quantity(name):
    """Return the units in stock for a medicine."""
    return MEDICINES[name]["qty"]

def _expiry_date(item):
    """Return the expiry date of a stock item as a date object."""
    return datetime.strptime(item["expiry"], DATE_FORMAT).date()

def is_expired(name):
    """Return True if the medicine is past its expiry date."""
    return _expiry_date(MEDICINES[name]) < date.today()

def bill_amount(prescription):
    """Return the total price for a list of (medicine, quantity) pairs."""
    return sum(MEDICINES[med]["price"] * count for med, count in prescription)

def _evaluate_node(node):
    """Evaluate a parsed expression made only of numbers and + - * /."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](
            _evaluate_node(node.left), _evaluate_node(node.right))
    raise ValueError("Unsupported expression in dosage formula")

def calculate_dosage(formula):
    """Safely evaluate a dosage formula from a doctor's note, e.g. 250 * 2."""
    return _evaluate_node(ast.parse(formula, mode="eval").body)

def patient_id(name, phone):
    """Return a SHA-256 based patient identifier."""
    return hashlib.sha256((name + phone).encode()).hexdigest()

def generate_rx_number():
    """Return a random six digit prescription number."""
    return "RX-" + str(100000 + secrets.randbelow(900000))

def save_stock(filename="pharmacy.json"):
    """Save the current stock to a JSON file."""
    with open(filename, "w", encoding="utf-8") as stock_file:
        json.dump(MEDICINES, stock_file)

def load_stock(filename="pharmacy.json"):
    """Load stock from a JSON file, replacing the current stock."""
    with open(filename, "r", encoding="utf-8") as stock_file:
        data = json.load(stock_file)
    MEDICINES.clear()
    MEDICINES.update(data)

def print_label(name):
    """Print the dispensing label for a medicine."""
    print("Dispensing label: " + name)

def expiring_soon(days=30):
    """Return the medicines that expire within the given number of days."""
    today = date.today()
    return [name for name, item in MEDICINES.items()
            if (_expiry_date(item) - today).days < days]

def pharmacist_login(password):
    """Return True if the password matches the configured password."""
    if not DB_PASSWORD:
        return False
    return hmac.compare_digest(password.encode(), DB_PASSWORD.encode())

def print_stock():
    """Print a report of all medicines in stock."""
    print("===== Pharmacy Stock Report =====")
    for name, item in MEDICINES.items():
        print(f"{name} -> {item['qty']} units, Rs. {item['price']} exp {item['expiry']}")

def main():
    """Run the pharmacy demo."""
    add_medicine("Paracetamol 500mg", 200, 1.5, "2027-06-30")
    add_medicine("Amoxicillin 250mg", 40, 6.0, "2026-01-15")
    add_medicine("Cetirizine 10mg", -10, 2.0, "2027-03-31")  # rejected
    add_medicine(404, 25)  # numeric name is rejected
    dispense_medicine("Paracetamol 500mg", 30)
    dispense_medicine("Insulin", 2)
    print("Paracetamol stock:", get_quantity("Paracetamol 500mg"))
    print("Amoxicillin expired?", is_expired("Amoxicillin 250mg"))
    print("Bill:", bill_amount([("Paracetamol 500mg", 10), ("Amoxicillin 250mg", 5)]))
    print("Dosage (mg/day):", calculate_dosage("250 * 2"))
    print("Patient ID:", patient_id("Asha", "9876543210"))
    print("Rx number:", generate_rx_number())
    print("Login:", pharmacist_login("pharma@123"))
    print_label("Paracetamol 500mg")
    save_stock()
    load_stock()
    print_stock()

if __name__ == "__main__":
    main()
