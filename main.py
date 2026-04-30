import json
import os
import requests
import torch
import torch.nn as nn
import numpy as np
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.metrics import dp
from kivy.animation import Animation
from main_app import get_forecast

DB_FILE = "users.json"
SESSION_FILE = "session.json"

DB_URL = "https://air-bd-e3d6b-default-rtdb.firebaseio.com/"

recent_data = np.array([
    [12.5, 1, 8, 13.5], [11.8, 1, 8, 13.4], [12.4, 17.5, 8, 14.3],
    [12.8, 1, 8, 13.2], [13.2, 1, 8, 13.1], [11.5, 16.5, 9, 11.0],
    [13.2, 1, 9, 13.1], [14.6, 1, 8, 22.5], [21.4, 17.5, 8, 21.1],
    [51.1, 1, 7, 23.8], [24.8, 2, 6, 33.2], [21.5, 22.8, 6, 32.5],
    [23.2, 2, 5, 33.8], [11.8, 2, 5, 41.0], [11.5, 2.3, 4, 43.2],
    [12.4, 2, 5, 33.9], [62.2, 2, 6, 31.5], [51.8, 21.9, 6, 22.8],
    [13.5, 2, 7, 21.2], [123.1, 1, 7, 11.8], [11.4, 19.1, 8, 13.6],
    [12.2, 1, 4, 12.5], [13.1, 1, 8, 12.4], [21.0, 18.23, 8, 11.3]
])

def load_users():
    try:
        response = requests.get(f"{DB_URL}users.json", timeout=5)
        if response.status_code == 200:
            users = response.json()
            return users if users else {}
        return {}
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return {}


def save_user(username, password):
    users = load_users()
    if username in users:
        return False

    try:
        data = {username: password}
        response = requests.patch(f"{DB_URL}users.json", json=data, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False

class AirModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=4, hidden_size=64, num_layers=1, batch_first=True)
        self.fc = nn.Linear(64, 1)

    def forward(self, x):
        lstm_out, (hn, cn) = self.lstm(x)
        return self.fc(hn[-1])


def forecast(input_data, model_path='kemerovo_model.pth'):
    checkpoint = torch.load(model_path, weights_only=False, map_location=torch.device('cpu'))
    scaler = checkpoint['scaler']

    model = AirModel()
    model.lstm.load_state_dict(checkpoint['lstm_state'])
    model.fc.load_state_dict(checkpoint['fc_state'])
    model.eval()

    current_batch = scaler.transform(input_data)
    input_seq = torch.tensor(current_batch, dtype=torch.float32).unsqueeze(0)

    forecast_results = []

    with torch.no_grad():
        for _ in range(24):
            pred = model(input_seq)
            pred_value = pred.item()
            forecast_results.append(pred_value)

            last_features = input_seq[:, -1, :].clone()

            next_step = last_features.clone()
            next_step[0, 0] = pred_value

            input_seq = torch.cat((input_seq[:, 1:, :], next_step.unsqueeze(1)), dim=1)

    dummy = np.zeros((len(forecast_results), 4))
    dummy[:, 0] = forecast_results
    final_forecast = scaler.inverse_transform(dummy)[:, 0]

    return final_forecast

class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        with self.canvas.before:
            self.rect_color = Color(0.1, 0.5, 0.7, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class TextCard(Label):
    def __init__(self, text, **kwargs):
        super().__init__(text=text, **kwargs)
        self.size_hint_y = None
        self.height = dp(80)
        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = (self.x + dp(10), self.y + dp(5))
        self.rect.size = (self.width - dp(20), self.height - dp(10))


class ProfileScreen(Screen):
    def on_enter(self):
        self.username_label.text = f"Логин: {App.get_running_app().current_user}"

    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(20), pos_hint={'center_y': 0.5})
        self.username_label = Label(text="", font_size=dp(22), bold=True)
        logout_btn = RoundedButton(text="ВЫЙТИ ИЗ АККАУНТА", size_hint=(1, None), height=dp(55))
        logout_btn.rect_color.rgba = (0.7, 0.1, 0.1, 1)
        logout_btn.bind(on_release=lambda x: App.get_running_app().logout())
        layout.add_widget(Label(text="МОЙ ПРОФИЛЬ", font_size=dp(25), bold=True))
        layout.add_widget(self.username_label)
        layout.add_widget(logout_btn)
        self.add_widget(layout)


