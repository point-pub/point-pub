from app import app, db
from models import Service, Product, FAQ, SiteInfo

with app.app_context():
    # ===== إضافة الخدمات =====
    if Service.query.count() == 0:
        services = [
            Service(title='اللافتات الإشهارية', description='لافتات خارجية وداخلية بجودة عالية', order=1),
            Service(title='الفيديوهات الإشهارية', description='فيديوهات احترافية تعكس هويتك', order=2),
            Service(title='التغليف والطباعة', description='تغليف المركبات، الواجهات، الطباعة الحرارية', order=3),
            Service(title='التصميم والغرافيك', description='هويات بصرية وشعارات مميزة', order=4),
            Service(title='الديكور والتهيئة', description='تهيئة المحلات بأسلوب عصري', order=5),
            Service(title='التصوير وصناعة المحتوى', description='تصوير احترافي للمنتجات', order=6),
            Service(title='صناعة المواقع', description='تصميم وبرمجة مواقع احترافية', order=7),
        ]
        db.session.add_all(services)
        db.session.commit()
        print('✅ تم إضافة 7 خدمات')

    # ===== إضافة منتجات تجريبية =====
    if Product.query.count() == 0:
        products = [
            Product(name='منتج تجريبي 1', description='وصف المنتج الأول', price=2500, category='عام', stock=10),
            Product(name='منتج تجريبي 2', description='وصف المنتج الثاني', price=3500, category='عام', stock=10),
            Product(name='منتج تجريبي 3', description='وصف المنتج الثالث', price=4500, category='عام', stock=10),
        ]
        db.session.add_all(products)
        db.session.commit()
        print('✅ تم إضافة 3 منتجات')

    # ===== إضافة الأسئلة الشائعة =====
    if FAQ.query.count() == 0:
        faqs = [
            FAQ(question='ما هي خدمات POINT PUB؟', answer='نقدم حلولاً إشهارية متكاملة...', order=1),
            FAQ(question='كيف أحصل على عرض سعر؟', answer='يمكنك التواصل معنا عبر واتساب...', order=2),
            FAQ(question='كم تستغرق مدة التنفيذ؟', answer='تختلف المدة حسب نوع الخدمة...', order=3),
        ]
        db.session.add_all(faqs)
        db.session.commit()
        print('✅ تم إضافة 3 أسئلة شائعة')

    # ===== إضافة معلومات الموقع =====
    if SiteInfo.query.count() == 0:
        infos = [
            SiteInfo(key='whatsapp', value='0793432883'),
            SiteInfo(key='email', value='anisattaallahanis@gmail.com'),
            SiteInfo(key='telegram', value='https://t.me/pointpubdz'),
            SiteInfo(key='address', value='الجزائر'),
        ]
        db.session.add_all(infos)
        db.session.commit()
        print('✅ تم إضافة معلومات الموقع')

    print('🎉 تمت تهيئة قاعدة البيانات بنجاح!')