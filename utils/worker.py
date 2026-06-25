from PySide6.QtCore import QThread, Signal
import traceback

active_workers = []

class Worker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
        active_workers.append(self)
        self.finished.connect(self._cleanup)
        self.error.connect(self._cleanup)
        
    def _cleanup(self):
        if self in active_workers:
            active_workers.remove(self)

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            traceback.print_exc()
            self.error.emit(str(e))
