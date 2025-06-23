from PyQt5.QtCore import QThread, pyqtSignal
from db import CardDatabase

class SearchThread(QThread):
    search_finished = pyqtSignal(object)

    def __init__(self, db: CardDatabase, query: str, multi_match: bool = False):
        super().__init__()
        self.db = db
        self.query = query
        self.multi_match = multi_match

    def run(self):
        # self.msleep(3000) # Just for demonstration purposes, simulating a delay
        if self.multi_match:
            results = self.db.find_multiple_matches(self.query)
        else:
            results = self.db.find_best_match(self.query)
        
        self.search_finished.emit(results)