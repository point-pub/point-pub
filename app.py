from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
import os

from models import (
    db, User, Product, Order, OrderItem, Review, Coupon,
    Service, FAQ, SiteInfo, GalleryItem,
    Marketer, MarketerSale, MarketerPayment, Partner
)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

# ===== إعداد قاعدة البيانات (PostgreSQL على Render، SQLite محلياً) =====
database_url = os.getenv('DATABASE_URL')
if database_url:
    # إجبار SQLAlchemy على استخدام psycopg2 بدلاً من psycopg (v3)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///point_pub.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/products'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============================================
# ===== Context Processor (عدد السلة) =====
# ============================================
@app.context_processor
def cart_count():
    cart = session.get('cart', {})
    count = sum(cart.values()) if cart else 0
    return {'cart_count': count}


# ============================================
# ===== الصفحة الرئيسية =====
# ============================================
@app.route('/')
def home():
    products = Product.query.filter_by(is_active=True).limit(8).all()
    services = Service.query.filter_by(is_active=True).order_by(Service.order).all()
    
    folder_path = os.path.join(app.static_folder, 'images/gallery')
    gallery_images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if os.path.exists(folder_path) else []
    gallery_images.sort()
    
    return render_template('index.html', products=products, services=services, gallery_images=gallery_images)


# ============================================
# ===== المتجر =====
# ============================================
@app.route('/shop')
def shop():
    search = request.args.get('search', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    category = request.args.get('category', '')

    query = Product.query.filter_by(is_active=True)

    if search:
        query = query.filter(Product.name.contains(search))
    if min_price:
        query = query.filter(Product.price >= min_price)
    if max_price:
        query = query.filter(Product.price <= max_price)
    if category:
        query = query.filter_by(category=category)

    products = query.all()
    categories = db.session.query(Product.category).distinct().all()

    return render_template('shop.html',
                           products=products,
                           categories=categories,
                           search=search,
                           min_price=min_price,
                           max_price=max_price)


# ============================================
# ===== صفحة المنتج =====
# ============================================
@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    reviews = Review.query.filter_by(product_id=id, is_approved=True).order_by(Review.created_at.desc()).all()
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(product_id=id, is_approved=True).scalar()
    return render_template('product.html', product=product, reviews=reviews, avg_rating=avg_rating)


@app.route('/product/<int:id>/review', methods=['POST'])
def add_review(id):
    product = Product.query.get_or_404(id)
    name = request.form.get('name')
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '')

    if not name or not rating:
        flash('الرجاء إدخال الاسم والتقييم', 'error')
        return redirect(url_for('product_detail', id=id))

    review = Review(product_id=id, customer_name=name, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    flash('شكراً لك! تم استلام تقييمك وسيتم عرضه بعد المراجعة.', 'success')
    return redirect(url_for('product_detail', id=id))


# ============================================
# ===== السلة =====
# ============================================
@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            subtotal = product.price * qty
            total += subtotal
            items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
    return render_template('cart.html', items=items, total=total)


@app.route('/add-to-cart/<int:id>')
def add_to_cart(id):
    cart = session.get('cart', {})
    cart[str(id)] = cart.get(str(id), 0) + 1
    session['cart'] = cart
    flash('تمت إضافة المنتج إلى السلة', 'success')
    return redirect(url_for('shop'))


@app.route('/remove-from-cart/<int:id>')
def remove_from_cart(id):
    cart = session.get('cart', {})
    if str(id) in cart:
        del cart[str(id)]
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/update-cart/<int:id>/<int:qty>')
def update_cart(id, qty):
    cart = session.get('cart', {})
    if qty <= 0:
        cart.pop(str(id), None)
    else:
        cart[str(id)] = qty
    session['cart'] = cart
    return redirect(url_for('cart'))


# ============================================
# ===== إتمام الطلب =====
# ============================================
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        city = request.form.get('city')
        notes = request.form.get('notes', '')
        coupon_code = request.form.get('coupon', '')
        marketer_code = request.form.get('marketer_code', '')

        cart = session.get('cart', {})
        if not cart:
            flash('السلة فارغة', 'error')
            return redirect(url_for('shop'))

        items = []
        total = 0
        for pid, qty in cart.items():
            product = Product.query.get(int(pid))
            if product:
                subtotal = product.price * qty
                total += subtotal
                items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})

        discount = 0
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
            if coupon:
                valid = True

                if coupon.coupon_type == 'time':
                    now = datetime.utcnow()
                    if coupon.start_date and now < coupon.start_date:
                        valid = False
                    if coupon.end_date and now > coupon.end_date:
                        valid = False

                elif coupon.coupon_type == 'quantity':
                    if coupon.max_uses and coupon.used_count >= coupon.max_uses:
                        valid = False

                if valid:
                    discount = total * (coupon.discount_percent / 100)
                    total -= discount
                    coupon.used_count += 1
                    flash(f'تم تطبيق الخصم: {coupon.discount_percent}%', 'success')
                else:
                    flash('عذراً، هذا الكوبون غير صالح', 'error')

        order = Order(
            customer_name=name,
            customer_phone=phone,
            customer_address=address,
            customer_city=city,
            notes=notes,
            total=total,
            discount=discount,
            marketer_code=marketer_code
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product'].id,
                product_name=item['product'].name,
                price=item['product'].price,
                quantity=item['quantity']
            )
            db.session.add(order_item)

        if marketer_code:
            marketer = Marketer.query.filter_by(code=marketer_code, status='approved').first()
            if marketer:
                commission = total * 0.15
                sale = MarketerSale(
                    marketer_id=marketer.id,
                    order_id=order.id,
                    amount=total,
                    commission=commission
                )
                db.session.add(sale)
                marketer.total_sales += total
                marketer.total_commission += commission

        db.session.commit()
        session['cart'] = {}

        flash('تم استلام طلبك بنجاح! سنتواصل معك قريباً.', 'success')
        return redirect(url_for('order_success', id=order.id))

    return render_template('checkout.html')


