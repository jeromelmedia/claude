#!/usr/bin/env python3
"""
Project Knowledge Base Loader
Loads files from a local directory to simulate Claude Project context.
"""

import os
from pathlib import Path
from typing import List, Dict
import json


class ProjectKnowledgeLoader:
    """Load and format project knowledge files for Claude API."""

    def __init__(self, project_dir: str = "./project_files"):
        """Initialize with project files directory."""
        self.project_dir = Path(project_dir)
        self.supported_extensions = {'.txt', '.md', '.json', '.csv', '.py', '.js', '.html', '.css'}

    def load_all_files(self) -> str:
        """Load all supported files from project directory."""
        if not self.project_dir.exists():
            return ""

        knowledge_base = []

        for file_path in sorted(self.project_dir.rglob('*')):
            if file_path.is_file() and file_path.suffix in self.supported_extensions:
                try:
                    content = self._load_file(file_path)
                    if content:
                        knowledge_base.append(content)
                except Exception as e:
                    print(f"Warning: Could not load {file_path}: {e}")

        if knowledge_base:
            return "\n\n".join(knowledge_base)
        return ""

    def _load_file(self, file_path: Path) -> str:
        """Load a single file with proper formatting."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Format the content with file name header
            relative_path = file_path.relative_to(self.project_dir)
            formatted = f"=== File: {relative_path} ===\n\n{content}\n\n=== End of {relative_path} ==="
            return formatted
        except Exception as e:
            return ""

    def create_system_prompt(self, base_instructions: str = "") -> str:
        """Create a system prompt that includes project knowledge."""
        knowledge = self.load_all_files()

        if not knowledge:
            return base_instructions

        prompt = base_instructions + "\n\n"
        prompt += "=== PROJECT KNOWLEDGE BASE ===\n\n"
        prompt += "You have access to the following project files and references. Use this knowledge to inform your responses:\n\n"
        prompt += knowledge
        prompt += "\n\n=== END PROJECT KNOWLEDGE BASE ===\n\n"
        prompt += "Use the information and examples from the knowledge base above to generate content that matches the style, topics, and format demonstrated in these files."

        return prompt

    def get_file_list(self) -> List[str]:
        """Get list of all loaded files."""
        if not self.project_dir.exists():
            return []

        return [
            str(f.relative_to(self.project_dir))
            for f in sorted(self.project_dir.rglob('*'))
            if f.is_file() and f.suffix in self.supported_extensions
        ]


def main():
    """Test the project loader."""
    loader = ProjectKnowledgeLoader()
    files = loader.get_file_list()

    print("=== PROJECT KNOWLEDGE LOADER ===\n")

    if files:
        print(f"Found {len(files)} file(s):\n")
        for f in files:
            print(f"  - {f}")

        print(f"\n{'='*60}")
        print("Sample System Prompt (first 500 chars):")
        print(f"{'='*60}\n")

        prompt = loader.create_system_prompt("You are a video script writer.")
        print(prompt[:500] + "...\n")
    else:
        print("No files found in ./project_files/")
        print("\nTo use this feature:")
        print("1. Create a 'project_files' folder")
        print("2. Add your reference files (txt, md, json, etc.)")
        print("3. Run the macro - it will automatically load them")


if __name__ == "__main__":
    main()
