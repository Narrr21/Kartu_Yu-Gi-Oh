from PyQt5.QtCore import QThread, pyqtSignal
from db import CardDatabase
import time

class SearchThread(QThread):
    search_finished = pyqtSignal(object, float)

    def __init__(self, db: CardDatabase, query: str, multi_match: bool = False):
        super().__init__()
        self.db = db
        self.query = query
        self.multi_match = multi_match

    def run(self):
        start_time = time.time()
        try:
            if self.multi_match:
                results = self.db.find_multiple_matches(self.query)
            else:
                results = self.db.find_best_match(self.query)
            elapsed_time = time.time() - start_time
            self.search_finished.emit(results, elapsed_time)
        except Exception as e:
            print(f"Error during search: {e}")
            self.search_finished.emit(None, 0.0)