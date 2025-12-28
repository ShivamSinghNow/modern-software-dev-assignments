# `extract_action_items()` Function Examples

## Overview

The `extract_action_items()` function in `app/services/extract.py` extracts actionable items from free-form text using pattern matching and heuristics.

## How It Works

The function uses a **three-stage approach**:

1. **Pattern Detection**: Looks for common action item patterns (bullets, checkboxes, keywords)
2. **Fallback Strategy**: If no patterns found, uses imperative verb detection
3. **Deduplication**: Removes duplicate items (case-insensitive)

---

## Example 1: Mixed Formats (Most Common Use Case)

### Input:
```
Meeting Notes - Project Planning

Here are some action items from our discussion:
- [ ] Set up the database schema
* Implement the API extract endpoint
1. Write unit tests for the extraction service
- Review the code architecture
• Update the documentation
[todo] Add error handling
action: Deploy to staging environment
next: Schedule follow-up meeting

Some regular narrative text that won't be extracted.
This is just context information.
```

### Output:
```python
[
  "Set up the database schema",
  "Implement the API extract endpoint",
  "Write unit tests for the extraction service",
  "Review the code architecture",
  "Update the documentation",
  "Add error handling",
  "action: Deploy to staging environment",
  "next: Schedule follow-up meeting"
]
```

### What Happened:
- ✅ Detected `- [ ]` checkbox → extracted "Set up the database schema"
- ✅ Detected `*` bullet → extracted "Implement the API extract endpoint"
- ✅ Detected `1.` numbered list → extracted "Write unit tests..."
- ✅ Detected `-` bullet → extracted "Review the code architecture"
- ✅ Detected `•` bullet → extracted "Update the documentation"
- ✅ Detected `[todo]` → extracted "Add error handling"
- ✅ Detected `action:` prefix → extracted line (prefix kept)
- ✅ Detected `next:` prefix → extracted line (prefix kept)
- ❌ Regular sentences ignored

---

## Example 2: Keyword Prefixes

### Input:
```
TODO: Fix the bug in the login system
action: Update user authentication
next: Test the new feature
todo: Review pull requests
```

### Output:
```python
[
  "TODO: Fix the bug in the login system",
  "action: Update user authentication",
  "next: Test the new feature",
  "todo: Review pull requests"
]
```

### What Happened:
- All lines start with recognized keywords (`todo:`, `action:`, `next:`)
- The keywords are **kept in the output** (not stripped)
- Case-insensitive matching (`TODO:` and `todo:` both work)

---

## Example 3: Fallback to Imperative Sentences

### Input:
```
This is a note without any bullet points or special formatting.
Implement the new feature by next week.
Add comprehensive error handling.
Create a user dashboard.
This is just a regular sentence that won't be extracted.
Write unit tests for all new code.
```

### Output:
```python
[
  "Implement the new feature by next week.",
  "Add comprehensive error handling.",
  "Create a user dashboard.",
  "Write unit tests for all new code."
]
```

### What Happened:
- No bullets, checkboxes, or keywords detected
- Function falls back to **imperative verb detection**
- Looks for sentences starting with verbs like: `implement`, `add`, `create`, `write`, `fix`, `update`, etc.
- Extracted sentences that start with imperative verbs
- Regular sentences (like "This is a note...") were ignored

### Supported Imperative Verbs:
- `add`, `create`, `implement`, `fix`, `update`, `write`, `check`, `verify`, `refactor`, `document`, `design`, `investigate`

---

## Example 4: Duplicate Removal

### Input:
```
- Set up database
- SET UP DATABASE
- set up database
* Implement API
* implement api
```

### Output:
```python
[
  "Set up database",
  "Implement API"
]
```

### What Happened:
- Found 3 variations of "Set up database" (different cases)
- Found 2 variations of "Implement API" (different cases)
- **Deduplication** removed duplicates (case-insensitive)
- Kept the first occurrence of each unique item
- Preserved original capitalization of first occurrence

---

## Example 5: No Action Items Found

### Input:
```
This is just a regular note.
It contains some information.
There are no action items here.
Just narrative text.
```

### Output:
```python
[]
```

### What Happened:
- No bullets, checkboxes, or keywords detected
- No sentences start with imperative verbs
- Returns empty list

---

## Pattern Detection Rules

The function recognizes these patterns:

### 1. Bullet Points
- `-` (hyphen)
- `*` (asterisk)
- `•` (bullet character)
- `1.`, `2.`, etc. (numbered lists)

### 2. Checkbox Markers
- `[ ]` (empty checkbox)
- `[todo]` (todo marker)

### 3. Keyword Prefixes
- `todo:` (case-insensitive)
- `action:` (case-insensitive)
- `next:` (case-insensitive)

### 4. Cleaning Process
- Removes bullet prefixes (`-`, `*`, `•`, `1.`, etc.)
- Removes checkbox markers (`[ ]`, `[todo]`)
- Trims whitespace
- **Does NOT remove keyword prefixes** (`todo:`, `action:`, `next:`)

---

## Step-by-Step Processing

For the input:
```
- [ ] Set up database
* Implement API
```

1. **Split into lines**: `["- [ ] Set up database", "* Implement API"]`
2. **Check each line**:
   - Line 1: Matches bullet pattern `-` and checkbox `[ ]` → **extract**
   - Line 2: Matches bullet pattern `*` → **extract**
3. **Clean extracted items**:
   - Remove `-` and `[ ]` → "Set up database"
   - Remove `*` → "Implement API"
4. **Deduplicate**: No duplicates found
5. **Return**: `["Set up database", "Implement API"]`

---

## Testing the Function

You can test it yourself by running:

```bash
python example_extraction.py
```

Or in Python:

```python
from app.services.extract import extract_action_items

text = """
- [ ] Set up database
* Implement API
"""

items = extract_action_items(text)
print(items)  # ['Set up database', 'Implement API']
```

---

## Notes

- **Case-insensitive deduplication**: "Set up database" and "SET UP DATABASE" are considered duplicates
- **Keyword prefixes preserved**: Lines starting with `todo:`, `action:`, `next:` keep the prefix
- **Order preserved**: Items are returned in the order they appear in the text
- **Whitespace handling**: Leading/trailing whitespace is trimmed
- **Empty lines ignored**: Blank lines are skipped