@app.route('/order-success/<int:id>')
def order_success(id):
    order = Order.query.get_or_404(id)
    return render_template('order_success.html', order=order)


# ============================================
# ===== صفحة الشركاء =====
# ============================================
@app.route('/partners', methods=['GET', 'POST'])
def partners():
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        sector = request.form.get('sector')
        contact_name = request.form.get('contact_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address', '')
        website = request.form.get('website', '')
        partnership_type = request.form.get('partnership_type')
        motivation = request.form.get('motivation', '')

        if sector == 'other':
            custom_sector = request.form.get('custom_sector', '').strip()
            if custom_sector:
                sector = custom_sector

        if not all([company_name, sector, contact_name, phone, email, partnership_type]):
            flash('الرجاء ملء جميع الحقول المطلوبة', 'error')
            return redirect(url_for('partners'))

        partner = Partner(
            company_name=company_name,
            sector=sector,
            contact_name=contact_name,
            phone=phone,
            email=email,
            address=address,
            website=website,
            partnership_type=partnership_type,
            motivation=motivation,
            status='pending'
        )
        db.session.add(partner)
        db.session.commit()

        flash('تم استلام طلب الشراكة بنجاح! سنتواصل معك قريباً.', 'success')
        return redirect(url_for('partners'))

    return render_template('partners.html')


