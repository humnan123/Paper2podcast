from app.db import SessionLocal
from app.models import User
from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def create_admin():

    db = SessionLocal()

    try:

        existing = (
            db.query(User)
            .filter(
                User.email == "admin@papercms.com"
            )
            .first()
        )


        if existing:
            print("Admin already exists")
            return


        admin = User(
            name="System Admin",
            email="admin@papercms.com",
            password_hash=pwd_context.hash(
                "Admin@123"
            ),
            role="admin",
            is_verified=True
        )


        db.add(admin)
        db.commit()
        db.refresh(admin)


        print(
            "Admin created successfully"
        )

        print(
            "Email: admin@papercms.com"
        )

        print(
            "Password: Admin@123"
        )


    finally:
        db.close()



if __name__ == "__main__":
    create_admin()