"""
Quick validation script - run after schema.sql and seed_schools.sql
Usage: python validate_db.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from tools.database import query, search_schools, get_school_by_slug


def main():
    print("=" * 60)
    print("EduScout Database Validation")
    print("=" * 60)

    # 1. Count schools
    result = query("SELECT COUNT(*) as total FROM schools")
    total = result[0]["total"]
    print(f"\n✅ Total schools: {total}")
    assert total == 25, f"Expected 25 schools, got {total}"

    # 2. Schools by level
    levels = query("SELECT level, COUNT(*) as cnt FROM schools GROUP BY level ORDER BY cnt DESC")
    print("\n📊 Schools by level:")
    for row in levels:
        print(f"   {row['level']}: {row['cnt']}")

    # 3. Schools by type
    types = query("SELECT school_type, COUNT(*) as cnt FROM schools GROUP BY school_type ORDER BY cnt DESC")
    print("\n📊 Schools by type:")
    for row in types:
        print(f"   {row['school_type']}: {row['cnt']}")

    # 4. Test search: middle school, wheelchair access
    print("\n🔍 Test: Middle schools with wheelchair access")
    results = search_schools(level="middle", has_wheelchair_access=True)
    for s in results:
        print(f"   - {s['name']} ({s['neighborhood']}) ${s['annual_tuition_max']}/yr")
    assert len(results) > 0, "Should find at least 1 school"

    # 5. Test search: budget under $10,000
    print("\n🔍 Test: Schools under $10,000/year (public/charter)")
    results = search_schools(budget_max=10000)
    for s in results:
        print(f"   - {s['name']} ({s['school_type']}) ${s['annual_tuition_max']}/yr")
    assert len(results) > 0, "Should find public/charter schools"

    # 6. Test search: Upper East Side, private
    print("\n🔍 Test: Private schools in Upper East Side")
    results = search_schools(neighborhood="Upper East Side", school_type="private")
    for s in results:
        print(f"   - {s['name']} ${s['annual_tuition_max']}/yr")

    # 7. Test search: special needs support
    print("\n🔍 Test: Schools with special needs support")
    results = search_schools(has_special_needs_support=True)
    for s in results:
        print(f"   - {s['name']} ({s['school_type']})")

    # 8. Test get school detail
    print("\n🔍 Test: Get IDEAL School details")
    school = get_school_by_slug("ideal-school")
    assert school is not None, "IDEAL School should exist"
    print(f"   Name: {school['name']}")
    print(f"   Special needs programs: {len(school['special_needs_programs'])} conditions supported")
    print(f"   Extracurriculars: {len(school['extracurriculars'])} activities")
    print(f"   Wheelchair access: {school['has_wheelchair_access']}")

    # 9. Test extracurriculars
    extras = query("SELECT COUNT(*) as total FROM school_extracurriculars")
    print(f"\n✅ Total extracurricular records: {extras[0]['total']}")

    # 10. Test sports
    sports = query("SELECT COUNT(*) as total FROM school_sports")
    print(f"✅ Total sports records: {sports[0]['total']}")

    # 11. Test special needs
    sn = query("SELECT COUNT(*) as total FROM school_special_needs")
    print(f"✅ Total special needs records: {sn[0]['total']}")

    print("\n" + "=" * 60)
    print("✅ ALL VALIDATIONS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
