import sys
from worker import export_invoice_ids

cases = [
    ([], []),
    (["inv-1"], ["inv-1"]),
    (["inv-1", "inv-1"], ["inv-1"]),
    (["inv-2", "inv-1", "inv-2"], ["inv-2", "inv-1"]),
    (["inv-3", "inv-2", "inv-1"], ["inv-3", "inv-2", "inv-1"]),
    (["INV-1", "inv-1", "INV-1"], ["INV-1", "inv-1"]),
    (["x", "x", "y", "y", "x"], ["x", "y"]),
    (["a", "b", "c", "a", "c"], ["a", "b", "c"]),
]
errors = 0
for index, (source, expected) in enumerate(cases, 1):
    before = source.copy()
    actual = export_invoice_ids(source)
    if actual != expected or source != before or not isinstance(actual, list):
        errors += 1
        print(f"case {index}: expected {expected!r}, got {actual!r}; input preserved={source == before}")
print(f"work_done={len(cases)} errors={errors}")
sys.exit(bool(errors))
