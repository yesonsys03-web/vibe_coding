from pathlib import Path
import sys

# setup path
ROOT = Path("/Users/usabatch/coding/python312_qt6/docstyle-pro_claude_v4")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.vault_indexer import get_chroma_collection, index_document, query_vault

# Create a test file
vault_dir = Path.home() / "Documents" / "DocStyle_Vault"
vault_dir.mkdir(parents=True, exist_ok=True)
test_file = vault_dir / "test_rag.md"
with open(test_file, 'w', encoding='utf-8') as f:
    f.write("안녕하세요. 이 문서는 RAG 테스트를 위한 문서입니다. 여기에 중요한 내용이 많이 들어있습니다.\n\n두번째 문단입니다. 내용이 충분히 길어야 청킹이 됩니다. 1234567890\n")

print("1. Indexing...")
index_document(str(test_file))

print("2. Collection Count:")
col = get_chroma_collection()
print(col.count())

print("3. Querying with filter...")
res1 = query_vault("문서 요약해줘", n_results=5, filter_files=[str(test_file)])
print(f"Res1 length: {len(res1)}")
for r in res1:
    print(r)

print("4. Querying without filter...")
res2 = query_vault("문서 요약해줘", n_results=5)
print(f"Res2 length: {len(res2)}")
