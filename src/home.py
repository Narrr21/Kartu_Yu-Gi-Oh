import os
from typing import Optional
from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QLineEdit, QPushButton, QTextBrowser, QProgressBar, QStatusBar, QAction)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import logging

import config
from db import CardDatabase
from scraper import ScraperThread, scrape_pack_urls
from search import SearchThread 
from toast import ToastOverlay

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.db: Optional[CardDatabase] = None
        self.setup_ui()
        self.setup_connections()
        self.setup_menu()
        self.toast_overlay = ToastOverlay(self)
        self.search_thread = None
        QTimer.singleShot(1000, self.scrape_initial_data)

    def setup_ui(self):
        self.setWindowTitle("Yu-Gi-Oh! Database")
        self.setGeometry(100, 100, 1000, 700)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        title_label = QLabel("Yu-Gi-Oh! TCG Card Database")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #8b4513; margin: 10px; padding: 10px;")
        main_layout.addWidget(title_label)
        search_layout = QHBoxLayout()
        self.search_line_edit = QLineEdit()
        self.search_line_edit.setPlaceholderText("Enter card name, effect, type, or attribute...")
        self.search_line_edit.setStyleSheet("padding: 8px; font-size: 12px; border: 2px solid #d4af37; border-radius: 5px;")
        self.search_button = QPushButton("Search")
        self.search_button.setStyleSheet("padding: 8px 15px; font-size: 12px; background: #d4af37; border: none; border-radius: 5px; color: white; font-weight: bold;")
        self.multi_search_button = QPushButton("Multi Search")
        self.multi_search_button.setStyleSheet("padding: 8px 15px; font-size: 12px; background: #4682b4; border: none; border-radius: 5px; color: white; font-weight: bold;")
        search_layout.addWidget(self.search_line_edit)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.multi_search_button)
        main_layout.addLayout(search_layout)
        self.result_text_browser = QTextBrowser()
        self.result_text_browser.setStyleSheet("border: 2px solid #d4af37; border-radius: 5px; padding: 10px;")
        main_layout.addWidget(self.result_text_browser)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { border: 2px solid #d4af37; border-radius: 5px; } QProgressBar::chunk { background-color: #d4af37; }")
        main_layout.addWidget(self.progress_bar)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Starting up... Please wait while we initialize the database.")
        
    def setup_connections(self):
        self.search_button.clicked.connect(self.search_card)
        self.multi_search_button.clicked.connect(self.multi_search_card)
        self.search_line_edit.returnPressed.connect(self.search_card)

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        refresh_action = QAction('Refresh Database', self)
        refresh_action.triggered.connect(self.refresh_database)
        file_menu.addAction(refresh_action)
        clear_cache_action = QAction('Clear Cache', self)
        clear_cache_action.triggered.connect(self.clear_cache)
        file_menu.addAction(clear_cache_action)
        file_menu.addSeparator()
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def scrape_initial_data(self):
        self.search_button.setEnabled(False)
        self.multi_search_button.setEnabled(False)
        self.search_line_edit.setEnabled(False)
        self.progress_bar.setValue(0)
        
        try:
            if not os.path.exists(config.PACK_URLS_FILE):
                self.status_bar.showMessage("Scraping pack URLs for the first time...")
                scrape_pack_urls(config.MAIN_SEARCH_PAGE_URL, config.PACK_URLS_FILE)

            self.scraper_thread = ScraperThread()
            self.scraper_thread.progress.connect(self.update_progress)
            self.scraper_thread.status_update.connect(self.update_status)
            self.scraper_thread.finished.connect(self.on_scraping_finished)
            self.scraper_thread.error_occurred.connect(self.on_scraping_error)
            self.scraper_thread.start()
        except Exception as e:
            self.show_toast("Initialization Error", f"Could not initialize the scraper: {e}", "error")
            
    def update_progress(self, value: int):
        self.progress_bar.setValue(value)

    def update_status(self, message: str):
        self.status_bar.showMessage(message)

    def on_scraping_finished(self, db_instance: Optional[CardDatabase], elapsed_time: float):
        self.db = db_instance
        if self.db and self.db.cards:
            self.search_button.setEnabled(True)
            self.multi_search_button.setEnabled(True)
            self.search_line_edit.setEnabled(True)
            self.status_bar.showMessage(f"Database ready! {len(self.db.cards)} cards loaded. Happy searching!")
            self.result_text_browser.setHtml(f"""
                <div style="text-align: center; padding: 20px;">
                    <h2 style="color: #d4af37;">Welcome Duelist !!!</h2>
                    <p style="font-size: 16px;">
                        Database successfully loaded with <strong>{len(self.db.cards)} cards</strong>!<br>
                        Start typing in the search box above to find your favorite cards.
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        <em>Tip: You can search by card name, effect text, type, or attribute!</em>
                    </p>
                </div>
            """)
            logger.info(f"Scraping and database initialization took {elapsed_time:.2f} seconds.")
        else:
            self.show_toas("Scraping Failed", "Could not scrape any cards. Please check your internet connection.", "error")

    def on_scraping_error(self, error_message: str):
        self.show_toas("Scraping Error", f"An error occurred during scraping: {error_message}", "error")

    def search_card(self):
        query = self.search_line_edit.text().strip()
        if not query or not self.db:
            return

        self._start_search(query, multi_match=False)

    def multi_search_card(self):
        query = self.search_line_edit.text().strip()
        if not query or not self.db:
            return
        
        self._start_search(query, multi_match=True)

    def _start_search(self, query: str, multi_match: bool):
        self.search_button.setEnabled(False)
        self.multi_search_button.setEnabled(False)
        self.search_line_edit.setEnabled(False)
        self.status_bar.showMessage(f"Searching for '{query}'...")
        self.search_thread = SearchThread(self.db, query, multi_match)
        self.search_thread.search_finished.connect(self.on_search_finished)
        self.search_thread.start()

    def on_search_finished(self, results, elapsed_time: float):
        query = self.search_line_edit.text().strip()
        self.search_button.setEnabled(True)
        self.multi_search_button.setEnabled(True)
        self.search_line_edit.setEnabled(True)

        if isinstance(results, list):
            self._display_multi_results(results, query)
        else:
            self._display_single_result(results, query)
        logger.info(f"Search for '{query}' took {elapsed_time:.4f} seconds.")

    def _display_single_result(self, match, query):
        if match:
            matched_card, score, query_str = match
            html_content = f"""
                <div style="text-align: center; margin-bottom: 15px;">...</div>
                {matched_card.to_html(query_str)}
            """
            self.result_text_browser.setHtml(html_content)
            self.status_bar.showMessage(f"Found: {matched_card.name} ({score}% match)")
        else:
            self.status_bar.showMessage(f"No matches found for '{query}'")

    def _display_multi_results(self, matches, query):
        if matches:
            html_content = f"""
                <div style="text-align: center; margin-bottom: 15px;">
                    <h3 style="color: #d4af37;">Multiple Matches Found!</h3>
                    <p style="color: #666;">Showing top {len(matches)} results for: <em>"{query}"</em></p>
                </div>
            """
            for i, (card, _, query_str) in enumerate(matches, 1):
                html_content += f"""
                    <div style="margin-bottom: 10px;">...</div>
                    {card.to_html(query_str)}
                """
            self.result_text_browser.setHtml(html_content)
            self.status_bar.showMessage(f"Found {len(matches)} matches for '{query}'")
        else:
            self.status_bar.showMessage(f"No matches found for '{query}'")
            
    def refresh_database(self):
        reply = QMessageBox.question(self, 'Refresh Database', 
                                     'This will clear the cache and re-scrape all data. Continue?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.clear_cache()
            self.scrape_initial_data()

    def clear_cache(self):
        try:
            if os.path.exists(config.CACHE_FILE):
                os.remove(config.CACHE_FILE)
            self.status_bar.showMessage("Cache cleared successfully")
        except Exception as e:
            self.show_toas("Cache Error", f"Could not clear cache: {e}", "error")

    def show_about(self):
        QMessageBox.about(self, "About", 
                          "Yu-Gi-Oh! Card DataBase\n\n"
                          "A powerful tool for searching Yu-Gi-Oh! cards with fuzzy matching.\n\n"
                          "Features:\n"
                          "• Fuzzy search\n"
                          "• Caching for faster loading\n"
                          "Developed by: Nadhif Al Rozin\n")

    def show_toast(self, title: str, message: str, toast_type: str = 'info'):
        full_message = f"<b>{title}</b><br>{message}"
        self.toast_overlay.add_toast(full_message, duration=4000, toast_type=toast_type)
        self.status_bar.showMessage(f"Error: {title}")

    def closeEvent(self, event):
        if hasattr(self, 'scraper_thread') and self.scraper_thread.isRunning():
            reply = QMessageBox.question(self, 'Exit', 
                                         'Scraping is in progress. Exit anyway?',
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.scraper_thread.terminate()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()