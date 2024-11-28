import random
import sys
from PyQt6 import uic
from PyQt6.QtCore import QTimer, QSize, QUrl, QDir, Qt
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QFont, QIcon, QPixmap, QMovie, QAction
from PyQt6.QtWidgets import QMainWindow, QApplication, QInputDialog, QPushButton, QLabel, QToolBar, QTextEdit

bomb_pic = 'bomba.png'
bomb_movie = 'bomba_v1.gif'
bomb_background = 'label_background.gif'

music_main_fon = 'music_fon_sapper.mp3'
music_game_over = 'music_bomb_exploded.mp3'
music_win = 'music_win.mp3'

cars = ['tank.png', 'casca.png', 'plain.png', 'pistolet.png', 'parashut.png']


class Cell(QPushButton):
    """ Класс для отдельной клетки поля. Каждая клетка либо хранит в себе значение бомбы или цифры"""
    def __init__(self, button_obj, game, index, open=False, value=0, mark=False):
        super().__init__()
        # клетка открыта(True) или закрыта(False)
        self.open = open
        # значение: мина или цифра
        self.value = value
        # присутствие метки "?" для отображения
        self.mark = mark
        # объект кнопки
        self.button_obj = button_obj
        self.button_obj.clicked.connect(self.on_click)
        # ссылка на сам класса Поля
        self.game = game
        # индекс именно этой кнопки в Поле
        self.indxes = index

    def on_click(self):
        # Если клетка не открыта
        if not self.open:
            # для того чтобы поставить флаг (здесь немного наоборот, метод поля get_flag меняет значение флага сразу)
            if self.game.value_flag is True and self.game.one_flag == 0:
                self.button_obj.setText('?')
                self.button_obj.setStyleSheet('color:blue')
                self.button_obj.setFont(QFont('Times font', 20))
                self.mark = True
                self.game.put_flag_btn.setText("Remove the note")
                self.game.put_flag_btn.setStyleSheet("color: #00008B; background-color: white;")
                self.game.one_flag = 1

            elif self.game.value_flag is False and self.mark:
                self.button_obj.setText('')
                self.mark = False
                self.game.put_flag_btn.setText('Put a note "?"')
                self.game.put_flag_btn.setStyleSheet("color: white; background-color: #00008B;")
                self.game.one_flag = 0

            # если нет флага
            elif not self.mark:
                self.open = True
                # если нажатая кнопка является бомбой
                if self.value == '*':
                    self.button_obj.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
                    # видео взрыва бомбы
                    self.game.show_bomba(self.button_obj.pos().x(), self.button_obj.pos().y())
                    # смена текста
                    self.game.result_label.setText('Game Over!!!')
                    self.game.result_label_2.setText('Game Over!!!')
                    self.game.result_label.setStyleSheet('color: red')
                    self.game.play_music(music_game_over)
                    # завершение игры через 4 секунды после проигрыша
                    QTimer.singleShot(5000, app.exit)

                # не бомба
                else:
                    self.button_obj.setText(str(self.value))
                    # показать значение соседей
                    self.game.show_neighbors(self.indxes)

        # Проверка на победу: если все клетки открыты и в том случае если все оставшиеся закрытые клетки - бомбы
        lst_no_open = [y for x in self.game.pole for y in x if y.open is False]
        if all([y.open for x in self.game.pole for y in x]) or all([x.value == '*' for x in lst_no_open]):
            self.game.result_label.setText("You've won!!!")
            self.game.result_label.setStyleSheet('color: #00DB00')
            self.game.result_label_2.setText("You've won!!!")
            self.game.play_music(music_win)
            # завершение игры через 4 секунды после победы
            QTimer.singleShot(5000, app.exit)


