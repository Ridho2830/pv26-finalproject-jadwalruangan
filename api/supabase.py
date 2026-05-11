import requests


class SupabaseClient:
    def __init__(self, url: str, key: str):
        # Menghapus trailing slash jika ada dan menambahkan path REST API
        self.url = url.rstrip('/') + "/rest/v1"
        self.key = key
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"  # Agar mengembalikan data setelah insert/update
        }

    def table(self, table_name: str):
        return SupabaseTable(self.url, self.headers, table_name)

class SupabaseTable:
    def __init__(self, base_url: str, headers: dict, table_name: str):
        self.url = f"{base_url}/{table_name}"
        self.headers = headers

    def select(self, query: str = "*"):
        """Mengambil data dari tabel."""
        response = requests.get(f"{self.url}?select={query}", headers=self.headers)
        return self._handle_response(response)

    def insert(self, data: dict):
        """Menambahkan data ke tabel."""
        response = requests.post(self.url, headers=self.headers, json=data)
        return self._handle_response(response)

    def update(self, data: dict, filters: str):
        """Memperbarui data di tabel. Contoh filters: 'id=eq.1'"""
        response = requests.patch(f"{self.url}?{filters}", headers=self.headers, json=data)
        return self._handle_response(response)

    def delete(self, filters: str):
        """Menghapus data dari tabel. Contoh filters: 'id=eq.1'"""
        response = requests.delete(f"{self.url}?{filters}", headers=self.headers)
        return self._handle_response(response)

    def _handle_response(self, response):
        """Menangani response dari API."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            try:
                print(f"Detail: {response.json()}")
            except:
                pass
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

# Konfigurasi
SUPABASE_URL = "https://gqeylubpnjewpqkswmqs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdxZXlsdWJwbmpld3Bxa3N3bXFzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg0NTg1MTQsImV4cCI6MjA5NDAzNDUxNH0._sP5xrp_uodpvEqUps7lvQooO4TRWFyw_9Z9Wo5maS8"

# Inisialisasi client global
supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client() -> SupabaseClient:
    """Mengembalikan client Supabase yang sudah diinisialisasi."""
    return supabase
