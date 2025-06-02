import requests
import os
from flask import current_app, url_for
import json

def send_deposit_notification(deposit):
    """Отправляет уведомление о новой заявке на пополнение в Telegram"""
    bot_token = "7920897127:AAEwPurfsyDT5KwEyHjCtosr7XrDxNjxOr4"
    chat_id = "1048782601"
    
    message = f"""🆕 Новая заявка на пополнение!
    
👤 Пользователь: {deposit.user.username}
💰 Сумма: {deposit.amount}₽
💭 Комментарий: {deposit.comment or 'Нет'}
🆔 ID заявки: {deposit.id}
⏰ Время: {deposit.created_at.strftime('%d.%m.%Y %H:%M')}

Модерация доступна в админ-панели."""

    # Отправляем текстовое сообщение
    response = requests.post(
        f'https://api.telegram.org/bot{bot_token}/sendMessage',
        json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
    )

    if not response.ok:
        current_app.logger.error(f'Failed to send Telegram notification: {response.text}')
        return False

    # Отправляем скриншот
    try:
        with open(os.path.join(current_app.config['UPLOAD_FOLDER'], deposit.screenshot_path), 'rb') as photo:
            files = {'photo': photo}
            photo_response = requests.post(
                f'https://api.telegram.org/bot{bot_token}/sendPhoto',
                data={'chat_id': chat_id},
                files=files
            )
            if not photo_response.ok:
                current_app.logger.error(f'Failed to send screenshot: {photo_response.text}')
    except Exception as e:
        current_app.logger.error(f'Error sending screenshot: {str(e)}')

    return True

def send_deposit_status(deposit):
    """Отправляет уведомление пользователю о статусе депозита"""
    status_emoji = "✅" if deposit.status == "approved" else "❌"
    status_text = "одобрена" if deposit.status == "approved" else "отклонена"
    
    message = (
        f"{status_emoji} Ваша заявка на пополнение {status_text}\n\n"
        f"💰 Сумма: {deposit.amount}₽\n"
        f"🕒 Время: {deposit.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    
    # В реальном приложении здесь нужно отправить сообщение пользователю
    # через веб-сокеты или другой механизм уведомлений
    return message 