# ============================================
# ===== صفحة المسوقين =====
# ============================================
@app.route('/marketers', methods=['GET', 'POST'])
def marketers():
    marketers_enabled = os.getenv('MARKETERS_ENABLED', 'false').lower() == 'true'

    if request.method == 'POST':
        if not marketers_enabled:
            flash('التسجيل في برنامج المسوقين مغلق حالياً', 'error')
            return redirect(url_for('marketers'))

        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        baridimob = request.form.get('baridimob')
        state = request.form.get('state')
        experience = request.form.get('experience', '')
        social_link = request.form.get('social_link', '')
        motivation = request.form.get('motivation', '')

        if not all([full_name, phone, email, baridimob, state]):
            flash('الرجاء ملء جميع الحقول المطلوبة', 'error')
            return redirect(url_for('marketers'))

        existing = Marketer.query.filter_by(email=email).first()
        if existing:
            session['marketer_email'] = email
            flash('هذا البريد الإلكتروني مسجل مسبقاً. يمكنك رؤية حالة طلبك أدناه.', 'success')
            return redirect(url_for('marketers'))

        last_marketer = Marketer.query.order_by(Marketer.id.desc()).first()
        next_id = (last_marketer.id + 1) if last_marketer else 1
        code = f"POINT/{next_id:05d}"

        marketer = Marketer(
            code=code,
            full_name=full_name,
            phone=phone,
            email=email,
            baridimob=baridimob,
            state=state,
            experience=experience,
            social_link=social_link,
            motivation=motivation,
            status='pending' 
        )
        db.session.add(marketer)
        db.session.commit()

        session['marketer_email'] = email
        flash('تم استلام طلبك بنجاح! سيتم مراجعته قريباً.', 'success')
        return redirect(url_for('marketers'))

    marketer = None
    if 'marketer_email' in session:
        marketer = Marketer.query.filter_by(email=session['marketer_email']).first()

    return render_template('marketers.html', marketers_enabled=marketers_enabled, marketer=marketer)


@app.route('/marketers/reset')
def marketers_reset():
    session.pop('marketer_email', None)
    return redirect(url_for('marketers'))


# ============================================
# ===== صفحة الدعم =====
# ============================================
@app.route('/support')
def support_page():
    return render_template('support.html')


# ============================================
# ===== صفحة الأسئلة الشائعة =====
# ============================================
@app.route('/faq')
def faq_page():
    faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.order).all()
    return render_template('faq.html', faqs=faqs)


# ============================================
# ===== صفحات الخدمات (قراءة تلقائية) =====
# ============================================
@app.route('/services/billboards')
def service_billboards():
    folder_path = os.path.join(app.static_folder, 'images/services/billboards')
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if os.path.exists(folder_path) else []
    images.sort()
    return render_template('services/billboards.html', images=images)

@app.route('/services/media')
def service_media():
    folder_path = os.path.join(app.static_folder, 'images/services/media')
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if os.path.exists(folder_path) else []
    images.sort()
    return render_template('services/media.html', images=images)

@app.route('/services/packaging')
def service_packaging():
    folder_path = os.path.join(app.static_folder, 'images/services/packaging')
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if os.path.exists(folder_path) else []
    images.sort()
    return render_template('services/packaging.html', images=images)

@app.route('/services/printing')
def service_printing():
    folder_path = os.path.join(app.static_folder, 'images/services/printing')
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if os.path.exists(folder_path) else []
    images.sort()
    return render_template('services/printing.html', images=images)

@app.route('/services/design')
def service_design():
    folder_path = os.path.join(app.static_folder, 'images/services/design')
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if os.path.exists(folder_path) else []
    images.sort()
    return render_template('services/design.html', images=images)

@app.route('/services/branding')
def service_branding():
    folder_path = os.path.join(app.static_folder, 'images/services/branding')
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if os.path.exists(folder_path) else []
    images.sort()
    return render_template('services/branding.html', images=images)

@app.route('/services/decoration')
def service_decoration():
    folder_path = os.path.join(app.static_folder, 'images/services/decoration')
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if os.path.exists(folder_path) else []
    images.sort()
    return render_template('services/decoration.html', images=images)

@app.route('/services/websites')
def service_websites():
    folder_path = os.path.join(app.static_folder, 'images/services/websites')
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if os.path.exists(folder_path) else []
    images.sort()
    return render_template('services/websites.html', images=images)


