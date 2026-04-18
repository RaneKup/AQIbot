from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle

Window.clearcolor = (0.1, 0.1, 0.1, 1)

class ButtonDesign(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)

        with self.canvas.before:
            Color(0.9, 0.1, 0.4, 1)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[25, ]
            )
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class Gui(App):
    def window(self):
        layout = BoxLayout(padding=30, orientation='vertical', spacing=15)

    def build(self):
        layout = BoxLayout(padding=200)
        self.text_input = TextInput(
            hint_text='Введите текст здесь...',
            multiline=False,
            size_hint=(1, None),
            height=50,
            font_size=18
        )
        self.text_input.bind(on_text_validate=self.on_enter)

        self.result_label = Label(
            text="Результат появится здесь",
            font_size=22,
            color=(1, 1, 1, 1)
        )

        self.show_button = ButtonDesign(
            text="ВЫВЕСТИ ТЕКСТ",
            size_hint=(0.7, None),
            height=60,
            pos_hint={'center_x': 0.5}  # Центрируем кнопку
        )
        self.show_button.bind(on_press=self.display_text)

        layout.add_widget(self.text_input)  # Ввод сверху
        layout.add_widget(self.result_label)  # Текст посередине
        layout.add_widget(self.show_button)  # Кнопка ниже текста
        layout.add_widget(Widget())

        layout.add_widget(self.text_input)

        return layout

    def on_enter(self, instance):
        self.user_data = instance.text

        print(f"Текст сохранен в переменную: {self.user_data}")
        print(self.user_data)

        instance.text = ""

Gui().run()