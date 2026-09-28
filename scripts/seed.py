from app.database.connection import SessionLocal
from app.database.seeders.rbac_seeder import seed_rbac


def main() -> None:
    with SessionLocal() as session:
        seed_rbac(session)

    print("RBAC seeding completed successfully.")


if __name__ == "__main__":
    main()