# ============================================
# ===== تسجيل الدخول =====
# ============================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# ============================================
# ===== لوحة التحكم الرئيسية =====
# ============================================
@app.route('/admin')
@login_required
def admin_dashboard():
    products_count = Product.query.count()
    orders_count = Order.query.count()
    reviews_count = Review.query.count()
    coupons_count = Coupon.query.count()
    marketers_count = Marketer.query.count()
    partners_count = Partner.query.count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           products_count=products_count,
                           orders_count=orders_count,
                           reviews_count=reviews_count,
                           coupons_count=coupons_count,
                           marketers_count=marketers_count,
                           partners_count=partners_count,
                           recent_orders=recent_orders)


# ============================================
# ===== إدارة المنتجات =====
# ============================================
@app.route('/admin/products')
@login_required
def admin_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)


@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
def admin_product_add():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price', type=float)
        old_price = request.form.get('old_price', type=float)
        category = request.form.get('category', '')
        stock = request.form.get('stock', type=int, default=0)

        image_file = request.files.get('image')
        image_name = None
        if image_file and image_file.filename:
            image_name = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

        product = Product(
            name=name,
            description=description,
            price=price,
            old_price=old_price,
            category=category,
            stock=stock,
            image=image_name,
            is_active=True
        )
        db.session.add(product)
        db.session.commit()
        flash('تمت إضافة المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=None)


@app.route('/admin/product/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_product_edit(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description', '')
        product.price = request.form.get('price', type=float)
        product.old_price = request.form.get('old_price', type=float)
        product.category = request.form.get('category', '')
        product.stock = request.form.get('stock', type=int, default=0)

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_name = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
            product.image = image_name

        db.session.commit()
        flash('تم تحديث المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=product)


@app.route('/admin/product/delete/<int:id>')
@login_required
def admin_product_delete(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('تم حذف المنتج', 'success')
    return redirect(url_for('admin_products'))


# ============================================
# ===== إدارة الطلبات =====
# ============================================
@app.route('/admin/orders')
@login_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@app.route('/admin/order/<int:id>')
@login_required
def admin_order_detail(id):
    order = Order.query.get_or_404(id)
    items = OrderItem.query.filter_by(order_id=id).all()
    return render_template('admin/order_detail.html', order=order, items=items)


@app.route('/admin/order/status/<int:id>/<status>')
@login_required
def admin_order_status(id, status):
    order = Order.query.get_or_404(id)
    order.status = status
    db.session.commit()
    flash('تم تحديث حالة الطلب', 'success')
    return redirect(url_for('admin_order_detail', id=id))


# ============================================
# ===== إدارة المسوقين =====
# ============================================
@app.route('/admin/marketers')
@login_required
def admin_marketers():
    marketers = Marketer.query.order_by(Marketer.created_at.desc()).all()
    return render_template('admin/marketers.html', marketers=marketers)


@app.route('/admin/marketer/<int:id>')
@login_required
def admin_marketer_detail(id):
    marketer = Marketer.query.get_or_404(id)
    return render_template('admin/marketer_detail.html', marketer=marketer)


@app.route('/admin/marketer/<int:id>/<action>')
@login_required
def admin_marketer_action(id, action):
    marketer = Marketer.query.get_or_404(id)
    if action == 'approve':
        marketer.status = 'approved'
        flash('تم قبول المسوق', 'success')
    elif action == 'reject':
        marketer.status = 'rejected'
        flash('تم رفض المسوق', 'error')
    db.session.commit()
    return redirect(url_for('admin_marketers'))


@app.route('/admin/marketer/<int:id>/pay', methods=['POST'])
@login_required
def admin_marketer_pay(id):
    marketer = Marketer.query.get_or_404(id)
    amount = request.form.get('amount', type=float)
    note = request.form.get('note', '')

    if amount and amount > 0:
        payment = MarketerPayment(
            marketer_id=marketer.id,
            amount=amount,
            note=note
        )
        db.session.add(payment)
        marketer.total_paid += amount
        db.session.commit()
        flash(f'تم تسجيل دفعة {amount} دج', 'success')

    return redirect(url_for('admin_marketer_detail', id=id))


# ============================================
# ===== إدارة الشركاء =====
# ============================================
@app.route('/admin/partners')
@login_required
def admin_partners():
    partners = Partner.query.order_by(Partner.created_at.desc()).all()
    return render_template('admin/partners.html', partners=partners)


@app.route('/admin/partner/<int:id>')
@login_required
def admin_partner_detail(id):
    partner = Partner.query.get_or_404(id)
    return render_template('admin/partner_detail.html', partner=partner)


@app.route('/admin/partner/<int:id>/<action>')
@login_required
def admin_partner_action(id, action):
    partner = Partner.query.get_or_404(id)
    if action == 'approve':
        partner.status = 'approved'
        flash('تم قبول الشريك', 'success')
    elif action == 'reject':
        partner.status = 'rejected'
        flash('تم رفض الشريك', 'error')
    db.session.commit()
    return redirect(url_for('admin_partners'))


# ============================================
# ===== إدارة التقييمات =====
# ============================================
@app.route('/admin/reviews')
@login_required
def admin_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)


@app.route('/admin/review/<int:id>/<action>')
@login_required
def admin_review_action(id, action):
    review = Review.query.get_or_404(id)
    if action == 'approve':
        review.is_approved = True
        flash('تم قبول التقييم', 'success')
    elif action == 'delete':
        db.session.delete(review)
        flash('تم حذف التقييم', 'success')
        db.session.commit()
        return redirect(url_for('admin_reviews'))
    db.session.commit()
    return redirect(url_for('admin_reviews'))


# ============================================
# ===== إدارة الكوبونات =====
# ============================================
@app.route('/admin/coupons')
@login_required
def admin_coupons():
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons)


@app.route('/admin/coupon/add', methods=['GET', 'POST'])
@login_required
def admin_coupon_add():
    if request.method == 'POST':
        code = request.form.get('code').upper()
        discount_percent = request.form.get('discount_percent', type=float)
        product_id = request.form.get('product_id', type=int)
        coupon_type = request.form.get('coupon_type', 'quantity')

        coupon = Coupon(
            code=code,
            discount_percent=discount_percent,
            product_id=product_id if product_id else None,
            coupon_type=coupon_type,
            is_active=True
        )

        if coupon_type == 'time':
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            if start_date:
                coupon.start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                coupon.end_date = datetime.strptime(end_date, '%Y-%m-%d')

        elif coupon_type == 'quantity':
            max_uses = request.form.get('max_uses', type=int)
            coupon.max_uses = max_uses

        db.session.add(coupon)
        db.session.commit()
        flash('تم إنشاء الكوبون', 'success')
        return redirect(url_for('admin_coupons'))

    products = Product.query.filter_by(is_active=True).all()
    return render_template('admin/coupon_form.html', products=products)


@app.route('/admin/coupon/delete/<int:id>')
@login_required
def admin_coupon_delete(id):
    coupon = Coupon.query.get_or_404(id)
    db.session.delete(coupon)
    db.session.commit()
    flash('تم حذف الكوبون', 'success')
    return redirect(url_for('admin_coupons'))


# ============================================
# ===== إنشاء قاعدة البيانات =====
# ============================================
with app.app_context():
    db.create_all()
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    if not User.query.filter_by(username=admin_username).first():
        admin = User(
            username=admin_username,
            password=generate_password_hash(os.getenv('ADMIN_PASSWORD', 'admin123')),
            email=os.getenv('ADMIN_EMAIL', 'admin@pointpub.dz')
        )
        db.session.add(admin)
        db.session.commit()
        print('تم إنشاء حساب المدير')


if __name__ == '__main__':
    app.run(debug=True, threaded=True)