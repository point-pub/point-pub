from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float, nullable=True)
    image = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    customer_city = db.Column(db.String(100), nullable=True)
    wilaya = db.Column(db.String(100), nullable=True)
    daira = db.Column(db.String(100), nullable=True)
    delivery_type = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    total = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    marketer_code = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='جديد')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product', backref='order_items')


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='reviews')


class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    coupon_type = db.Column(db.String(20), default='quantity')  # 'time' | 'quantity' | 'influencer'
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    max_uses = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='coupons')

    # ===== حقول كوبون المؤثر =====
    # unique=True: كل مؤثر له كوبون واحد فقط (NULL مسموح متعدد للكوبونات العادية)
    influencer_name = db.Column(db.String(100), unique=True, nullable=True, index=True)
    influencer_commission_percent = db.Column(db.Float, default=0.0)
    influencer_total_sales = db.Column(db.Float, default=0.0)
    influencer_total_commission = db.Column(db.Float, default=0.0)
    influencer_total_paid = db.Column(db.Float, default=0.0)

    @property
    def influencer_balance(self):
        """الرصيد المتبقي للمؤثر = إجمالي العمولة - إجمالي المدفوع"""
        return (self.influencer_total_commission or 0) - (self.influencer_total_paid or 0)

    def is_valid(self):
        """التحقق من صلاحية الكوبون. يُرجع (bool, reason)."""
        if not self.is_active:
            return False, 'الكوبون غير نشط'

        if self.coupon_type == 'time':
            now = datetime.utcnow()
            if self.start_date and now < self.start_date:
                return False, 'لم يبدأ الكوبون بعد'
            if self.end_date and now > self.end_date:
                return False, 'انتهت صلاحية الكوبون'

        elif self.coupon_type == 'quantity':
            if self.max_uses and self.used_count >= self.max_uses:
                return False, 'تم استنفاد الكوبون'

        # 'influencer' = لا نهائي
        return True, None


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=True)
    image = db.Column(db.String(200), nullable=True)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(300), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)


class SiteInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)


class GalleryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Marketer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    baridimob = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(50), nullable=True)
    social_link = db.Column(db.String(300), nullable=True)
    motivation = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    total_sales = db.Column(db.Float, default=0)
    total_commission = db.Column(db.Float, default=0)
    total_paid = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MarketerSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marketer_id = db.Column(db.Integer, db.ForeignKey('marketer.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    commission = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    marketer = db.relationship('Marketer', backref='sales')
    order = db.relationship('Order', backref='marketer_sale')


class MarketerPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marketer_id = db.Column(db.Integer, db.ForeignKey('marketer.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    marketer = db.relationship('Marketer', backref='payments')


class Partner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(200), nullable=True)
    partnership_type = db.Column(db.Text, nullable=False)
    motivation = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)