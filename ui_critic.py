#!/usr/bin/env python3
"""
UI Critic Agent — Reviews interfaces and gives actionable feedback.
Usage:
  python ui_critic.py screenshot.png
  python ui_critic.py https://example.com/screenshot.png
  python ui_critic.py index.html
  python ui_critic.py "A login form with a blue submit button..."
"""

import sys
import base64
import mimetypes
import urllib.request
from pathlib import Path

import anthropic

SYSTEM_PROMPT = """You are an expert UI critic for digital products.

## Your role
Review user interfaces and provide practical, high-signal feedback that helps product designers improve quality fast.

## What you focus on
- Visual hierarchy
- Spacing and alignment
- Typography
- Color usage and contrast
- Accessibility
- Consistency of components and patterns
- Clarity of CTA placement
- Scannability
- Mobile responsiveness
- Interaction affordances

## How you work
When reviewing a screen, flow, or component:
1. Start with a short summary of overall quality.
2. Identify the most important issues first.
3. Explain why each issue matters.
4. Suggest specific improvements.
5. Separate critical issues from optional polish improvements.

## Output format
Use this structure:

### Overall impression
Brief summary.

### What works well
- ...

### Key issues
1. Issue
   - Why it matters
   - Recommendation

### Accessibility concerns
- ...

### Suggested improvements
- ...

## Rules
- Be specific, not generic.
- Prefer practical recommendations over theory.
- Avoid vague comments like "make it cleaner."
- When possible, explain tradeoffs.
- Prioritize usability over decoration."""

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def build_content(input_str: str) -> list:
    """Return a list of content blocks for the given input."""
    path = Path(input_str)

    # Local image file
    if path.exists() and path.suffix.lower() in IMAGE_EXTENSIONS:
        mime = mimetypes.guess_type(input_str)[0] or "image/png"
        data = base64.standard_b64encode(path.read_bytes()).decode()
        return [
            {"type": "image", "source": {"type": "base64", "media_type": mime, "data": data}},
            {"type": "text", "text": "Please review this UI."},
        ]

    # Local HTML file
    if path.exists() and path.suffix.lower() in {".html", ".htm"}:
        html = path.read_text(encoding="utf-8")
        return [{"type": "text", "text": f"Please review this HTML interface:\n\n```html\n{html}\n```"}]

    # URL pointing to an image
    if input_str.startswith(("http://", "https://")):
        suffix = Path(input_str.split("?")[0]).suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            return [
                {"type": "image", "source": {"type": "url", "url": input_str}},
                {"type": "text", "text": "Please review this UI."},
            ]
        # Non-image URL — treat as text description
        return [{"type": "text", "text": f"Please review the UI at this URL: {input_str}"}]

    # Plain text description
    return [{"type": "text", "text": f"Please review this UI:\n\n{input_str}"}]


def main():
    if len(sys.argv) < 2:
        print("Usage: python ui_critic.py <image|html|url|description>")
        sys.exit(1)

    input_str = " ".join(sys.argv[1:])
    content = build_content(input_str)

    client = anthropic.Anthropic()

    print("Reviewing UI...\n")
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": content}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    print()  # trailing newline


if __name__ == "__main__":
    main()
