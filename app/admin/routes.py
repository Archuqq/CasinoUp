from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import User, PromoCode, Transaction, Deposit
from app.admin.forms import UserBalanceForm, PromoCodeForm
from datetime import datetime
from app.decorators import admin_required

@bp.route('/')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    promo_codes = PromoCode.query.all()
    return render_template('admin/panel.html', users=users, promo_codes=promo_codes)

@bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserBalanceForm()
    if form.validate_on_submit():
        old_balance = user.balance
        user.balance = form.balance.data
        
        # Записываем транзакцию
        transaction = Transaction(
            user_id=user.id,
            amount=form.balance.data - old_balance,
            type='admin_adjustment'
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Баланс пользователя {user.username} обновлен.', 'success')
        return redirect(url_for('admin.admin_panel'))
    form.balance.data = user.balance
    return render_template('admin/manage_user.html', user=user, form=form)

@bp.route('/promo/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_promo():
    form = PromoCodeForm()
    if form.validate_on_submit():
        promo = PromoCode(
            code=form.code.data,
            amount=form.amount.data,
            max_uses=form.max_uses.data,
            is_active=True,
            expires_at=None  # Явно устанавливаем None для expires_at
        )
        db.session.add(promo)
        db.session.commit()
        flash('Промокод создан успешно.', 'success')
        return redirect(url_for('admin.admin_panel'))
    return render_template('admin/create_promo.html', form=form)

@bp.route('/promo/<int:promo_id>/toggle')
@login_required
@admin_required
def toggle_promo(promo_id):
    promo = PromoCode.query.get_or_404(promo_id)
    promo.is_active = not promo.is_active
    db.session.commit()
    flash(f'Статус промокода {promo.code} изменен.', 'success')
    return redirect(url_for('admin.admin_panel'))

@bp.route('/deposits')
@admin_required
def deposits():
    deposits = Deposit.query.order_by(Deposit.created_at.desc()).all()
    return render_template('admin/deposits.html', deposits=deposits)

@bp.route('/deposits/approve/<int:deposit_id>', methods=['POST'])
@admin_required
def approve_deposit(deposit_id):
    deposit = Deposit.query.get_or_404(deposit_id)
    if deposit.status == 'pending':
        deposit.status = 'approved'
        deposit.processed_at = datetime.utcnow()
        
        # Создаем транзакцию
        transaction = Transaction(
            user_id=deposit.user_id,
            amount=deposit.amount,
            type='deposit',
            game_id=None,
            description=f'Пополнение баланса #{deposit.id}'
        )
        db.session.add(transaction)
        
        # Обновляем баланс пользователя
        deposit.user.balance += deposit.amount
        
        db.session.commit()
        flash(f'Депозит #{deposit.id} одобрен', 'success')
    return redirect(url_for('admin.deposits'))

@bp.route('/deposits/reject/<int:deposit_id>', methods=['POST'])
@admin_required
def reject_deposit(deposit_id):
    deposit = Deposit.query.get_or_404(deposit_id)
    if deposit.status == 'pending':
        deposit.status = 'rejected'
        deposit.processed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Депозит #{deposit.id} отклонен', 'warning')
    return redirect(url_for('admin.deposits')) 