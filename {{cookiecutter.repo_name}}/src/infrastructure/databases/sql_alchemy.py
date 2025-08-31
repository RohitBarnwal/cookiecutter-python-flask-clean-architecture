from databases import Database
from src.domain import SQLALCHEMY_DATABASE_URI, OperationalException

database = Database(SQLALCHEMY_DATABASE_URI)

def setup_database(app):
    @app.on_event("startup")
    async def startup():
        try:
            await database.connect()
        except Exception as e:
            raise OperationalException(f"Could not connect to database: {e}")

    @app.on_event("shutdown")
    async def shutdown():
        try:
            await database.disconnect()
        except Exception as e:
            raise OperationalException(f"Could not disconnect from database: {e}")
