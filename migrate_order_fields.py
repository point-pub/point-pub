from app import app, db
from sqlalchemy import text

MIGRATIONS = [
    'ALTER TABLE "order" ADD COLUMN wilaya VARCHAR(100)',
    'ALTER TABLE "order" ADD COLUMN daira VARCHAR(100)',
    'ALTER TABLE "order" ADD COLUMN delivery_type VARCHAR(50)',
]

with app.app_context():
    for sql in MIGRATIONS:
        try:
            db.session.execute(text(sql))
            db.session.commit()
            print(f" OK: {sql}")
        except Exception as e:
            db.session.rollback()
            print(f" SKIP (موجود مسبقاً): {e}")
    print("\n تمت ترحيل حقول Order بنجاح.")