import requests
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import TelegramUser, Section, Enrollment

TOKEN = "bot8170938193:AAEPymoeUX00La7AtjKdR-h3OpTo3m1e668"
TELEGRAM_API_URL = f"https://api.telegram.org/bot8170938193:AAEPymoeUX00La7AtjKdR-h3OpTo3m1e668"

user_registration = {}


@csrf_exempt
def webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            if 'callback_query' in data:
                chat_id = data['callback_query']['message']['chat']['id']
                callback_data = data['callback_query']['data']
                callback_query_id = data['callback_query']['id']

                if callback_data.startswith('enroll_'):
                    try:
                        section_id = int(callback_data.split('_')[1])
                        enroll_to_section(chat_id, section_id)
                    except ValueError:
                        send_message(chat_id, "Ошибка: неверные данные для записи на секцию.")
                    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
                    payload = {"callback_query_id": callback_query_id, "text": "Вы записаны на секцию!"}
                    requests.post(url, json=payload)

                elif callback_data == '/sections':
                    handle_sections(chat_id)

                elif callback_data == '/enroll':
                    handle_enroll(chat_id)

                elif callback_data == '/register':
                    handle_registration(chat_id)

                url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
                payload = {"callback_query_id": callback_query_id}
                requests.post(url, json=payload)

            elif 'message' in data:
                chat_id = data['message']['chat']['id']
                text = data['message'].get('text', '')

                if text == '/start':
                    user = get_user_by_telegram_id(chat_id)
                    if user:
                        send_message(chat_id, "Добро пожаловать обратно! Используйте команды:\n"
                                              "/sections - список секций\n"
                                              "/enroll - записаться на секцию", is_keyboard=True)
                    else:
                        send_message(chat_id, "Добро пожаловать! Используйте команды:\n"
                                              "/register - зарегистрироваться\n"
                                              "/sections - список секций\n"
                                              "/enroll - записаться на секцию", is_keyboard=True)

                elif text == '/register':
                    handle_registration(chat_id)  # Обрабатываем регистрацию при вводе команды

                elif text == '/sections':
                    handle_sections(chat_id)
                elif text == '/enroll':
                    handle_enroll(chat_id)
                else:
                    handle_registration_input(chat_id, text)  # Обрабатываем ввод для регистрации

        except Exception as e:
            print(f"Ошибка обработки вебхука: {e}")
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)


def send_message(chat_id, text, is_keyboard=False, keyboard=None):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    user = get_user_by_telegram_id(chat_id)
    if is_keyboard:
        main_menu_keyboard = [
            [{"text": "Секции", "callback_data": "/sections"}],
            [{"text": "Записаться на секцию", "callback_data": "/enroll"}]
        ]

        if not user:
            main_menu_keyboard.insert(0, [{"text": "Регистрация", "callback_data": "/register"}])

        if keyboard is None:
            keyboard = main_menu_keyboard

        payload["reply_markup"] = {
            "inline_keyboard": keyboard
        }

    requests.post(url, json=payload)


def handle_registration(chat_id):
    user = get_user_by_telegram_id(chat_id)
    if user:
        send_message(chat_id, "Вы уже зарегистрированы. Используйте команды /sections или /enroll.")
        return

    if chat_id not in user_registration:
        user_registration[chat_id] = {'step': 1}

    send_message(chat_id, "Введите ваше имя пользователя:")
    user_registration[chat_id]['step'] = 1


def handle_registration_input(chat_id, text):
    step = user_registration[chat_id]['step']

    if step == 1:
        user_registration[chat_id]['username'] = text
        user_registration[chat_id]['step'] = 2
        send_message(chat_id, "Введите ваш email:")

    elif step == 2:
        user_registration[chat_id]['email'] = text
        user_registration[chat_id]['step'] = 3
        send_message(chat_id, "Введите ваш пароль:")

    elif step == 3:
        user_registration[chat_id]['password'] = text
        # Завершаем регистрацию
        register_user(
            chat_id,
            user_registration[chat_id]['username'],
            user_registration[chat_id]['email'],
            text
        )
        # Убираем данные о пользователе из временного словаря после регистрации
        del user_registration[chat_id]


def register_user(chat_id, username, email, password):
    try:
        # Создаем пользователя
        user = User.objects.create_user(username=username, email=email, password=password)

        # Создаем связанного пользователя для телеграм
        telegram_user = TelegramUser.objects.create(
            user=user,
            telegram_id=chat_id,
            username=username,
            email=email
        )

        send_message(chat_id, "Регистрация успешна! Добро пожаловать!", is_keyboard=True)
    except Exception as e:
        send_message(chat_id, f"Ошибка регистрации: {e}", is_keyboard=True)


def get_user_by_telegram_id(chat_id):
    try:
        return TelegramUser.objects.get(telegram_id=chat_id)
    except TelegramUser.DoesNotExist:
        return None


def enroll_to_section(chat_id, section_id):
    user = get_user_by_telegram_id(chat_id)
    if not user:
        send_message(chat_id, "Вы не зарегистрированы. Пожалуйста, пройдите регистрацию.")
        return

    try:
        section = Section.objects.get(id=section_id)
        enrollment, created = Enrollment.objects.get_or_create(user=user.user)

        enrollment.section.add(section)
        if created:
            send_message(chat_id, f"Вы успешно записаны на секцию: {section.name}!")
        else:
            send_message(chat_id, f"Вы уже записаны на эту секцию: {section.name}.")
    except Section.DoesNotExist:
        send_message(chat_id, "Секция с таким ID не найдена.")


def handle_sections(chat_id):
    user = get_user_by_telegram_id(chat_id)
    if not user:
        send_message(chat_id, "Вы не зарегистрированы. Пожалуйста, пройдите регистрацию.")
        return

    sections = Section.objects.all()
    if sections:
        sections_list = "\n".join([f"{section.id}. {section.name}" for section in sections])
        send_message(chat_id, f"Доступные секции:\n{sections_list}")
    else:
        send_message(chat_id, "Нет доступных секций.")


def handle_enroll(chat_id):
    user = get_user_by_telegram_id(chat_id)
    if not user:
        send_message(chat_id, "Вы не зарегистрированы. Пожалуйста, пройдите регистрацию.")
        return

    sections = Section.objects.all()
    if sections:
        keyboard = []
        for section in sections:
            keyboard.append([{"text": section.name, "callback_data": f"enroll_{section.id}"}])

        send_message(chat_id, "Выберите секцию для записи:", is_keyboard=True, keyboard=keyboard)
    else:
        send_message(chat_id, "Нет доступных секций.")
