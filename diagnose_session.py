#!/usr/bin/env python3
"""
Diagnostic: Test update_session with each field individually.
Run: cd /opt/eduscout && source venv/bin/activate && python3 diagnose_session.py

This will tell you EXACTLY which fields fail to update.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from tools.database import (
    create_search_session,
    update_session,
    get_active_session,
    get_db_connection,
)
from tools.preference_extractor import extract_preferences

print("=" * 60)
print("PART 1: Test preference extractor")
print("=" * 60)

tests = [
    "She has ADHD and loves theater",
    "He needs wheelchair access",
    "We prefer montessori in Chelsea budget 40000",
    "Looking for a high school",
    "She also likes robotics and basketball",
]

for t in tests:
    result = extract_preferences(t)
    print(f"  '{t}'")
    print(f"  → {result}\n")

print("=" * 60)
print("PART 2: Test update_session with each field")
print("=" * 60)

# Create a test session
PARENT_ID = 999  # test parent, won't conflict

# Clean up any old test data
conn = get_db_connection()
cur = conn.cursor()
cur.execute("DELETE FROM search_sessions WHERE parent_id = %s", (PARENT_ID,))
conn.commit()
cur.close()
conn.close()

# Create fresh session
session = create_search_session(PARENT_ID, target_level="high")
session_id = session["id"]
print(f"Created test session id={session_id}")

# Test each field individually
test_fields = {
    "budget_max": 50000,
    "special_needs": "adhd",
    "interests": "theater",
    "preferred_neighborhood": "Chelsea",
    "preferred_methodology": "montessori",
    "needs_wheelchair_access": True,
    "religious_preference": "secular",
}

for field, value in test_fields.items():
    try:
        update_session(session_id, **{field: value})
        
        # Read back to verify
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT {field} FROM search_sessions WHERE id = %s", (session_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        actual = row[0] if row else "NOT FOUND"
        status = "✅" if actual is not None and str(actual) != "None" else "❌ NULL"
        print(f"  {field} = {value} → DB has: {actual} {status}")
        
    except Exception as e:
        print(f"  {field} = {value} → ❌ ERROR: {e}")

print()

# Final state
conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT * FROM search_sessions WHERE id = %s", (session_id,))
colnames = [desc[0] for desc in cur.description]
row = cur.fetchone()
cur.close()
conn.close()

print("=" * 60)
print(f"PART 3: Final session state (id={session_id})")
print("=" * 60)
if row:
    for col, val in zip(colnames, row):
        print(f"  {col}: {val}")

# Clean up
conn = get_db_connection()
cur = conn.cursor()
cur.execute("DELETE FROM search_sessions WHERE parent_id = %s", (PARENT_ID,))
conn.commit()
cur.close()
conn.close()
print(f"\nCleaned up test session.")

print()
print("=" * 60)
print("PART 4: Show update_session source code")
print("=" * 60)
import inspect
print(inspect.getsource(update_session))
