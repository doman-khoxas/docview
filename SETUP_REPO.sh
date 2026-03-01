#!/bin/bash
# DocView — GitHub Repository Setup Script
# Run this from the pdf_editor directory to initialize and push to GitHub

set -e

REPO_NAME="docview"
DESCRIPTION="DocView — MS Paint-inspired PDF Editor with Redaction, OCR & Annotation Tools"

echo "=== DocView — GitHub Repo Setup ==="
echo ""

# Initialize git if needed
if [ ! -d ".git" ]; then
    git init
    echo "Initialized git repo"
fi

# Add all files
git add -A
git commit -m "Initial commit: DocView v1.0

- PyQt5 Paint-style editor with Windows 7 ribbon UI
- Redaction tool (area + text search) and OCR via ocrmypdf
- Full annotation suite: Pen, Highlighter, Shapes, Text, Eraser
- CLI mode for Claude Code headless operation
- PyInstaller single-executable build support

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# Create GitHub repo and push
echo ""
echo "Creating GitHub repo..."
gh repo create "$REPO_NAME" --public --description "$DESCRIPTION" --source . --remote origin --push

echo ""
echo "=== Done! ==="
echo "Repo: https://github.com/$(gh api user -q .login)/$REPO_NAME"
