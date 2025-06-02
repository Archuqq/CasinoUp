from flask import render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.games import bp
from app.models import Transaction, User
import random
import uuid
from datetime import datetime

@bp.route('/')
@login_required
def index():
    return render_template('games/index.html', has_valb1k_promo=current_user.has_promo_valb1k)

@bp.route('/slots', methods=['GET', 'POST'])
@login_required
def slots():
    if request.method == 'POST':
        bet = float(request.form.get('bet', 0))
        
        if bet <= 0 or bet > current_user.balance:
            return jsonify({'error': 'Неверная ставка'}), 400
        
        symbols = ['🍒', '🍊', '🍋', '7️⃣', '💎']
        result = [random.choice(symbols) for _ in range(3)]
        
        win = False
        multiplier = 0
        
        if all(s == result[0] for s in result):  
            win = True
            multiplier = 5 if result[0] in ['7️⃣', '💎'] else 3
        elif result.count(result[0]) == 2 or result.count(result[1]) == 2:  
            win = True
            multiplier = 2
            
        if win:
            win_amount = bet * multiplier
            current_user.balance += win_amount - bet
        else:
            win_amount = 0
            current_user.balance -= bet
            
        transaction = Transaction(
            user_id=current_user.id,
            amount=win_amount - bet,
            type='game_slots',
            game_id=str(uuid.uuid4())
        )
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'result': result,
            'win': win,
            'amount': win_amount,
            'new_balance': current_user.balance
        })
        
    return render_template('games/slots.html')

@bp.route('/dice', methods=['GET', 'POST'])
@login_required
def dice():
    if request.method == 'POST':
        bet = float(request.form.get('bet', 0))
        choice = request.form.get('choice')  
        number = float(request.form.get('number', 50))  
        
        if bet <= 0 or bet > current_user.balance:
            return jsonify({'error': 'Неверная ставка'}), 400
            
        if number < 1 or number > 99:
            return jsonify({'error': 'Неверное число'}), 400
            
        result = random.uniform(1, 100)
        
        win = (choice == 'over' and result > number) or (choice == 'under' and result < number)
        
        multiplier = 100 / (100 - number if choice == 'over' else number)
        
        if win:
            win_amount = bet * multiplier
            current_user.balance += win_amount - bet
        else:
            win_amount = 0
            current_user.balance -= bet
            
        transaction = Transaction(
            user_id=current_user.id,
            amount=win_amount - bet,
            type='game_dice',
            game_id=str(uuid.uuid4())
        )
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'result': result,
            'win': win,
            'amount': win_amount,
            'new_balance': current_user.balance
        })
        
    return render_template('games/dice.html')

@bp.route('/miner')
@login_required
def miner():
    return render_template('games/miner.html')

@bp.route('/miner/start', methods=['POST'])
@login_required
def miner_start():
    data = request.get_json()
    bet = data.get('bet', 0)
    
    if bet < 1:
        return jsonify({'success': False, 'message': 'Минимальная ставка 1₽'})
    
    if bet > current_user.balance:
        return jsonify({'success': False, 'message': 'Недостаточно средств'})
    
    current_user.balance -= bet
    
    transaction = Transaction(
        user_id=current_user.id,
        amount=-bet,
        type='miner_bet',
        game_id=str(uuid.uuid4())
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/miner/collect', methods=['POST'])
@login_required
def miner_collect():
    data = request.get_json()
    win = data.get('win', 0)
    
    if win < 0:
        return jsonify({'success': False, 'message': 'Некорректная сумма выигрыша'})
    
    current_user.balance += win
    
    transaction = Transaction(
        user_id=current_user.id,
        amount=win,
        type='miner_win',
        game_id=str(uuid.uuid4())
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/coinflip')
@login_required
def coinflip():
    return render_template('games/coinflip.html')

@bp.route('/coinflip/start', methods=['POST'])
@login_required
def coinflip_start():
    data = request.get_json()
    bet = float(data.get('bet', 0))
    side = data.get('side')

    if bet < 1:
        return jsonify({'success': False, 'message': 'Минимальная ставка 1₽'})

    if current_user.balance < bet:
        return jsonify({'success': False, 'message': 'Недостаточно средств'})

    current_user.balance -= bet
    db.session.commit()

    result = random.choice(['heads', 'tails'])
    won = result == side

    if won:
        win_amount = bet * 2
        current_user.balance += win_amount
        transaction = Transaction(
            user_id=current_user.id,
            amount=win_amount - bet,
            type='game_coinflip',
            game_id=str(uuid.uuid4())
        )
        db.session.add(transaction)
    else:
        transaction = Transaction(
            user_id=current_user.id,
            amount=-bet,
            type='game_coinflip',
            game_id=str(uuid.uuid4())
        )
        db.session.add(transaction)

    db.session.commit()

    return jsonify({
        'success': True,
        'result': result,
        'won': won,
        'amount': win_amount if won else 0
    })

@bp.route('/valb1k/check_promo', methods=['POST'])
@login_required
def check_valb1k_promo():
    data = request.get_json()
    code = data.get('code', '').upper()
    
    if current_user.has_promo_valb1k:
        return jsonify({'success': True})
    
    if code == 'VALB1K':
        current_user.has_promo_valb1k = True
        db.session.commit()
        return jsonify({'success': True})
        
    return jsonify({'success': False, 'message': 'Неверный промокод'})

@bp.route('/valb1k')
@login_required
def valb1k():
    if not current_user.has_promo_valb1k:
        return redirect(url_for('games.index'))
    return render_template('games/valb1k.html', has_valb1k_promo=True)

@bp.route('/valb1k/collect', methods=['POST'])
@login_required
def valb1k_collect():
    if not current_user.has_promo_valb1k:
        return jsonify({'success': False, 'message': 'Промокод не активирован'})
        
    data = request.get_json()
    amount = data.get('amount', 0)
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Некорректная сумма выигрыша'})
    
    current_user.balance += amount
    
    transaction = Transaction(
        user_id=current_user.id,
        amount=amount,
        type='game_valb1k',
        game_id=str(uuid.uuid4())
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/top')
@login_required
def top_users():
    top_users = User.query.order_by(User.balance.desc()).limit(10).all()
    return render_template('games/top.html', top_users=top_users)