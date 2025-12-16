# -*- coding: utf-8 -*-
"""
VCU Trading Bot - Mobile Android Application
Optimized for OnePlus 13R and modern Android devices
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window

import threading
import queue
import json
from datetime import datetime as DT
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend trading logic
try:
    from trading_bot_backend import TradingBot
    from telegram_notifier import TelegramNotifier
    from SmartApi import SmartConnect
    import pyotp
except ImportError as e:
    print(f"Import Error: {e}")
    TradingBot = None
    TelegramNotifier = None

# Set window size for development (will be fullscreen on Android)
if platform != 'android':
    Window.size = (400, 800)


class LoginScreen(Screen):
    """Login screen for Angel One credentials"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Title
        title = Label(
            text='[b]🚀 VCU Trading Bot[/b]',
            markup=True,
            size_hint=(1, 0.15),
            font_size='28sp',
            color=(0.2, 0.8, 1, 1)
        )
        layout.add_widget(title)

        # Subtitle
        subtitle = Label(
            text='Mobile Edition for Android',
            size_hint=(1, 0.08),
            font_size='16sp',
            color=(0.7, 0.7, 0.7, 1)
        )
        layout.add_widget(subtitle)

        # Form container
        form_layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, 0.6))

        # Client ID
        form_layout.add_widget(Label(text='Client ID:', size_hint=(1, 0.12), halign='left'))
        self.client_input = TextInput(
            hint_text='Enter Client ID',
            multiline=False,
            size_hint=(1, 0.12)
        )
        form_layout.add_widget(self.client_input)

        # API Key
        form_layout.add_widget(Label(text='API Key:', size_hint=(1, 0.12), halign='left'))
        self.api_input = TextInput(
            hint_text='Enter API Key',
            multiline=False,
            size_hint=(1, 0.12)
        )
        form_layout.add_widget(self.api_input)

        # Password
        form_layout.add_widget(Label(text='Password:', size_hint=(1, 0.12), halign='left'))
        self.pass_input = TextInput(
            hint_text='Enter Password',
            password=True,
            multiline=False,
            size_hint=(1, 0.12)
        )
        form_layout.add_widget(self.pass_input)

        # TOTP Token
        form_layout.add_widget(Label(text='TOTP Token:', size_hint=(1, 0.12), halign='left'))
        self.totp_input = TextInput(
            hint_text='Enter TOTP Secret',
            multiline=False,
            size_hint=(1, 0.12)
        )
        form_layout.add_widget(self.totp_input)

        layout.add_widget(form_layout)

        # Status label
        self.status_label = Label(
            text='',
            size_hint=(1, 0.08),
            color=(1, 1, 0, 1)
        )
        layout.add_widget(self.status_label)

        # Login button
        login_btn = Button(
            text='Login & Connect',
            size_hint=(1, 0.12),
            background_color=(0.2, 0.8, 0.4, 1),
            font_size='18sp'
        )
        login_btn.bind(on_press=self.do_login)
        layout.add_widget(login_btn)

        self.add_widget(layout)

        # Auto-load credentials if available
        self.load_credentials()

    def load_credentials(self):
        """Load saved credentials from file"""
        try:
            creds_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.txt')
            if os.path.exists(creds_file):
                creds = {}
                with open(creds_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            creds[key.strip()] = value.strip()

                self.client_input.text = creds.get('Client_id', '')
                self.api_input.text = creds.get('API_KEY', '')
                self.pass_input.text = creds.get('PASSWORD', '')
                self.totp_input.text = creds.get('TOKEN', '')
        except Exception as e:
            print(f"Error loading credentials: {e}")

    def do_login(self, instance):
        """Handle login process"""
        self.status_label.text = 'Connecting...'
        self.status_label.color = (1, 1, 0, 1)

        # Run login in background thread
        threading.Thread(target=self._login_thread, daemon=True).start()

    def _login_thread(self):
        """Background thread for login"""
        try:
            api_key = self.api_input.text.strip()
            client_id = self.client_input.text.strip()
            password = self.pass_input.text.strip()
            totp_token = self.totp_input.text.strip()

            if not all([api_key, client_id, password, totp_token]):
                Clock.schedule_once(lambda dt: self.show_error("Please fill all fields"))
                return

            # Initialize SmartConnect
            obj = SmartConnect(api_key=api_key)
            data = obj.generateSession(client_id, password, pyotp.TOTP(totp_token).now())

            if data and 'data' in data:
                # Store credentials in app
                app = App.get_running_app()
                app.api_object = obj
                app.credentials = {
                    'api_key': api_key,
                    'client_id': client_id,
                    'password': password,
                    'token': totp_token
                }

                Clock.schedule_once(lambda dt: self.login_success())
            else:
                Clock.schedule_once(lambda dt: self.show_error("Invalid credentials"))

        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)))

    def login_success(self):
        """Navigate to main screen on successful login"""
        self.status_label.text = 'Login Successful!'
        self.status_label.color = (0, 1, 0, 1)
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'main'), 0.5)

    def show_error(self, message):
        """Show error message"""
        self.status_label.text = f'Error: {message}'
        self.status_label.color = (1, 0, 0, 1)


