from PySide6.QtCore import QThread, Signal
import traceback

# List global untuk menjaga referensi thread yang sedang berjalan 
# agar tidak digarbage-collect oleh Python saat widget di-destroy
active_workers = []

class Worker(QThread):
    """
    Worker thread reusable untuk menjalankan task I/O-bound (seperti request Supabase)
    secara asynchronous agar tidak memblokir main thread GUI.
    """
    finished = Signal(object)  # Dipancarkan ketika fungsi berhasil dengan membawa return value
    error = Signal(str)        # Dipancarkan ketika terjadi exception dengan membawa pesan error

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
        # Simpan referensi ke global list
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
