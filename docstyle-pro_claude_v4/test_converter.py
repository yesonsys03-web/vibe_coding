from bridge.converter import convert
import sys
try:
    res = convert("test_doc.md", "/private/var/tmp/test_out.docx", "01")
    print(f"Success: {res.success}")
    if not res.success:
        print(f"Error: {res.error}")
except Exception as e:
    print(f"Exception: {e}")
