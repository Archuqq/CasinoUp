from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.main.forms import PromoActivationForm, DepositForm
from app.models import PromoCode, Transaction, PromoUsage, User, Deposit
from datetime import datetime
from sqlalchemy import func
import os
from werkzeug.utils import secure_filename

def get_site_stats():
    total_users = User.query.count()
    total_transactions = Transaction.query.count()
    total_volume = db.session.query(func.sum(Transaction.amount)).filter(Transaction.amount > 0).scalar() or 0
    active_promos = PromoCode.query.filter_by(is_active=True).count()
    return {
        'total_users': total_users,
        'total_transactions': total_transactions,
        'total_volume': total_volume,
        'active_promos': active_promos
    }

@bp.context_processor
def inject_stats():
    return dict(site_stats=get_site_stats())

@bp.route('/')
def index():
    return render_template('main/index.html', title='Главная')

@bp.route('/activate_promo', methods=['GET', 'POST'])
@login_required
def activate_promo():
    form = PromoActivationForm()
    if form.validate_on_submit():
        promo = PromoCode.query.filter_by(code=form.code.data).first()
        
        if not promo:
            flash('Промокод не найден.', 'danger')
            return redirect(url_for('main.activate_promo'))
            
        if not promo.is_active:
            flash('Этот промокод неактивен.', 'danger')
            return redirect(url_for('main.activate_promo'))
            
        if promo.is_maxed_out:
            flash('Превышено максимальное количество использований промокода.', 'danger')
            return redirect(url_for('main.activate_promo'))
            
        if current_user in promo.used_by:
            flash('Вы уже использовали этот промокод.', 'danger')
            return redirect(url_for('main.activate_promo'))
        
        # Активируем промокод
        usage = PromoUsage(user_id=current_user.id, promo_id=promo.id)
        current_user.balance += promo.amount
        
        # Записываем транзакцию
        transaction = Transaction(
            user_id=current_user.id,
            amount=promo.amount,
            type='promo_code'
        )
        
        db.session.add(usage)
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Промокод успешно активирован! Начислено {promo.amount}₽', 'success')
        return redirect(url_for('main.index'))
        
    return render_template('main/activate_promo.html', form=form)

@bp.route('/profile')
@login_required
def profile():
    # Получаем последние 10 транзакций пользователя
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.timestamp.desc())\
        .limit(10)\
        .all()
    
    return render_template('main/profile.html', 
                         title='Профиль',
                         transactions=transactions)

@bp.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    form = DepositForm()
    if form.validate_on_submit():
        # Сохраняем скриншот
        screenshot = form.screenshot.data
        filename = secure_filename(f"{current_user.username}_{screenshot.filename}")
        
        # Создаем директорию для загрузок, если её нет
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'deposits')
        os.makedirs(upload_path, exist_ok=True)
        
        # Сохраняем файл
        screenshot_path = os.path.join(upload_path, filename)
        screenshot.save(screenshot_path)
        
        # Создаем запись о депозите
        deposit = Deposit(
            user_id=current_user.id,
            amount=form.amount.data,
            screenshot=filename,
            comment=form.comment.data,
            status='pending'
        )
        db.session.add(deposit)
        db.session.commit()
        
        flash('Ваша заявка на пополнение принята и будет рассмотрена администратором', 'success')
        return redirect(url_for('main.deposit'))
        
    return render_template('main/deposit.html', form=form)