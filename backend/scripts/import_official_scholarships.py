import sys
from pathlib import Path

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.database.collections import scholarships_collection
from app.ingestion.official_scholarships import OFFICIAL_SCHOLARSHIPS


def import_scholarships():
    inserted = 0
    updated = 0

    for scholarship in OFFICIAL_SCHOLARSHIPS:

        existing = scholarships_collection.find_one(
            {
                "name": scholarship["name"],
                "academic_year": scholarship["academic_year"],
            }
        )

        if existing:
            scholarships_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": scholarship},
            )

            updated += 1
            print(f"UPDATED: {scholarship['name']}")

        else:
            scholarships_collection.insert_one(scholarship)

            inserted += 1
            print(f"INSERTED: {scholarship['name']}")

    print()
    print("====================================")
    print("Scholarship import completed")
    print("====================================")
    print(f"Inserted : {inserted}")
    print(f"Updated  : {updated}")
    print(f"Total    : {len(OFFICIAL_SCHOLARSHIPS)}")


if __name__ == "__main__":
    import_scholarships()