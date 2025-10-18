from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.properties import NumericProperty, ListProperty, StringProperty
from app_logic import get_quizzes, get_questions, save_record, get_records, base_points_for

DB_FILE = "quiz_data.db"


class ThemedScreen(Screen):
    pass


class MenuScreen(ThemedScreen):
    pass


class QuizListScreen(ThemedScreen):
    def on_pre_enter(self, *a):
        app = App.get_running_app()
        box = self.ids.quiz_box
        box.clear_widgets()
        for qid, title in get_quizzes(DB_FILE):
            b = Button(
                text=title,
                size_hint_y=None,
                height=60,
                background_color=app.button_bg,
                color=app.button_text,
                font_size='18sp'
            )
            b.bind(on_release=lambda btn, i=qid, t=title: self.start_quiz(i, t))
            box.add_widget(b)

    def start_quiz(self, quiz_id, title):
        app = App.get_running_app()
        qs = get_questions(DB_FILE, quiz_id, app.question_count)
        if not qs:
            popup = Popup(
                title="Ошибка",
                content=Label(text="Нет вопросов по этой теме!"),
                size_hint=(.6, .3)
            )
            popup.open()
            return
        q = app.root.get_screen("quiz")
        q.start_round(quiz_id, title, qs)
        app.root.current = "quiz"


class SettingsScreen(ThemedScreen):
    def on_pre_enter(self, *a):
        app = App.get_running_app()
        # Обновляем отображение текущей темы
        theme_btn = self.ids.theme_btn
        theme_btn.text = "Тёмная тема" if app.theme_name == "light" else "Светлая тема"

        # Обновляем отображение количества вопросов
        qcount_label = self.ids.qcount_label
        qcount_label.text = f"Количество вопросов: {app.question_count}"

        # Устанавливаем значение слайдера
        qcount_slider = self.ids.qcount_slider
        qcount_slider.value = app.question_count

    def toggle_theme(self):
        app = App.get_running_app()
        if app.theme_name == "light":
            app.set_theme("dark")
        else:
            app.set_theme("light")
        self.on_pre_enter()  # Обновляем интерфейс

    def change_qcount(self, value):
        app = App.get_running_app()
        app.set_qcount(int(value))
        self.ids.qcount_label.text = f"Количество вопросов: {app.question_count}"


class RecordsScreen(ThemedScreen):
    def on_pre_enter(self, *a):
        app = App.get_running_app()
        box = self.ids.records_box
        box.clear_widgets()
        records = get_records(DB_FILE)

        if not records:
            box.add_widget(Label(
                text="Рекордов пока нет!",
                size_hint_y=None,
                height=40,
                color=app.text_color
            ))
        else:
            for n, s, t in records:
                btn = Button(
                    text=f"{n}: {s} очков ({t})",
                    size_hint_y=None,
                    height=50,
                    background_color=app.button_bg,
                    color=app.button_text,
                    font_size='14sp'
                )
                box.add_widget(btn)


class QuizScreen(ThemedScreen):
    quiz_title = StringProperty("")
    qpack = ListProperty([])
    index = NumericProperty(0)
    score = NumericProperty(0)
    mult = NumericProperty(1)

    def start_round(self, quiz_id, title, qs):
        self.qpack = qs
        self.quiz_title = title
        self.index = 0
        self.score = 0
        self.mult = 1
        self.load_q()

    def load_q(self):
        if self.index >= len(self.qpack):
            self.finish()
            return

        # Получаем данные вопроса (8 значений: id, quiz_id, text, difficulty, correct_answer, wrong1, wrong2, wrong3)
        q_data = self.qpack[self.index]
        # Нам нужны только: text, difficulty, correct_answer, wrong1, wrong2, wrong3
        _, _, text, diff, corr, w1, w2, w3 = q_data

        self.ids.qtext.text = f"Вопрос {self.index + 1}/{len(self.qpack)}\n\n{text}"
        self.ids.score_label.text = f"Очки: {self.score} (x{self.mult})"

        import random
        arr = [(corr, 1), (w1, 0), (w2, 0), (w3, 0)]
        random.shuffle(arr)

        for i, (answer, is_correct) in enumerate(arr, 1):
            btn = self.ids[f"a{i}"]
            btn.text = answer
            btn.is_correct = is_correct
            # Сбрасываем цвет кнопки
            app = App.get_running_app()
            btn.background_color = app.button_bg

    def answer(self, btn):
        if self.index >= len(self.qpack):
            return

        q_data = self.qpack[self.index]
        # Получаем difficulty из данных вопроса
        _, _, _, diff, corr, _, _, _ = q_data

        app = App.get_running_app()

        if btn.is_correct:
            # Правильный ответ - зелёный
            btn.background_color = (0, 0.7, 0, 1)
            points = base_points_for(diff) * self.mult
            self.score += points
            self.mult += 1
        else:
            # Неправильный ответ - красный
            btn.background_color = (0.7, 0, 0, 1)
            self.mult = 1

        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.next_question(), 0.8)

    def next_question(self):
        self.index += 1
        self.load_q()

    def finish(self):
        app = App.get_running_app()

        # Создаем popup для ввода имени
        name_input = TextInput(
            hint_text="Введите ваше имя",
            size_hint_y=None,
            height=50,
            multiline=False
        )

        ok_btn = Button(
            text="Сохранить результат",
            size_hint_y=None,
            height=50
        )

        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text=f"Ваш результат: {self.score} очков!"))
        box.add_widget(name_input)
        box.add_widget(ok_btn)

        popup = Popup(
            title="Викторина завершена!",
            content=box,
            size_hint=(0.8, 0.5)
        )

        def save_and_close(instance):
            name = name_input.text.strip() or "Игрок"
            save_record(DB_FILE, name, self.score, self.quiz_title)
            popup.dismiss()
            # Переходим на экран результатов
            result_screen = app.root.get_screen("result")
            result_screen.ids.result_label.text = f"{name}, ваш результат: {self.score} очков!\nТема: {self.quiz_title}"
            app.root.current = "result"

        ok_btn.bind(on_release=save_and_close)
        name_input.bind(on_text_validate=save_and_close)  # Enter для сохранения
        popup.open()


class ResultScreen(ThemedScreen):
    pass