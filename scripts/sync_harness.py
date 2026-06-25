import os
import shutil
from pathlib import Path

def sync_harness():
    # The sync command is valid from any project subdirectory.
    root = str(Path(__file__).resolve().parents[1])
    claude_dir = os.path.join(root, ".claude")
    agents_dir = os.path.join(root, ".agents")

    if not os.path.exists(claude_dir):
        print("Error: .claude directory not found.")
        return

    # 1. Clean and recreate .agents directory
    if os.path.exists(agents_dir):
        shutil.rmtree(agents_dir)
    os.makedirs(agents_dir)

    # 2. Recursively copy files from .claude to .agents with path translation
    for dirpath, dirnames, filenames in os.walk(claude_dir):
        rel_path = os.path.relpath(dirpath, claude_dir)
        target_dir = agents_dir if rel_path == "." else os.path.join(agents_dir, rel_path)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        for filename in filenames:
            src_file = os.path.join(dirpath, filename)
            dest_file = os.path.join(target_dir, filename)

            # Skip settings.local.json or state files if we don't want to copy them
            if filename in ["settings.local.json", "launch.json"] or "state" in rel_path:
                continue

            try:
                # Read content and translate path strings
                with open(src_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Replace path strings
                translated_content = content.replace(".claude/", ".agents/")

                # Write content to target file
                with open(dest_file, "w", encoding="utf-8", newline="\n") as f:
                    f.write(translated_content)
            except Exception as e:
                print(f"Failed to copy and translate {src_file}: {e}")

    # 3. Read CLAUDE.md, translate, and write to AGENTS.md
    claude_md_path = os.path.join(root, "CLAUDE.md")
    agents_md_path = os.path.join(root, "AGENTS.md")

    if os.path.exists(claude_md_path):
        try:
            with open(claude_md_path, "r", encoding="utf-8") as f:
                content = f.read()

            translated_content = content.replace(".claude/", ".agents/")
            
            with open(agents_md_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(translated_content)
            print("Successfully synced .claude/ to .agents/ and CLAUDE.md to AGENTS.md.")
        except Exception as e:
            print(f"Failed to sync CLAUDE.md to AGENTS.md: {e}")
    else:
        print("Warning: CLAUDE.md not found.")

if __name__ == "__main__":
    sync_harness()