class MainScreen(Screen):
    """Main trading screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.strategy_running = False
        self.bot_thread = None
        self.log_queue = queue.Queue()
        self.data_queue = queue.Queue()
        self.command_queue = queue.Queue()

        self.build_ui()

        # Start update loop
        Clock.schedule_interval(self.update_ui, 0.5)

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Header
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=10)

        header.add_widget(Label(
            text='[b]VCU Mobile[/b]',
            markup=True,
            size_hint=(0.4, 1),
            font_size='20sp'
        ))

        self.status_label = Label(
            text='[color=808080]IDLE[/color]',
            markup=True,
            size_hint=(0.4, 1),
            font_size='16sp'
        )
        header.add_widget(self.status_label)

        # Logout button
        logout_btn = Button(
            text='Logout',
            size_hint=(0.2, 1),
            background_color=(0.8, 0.2, 0.2, 1)
        )
        logout_btn.bind(on_press=self.logout)
        header.add_widget(logout_btn)

        layout.add_widget(header)

        # Control Panel
        control_panel = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)

        self.start_btn = Button(
            text='▶ Start Strategy',
            size_hint=(0.6, 1),
            background_color=(0.2, 0.8, 0.4, 1),
            font_size='16sp'
        )
        self.start_btn.bind(on_press=self.toggle_strategy)
        control_panel.add_widget(self.start_btn)

        self.force_exit_btn = Button(
            text='🚨 Exit All',
            size_hint=(0.4, 1),
            background_color=(0.8, 0.2, 0.2, 1)
        )
        self.force_exit_btn.bind(on_press=self.force_exit_all)
        control_panel.add_widget(self.force_exit_btn)

        layout.add_widget(control_panel)

        # Setup selector
        setup_panel = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=10)
        setup_panel.add_widget(Label(text='Setup:', size_hint=(0.3, 1)))

        setup_btns = BoxLayout(orientation='horizontal', size_hint=(0.7, 1), spacing=5)
        self.setup_both_btn = Button(text='Both', background_color=(0.3, 0.3, 0.8, 1))
        self.setup_a_btn = Button(text='A Only', background_color=(0.3, 0.8, 0.3, 1))
        self.setup_b_btn = Button(text='B Only', background_color=(0.8, 0.5, 0.2, 1))

        self.setup_both_btn.bind(on_press=lambda x: self.set_setup('Both Setup'))
        self.setup_a_btn.bind(on_press=lambda x: self.set_setup('A Setup Only'))
        self.setup_b_btn.bind(on_press=lambda x: self.set_setup('B Setup Only'))

        setup_btns.add_widget(self.setup_both_btn)
        setup_btns.add_widget(self.setup_a_btn)
        setup_btns.add_widget(self.setup_b_btn)
        setup_panel.add_widget(setup_btns)

        self.setup_mode = 'A Setup Only'  # Default
        layout.add_widget(setup_panel)

        # Position Cards
        positions_scroll = ScrollView(size_hint=(1, 0.35))
        positions_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        positions_layout.bind(minimum_height=positions_layout.setter('height'))

        # CE Position Card
        self.ce_card = self.create_position_card('CE')
        positions_layout.add_widget(self.ce_card)

        # PE Position Card
        self.pe_card = self.create_position_card('PE')
        positions_layout.add_widget(self.pe_card)

        positions_scroll.add_widget(positions_layout)
        layout.add_widget(positions_scroll)

        # Log Panel
        log_header = Label(
            text='[b]Trading Logs[/b]',
            markup=True,
            size_hint=(1, 0.05),
            font_size='16sp'
        )
        layout.add_widget(log_header)

        log_scroll = ScrollView(size_hint=(1, 0.34))
        self.log_label = Label(
            text='Ready to start trading...\n',
            markup=True,
            size_hint_y=None,
            text_size=(Window.width - 40, None),
            halign='left',
            valign='top'
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        log_scroll.add_widget(self.log_label)
        layout.add_widget(log_scroll)

        self.add_widget(layout)

    def create_position_card(self, strike_type):
        """Create position card for CE or PE"""
        card = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=180,
            padding=10,
            spacing=5
        )

        # Header
        header = Label(
            text=f'[b]{strike_type} Position[/b]',
            markup=True,
            size_hint=(1, 0.2),
            font_size='16sp'
        )
        card.add_widget(header)

        # Info grid
        info_grid = GridLayout(cols=3, size_hint=(1, 0.5), spacing=5)

        # Entry
        info_grid.add_widget(Label(text='Entry', font_size='12sp', color=(0.7, 0.7, 0.7, 1)))
        info_grid.add_widget(Label(text='Current', font_size='12sp', color=(0.7, 0.7, 0.7, 1)))
        info_grid.add_widget(Label(text='P&L', font_size='12sp', color=(0.7, 0.7, 0.7, 1)))

        entry_label = Label(text='-', font_size='14sp')
        current_label = Label(text='-', font_size='14sp', bold=True)
        pnl_label = Label(text='₹0', font_size='14sp', bold=True)

        info_grid.add_widget(entry_label)
        info_grid.add_widget(current_label)
        info_grid.add_widget(pnl_label)

        card.add_widget(info_grid)

        # Status
        status_label = Label(
            text='[color=808080]⏸ No Position[/color]',
            markup=True,
            size_hint=(1, 0.3),
            font_size='13sp'
        )
        card.add_widget(status_label)

        # Store references
        if strike_type == 'CE':
            self.ce_entry_label = entry_label
            self.ce_current_label = current_label
            self.ce_pnl_label = pnl_label
            self.ce_status_label = status_label
        else:
            self.pe_entry_label = entry_label
            self.pe_current_label = current_label
            self.pe_pnl_label = pnl_label
            self.pe_status_label = status_label

        return card

    def set_setup(self, mode):
        """Set setup mode"""
        self.setup_mode = mode
        self.add_log(f"Setup mode: {mode}")

    def toggle_strategy(self, instance):
        """Start/Stop strategy"""
        if not self.strategy_running:
            self.start_strategy()
        else:
            self.stop_strategy()

    def start_strategy(self):
        """Start trading strategy"""
        try:
            app = App.get_running_app()

            if not hasattr(app, 'api_object') or app.api_object is None:
                self.add_log("Error: Not logged in!")
                return

            self.strategy_running = True
            self.start_btn.text = '⏸ Stop Strategy'
            self.start_btn.background_color = (0.8, 0.4, 0.2, 1)
            self.status_label.text = '[color=00ff00]RUNNING[/color]'
            self.status_label.markup = True

            self.add_log("Strategy started...")

            # Initialize backend
            strike_config = {
                'mode': 'Auto',
                'min_premium': 170,
                'max_premium': 190,
                'lot_size': 2,
                'quantity': 150
            }

            # Initialize Telegram
            telegram_notifier = None
            try:
                creds_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.txt')
                if os.path.exists(creds_file):
                    creds = {}
                    with open(creds_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                creds[key.strip()] = value.strip()

                    telegram_token = creds.get('Telegram_Token')
                    telegram_chatid = creds.get('Telegram_ChatID')

                    if telegram_token and telegram_chatid:
                        telegram_notifier = TelegramNotifier(telegram_token, telegram_chatid)
                        self.add_log("Telegram enabled")
            except:
                pass

            self.bot = TradingBot(
                app.api_object,
                self.log_queue,
                self.data_queue,
                self.command_queue,
                self.setup_mode,
                strike_config,
                telegram_notifier
            )

            # Start bot thread
            self.bot_thread = threading.Thread(
                target=self.bot.run,
                args=(lambda: self.strategy_running,),
                daemon=True
            )
            self.bot_thread.start()

        except Exception as e:
            self.add_log(f"Error: {str(e)}")
            self.strategy_running = False
            self.start_btn.text = '▶ Start Strategy'
            self.start_btn.background_color = (0.2, 0.8, 0.4, 1)

    def stop_strategy(self):
        """Stop trading strategy"""
        self.strategy_running = False
        self.start_btn.text = '▶ Start Strategy'
        self.start_btn.background_color = (0.2, 0.8, 0.4, 1)
        self.status_label.text = '[color=808080]STOPPED[/color]'
        self.status_label.markup = True
        self.add_log("Strategy stopped")

    def force_exit_all(self, instance):
        """Force exit all positions"""
        if hasattr(self, 'bot') and self.bot:
            self.command_queue.put({'type': 'force_exit_all'})
            self.add_log("Force exit all requested")

    def update_ui(self, dt):
        """Update UI from queues"""
        # Process logs
        try:
            while not self.log_queue.empty():
                timestamp, message, color = self.log_queue.get_nowait()
                self.add_log(f"[{timestamp}] {message}")
        except:
            pass

        # Process data updates
        try:
            while not self.data_queue.empty():
                data = self.data_queue.get_nowait()
                if data.get('type') == 'position':
                    self.update_position(data)
        except:
            pass

    def update_position(self, data):
        """Update position card with new data"""
        strike_type = data.get('strike_type')

        if strike_type == 'CE':
            self.ce_entry_label.text = f"₹{data.get('entry', 0):.2f}"
            self.ce_current_label.text = f"₹{data.get('current', 0):.2f}"

            pnl = data.get('pnl', 0)
            color = '00ff00' if pnl >= 0 else 'ff0000'
            self.ce_pnl_label.text = f"[color={color}]₹{pnl:.2f}[/color]"
            self.ce_pnl_label.markup = True

            if data.get('trailing'):
                self.ce_status_label.text = '[color=00ffff]📈 Trailing Active[/color]'
            else:
                self.ce_status_label.text = '[color=00ff00]✅ Position Open[/color]'
            self.ce_status_label.markup = True

        elif strike_type == 'PE':
            self.pe_entry_label.text = f"₹{data.get('entry', 0):.2f}"
            self.pe_current_label.text = f"₹{data.get('current', 0):.2f}"

            pnl = data.get('pnl', 0)
            color = '00ff00' if pnl >= 0 else 'ff0000'
            self.pe_pnl_label.text = f"[color={color}]₹{pnl:.2f}[/color]"
            self.pe_pnl_label.markup = True

            if data.get('trailing'):
                self.pe_status_label.text = '[color=00ffff]📈 Trailing Active[/color]'
            else:
                self.pe_status_label.text = '[color=00ff00]✅ Position Open[/color]'
            self.pe_status_label.markup = True

    def add_log(self, message):
        """Add log message"""
        timestamp = DT.now().strftime("%H:%M:%S")
        self.log_label.text += f"[{timestamp}] {message}\n"

        # Limit log size
        lines = self.log_label.text.split('\n')
        if len(lines) > 100:
            self.log_label.text = '\n'.join(lines[-100:])

    def logout(self, instance):
        """Logout and return to login screen"""
        if self.strategy_running:
            self.stop_strategy()

        app = App.get_running_app()
        app.api_object = None
        app.credentials = None

        self.manager.current = 'login'


class VCUMobileApp(App):
    """Main application class"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_object = None
        self.credentials = None

    def build(self):
        """Build the app"""
        self.title = 'VCU Trading Bot Mobile'

        # Request permissions on Android
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])

        # Create screen manager
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))

        return sm

    def on_pause(self):
        """Handle app pause (Android)"""
        return True

    def on_resume(self):
        """Handle app resume (Android)"""
        pass


if __name__ == '__main__':
    VCUMobileApp().run()

