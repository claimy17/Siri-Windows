#!/usr/bin/env python3
import sys
import os
import re
import math
import random
import platform
import subprocess
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, QSettings
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QFrame, QStackedWidget, QFileDialog
)
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QIcon, QKeyEvent

IS_WINDOWS = sys.platform.startswith("win")


def get_asset_path(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def launch_app(win_cmd, linux_cmds):
    if IS_WINDOWS:
        subprocess.Popen(f"start {win_cmd}", shell=True)
        return True
    for cmd in linux_cmds:
        if subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    return False


class WaveAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.phase = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(16)

    def update_wave(self):
        self.phase += 0.05
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width()
        height = self.height()

        colors = [
            QColor(0, 242, 254, 100),
            QColor(0, 119, 255, 120),
            QColor(128, 0, 255, 80)
        ]

        for i, color in enumerate(colors):
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            last_x, last_y = 0, height / 2
            for x in range(0, width, 5):
                y = (height / 2) + math.sin(x * 0.02 + self.phase + i) * 15 * math.sin(x * math.pi / width)
                if x == 0:
                    last_x, last_y = x, y
                else:
                    painter.drawLine(int(last_x), int(last_y), int(x), int(y))
                    last_x, last_y = x, y


class TeachPanel(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_widget = parent
        self.mode = "text"

        self.setStyleSheet("""
            QFrame#TeachPanel {
                background-color: #121214;
                border-top-left-radius: 25px;
                border-top-right-radius: 25px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QLabel { color: #ffffff; background-color: transparent; border: none; }
            QLabel#Subtitle { color: #8e8e93; font-size: 11px; }
            QLabel#FieldLabel { color: #8e8e93; font-size: 10px; font-weight: bold; }
            QLineEdit {
                background-color: #1c1c1e;
                border: 1px solid #2c2c2e;
                border-radius: 10px;
                color: white;
                padding: 10px;
            }
            QLineEdit:focus { border: 1px solid #00f2fe; }
            QPushButton#BtnText, QPushButton#BtnCmd {
                background-color: #1c1c1e;
                border: 1px solid #2c2c2e;
                border-radius: 12px;
                color: #8e8e93;
                font-size: 11px;
                padding: 6px 14px;
            }
            QPushButton#BtnCancel {
                background-color: #1c1c1e;
                border-radius: 12px;
                color: white;
                font-weight: bold;
                padding: 12px;
            }
            QPushButton#BtnSave {
                background: #00f2fe;
                border-radius: 12px;
                color: black;
                font-weight: bold;
                padding: 12px;
            }
        """)
        self.setObjectName("TeachPanel")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(10)

        top_bar = QHBoxLayout()
        handle = QFrame()
        handle.setFixedSize(40, 5)
        handle.setStyleSheet("background-color: #3a3a3c; border-radius: 2px;")
        top_bar.addStretch()
        top_bar.addWidget(handle)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        self.title = QLabel("Teach Siri")
        self.title.setFont(QFont("Sans Serif", 18, QFont.Weight.Bold))
        layout.addWidget(self.title)

        self.subtitle = QLabel("Add a phrase Siri will recognize forever.")
        self.subtitle.setObjectName("Subtitle")
        layout.addWidget(self.subtitle)

        lbl1 = QLabel("WHEN I SAY...")
        lbl1.setObjectName("FieldLabel")
        layout.addWidget(lbl1)
        self.input_say = QLineEdit()
        self.input_say.setPlaceholderText("e.g. tell me a joke")
        layout.addWidget(self.input_say)

        mode_layout = QHBoxLayout()
        self.btn_text = QPushButton("Reply text")
        self.btn_text.setObjectName("BtnText")
        self.btn_text.clicked.connect(self.set_mode_text)
        self.btn_cmd = QPushButton("Run command")
        self.btn_cmd.setObjectName("BtnCmd")
        self.btn_cmd.clicked.connect(self.set_mode_cmd)
        mode_layout.addWidget(self.btn_text)
        mode_layout.addWidget(self.btn_cmd)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        self.lbl2 = QLabel("SIRI REPLIES...")
        self.lbl2.setObjectName("FieldLabel")
        layout.addWidget(self.lbl2)
        self.input_reply = QLineEdit()
        self.input_reply.setPlaceholderText("Sure! Here you go.")
        layout.addWidget(self.input_reply)

        layout.addSpacing(10)

        actions_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("BtnCancel")
        self.btn_cancel.clicked.connect(self.slide_down)
        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("BtnSave")
        self.btn_save.clicked.connect(self.save_data)

        actions_layout.addWidget(self.btn_cancel, 1)
        actions_layout.addWidget(self.btn_save, 1)
        layout.addLayout(actions_layout)

        self.setLayout(layout)
        self.set_mode_text()

    def set_mode_text(self):
        self.mode = "text"
        self.btn_text.setStyleSheet("background-color: rgba(0, 242, 254, 0.15); border: 1px solid #00f2fe; color: #00f2fe;")
        self.btn_cmd.setStyleSheet("")
        self.lbl2.setText("SIRI REPLIES...")
        self.input_reply.setPlaceholderText("Sure! Here you go.")

    def set_mode_cmd(self):
        self.mode = "command"
        self.btn_cmd.setStyleSheet("background-color: rgba(0, 242, 254, 0.15); border: 1px solid #00f2fe; color: #00f2fe;")
        self.btn_text.setStyleSheet("")
        self.lbl2.setText("COMMAND TO RUN...")
        self.input_reply.setPlaceholderText("e.g. chromium, mousepad, terminal")

    def slide_up(self):
        self.input_say.clear()
        self.input_reply.clear()
        self.set_mode_text()
        self.show()
        self.raise_()

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(QPoint(0, self.parent_widget.height()))
        self.anim.setEndValue(QPoint(0, self.parent_widget.height() - self.height()))
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()

    def slide_down(self):
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(250)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(QPoint(0, self.parent_widget.height()))
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.finished.connect(self.hide)
        self.anim.start()

    def save_data(self):
        say = self.input_say.text().strip()
        reply = self.input_reply.text().strip()

        if say and reply:
            pulita = say.lower().replace('?', '').replace('!', '').replace('.', '').strip()
            file_memoria = os.path.expanduser("~/.siri_memory")
            try:
                with open(file_memoria, "a", encoding="utf-8") as f:
                    if self.mode == "command":
                        f.write(f"{pulita}=EXEC:{reply}\n")
                    else:
                        f.write(f"{pulita}={reply}\n")

                self.parent_widget.chat_area.append(
                    f"<span style='background-color: rgb(15, 35, 70); border-radius: 5px; color: rgb(255, 255, 255); font-weight: bold;'>Siri:</span> I learned the new instruction! When you say '{say}', I know what to do."
                )
            except Exception as e:
                self.parent_widget.chat_area.append(
                    f"<span style='background-color: rgb(15, 35, 70); border-radius: 5px; color: rgb(255, 59, 48);'>Memory error: {str(e)}</span>"
                )

        self.slide_down()


class SiriAssistant(QWidget):
    def __init__(self):
        super().__init__()
        self.blocco_proposte = 0
        self.file_memoria = os.path.expanduser("~/.siri_memory")
        if not os.path.exists(self.file_memoria):
            try:
                open(self.file_memoria, "w", encoding="utf-8").close()
            except OSError:
                pass

        self.proposte = [
            "Do you want to know how to make your computer faster?",
            "Do you want to check how much RAM your computer is using?",
            "Do you want to check your processor temperature?",
            "Do you want to customize Siri's appearance?",
            "Do you want to teach me a new command?",
            "Do you want to know useful Linux commands?",
            "Do you want to clean unnecessary files?",
            "Do you want to see your system information?",
            "Do you want to improve battery life?",
            "Do you want to know what Siri can do?"
        ]
        self.current_proposal_index = -1
        self.attesa_conferma_proposta = False
        self.attesa_risposta_umore = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Siri iOS 27 Style')
        self.resize(480, 720)

        icon_path = get_asset_path('icon.png')
        if not os.path.exists(icon_path):
            icon_path = get_asset_path('Click_Here_For_a_cookie.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.settings = QSettings("Siri_For_Raspberry", "Siri_Theme")

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(120, 150, 180, 0.85);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            QLabel#Title {
                color: #ffffff;
                background: transparent;
                border: none;
            }
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 242, 254, 0.15),
                    stop:0.5 rgba(255, 255, 255, 0.05),
                    stop:1 rgba(128, 0, 255, 0.15)
                );
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 20px;
                color: white;
                padding: 10px 15px;
            }
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 242, 254, 0.15),
                    stop:0.5 rgba(255, 255, 255, 0.05),
                    stop:1 rgba(128, 0, 255, 0.15)
                );
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 20px;
                color: white;
                padding: 10px 15px;
            }
            QLineEdit:focus { border: 1px solid #00f2fe; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 242, 254, 0.15),
                    stop:0.5 rgba(255, 255, 255, 0.05),
                    stop:1 rgba(128, 0, 255, 0.15)
                );
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 22px;
                color: white;
                padding: 12px 25px;
            }
            QPushButton#BtnDiamond {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 242, 254, 0.15),
                    stop:0.5 rgba(255, 255, 255, 0.05),
                    stop:1 rgba(128, 0, 255, 0.15)
                );
                border: 1px solid rgba(0, 242, 254, 0.25);
                font-size: 16px;
                padding: 12px 15px;
                border-radius: 22px;
            }
            QPushButton#BtnTeach {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 242, 254, 0.15),
                    stop:0.5 rgba(255, 255, 255, 0.05),
                    stop:1 rgba(128, 0, 255, 0.15)
                );
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 12px 20px;
                border-radius: 22px;
            }
            QPushButton[text="⚙"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 242, 254, 0.2),
                    stop:0.5 rgba(255, 255, 255, 0.05),
                    stop:1 rgba(128, 0, 255, 0.2)
                );
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 22px;
                padding: 12px 20px;
            }
            QLabel#Disclaimer {
                color: rgba(255, 255, 255, 0.5);
                background-color: transparent;
                border: none;
                border-radius: 12px;
            }
        """)

        main_layout = QVBoxLayout()
        self.pages = QStackedWidget()

        self.chat_page = QWidget()
        self.chat_page.setObjectName("ChatPage")
        self.chat_page_layout = QVBoxLayout(self.chat_page)

        self.settings_page = QWidget()
        self.settings_page_layout = QVBoxLayout(self.settings_page)

        self.pages.addWidget(self.chat_page)
        self.pages.addWidget(self.settings_page)
        main_layout.addWidget(self.pages)
        main_layout.setContentsMargins(25, 25, 25, 25)

        self.title_label = QLabel("Siri", self)
        self.title_label.setObjectName("Title")
        self.title_label.setFont(QFont("Sans Serif", 28, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.settings_btn = QPushButton("⚙", self)
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.title_label)
        top_layout.addWidget(self.settings_btn)
        self.chat_page_layout.addLayout(top_layout)

        self.chat_area = QTextEdit(self)
        self.chat_area.setFont(QFont("Sans Serif", 13))
        self.chat_area.setReadOnly(True)
        self.chat_area.append("<span style='background-color: rgb(35, 45, 65); color: rgb(255, 255, 255); border-radius: 5px; font-weight: bold;'>Siri: Hi, I am ready. Ask me something!</span>")
        self.chat_page_layout.addWidget(self.chat_area)

        self.clear_chat_btn = QPushButton("🗑", self)
        self.clear_chat_btn.setFixedSize(35, 35)
        self.clear_chat_btn.clicked.connect(self.clear_chat)
        self.clear_chat_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 242, 254, 0.2),
                    stop:0.5 rgba(255, 255, 255, 0.05),
                    stop:1 rgba(128, 0, 255, 0.2)
                );
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 17px;
                padding: 0px;
                font-size: 16px;
            }
        """)

        self.wave_anim = WaveAnimation(self)
        self.chat_page_layout.addWidget(self.wave_anim)

        sfondo = self.settings.value("chat_background", "")
        if sfondo and os.path.exists(sfondo):
            self.chat_area.viewport().setStyleSheet(f"""
                background-image: url("{sfondo}");
                background-repeat: no-repeat;
                background-position: center;
            """)

        input_layout = QHBoxLayout()

        self.diamond_btn = QPushButton("⚡", self)
        self.diamond_btn.setObjectName("BtnDiamond")
        self.diamond_btn.clicked.connect(self.trigger_proposal)
        input_layout.addWidget(self.diamond_btn)

        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Write a command...")
        self.input_field.setFont(QFont("Sans Serif", 12))
        self.input_field.returnPressed.connect(self.process_command)
        input_layout.addWidget(self.input_field)

        self.send_btn = QPushButton("Send", self)
        self.send_btn.setFont(QFont("Sans Serif", 11))
        self.send_btn.clicked.connect(self.process_command)
        input_layout.addWidget(self.send_btn)

        self.teach_btn = QPushButton("Teach", self)
        self.teach_btn.setObjectName("BtnTeach")
        self.teach_btn.setFont(QFont("Sans Serif", 11))
        self.teach_btn.clicked.connect(self.open_teach_panel)
        input_layout.addWidget(self.teach_btn)

        self.chat_page_layout.addLayout(input_layout)

        self.disclaimer = QLabel("Siri is a local assistant and could make mistakes", self)
        self.disclaimer.setObjectName("Disclaimer")
        self.disclaimer.setFont(QFont("Sans Serif", 9))
        self.disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.disclaimer.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border: none; border-radius: 12px; color: rgba(255, 255, 255, 0.5); padding: 4px;")
        self.chat_page_layout.addWidget(self.disclaimer)

        self.setLayout(main_layout)

        # --- PAGINA IMPOSTAZIONI ---
        settings_top_layout = QHBoxLayout()
        self.back_btn = QPushButton("← Back", self)
        settings_top_layout.addWidget(self.back_btn)
        settings_top_layout.addStretch()
        self.settings_page_layout.addLayout(settings_top_layout)

        settings_title = QLabel("Theme Settings", self)
        settings_title.setStyleSheet("background-color: transparent; border: none; color: rgb(255, 255, 255); font-weight: bold; font-size: 32px;")
        self.settings_page_layout.addWidget(settings_title)

        tema_salvato = self.settings.value("tema_attivo", "Liquid")
        self.applica_tema_visivo(tema_salvato)

        self.dark_theme_btn = QPushButton("🌑 Dark Theme", self)
        self.light_theme_btn = QPushButton("☀️ Light Theme", self)
        self.glass_theme_btn = QPushButton("✨ Liquid Glass", self)

        self.settings_page_layout.addWidget(self.dark_theme_btn)
        self.settings_page_layout.addWidget(self.light_theme_btn)
        self.settings_page_layout.addWidget(self.glass_theme_btn)

        self.dark_theme_btn.clicked.connect(lambda: self.applica_tema_visivo("Dark"))
        self.light_theme_btn.clicked.connect(lambda: self.applica_tema_visivo("Light"))
        self.glass_theme_btn.clicked.connect(lambda: self.applica_tema_visivo("Liquid"))

        self.settings_page_layout.addStretch()

        self.reset_theme_label = QLabel("<u>RESET default chat theme</u>", self)
        self.reset_theme_label.setStyleSheet("""
            color: #00f2fe;
            background: transparent;
            font-size: 12px;
            border-radius: 12px;
            padding-left: 100px;
        """)
        self.reset_theme_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_page_layout.addWidget(self.reset_theme_label)
        self.reset_theme_label.mousePressEvent = self.reset_chat_theme

        self.background_btn = QPushButton("Change chat background", self)
        self.settings_page_layout.addWidget(self.background_btn)
        self.background_btn.clicked.connect(self.change_background)

        self.settings_page_layout.addStretch()

        self.settings_btn.clicked.connect(self.open_settings)
        self.back_btn.clicked.connect(self.open_chat)

        self.teach_panel = TeachPanel(self)
        self.teach_panel.setFixedSize(480, 350)
        self.teach_panel.hide()

    def reply(self, html_text):
        self.chat_area.append(
            f"<span style='background-color: rgb(35, 45, 65); color: rgb(255, 255, 255); border-radius: 5px; font-weight: bold;'>{html_text}</span>"
        )

    def applica_tema_visivo(self, tema):
        if tema == "Dark":
            self.chat_page.setStyleSheet("background-color: rgba(20, 35, 60, 0.80); border-radius: 22px;")
            self.settings_page.setStyleSheet("background-color: rgba(20, 35, 60, 0.80); border-radius: 22px;")
            self.settings.setValue("tema_attivo", "Dark")
        elif tema == "Light":
            self.chat_page.setStyleSheet("background-color: rgba(100, 130, 160, 0.5); border-radius: 22px;")
            self.settings_page.setStyleSheet("background-color: rgba(100, 130, 160, 0.5); border-radius: 22px;")
            self.settings.setValue("tema_attivo", "Light")
        else:
            self.chat_page.setStyleSheet("")
            self.settings_page.setStyleSheet("")
            self.settings.setValue("tema_attivo", "Liquid")

    def open_teach_panel(self):
        self.teach_panel.slide_up()

    def trigger_proposal(self):
        if self.blocco_proposte == 1:
            self.reply("Siri: You said no before so I will not give you hints after now. (*^*)")
            return

        self.current_proposal_index = random.randint(0, len(self.proposte) - 1)
        prop = self.proposte[self.current_proposal_index]
        self.chat_area.append(
            f"<hr><span style='color: #00f2fe; font-weight: bold;'>Siri: {prop}</span><br><span style='color: #8e8e93;'>Type 'yes' or 'no' to respond.</span>"
        )
        self.attesa_conferma_proposta = True

    def get_ram_info(self):
        if IS_WINDOWS:
            return subprocess.getoutput("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value")
        return subprocess.getoutput("free -h")

    def get_cpu_temp(self):
        if not IS_WINDOWS:
            if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
                try:
                    with open("/sys/class/thermal/thermal_zone0/temp", "r", encoding="utf-8") as f:
                        temp_c = int(f.read().strip()) / 1000.0
                        return f"CPU Temperature: {temp_c:.1f} °C"
                except OSError:
                    pass
            return subprocess.getoutput("vcgencmd measure_temp")
        return "On Windows you can check CPU temperature with hardware monitor tools."

    def process_command(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self.chat_area.append(
            f"<hr><span style='background-color: rgb(0, 122, 255); color: rgb(255, 255, 255); font-weight: bold; border-radius: 5px; padding: 5px;'>You: {text}</span>"
        )
        self.input_field.clear()
        QApplication.processEvents()

        pulita = text.lower().replace('?', '').replace('!', '').replace('.', '').strip()

        # Risposta alla domanda "How are you?"
        if self.attesa_risposta_umore:
            self.attesa_risposta_umore = False
            if pulita in ["yes", "yap", "yeah", "im fine", "i'm fine", "all good", "good", "fine"]:
                self.reply("Siri: I am happy that you're doing well!")
            elif pulita in ["bad", "not good", "no", "very bad", "not good at all"]:
                self.reply("Siri: I am sorry to hear that. Can I help you with something?")
            else:
                self.reply("Siri: Got it!")
            return

        # Gestione risposte alle proposte flash (yes/no)
        if self.attesa_conferma_proposta:
            self.attesa_conferma_proposta = False
            if pulita in ["yes", "yeah", "yap", "yep"]:
                idx = self.current_proposal_index
                if idx == 0:
                    self.reply("Siri: To make your device faster, close unused programs, clean temporary files and disable heavy background apps.")
                elif idx == 1:
                    self.reply(f"Siri: Here is your RAM usage:<br><pre>{self.get_ram_info()}</pre>")
                elif idx == 2:
                    self.reply(f"Siri: {self.get_cpu_temp()}")
                elif idx == 3:
                    self.reply("Siri: Open Settings (⚙) at the top right to switch between Dark, Light, and Liquid Glass themes or set a custom background.")
                elif idx == 4:
                    self.reply("Siri: Press the Teach button to teach me new answers or custom system commands.")
                elif idx == 5:
                    self.reply("Siri: Useful Linux commands: ls, cd, mkdir, top, htop, free -h, df -h, sudo apt update.")
                elif idx == 6:
                    self.reply("Siri: On Raspberry Pi OS you can run 'sudo apt autoremove && sudo apt clean' to free up space.")
                elif idx == 7:
                    self.reply(f"Siri: System Info:<br>OS: {platform.system()} {platform.release()}<br>Architecture: {platform.machine()}")
                elif idx == 8:
                    self.reply("Siri: Reduce screen brightness, turn off unused Wi-Fi/Bluetooth and close idle apps to save power.")
                elif idx == 9:
                    self.reply("Siri: I can answer questions, check RAM/CPU temp, open apps, calculate math, and learn new phrases!")
                return
            else:
                self.reply("Siri: No more suggestions for this session. (*^*)")
                self.blocco_proposte = 1
                return

        # Controllo memoria locale (.siri_memory)
        if os.path.exists(self.file_memoria):
            with open(self.file_memoria, "r", encoding="utf-8") as f:
                for linea in f:
                    if "=" in linea:
                        chiave, risposta = linea.strip().split("=", 1)
                        if chiave == pulita:
                            if risposta.startswith("EXEC:"):
                                cmd = risposta.replace("EXEC:", "", 1).strip()
                                self.reply("Siri: Ok, running it now!")
                                if IS_WINDOWS:
                                    subprocess.Popen(f"start {cmd}", shell=True)
                                else:
                                    subprocess.Popen(cmd, shell=True)
                            else:
                                self.reply(f"Siri: {risposta}")
                            return

        # Calcolatrice integrata
        if re.match(r'^[0-9\s+\-*/().]+$', pulita) or any(k in pulita for k in ["calculate", "what is", "how much is"]):
            expr = pulita.replace("calculate", "").replace("what is", "").replace("how much is", "").strip()
            expr_pulita = re.sub(r'[^0-9+\-*/().]', '', expr)
            if expr_pulita and any(c.isdigit() for c in expr_pulita):
                try:
                    risultato = eval(expr_pulita, {"__builtins__": None}, {})
                    self.reply(f"Siri: The result is {risultato}")
                    return
                except Exception:
                    pass

        # Comandi standard
        if pulita in ["good afternoon", "good morning", "good evening", "hey", "hey siri", "hi", "hello"]:
            self.reply("Siri: Hi, how can I help you?")
        elif pulita in ["how is it going", "how it's going", "how's it going", "how are you"]:
            self.reply("Siri: All fine! How are you doing? (yes/no)")
            self.attesa_risposta_umore = True
        elif "who are you" in pulita:
            self.reply("Siri: I am an offline assistant created by claimy17.")
        elif "time" in pulita:
            self.reply(f"Siri: It's currently {datetime.now().strftime('%H:%M')}")
        elif "day" in pulita or "today" in pulita or "date" in pulita:
            self.reply(f"Siri: Today is {datetime.now().strftime('%A, %d %B %Y')}")
        elif "operative system" in pulita or "operating system" in pulita or "kernel" in pulita or "system info" in pulita:
            self.reply(f"--- 🖥️ SYSTEM DETAILS ---<br>• OS: {platform.system()} ({platform.release()})<br>• Architecture: {platform.machine()}")
        elif "temperature" in pulita or "temp" in pulita:
            self.reply(f"Siri: {self.get_cpu_temp()}")
        elif "ram" in pulita or "check my memory" in pulita:
            self.reply(f"Siri: Memory status:<br><pre>{self.get_ram_info()}</pre>")
        elif "open notepad" in pulita or "text editor" in pulita:
            launch_app("notepad", ["mousepad", "geany", "nano"])
            self.reply("Siri: Opened Text Editor.")
        elif "open calculator" in pulita or "calc" in pulita:
            launch_app("calc", ["galculator", "gnome-calculator", "xcalc"])
            self.reply("Siri: Opened Calculator.")
        elif "open chrome" in pulita or "google" in pulita or "browser" in pulita:
            launch_app("chrome", ["chromium-browser", "chromium", "firefox"])
            self.reply("Siri: Opened Web Browser.")
        elif "open music" in pulita or "spotify" in pulita:
            launch_app("spotify", ["spotify", "rhythmbox", "vlc"])
            self.reply("Siri: Opened Music Player.")
        elif "open file manager" in pulita or "explorer" in pulita or "files" in pulita:
            launch_app("explorer", ["pcmanfm", "thunar", "nautilus"])
            self.reply("Siri: Opened File Manager.")
        elif "delete memory" in pulita or "clear memory" in pulita or "resetsiri" in pulita:
            if os.path.exists(self.file_memoria):
                try:
                    os.remove(self.file_memoria)
                    open(self.file_memoria, "w", encoding="utf-8").close()
                    self.reply("Siri: Memory cleared! Now I am like new. (^_^)v")
                except Exception as e:
                    self.reply(f"Siri: Error: {str(e)}")
        elif "what can you do" in pulita:
            self.reply("- Open applications<br>- Check RAM & CPU temperature<br>- Calculate math expressions<br>- Learn new commands (Teach)<br>- Customize themes & background")
        else:
            self.reply("Siri: I don't know this yet, but you can press <b>Teach</b> and tell me what I should answer next time!")

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_L:
            self.clear_chat()
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        if hasattr(self, 'teach_panel'):
            self.teach_panel.setGeometry(0, self.height() - self.teach_panel.height(), self.width(), self.teach_panel.height())
        super().resizeEvent(event)
        if hasattr(self, 'clear_chat_btn'):
            self.clear_chat_btn.move(self.width() - 80, self.height() - 230)
            self.clear_chat_btn.raise_()

    def clear_chat(self):
        self.chat_area.clear()

    def open_settings(self):
        self.pages.setCurrentIndex(1)
        self.clear_chat_btn.hide()

    def open_chat(self):
        self.pages.setCurrentIndex(0)
        self.clear_chat_btn.show()

    def change_background(self):
        file, _ = QFileDialog.getOpenFileName(self, "Choose background", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if file:
            file_path = file.replace("\\", "/")
            self.chat_area.viewport().setStyleSheet(
                f"background-image: url('{file_path}'); background-repeat: no-repeat; background-position: center;"
            )
            self.settings.setValue("chat_background", file_path)

    def reset_chat_theme(self, event):
        self.chat_area.viewport().setStyleSheet("")
        self.settings.remove("chat_background")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SiriAssistant()
    ex.show()
    sys.exit(app.exec())
