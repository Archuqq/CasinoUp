from flask import Blueprint, request, current_app, jsonify
from app import db
from app.models import Deposit, Transaction
from app.utils.telegram import send_deposit_status
import json
import requests

bp = Blueprint('telegram', __name__)

@bp.route('/webhook/<token>', methods=['POST'])
def webhook(token):
    """Обработка вебхуков от Telegram"""
    current_app.logger.info('Получен webhook от Telegram')
    current_app.logger.info(f'Данные запроса: {request.json}')
    
    if token != current_app.config.get('TELEGRAM_BOT_TOKEN', "7920897127:AAEwPurfsyDT5KwEyHjCtosr7XrDxNjxOr4"):
        current_app.logger.error('Неверный токен бота')
        return 'Invalid token', 403

    data = request.get_json()
    
    # Проверяем, что это callback query
    if 'callback_query' not in data:
        current_app.logger.info('Это не callback query')
        return jsonify({'ok': True})

    callback = data['callback_query']
    current_app.logger.info(f'Получен callback: {callback}')

    try:
        # Парсим данные из callback_data
        callback_data = json.loads(callback['data'])
        action = callback_data.get('action')
        deposit_id = callback_data.get('deposit_id')
        
        current_app.logger.info(f'Action: {action}, Deposit ID: {deposit_id}')

        if not action or not deposit_id:
            current_app.logger.error('Отсутствуют необходимые данные в callback')
            return jsonify({
                'method': 'answerCallbackQuery',
                'callback_query_id': callback['id'],
                'text': 'Ошибка: неверные данные'
            })

        # Получаем депозит из базы
        deposit = Deposit.query.get(deposit_id)
        if not deposit:
            current_app.logger.error(f'Депозит {deposit_id} не найден')
            return jsonify({
                'method': 'answerCallbackQuery',
                'callback_query_id': callback['id'],
                'text': 'Ошибка: депозит не найден'
            })

        bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN', "7920897127:AAEwPurfsyDT5KwEyHjCtosr7XrDxNjxOr4")
        chat_id = current_app.config.get('TELEGRAM_CHAT_ID', "1048782601")

        if action == 'approve_deposit':
            current_app.logger.info(f'Одобрение депозита {deposit_id}')
            
            # Создаем транзакцию
            transaction = Transaction(
                user_id=deposit.user_id,
                amount=deposit.amount,
                type='deposit'
            )
            
            # Обновляем баланс пользователя
            deposit.user.balance += deposit.amount
            # Отмечаем депозит как подтвержденный
            deposit.status = 'approved'
            
            db.session.add(transaction)
            db.session.commit()
            
            # Отправляем уведомление об успешном одобрении
            message = f"✅ Депозит #{deposit_id} на сумму {deposit.amount}₽ подтвержден"
            
        elif action == 'reject_deposit':
            current_app.logger.info(f'Отклонение депозита {deposit_id}')
            
            # Отмечаем депозит как отклоненный
            deposit.status = 'rejected'
            db.session.commit()
            
            # Отправляем уведомление об отклонении
            message = f"❌ Депозит #{deposit_id} на сумму {deposit.amount}₽ отклонен"
        
        # Отправляем ответ пользователю в Telegram
        requests.post(
            f'https://api.telegram.org/bot{bot_token}/answerCallbackQuery',
            json={
                'callback_query_id': callback['id'],
                'text': message
            }
        )
        
        # Обновляем сообщение, убирая кнопки
        requests.post(
            f'https://api.telegram.org/bot{bot_token}/editMessageText',
            json={
                'chat_id': chat_id,
                'message_id': callback['message']['message_id'],
                'text': f"{callback['message']['text']}\n\n{message}",
                'parse_mode': 'HTML'
            }
        )
        
        # Отправляем уведомление пользователю через систему
        send_deposit_status(deposit)
        
        current_app.logger.info('Успешно обработан callback')
        return jsonify({'ok': True})
        
    except Exception as e:
        current_app.logger.error(f'Ошибка при обработке callback: {str(e)}')
        return jsonify({
            'method': 'answerCallbackQuery',
            'callback_query_id': callback['id'],
            'text': 'Произошла ошибка при обработке запроса'
        }) 