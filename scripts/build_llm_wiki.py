#!/usr/bin/env python3
"""Script to compile the Obsidian Project Wiki into the Karpathy LLM Wiki structure."""

import os
import re
from datetime import datetime

WIKI_ROOT = "Project Wiki"
RAW_ROOT = "raw"
LLM_WIKI_ROOT = "wiki"

CATEGORY_MAPPING = {
    "01 Overview": "overview",
    "02 Architecture": "architecture",
    "03 Processes": "processes",
    "04 Security": "security-memory",
    "05 Memory": "security-memory",
    "06 Operations": "operations",
    "07 Harness": "harness",
}

def slugify(name):
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"[\s-]+", "-", name).strip("-")
    return name

def parse_frontmatter(block):
    """Parse the small YAML subset used by Project Wiki frontmatter."""
    parsed = {}
    current_key = None
    for raw_line in block.splitlines():
        if not raw_line.strip():
            continue
        if raw_line.startswith("  - ") and current_key:
            parsed.setdefault(current_key, []).append(raw_line[4:].strip())
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"')
        current_key = key
        parsed[key] = [] if value == "" else value
    return parsed

def main():
    print("Compiling Obsidian Project Wiki to Karpathy LLM Wiki...")
    os.makedirs(RAW_ROOT, exist_ok=True)
    os.makedirs(LLM_WIKI_ROOT, exist_ok=True)
    
    articles_by_category = {}
    
    # 1. Traverse Obsidian Wiki
    for root, dirs, files in os.walk(WIKI_ROOT):
        # Skip internal obsidian files or generated folder
        if ".obsidian" in root or "_generated" in root:
            continue
            
        parent_dir = os.path.basename(root)
        if parent_dir not in CATEGORY_MAPPING:
            continue
            
        category = CATEGORY_MAPPING[parent_dir]
        raw_category_dir = os.path.join(RAW_ROOT, category)
        wiki_category_dir = os.path.join(LLM_WIKI_ROOT, category)
        os.makedirs(raw_category_dir, exist_ok=True)
        os.makedirs(wiki_category_dir, exist_ok=True)
        
        if category not in articles_by_category:
            articles_by_category[category] = []
            
        for file in files:
            if not file.endswith(".md"):
                continue
                
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Parse Frontmatter
            frontmatter = {}
            body = content
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parse_frontmatter(parts[1])
                    body = parts[2].strip()
                    
            title = frontmatter.get("title", os.path.splitext(file)[0])
            updated_date = str(frontmatter.get("updated", "2026-07-05"))
            slug = slugify(os.path.splitext(file)[0])
            
            # Format raw source filename
            raw_filename = f"{updated_date}-{slug}.md"
            raw_filepath = os.path.join(raw_category_dir, raw_filename)
            
            # Write Raw file
            raw_content = f"""# {title}

> Source: {WIKI_ROOT}/{parent_dir}/{file}
> Collected: 2026-07-05
> Published: {updated_date}

{body}
"""
            with open(raw_filepath, "w", encoding="utf-8") as rf:
                rf.write(raw_content)
                
            # Write Compiled Wiki file
            wiki_filename = f"{slug}.md"
            wiki_filepath = os.path.join(wiki_category_dir, wiki_filename)
            
            wiki_content = f"""# {title}

> Sources: Antigravity, 2026-07-05
> Raw: [{title} Source](../../{raw_filepath.replace(os.sep, '/')})

{body}
"""
            with open(wiki_filepath, "w", encoding="utf-8") as wf:
                wf.write(wiki_content)
                
            # Store metadata for Index
            # Extract one-line summary (first paragraph of body)
            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
            summary = "No summary available."
            for p in paragraphs:
                if "\n" in p or p.startswith("<!--") or p.startswith("```"):
                    continue
                if not p.startswith("#") and not p.startswith(">") and not p.startswith("-") and not p.startswith("["):
                    summary = p.split(". ")[0].strip(".") + "."
                    break
            
            articles_by_category[category].append({
                "title": title,
                "path": f"{category}/{wiki_filename}",
                "summary": summary,
                "updated": updated_date
            })
            
    # 2. Build Global Index (wiki/index.md)
    index_filepath = os.path.join(LLM_WIKI_ROOT, "index.md")
    index_content = "# Knowledge Base Index\n\n"
    
    for category in sorted(articles_by_category.keys()):
        index_content += f"## {category}\n\n"
        index_content += f"Nexus compiled knowledge on {category.replace('-', ' ')}.\n\n"
        index_content += "| Article | Summary | Updated |\n"
        index_content += "|---------|---------|---------|\n"
        
        for art in sorted(articles_by_category[category], key=lambda x: x["title"]):
            index_content += f"| [{art['title']}]({art['path']}) | {art['summary']} | {art['updated']} |\n"
        index_content += "\n"
        
    with open(index_filepath, "w", encoding="utf-8") as idx_f:
        idx_f.write(index_content)
        
    # 3. Append to log (wiki/log.md)
    log_filepath = os.path.join(LLM_WIKI_ROOT, "log.md")
    now_str = datetime.now().strftime("%Y-%m-%d")
    log_entry = f"\n- {now_str}: Compiled {sum(len(v) for v in articles_by_category.values())} Obsidian wiki files into Karpathy LLM Wiki (raw/ and wiki/ directories).\n"
    
    if os.path.exists(log_filepath):
        with open(log_filepath, "a", encoding="utf-8") as log_f:
            log_f.write(log_entry)
    else:
        with open(log_filepath, "w", encoding="utf-8") as log_f:
            log_f.write("# Wiki Log\n" + log_entry)
            
    print("Compilation completed successfully!")

if __name__ == "__main__":
    main()
