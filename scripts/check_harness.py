import os
import re
import sys
from pathlib import Path

def check_harness():
    # Hooks may run from frontend/ or another project subdirectory. Anchor all
    # harness paths to this script instead of inheriting the caller's CWD.
    root = str(Path(__file__).resolve().parents[1])
    errors = []

    def require_exists(rel_path):
        abs_path = os.path.join(root, rel_path)
        if not os.path.exists(abs_path):
            errors.append(f"Missing {rel_path}")
            return False
        return True

    def read_file(rel_path):
        with open(os.path.join(root, rel_path), "r", encoding="utf-8") as f:
            return f.read()

    # 1. Check directories
    required_directories = [
        ".claude/agents",
        ".claude/commands",
        ".claude/memory",
        ".claude/references",
        ".claude/rules",
        ".claude/skills",
        ".claude/state"
    ]
    for directory in required_directories:
        require_exists(directory)

    # 2. Check root indexes
    root_indexes = ["CLAUDE.md", "AGENTS.md"]
    for idx in root_indexes:
        require_exists(idx)

    if len(errors) > 0:
        print_errors_and_exit(errors)

    # 3. Check gitignore
    if require_exists(".gitignore"):
        gitignore = read_file(".gitignore")
        required_ignores = [
            ".claude/settings.local.json",
            ".claude/state/",
            ".agents/state/",
            ".agents/settings.local.json"
        ]
        for pattern in required_ignores:
            if pattern not in gitignore:
                errors.append(f".gitignore missing '{pattern}'")

    # 4. Check CLAUDE.md and AGENTS.md syncing (excluding path differences)
    claude = read_file("CLAUDE.md")
    agents = read_file("AGENTS.md")

    # Sync starts from "## Default Style" or "## Harness Rules & Customizations"
    start_marker = "## Default Style"
    if start_marker in claude and start_marker in agents:
        claude_shared = claude[claude.index(start_marker):]
        agents_shared = agents[agents.index(start_marker):]
        
        # Translate .agents back to .claude in agents_shared to verify logical equality
        translated_agents_shared = agents_shared.replace(".agents/", ".claude/")
        if claude_shared != translated_agents_shared:
            errors.append("CLAUDE.md and AGENTS.md drift after '## Default Style' section")
    else:
        errors.append(f"Missing '{start_marker}' section in CLAUDE.md or AGENTS.md")

    # 5. Check skills and frontmatter
    skills_dir = os.path.join(root, ".claude/skills")
    if os.path.exists(skills_dir):
        skills = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
        for skill in skills:
            skill_path = f".claude/skills/{skill}/SKILL.md"
            if not require_exists(skill_path):
                continue
            
            body = read_file(skill_path)
            fm_match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n", body)
            if not fm_match:
                errors.append(f"{skill_path} missing YAML frontmatter enclosed in '---'")
                continue
            
            frontmatter_lines = fm_match.group(1).strip().splitlines()
            keys = []
            name_val = None
            desc_val = None
            
            for line in frontmatter_lines:
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                keys.append(k)
                if k == "name":
                    name_val = v
                elif k == "description":
                    desc_val = v

            unexpected_keys = [k for k in keys if k not in ["name", "description"]]
            if name_val != skill:
                errors.append(f"{skill_path} name '{name_val}' must match folder '{skill}'")
            if not desc_val or len(desc_val) < 40:
                errors.append(f"{skill_path} description is too short or missing (min 40 chars)")
            if unexpected_keys:
                errors.append(f"{skill_path} has non-portable frontmatter keys: {', '.join(unexpected_keys)}")

    # 6. Check indexing inside CLAUDE.md and AGENTS.md
    def check_indexed_paths(prefix, index_file_content, index_name):
        paths = []
        
        # Helper to collect files in a subdirectory
        def collect_files(subdir):
            full_subdir = os.path.join(root, prefix, subdir)
            if os.path.exists(full_subdir):
                for f in os.listdir(full_subdir):
                    if f == ".gitkeep":
                        continue
                    full_f = os.path.join(full_subdir, f)
                    if os.path.isfile(full_f):
                        paths.append(f"{prefix}/{subdir}/{f}")

        collect_files("rules")
        collect_files("commands")
        collect_files("references")
        collect_files("agents")

        # Collect skills
        skills_sub = os.path.join(root, prefix, "skills")
        if os.path.exists(skills_sub):
            for s in os.listdir(skills_sub):
                if os.path.isdir(os.path.join(skills_sub, s)):
                    paths.append(f"{prefix}/skills/{s}/SKILL.md")

        for p in paths:
            if p not in index_file_content:
                errors.append(f"{index_name} missing reference to {p}")

    check_indexed_paths(".claude", claude, "CLAUDE.md")
    check_indexed_paths(".agents", agents, "AGENTS.md")

    if len(errors) > 0:
        print_errors_and_exit(errors)
    else:
        print(f"Harness check passed successfully.")
        sys.exit(0)

def print_errors_and_exit(errors):
    print("Harness check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    check_harness()
