from pathlib import Path
import re

project_root = Path(__file__).resolve().parent.parent


files = [
    project_root / "README.md",
    project_root / "docs/usage.md",
    project_root / "docs/developer.md",
    project_root / "docs/CHANGELOG.md"
]

output_file = project_root / "CONCATENATED_README.md"

#Function to delete Table of Contents in CONCATENATED_README.md
def remove_table_of_contents(content_text: str) -> str:
    lines = content_text.splitlines()
    filtered_lines = []

    in_table_of_contents = False

    for line in lines:
        # Remove the Table of Contents title (e.g., **Table of Contents**)
        if "**Table of Contents**" in line:
            in_table_of_contents = True
            continue

        # Remove items in Table of Contents
        if line.strip().startswith("- ["):
            continue

        if in_table_of_contents and not line.strip().startswith("-"):
            in_table_of_contents = False

        if not in_table_of_contents:
            filtered_lines.append(line)

    return "\n".join(filtered_lines)

with open(output_file, "w", encoding="utf-8") as outfile:
    for file in files:
        with open(file, "r", encoding="utf-8") as infile:
            content = infile.read()
            if file.name == "README.md":
                content = remove_table_of_contents(content)  # Remove Table of Contents
            outfile.write(content + "\n\n")  # Add spacing between files