class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(15), pos_hint={'center_y': 0.5})
        self.login_i = TextInput(hint_text='Логин', multiline=False, size_hint_y=None, height=dp(50))
        self.pass_i = TextInput(hint_text='Пароль', password=True, multiline=False, size_hint_y=None, height=dp(50))
        self.msg = Label(text="", color=(1, 0, 0, 1), size_hint_y=None, height=dp(30))
        btn = Button(text="ВОЙТИ", size_hint_y=None, height=dp(50))
        btn.bind(on_release=self.check_auth)
        reg_btn = Button(text="Создать аккаунт", background_color=(0, 0, 0, 0), color=(0.1, 0.5, 0.7, 1))
        reg_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'reg_screen'))
        layout.add_widget(Label(text="ВХОД", font_size=dp(25), bold=True))
        layout.add_widget(self.login_i)
        layout.add_widget(self.pass_i)
        layout.add_widget(self.msg)
        layout.add_widget(btn)
        layout.add_widget(reg_btn)
        self.add_widget(layout)

    def check_auth(self, *args):
        users = load_users()
        if self.login_i.text in users and users[self.login_i.text] == self.pass_i.text:
            username = self.login_i.text
            App.get_running_app().current_user = username
            save_session(username)  # <-- Сохраняем сессию
            self.manager.current = 'main'

class RegisterScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(15), pos_hint={'center_y': 0.5})
        self.u_i = TextInput(hint_text='Логин', size_hint_y=None, height=dp(50))
        self.p_i = TextInput(hint_text='Пароль', password=True, size_hint_y=None, height=dp(50))
        btn = Button(text="ЗАРЕГИСТРИРОВАТЬСЯ", size_hint_y=None, height=dp(50))
        btn.bind(on_release=self.save_auth)
        layout.add_widget(Label(text="РЕГИСТРАЦИЯ", font_size=dp(25)))
        layout.add_widget(self.u_i)
        layout.add_widget(self.p_i)
        layout.add_widget(btn)
        self.add_widget(layout)

    def save_auth(self, *args):
        if save_user(self.u_i.text, self.p_i.text):
            self.manager.current = 'login_screen'



class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=[dp(20), dp(100), dp(20), dp(20)], spacing=dp(20))
        # self.text_input = TextInput(hint_text='Введите текст...', size_hint=(1, None), height=dp(50))
        self.res = Label(text="Результат появится здесь")
        btn = RoundedButton(text="Получить прогноз", size_hint=(0.8, None), height=dp(60), pos_hint={'center_x': 0.5})
        if recent_data.shape[0] == 24:
            try:
                forecast = get_forecast(recent_data)
                avg_pm25 = np.mean(forecast)
                btn.bind(on_press=lambda x: setattr(self.res, 'text', f"Среднесуточная концентрация PM2.5: {avg_pm25:.2f} µg/m³"))
            except Exception as e:
                print(f"Ошибка при расчете: {e}")
        else:
            print("Ошибка: Необходимо ровно 24 часа входных данных.")
        # layout.add_widget(self.text_input)
        layout.add_widget(btn)
        layout.add_widget(self.res)
        layout.add_widget(Widget())
        self.add_widget(layout)


class ScrollScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        s = ScrollView()
        l = BoxLayout(orientation='vertical', size_hint_y=None, padding=[0, dp(80), 0, dp(20)], spacing=dp(10))
        l.bind(minimum_height=l.setter('height'))
        for i in range(20):
            l.add_widget(TextCard(text=f"Карточка новости {i + 1}"))
        s.add_widget(l)
        self.add_widget(s)


class InfoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Label(text="[b]ИНФО[/b]\nВерсия 1.6", markup=True, halign='center'))

