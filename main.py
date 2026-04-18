from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle


# --- Класс закругленной кнопки ---
class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)  # Сама кнопка прозрачная

        with self.canvas.before:
            Color(0.9, 0.1, 0.4, 1)  # Малиновый цвет
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[25, ]  # Радиус скругления
            )
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# --- Главный класс приложения ---
class Gui(App):
    def build(self):
        self.user_data = "Тут пока пусто"

        # Главный контейнер
        layout = BoxLayout(padding=20, orientation='vertical', spacing=15)

        # 1. Поле ввода (сверху)
        self.text_input = TextInput(
            hint_text='Введите текст здесь...',
            multiline=False,
            size_hint=(1, None),
            height=50,
            font_size=18
        )
        self.text_input.bind(on_text_validate=self.on_enter)

        # 2. Метка для вывода результата
        self.result_label = Label(
            text="Результат появится здесь",
            font_size=22,
            color=(1, 1, 1, 1)
        )

        # 3. Наша закругленная кнопка
        self.show_button = RoundedButton(
            text="ВЫВЕСТИ ТЕКСТ",
            size_hint=(0.7, None),
            height=60,
            pos_hint={'center_x': 0.5}  # Центрируем кнопку
        )
        self.show_button.bind(on_press=self.display_text)

        # Собираем интерфейс
        layout.add_widget(self.text_input)  # Ввод сверху
        layout.add_widget(self.result_label)  # Текст посередине
        layout.add_widget(self.show_button)  # Кнопка ниже текста
        layout.add_widget(Widget())  # Пустой блок в самом низу выталкивает всё вверх

        return layout

    # Логика сохранения при нажатии Enter
    def on_enter(self, instance):
        self.user_data = instance.text
        self.result_label.text = f"Сохранено: {self.user_data}"

    # Логика вывода при нажатии на кнопку
    def display_text(self, instance):
        # Забираем актуальный текст прямо из поля
        self.user_data = self.text_input.text
        if self.user_data.strip():
            self.result_label.text = f"Вы ввели: {self.user_data}"
        else:
            self.result_label.text = "Поле пустое!"


if __name__ == "__main__":
    Gui().run()
