import os
from dotenv import load_dotenv
from api.database.database import engine, Base
from sqlalchemy import text

# Load environment variables
load_dotenv()


def check_database():
    """Check database status and create tables if needed"""
    print("🔍 Checking database status...")

    try:
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ Database connected successfully!")
            print(f"📊 Database version: {version[0]}")

            # Check if tables exist
            result = connection.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """
                )
            )
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"📋 Existing tables: {existing_tables}")

            # Check if our tables exist
            required_tables = [
                "trips",
                "passengers",
                "messages",
                "passports",
                "responses",
            ]
            missing_tables = [
                table for table in required_tables if table not in existing_tables
            ]

            if missing_tables:
                print(f"⚠️  Missing tables: {missing_tables}")
                print("🔧 Creating missing tables...")

                # Create all tables
                Base.metadata.create_all(bind=engine)
                print("✅ Tables created successfully!")

                # Verify tables were created
                result = connection.execute(
                    text(
                        """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                    )
                )
                updated_tables = [row[0] for row in result.fetchall()]
                print(f"📋 Updated tables: {updated_tables}")

            else:
                print("✅ All required tables exist!")

            return True

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def test_database_operations():
    """Test basic database operations"""
    print("\n🧪 Testing database operations...")

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

        # Test creating a passenger
        test_passenger = Passenger(
            trip_id=test_trip.id,
            fullName="Test Passenger",
            nationalId="1234567890",
            luggageCount=2,
        )
        db.add(test_passenger)
        db.commit()

        print(f"✅ Test trip created with ID: {test_trip.id}")
        print(f"✅ Test passenger created with ID: {test_passenger.id}")

        # Clean up test data
        db.delete(test_trip)
        db.commit()
        print("🧹 Test data cleaned up")

        return True

    except Exception as e:
        print(f"❌ Database operation error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Database Status Check")
    print("=" * 50)

    # Check database
    if check_database():
        # Test operations
        test_database_operations()
        print("\n🎉 Database is ready!")
    else:
        print("\n❌ Database setup failed!")
