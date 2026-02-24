import shutil
import sys
import os

src = "/private/var/tmp/11장. 지혜로운 우리 가족 건강 지킴이_포맷수정_optimized_styled_t01.docx"
dst = "/private/var/tmp/copy_test.docx"
try:
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print("Success! File copied.")
    else:
        print(f"Source file not found: {src}")
except Exception as e:
    print(f"Copy failed: {e}")
