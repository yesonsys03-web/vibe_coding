from docstyle_pro_claude_v4.bridge.vault_indexer import get_chroma_collection
collection = get_chroma_collection()
print("Collection count:", collection.count())
print("Collection peek:", collection.peek(2))
