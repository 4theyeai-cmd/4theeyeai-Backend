import os
from dotenv import load_dotenv
from api.database.database import engine
from sqlalchemy import text

# Load environment variables
load_dotenv()


def check_trips_table():
    """Check the structure of the trips table"""
    print("🔍 Checking trips table structure...")

    try:
        with engine.connect() as connection:
            # Check if table exists
            result = connection.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'trips'
                )
            """
                )
            )
            table_exists = result.fetchone()[0]

            if not table_exists:
                print("❌ Table 'trips' does not exist")
                return False

            print("✅ Table 'trips' exists")

            # Check table structure
            result = connection.execute(
                text(
                    """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'trips' AND table_schema = 'public'
                ORDER BY ordinal_position
            """
                )
            )
            columns = result.fetchall()

            print("📋 Current table structure:")
            for col in columns:
                print(
                    f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})"
                )

            # Check for required columns
            required_columns = ["id", "airportName", "travelDate", "flightNumber"]
            existing_columns = [col[0] for col in columns]
            missing_columns = [
                col for col in required_columns if col not in existing_columns
            ]

            if missing_columns:
                print(f"❌ Missing columns: {missing_columns}")
                return False
            else:
                print("✅ All required columns exist")
                return True

    except Exception as e:
        print(f"❌ Error checking table: {e}")
        return False


def fix_trips_table():
    """Fix the trips table by recreating it"""
    print("🔧 Fixing trips table...")

    try:
        with engine.connect() as connection:
            # Drop the trips table
            print("🗑️  Dropping trips table...")
            connection.execute(text("DROP TABLE IF EXISTS trips CASCADE"))
            connection.commit()

            # Create the trips table with correct structure
            print("🔧 Creating trips table...")
            connection.execute(
                text(
                    """
                CREATE TABLE trips (
                    id VARCHAR PRIMARY KEY,
                    "airportName" VARCHAR NOT NULL,
                    "travelDate" VARCHAR NOT NULL,
                    "flightNumber" VARCHAR NOT NULL
                )
            """
                )
            )

            # Create the passengers table
            print("🔧 Creating passengers table...")
            connection.execute(
                text(
                    """
                CREATE TABLE passengers (
                    id VARCHAR PRIMARY KEY,
                    trip_id VARCHAR NOT NULL,
                    "fullName" VARCHAR NOT NULL,
                    "nationalId" VARCHAR NOT NULL,
                    "luggageCount" INTEGER NOT NULL,
                    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
                )
            """
                )
            )

            connection.commit()
            print("✅ Tables created successfully!")

            # Verify the structure
            return check_trips_table()

    except Exception as e:
        print(f"❌ Error fixing table: {e}")
        return False


def test_trips_operations():
    """Test basic operations on the trips table"""
    print("\n🧪 Testing trips operations...")

    try:
        with engine.connect() as connection:
            # Test inserting a trip
            test_trip_id = "test-123"
            connection.execute(
                text(
                    """
                INSERT INTO trips (id, "airportName", "travelDate", "flightNumber")
                VALUES (:id, :airport, :date, :flight)
            """
                ),
                {
                    "id": test_trip_id,
                    "airport": "Test Airport",
                    "date": "2024-01-01",
                    "flight": "TEST123",
                },
            )

            # Test inserting a passenger
            connection.execute(
                text(
                    """
                INSERT INTO passengers (id, trip_id, "fullName", "nationalId", "luggageCount")
                VALUES (:id, :trip_id, :name, :national_id, :luggage)
            """
                ),
                {
                    "id": "passenger-123",
                    "trip_id": test_trip_id,
                    "name": "Test Passenger",
                    "national_id": "1234567890",
                    "luggage": 2,
                },
            )

            connection.commit()
            print("✅ Test data inserted successfully")

            # Test querying the data
            result = connection.execute(
                text(
                    """
                SELECT t.id, t."airportName", t."travelDate", t."flightNumber",
                       p."fullName", p."nationalId", p."luggageCount"
                FROM trips t
                LEFT JOIN passengers p ON t.id = p.trip_id
                WHERE t.id = :trip_id
            """
                ),
                {"trip_id": test_trip_id},
            )

            rows = result.fetchall()
            print("📋 Retrieved data:")
            for row in rows:
                print(
                    f"  - Trip: {row[0]} | Airport: {row[1]} | Date: {row[2]} | Flight: {row[3]}"
                )
                if row[4]:  # passenger data
                    print(f"    Passenger: {row[4]} | ID: {row[5]} | Luggage: {row[6]}")

            # Clean up test data
            connection.execute(
                text("DELETE FROM trips WHERE id = :id"), {"id": test_trip_id}
            )
            connection.commit()
            print("🧹 Test data cleaned up")

            return True

    except Exception as e:
        print(f"❌ Error testing operations: {e}")
        return False


def main():
    print("🚀 Trips Table Fix")
    print("=" * 50)

    # Check current table structure
    if check_trips_table():
        print("✅ Trips table is already correct!")
        return

    # Ask for confirmation
    response = input("⚠️  This will recreate the trips table. Continue? (y/N): ")
    if response.lower() != "y":
        print("❌ Operation cancelled")
        return

    # Fix the table
    if not fix_trips_table():
        print("❌ Failed to fix table")
        return

    # Test operations
    if not test_trips_operations():
        print("❌ Failed to test operations")
        return

    print("\n🎉 Trips table fixed successfully!")
    print("You can now use the trips endpoint.")


if __name__ == "__main__":
    main()
