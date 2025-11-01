import os
from dotenv import load_dotenv
from api.database.database import engine, Base
from sqlalchemy import text

# Load environment variables
load_dotenv()


def drop_all_tables():
    """Drop all existing tables"""
    print("🗑️  Dropping all existing tables...")

    try:
        with engine.connect() as connection:
            # Get all table names
            result = connection.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """
                )
            )
            tables = [row[0] for row in result.fetchall()]

            if tables:
                print(f"📋 Found tables: {tables}")

                # Drop all tables
                for table in tables:
                    print(f"🗑️  Dropping table: {table}")
                    connection.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

                connection.commit()
                print("✅ All tables dropped successfully!")
            else:
                print("ℹ️  No tables found to drop")

        return True

    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False


def create_all_tables():
    """Create all tables from models"""
    print("🔧 Creating all tables from models...")

    try:
        # Import all models to ensure they're registered
        from api.models.trip_model import Trip, Passenger
        from api.models.message_model import Message
        from api.models.passport_model import Passport
        from api.models.response_model import Response

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")

        # Verify tables were created
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """
                )
            )
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Created tables: {tables}")

            # Check table structure
            for table in tables:
                print(f"\n🔍 Checking structure of table: {table}")
                result = connection.execute(
                    text(
                        f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """
                    )
                )
                columns = result.fetchall()
                for col in columns:
                    print(
                        f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})"
                    )

        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def test_table_operations():
    """Test basic operations on the new tables"""
    print("\n🧪 Testing table operations...")

    try:
        from api.database.database import get_db
        from api.models.trip_model import Trip, Passenger

        db = next(get_db())

        # Test creating a trip
        test_trip = Trip(
            airportName="Test Airport", travelDate="2024-01-01", flightNumber="TEST123"
        )
        db.add(test_trip)
        db.flush()  # Get the ID

        print(f"✅ Test trip created with ID: {test_trip.id}")
        print(f"  - airportName: {test_trip.airportName}")
        print(f"  - travelDate: {test_trip.travelDate}")
        print(f"  - flightNumber: {test_trip.flightNumber}")

        # Test creating a passenger
        test_passenger = Passenger(
            trip_id=test_trip.id,
            fullName="Test Passenger",
            nationalId="1234567890",
            luggageCount=2,
        )
        db.add(test_passenger)
        db.commit()

        print(f"✅ Test passenger created with ID: {test_passenger.id}")
        print(f"  - fullName: {test_passenger.fullName}")
        print(f"  - nationalId: {test_passenger.nationalId}")
        print(f"  - luggageCount: {test_passenger.luggageCount}")

        # Clean up test data
        db.delete(test_trip)
        db.commit()
        print("🧹 Test data cleaned up")

        return True

    except Exception as e:
        print(f"❌ Error testing operations: {e}")
        return False


def main():
    print("🚀 Database Table Fix")
    print("=" * 50)

    # Ask for confirmation
    response = input(
        "⚠️  This will DROP ALL EXISTING TABLES and recreate them. Continue? (y/N): "
    )
    if response.lower() != "y":
        print("❌ Operation cancelled")
        return

    # Drop all tables
    if not drop_all_tables():
        print("❌ Failed to drop tables")
        return

    # Create all tables
    if not create_all_tables():
        print("❌ Failed to create tables")
        return

    # Test operations
    if not test_table_operations():
        print("❌ Failed to test operations")
        return

    print("\n🎉 Database tables fixed successfully!")
    print("You can now run your application.")


if __name__ == "__main__":
    main()
