import os

# --- 設定區 ---
# 要掃描的專案根目錄 (預設為當前目錄)
PROJECT_ROOT = r'C:\Users\reyliou\cve-2024-23334-lab'
# 輸出的總結檔路徑
OUTPUT_FILE = r'C:\Users\reyliou\lab_full_codebase.txt'

# 允許打包的檔案副檔名
ALLOWED_EXTENSIONS = {
    '.py', '.html', '.js', '.css', '.conf',
    '.yml', '.yaml', '.txt', '.sh', '.json','.bak', '.log',
}

# 要排除的資料夾名稱
EXCLUDE_DIRS = {
    '.git', '__pycache__', 'venv', '.vscode',
    '.idea', 'node_modules', 'uploads'
}

def generate_summary():
    print(f"🚀 開始掃描專案: {PROJECT_ROOT}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        outfile.write("# NEO-MALL Lab Project Full Codebase Summary\n")
        outfile.write(f"# Generated at: {os.path.abspath(OUTPUT_FILE)}\n\n")

        # --- 1. 目錄結構概覽 ---
        outfile.write("## 📂 目錄結構概覽\n")
        outfile.write("```text\n")
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # 排除不需要的資料夾
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            level = root.replace(PROJECT_ROOT, '').count(os.sep)
            indent = ' ' * 4 * level
            outfile.write(f'{indent}{os.path.basename(root)}/\n')
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if any(f.endswith(ext_ptrn) for ext_ptrn in ALLOWED_EXTENSIONS) or f == 'Dockerfile':
                    outfile.write(f'{sub_indent}{f}\n')
        outfile.write("```\n\n---\n\n")

        # --- 2. 遍歷並讀取檔案內容 ---
        outfile.write("## 📝 檔案內容詳情\n\n")
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()

                if ext in ALLOWED_EXTENSIONS or file == 'Dockerfile':
                    relative_path = os.path.relpath(file_path, PROJECT_ROOT)
                    print(f"📝 正在打包: {relative_path}")

                    outfile.write(f"### 📄 檔案路徑: {relative_path}\n")
                    
                    # 根據副檔名決定 Markdown 代碼塊標籤
                    lang = ext.replace('.', '')
                    if lang == 'conf': lang = 'nginx'
                    if lang == 'yml': lang = 'yaml'
                    if file == 'Dockerfile': lang = 'dockerfile'

                    outfile.write(f"```{lang}\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 防錯：如果檔案內包含 ```，替換成 ` ` ` 避免破壞總結檔的 Markdown 結構
                            if "```" in content:
                                content = content.replace("```", "` ` `")
                            outfile.write(content)
                    except Exception as e:
                        outfile.write(f"[無法讀取檔案內容: {str(e)}]")
                    
                    outfile.write("\n```\n\n")

    print(f"\n✅ 打包完成！總結檔已儲存至: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_summary()