import json
import xml.etree.ElementTree as ET
from seed_accounts import make_valid_account, make_invalid_account, total_records, valid_ratio

json_path = "seed_accounts.json"
xml_path = "seed_accounts.xml"

used_refs = set()
num_valid = int(total_records * valid_ratio)
num_invalid = total_records - num_valid

# Generate records
records = []
for i in range(num_valid):
    records.append(make_valid_account(i, used_refs))
for i in range(num_invalid):
    records.append(make_invalid_account(i, used_refs))

# Write JSON
with open(json_path, "w") as jf:
    json.dump(records, jf, indent=2)

# Write XML
root = ET.Element("records")
for rec in records:
    elem = ET.SubElement(root, "record")
    for k, v in rec.items():
        child = ET.SubElement(elem, k)
        child.text = str(v)
tree = ET.ElementTree(root)
tree.write(xml_path, encoding="utf-8", xml_declaration=True)

print(f"Seeded {len(records)} records to {json_path} and {xml_path}")
