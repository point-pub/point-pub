from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # فهرس فريد: يسمح بعدة NULL (كوبونات عادية) ويمنع تكرار الأسماء (مؤثرين)
        db.session.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_coupon_influencer_name "
            "ON coupon (influencer_name)"
        ))
        db.session.commit()
        print("✅ تم إنشاء الفهرس الفريد على influencer_name بنجاح.")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ خطأ: {e}")
        print("💡 قد تكون هناك أسماء مؤثرين مكررة في قاعدة البيانات.")
        print("   احذف الكوبونات المكررة ثم أعد تشغيل هذا السكريبت.")