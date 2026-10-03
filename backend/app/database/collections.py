from app.database.connection import database


users_collection = database["users"]
students_collection = database["students"]
scholarships_collection = database["scholarships"]
applications_collection = database["applications"]
saved_scholarships_collection = database["saved_scholarships"]