def save_session(username):
    with open(SESSION_FILE, "w") as f:
        json.dump({"current_user": username}, f)

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            try:
                return json.load(f).get("current_user", "")
            except:
                return ""
    return ""

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

class Gui(App):
    current_user = ""

    def build(self):

        self.current_user = load_session()

        self.root = FloatLayout()
        self.sm = ScreenManager()
        self.sm.add_widget(LoginScreen(name='login_screen'))
        self.sm.add_widget(RegisterScreen(name='reg_screen'))
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(ScrollScreen(name='scroll'))
        self.sm.add_widget(InfoScreen(name='info'))
        self.sm.add_widget(ProfileScreen(name='profile'))

        if self.current_user:
            self.sm.current = 'main'

        # Меню
        self.menu = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10), size_hint=(None, 1),
                              width=dp(260), x=-dp(260))
        with self.menu.canvas.before:
            Color(0.12, 0.12, 0.12, 1)
            self.m_rect = RoundedRectangle(pos=self.menu.pos, size=self.menu.size, radius=[0, dp(20), dp(20), 0])

        self.menu.bind(pos=self.update_menu_bg, size=self.update_menu_bg)

        for t, s in [("Главная", 'main'), ("Список", 'scroll'), ("Инфо", 'info'), ("Закрыть", None)]:
            btn = RoundedButton(text=t, size_hint_y=None, height=dp(50))
            btn.bind(on_release=lambda x, sc=s: self.change_screen(sc) if sc else self.toggle_menu())
            self.menu.add_widget(btn)

        self.menu_btn = Button(size_hint=(None, None), size=(dp(60), dp(60)), pos_hint={'top': 1, 'x': 0},
                               background_color=(0, 0, 0, 0))
        with self.menu_btn.canvas:
            Color(1, 1, 1, 1)
            self.l1 = RoundedRectangle(size=(dp(30), dp(3)))
            self.l2 = RoundedRectangle(size=(dp(30), dp(3)))
            self.l3 = RoundedRectangle(size=(dp(30), dp(3)))

        self.menu_btn.bind(pos=self.update_menu_icon, on_release=self.toggle_menu)

        # Кнопка профиля
        self.profile_btn = Button(size_hint=(None, None), size=(dp(60), dp(60)), pos_hint={'top': 1, 'right': 1},
                                  background_color=(0, 0, 0, 0))
        with self.profile_btn.canvas:
            Color(0.1, 0.5, 0.7, 1)
            self.p_circle = Ellipse(size=(dp(35), dp(35)))

        self.profile_btn.bind(pos=self.update_prof_icon, on_release=lambda x: setattr(self.sm, 'current', 'profile'))

        self.root.add_widget(self.sm)
        self.root.add_widget(self.menu_btn)
        self.root.add_widget(self.profile_btn)
        self.root.add_widget(self.menu)

        self.sm.bind(current=self.ui_check)
        self.ui_check()
        return self.root

    def update_menu_icon(self, inst, val):
        self.l1.pos = (inst.x + dp(15), inst.top - dp(20))
        self.l2.pos = (inst.x + dp(15), inst.top - dp(30))
        self.l3.pos = (inst.x + dp(15), inst.top - dp(40))

    def update_prof_icon(self, inst, val):
        self.p_circle.pos = (inst.x + dp(12), inst.y + dp(12))

    def update_menu_bg(self, inst, val):
        self.m_rect.pos = inst.pos
        self.m_rect.size = inst.size

    def ui_check(self, *args):
        is_auth = self.sm.current in ['login_screen', 'reg_screen']
        self.menu_btn.opacity = self.profile_btn.opacity = 0 if is_auth else 1
        self.menu_btn.disabled = self.profile_btn.disabled = is_auth

    def toggle_menu(self, *args):
        tx = 0 if self.menu.x < 0 else -self.menu.width
        Animation(x=tx, duration=0.2).start(self.menu)

    def change_screen(self, name):
        self.sm.current = name
        self.toggle_menu()

    def logout(self):
        self.current_user = ""
        clear_session()
        self.sm.current = 'login_screen'


Gui().run()