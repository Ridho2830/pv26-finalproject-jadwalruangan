import json
import requests
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QTextBrowser, QLineEdit, QPushButton, QComboBox, QFrame)

class AIWorker(QThread):
    response_received = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, prompt, model_name="phyrus:latest", parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.model_name = model_name
        
    def run(self):
        try:
            # Mengambil data dari Supabase di background thread
            try:
                from api.supabase import get_supabase_client
                supabase = get_supabase_client()
                rooms_data = supabase.table('ruangan').select() or []
                
                context_lines = []
                for r in rooms_data:
                    context_lines.append(f"- {r.get('nama')}: Kapasitas {r.get('kapasitas')} kursi, Status: {r.get('status')}, Fasilitas: {r.get('fasilitas')}")
                db_context = "\n".join(context_lines)
            except Exception as e:
                db_context = f"(Gagal mengambil data: {e})"

            system_prompt = (
                "Anda adalah asisten AI yang membantu mengelola sistem Reservasi Ruangan Kampus. "
                "Jawablah dengan ringkas dan informatif dalam Bahasa Indonesia. "
                "Berikut adalah data ruangan saat ini di database kampus (gunakan informasi ini untuk menjawab pertanyaan):\n"
                f"{db_context}"
            )
            
            url = "http://localhost:11434/api/chat"
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": self.prompt}
                ],
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            reply = data.get("message", {}).get("content", "")
            if reply:
                self.response_received.emit(reply)
            else:
                self.error_occurred.emit("AI memberikan balasan kosong.")
                
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Koneksi ke Ollama gagal. Pastikan Ollama sudah berjalan di background (localhost:11434).")
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Error pada saat menghubungi AI: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Terjadi kesalahan internal: {e}")

class ChatbotDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Assistant - ReservasiKampus")
        self.setMinimumSize(450, 600)
        
        self.setStyleSheet("""
            QDialog { background-color: #f8fafc; }
            QTextBrowser { background-color: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; font-size: 13px; color: #1e293b;}
            QLineEdit { background-color: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; font-size: 13px; color: #1e293b; }
            QPushButton#btn_send { background-color: #4f46e5; color: white; font-weight: bold; border-radius: 8px; padding: 10px 16px; border:none;}
            QPushButton#btn_send:hover { background-color: #4338ca; }
            QPushButton#btn_send:disabled { background-color: #94a3b8; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("🤖 Asisten AI Lokal (phyrus:latest)", styleSheet="font-size: 16px; font-weight: bold; color: #1e293b;"))
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Chat History
        self.chat_history = QTextBrowser()
        self.chat_history.setOpenExternalLinks(True)
        layout.addWidget(self.chat_history)
        
        self.chat_history.append("<b>AI:</b> Halo! Saya asisten AI lokal Anda. Ada yang bisa saya bantu hari ini?<br>")
        
        # Input Area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ketik pesan Anda...")
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_btn = QPushButton("Kirim")
        self.send_btn.setObjectName("btn_send")
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        self.worker = None

    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
            
        self.chat_history.append(f"<b style='color:#4f46e5;'>Anda:</b> {text}<br>")
        self.input_field.clear()
        
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Berpikir...")
        
        self.worker = AIWorker(text, model_name="phyrus:latest", parent=self)
        self.worker.response_received.connect(self.on_response)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_response(self, reply):
        # Format newline untuk HTML
        reply_html = reply.replace("\n", "<br>")
        self.chat_history.append(f"<b>AI:</b> {reply_html}<br>")
        # Auto scroll to bottom
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def on_error(self, error_msg):
        self.chat_history.append(f"<b style='color:#ef4444;'>Error:</b> {error_msg}<br>")
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_worker_finished(self):
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Kirim")
        self.input_field.setFocus()
