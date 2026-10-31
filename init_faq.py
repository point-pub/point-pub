from app import app, db
from models import FAQ

with app.app_context():
    if FAQ.query.count() == 0:
        faqs = [
            FAQ(
                question='ما هي خدمات POINT PUB؟',
                answer='نقدم حلولاً إشهارية متكاملة تشمل اللافتات الإشهارية، الفيديو والتصوير، التغليف، الطباعة، التصميم والغرافيك، الهوية البصرية، الديكور والتهيئة، وصناعة المواقع الإلكترونية.',
                order=1,
                is_active=True
            ),
            FAQ(
                question='كيف أحصل على عرض سعر؟',
                answer='يمكنك التواصل معنا عبر WhatsApp أو الاتصال بأحد أرقامنا، وسنقدم لك عرض سعر فوري ومخصص حسب احتياجاتك.',
                order=2,
                is_active=True
            ),
            FAQ(
                question='كم تستغرق مدة التنفيذ؟',
                answer='تختلف المدة حسب نوع الخدمة وحجم المشروع، ولكننا نحرص على التسليم في أقرب وقت ممكن مع الحفاظ على الجودة العالية.',
                order=3,
                is_active=True
            ),
            FAQ(
                question='هل تقدمون ضماناً على خدماتكم؟',
                answer='نعم، نقدم ضماناً على جميع خدماتنا لضمان رضا عملائنا الكامل وجودة العمل المقدم.',
                order=4,
                is_active=True
            ),
            FAQ(
                question='كيف يمكنني متابعة طلبي؟',
                answer='يمكنك التواصل مع فريق الدعم عبر WhatsApp أو الهاتف لمتابعة تقدم طلبك في أي وقت.',
                order=5,
                is_active=True
            ),
            FAQ(
                question='هل تخدمون خارج الجزائر؟',
                answer='حالياً نقدم خدماتنا داخل الجزائر، ويمكننا دراسة طلبات خارج الجزائر حسب كل حالة.',
                order=6,
                is_active=True
            ),
            FAQ(
                question='ما هي طرق الدفع المتاحة؟',
                answer='الدفع عند الاستلام هو الخيار الأساسي. كما يمكننا دراسة خيارات أخرى حسب الاتفاق.',
                order=7,
                is_active=True
            ),
            FAQ(
                question='هل يمكنني تعديل الطلب بعد إرساله؟',
                answer='نعم، يمكنك التواصل معنا في أقرب وقت لتعديل طلبك قبل بدء التنفيذ.',
                order=8,
                is_active=True
            ),
        ]

        db.session.add_all(faqs)
        db.session.commit()
        print('تم إضافة 8 أسئلة شائعة بنجاح')
    else:
        print('الأسئلة موجودة مسبقاً:', FAQ.query.count())