# Класс самой игры (поля)
class SapperGame(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('sapper_game.ui', self)
        self.setWindowTitle('Sapper Game')
        self.setWindowIcon(QIcon('icon.png'))

        # Диалоговое окно, для выбора размера поля
        self.N, ok_pressed = QInputDialog.getInt(self, 'Задайте размер поля', 'Введите количество строк: ',
                                                 10, 8, 12, 1)
        self.M, ok_pressed = QInputDialog.getInt(self, 'Задайте размер поля', 'Введите количество столбцов: ',
                                                 10, 8, 12, 1)

        self.pole = []  # для хранения кнопок в поле
        self.create_pole(self.N, self.M)  # создание поля

        # подсчет и установка мин
        self.count_mines = (self.N * self.M) // 5
        self.setting_mines()

        self.value_flag = False  # Значение флага (есть\нет) изначально нет
        self.one_flag = 0  # Флаг за всю игру только 1
        self.put_flag_btn.clicked.connect(self.get_flag)  # кнопка для установки и удаления флага

        self.bomba_label = QLabel(self)  # для видео взрыва бомбы
        self.create_background_video()  # задний фон(видео)

        self.rule = QTextEdit(self)  # текст правил игры
        self.rule.setGeometry(0, 26, 300, 400)
        self.rule_visible = False  # для отслеживания видимости
        self.create_rule()  # правила игры

        # музыка
        self.audio = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio)
        self.player.mediaStatusChanged.connect(self.play_music_again)
        self.play_music(music_main_fon)  # музыка фон

        # пасхалка от автора ('меня :)')
        self.i = 0
        self.pixmap = QPixmap(cars[0])
        self.lbl = QLabel(self)
        self.lbl.setGeometry(0, 0, 50, 50)
        self.lbl.setPixmap(self.pixmap)
        self.lbl.hide()
        self.setMouseTracking(True)
        self.tracking = False  # отслеживание состояний нажатых кнопок

    def create_pole(self, n, m):
        """ Метод создания поля (массива с кнопками класса Cell) и установки его посередине экрана"""
        width = 45 * m
        height = 45 * n
        center_x = 850 / 2
        center_y = 850 / 2
        start = (int(center_x - width / 2), int(center_y - height / 2))
        for x in range(n):
            row = []
            for y in range(m):
                button = QPushButton(self)
                button.setGeometry(*start, 45, 45)
                row.append(Cell(button_obj=button, game=self, index=(x, y)))
                start = (start[0] + 45, start[1])
            self.pole.append(row)
            start = (int(center_x - width / 2), start[1] + 45)

    def setting_mines(self):
        """ Метод для распределения бомб по полю и установка соответствующих цифровых значений соседним клеткам"""
        i = 0
        while i < self.count_mines:
            n = random.randint(0, self.N - 1)
            m = random.randint(0, self.M - 1)
            if self.pole[n][m].value != '*':
                self.pole[n][m].value = '*'
                self.__checking_neighbors(n, m)
                i += 1

        # подсматриваем работу
        self.look_console()

    def __checking_neighbors(self, n, m):
        """ Метод для установки цифровых значений в зависимости от рядом стоящих бомб"""
        for u in range(max(0, n - 1), min(n + 2, self.N)):
            for y in range(max(0, m - 1), min(m + 2, self.M)):
                if (u == n and y == m) or self.pole[u][y].value == '*':
                    continue
                else:
                    self.pole[u][y].value += 1

    def show_neighbors(self, now_indexes):
        """ Метод для отображения значения нажатой кнопки"""
        n, m = now_indexes
        for u in range(max(0, n - 1), min(n + 2, self.N)):
            for y in range(max(0, m - 1), min(m + 2, self.M)):
                if not self.pole[u][y].mark:
                    self.pole[u][y].open = True
                    self.pole[u][y].button_obj.setFont(QFont('Times font', 20))

                    if self.pole[u][y].value != '*':
                        self.pole[u][y].button_obj.setText(str(self.pole[u][y].value))
                        self.pole[u][y].button_obj.setStyleSheet('color:green')
                    else:
                        self.pole[u][y].button_obj.setIcon(QIcon(QPixmap(bomb_pic)))
                        self.pole[u][y].button_obj.setIconSize(QSize(30, 30))

    def look_console(self):
        """ Метод для просмотра корректной работы программы(значение всех клеток)"""
        for n in self.pole:
            for m in n:
                if m.mark:
                    print('?', end=' ')
                elif m.value == '*':
                    print('*', end=' ')
                else:
                    print(m.value, end=' ')
            print()
        print()

    def get_flag(self):
        """ Метод для изменения состояния флага"""
        self.value_flag = not self.value_flag

    def show_bomba(self, x, y):
        """ Метод для показа взрыва бомбы при проигрыше"""
        movie = QMovie(bomb_movie)
        self.bomba_label.setMovie(movie)
        self.bomba_label.setGeometry(x, y, 45, 45)
        movie.start()

    def create_background_video(self):
        """ Метод для показа видео для заднего фона"""
        background = QMovie(bomb_background)
        self.label_background.setMovie(background)
        background.start()

    def create_rule(self):
        """ Метод для показа правил игры"""
        self.rule.setEnabled(False)
        text = """
Цель игры — открыть все пустые ячейки, не наступив на мину.
Игра начинается с первого клика по любой ячейке на поле.
При клике на ячейку, она открывается.
Если в ней находится мина, вы проигрываете, и игра завершается.
Если же в самой ячейке мины нет, но есть мины в соседних ячейках,
то отображается число, соответствующее
количеству мин в соседних ячейках.Несколько соседних ячеек с числами
указывают на одни и те же мины, что позволяет точно определить расположение
опасных клеток.
Для удобства, если вы не уверены, что клетка не является миной, можно пометить её флажком "?".
Игра заканчивается победой, когда будут открыты все безопасные клетки,
и ни одна мина не будет активирована
Удачи! :)
"""
        self.rule.setText(text)
        self.rule.setStyleSheet('color: #00008B')
        self.rule.hide()

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        button_action = QAction("&Правила Игры", self)
        button_action.setCheckable(True)
        button_action.triggered.connect(self.rule_show)  # Подключаем сигнал к слоту
        toolbar.addAction(button_action)

    def rule_show(self):
        """ Метод для показа и скрывания правил игры"""
        self.rule_visible = not self.rule_visible  # Переключаем состояние
        if self.rule_visible:
            self.rule.show()
        else:
            self.rule.hide()

    def play_music(self, music):
        """ Метод для проигрывания музыки"""
        fullpath = QDir.current().absoluteFilePath(music)
        url = QUrl.fromLocalFile(fullpath)
        self.player.setSource(url)
        self.player.play()

    def play_music_again(self, status):
        """ Метод для повторного проигрывания музыки"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("Музыка закончилась, начинаю заново")
            self.player.setPosition(0)
            self.player.play()

    def keyPressEvent(self, event):
        """ Метод для нажатия клавиш (пасхалки от автора)"""
        if event.key() == Qt.Key.Key_T:
            self.tracking = not self.tracking
            if self.tracking:
                self.lbl.show()
            else:
                self.lbl.hide()

        elif event.key() == Qt.Key.Key_P:
            self.i = (self.i + 1) % 5
            self.pixmap = QPixmap(cars[self.i])
            self.lbl.setPixmap(self.pixmap)

    def mouseMoveEvent(self, event):
        """ Метод для преследования мыши картинкой (пасхалки от автора)"""
        if event.pos().x() <= 800 and event.pos().y() <= 800 and self.tracking:
            self.lbl.move(event.pos().x(), event.pos().y())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SapperGame()
    ex.show()
    sys.exit(app.exec())