"""
Example demonstrating how extract_action_items() works with various inputs.
Run this to see the function in action!
"""

from app.services.extract import extract_action_items

# Example 1: Mixed bullet points and checkboxes
print("=" * 60)
print("EXAMPLE 1: Mixed bullet points and checkboxes")
print("=" * 60)
input_text_1 = """
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
"""
print("\nINPUT TEXT:")
print(input_text_1)
print("\nEXTRACTED ACTION ITEMS:")
result_1 = extract_action_items(input_text_1)
for i, item in enumerate(result_1, 1):
    print(f"  {i}. {item}")

# Example 2: Keyword-prefixed lines
print("\n" + "=" * 60)
print("EXAMPLE 2: Keyword-prefixed lines")
print("=" * 60)
input_text_2 = """
TODO: Fix the bug in the login system
action: Update user authentication
next: Test the new feature
todo: Review pull requests
"""
print("\nINPUT TEXT:")
print(input_text_2)
print("\nEXTRACTED ACTION ITEMS:")
result_2 = extract_action_items(input_text_2)
for i, item in enumerate(result_2, 1):
    print(f"  {i}. {item}")

# Example 3: Fallback to imperative sentences (no bullets/keywords)
print("\n" + "=" * 60)
print("EXAMPLE 3: Fallback to imperative sentences")
print("=" * 60)
input_text_3 = """
This is a note without any bullet points or special formatting.
Implement the new feature by next week.
Add comprehensive error handling.
Create a user dashboard.
This is just a regular sentence that won't be extracted.
Write unit tests for all new code.
"""
print("\nINPUT TEXT:")
print(input_text_3)
print("\nEXTRACTED ACTION ITEMS:")
result_3 = extract_action_items(input_text_3)
for i, item in enumerate(result_3, 1):
    print(f"  {i}. {item}")

# Example 4: Duplicate handling
print("\n" + "=" * 60)
print("EXAMPLE 4: Duplicate removal (case-insensitive)")
print("=" * 60)
input_text_4 = """
- Set up database
- SET UP DATABASE
- set up database
* Implement API
* implement api
"""
print("\nINPUT TEXT:")
print(input_text_4)
print("\nEXTRACTED ACTION ITEMS (duplicates removed):")
result_4 = extract_action_items(input_text_4)
for i, item in enumerate(result_4, 1):
    print(f"  {i}. {item}")

# Example 5: Empty or no action items
print("\n" + "=" * 60)
print("EXAMPLE 5: Text with no action items")
print("=" * 60)
input_text_5 = """
This is just a regular note.
It contains some information.
There are no action items here.
Just narrative text.
"""
print("\nINPUT TEXT:")
print(input_text_5)
print("\nEXTRACTED ACTION ITEMS:")
result_5 = extract_action_items(input_text_5)
if result_5:
    for i, item in enumerate(result_5, 1):
        print(f"  {i}. {item}")
else:
    print("  (No action items found)")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Example 1 extracted {len(result_1)} items")
print(f"Example 2 extracted {len(result_2)} items")
print(f"Example 3 extracted {len(result_3)} items")
print(f"Example 4 extracted {len(result_4)} items (duplicates removed)")
print(f"Example 5 extracted {len(result_5)} items")

