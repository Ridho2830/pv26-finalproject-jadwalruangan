import requests


class SupabaseClient:
    def __init__(self, url: str, key: str):
        self.raw_url = url.rstrip('/')
        self.url = self.raw_url + "/rest/v1"
        self.key = key
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.storage = SupabaseStorage(self.raw_url, {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}"
        })

    def table(self, table_name: str):
        return SupabaseTable(self.url, self.headers, table_name)


class SupabaseTable:
    def __init__(self, base_url: str, headers: dict, table_name: str):
        self.url = f"{base_url}/{table_name}"
        self.headers = headers

    def select(self, query: str = "*", filters: str = ""):
        try:
            url = f"{self.url}?select={query}"
            if filters:
                url += f"&{filters}"
            response = requests.get(url, headers=self.headers)
            return self._handle_response(response)
        except Exception as e:
            print(f"Database select error: {e}")
            return None

    def insert(self, data: dict):
        try:
            response = requests.post(self.url, headers=self.headers, json=data)
            return self._handle_response(response)
        except Exception as e:
            print(f"Database insert error: {e}")
            return None

    def update(self, data: dict, filters: str):
        try:
            response = requests.patch(f"{self.url}?{filters}", headers=self.headers, json=data)
            return self._handle_response(response)
        except Exception as e:
            print(f"Database update error: {e}")
            return None

    def delete(self, filters: str):
        try:
            response = requests.delete(f"{self.url}?{filters}", headers=self.headers)
            return self._handle_response(response)
        except Exception as e:
            print(f"Database delete error: {e}")
            return None

    def _handle_response(self, response):
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


class SupabaseStorageBucket:
    def __init__(self, base_url: str, headers: dict, bucket_name: str):
        self.base_url = base_url
        self.headers = headers.copy()
        self.bucket_name = bucket_name

    def upload(self, path: str, file_bytes: bytes, file_options: dict = None):
        url = f"{self.base_url}/storage/v1/object/{self.bucket_name}/{path}"
        headers = self.headers.copy()
        if file_options and "content-type" in file_options:
            headers["Content-Type"] = file_options["content-type"]
        else:
            headers["Content-Type"] = "application/octet-stream"
        if file_options and file_options.get("upsert", "false") == "true":
            headers["x-upsert"] = "true"
        response = requests.post(url, headers=headers, data=file_bytes)
        response.raise_for_status()
        return response.json()

    def get_public_url(self, path: str):
        return f"{self.base_url}/storage/v1/object/public/{self.bucket_name}/{path}"

    def list(self, prefix: str = ""):
        url = f"{self.base_url}/storage/v1/object/list/{self.bucket_name}"
        response = requests.post(url, headers=self.headers, json={"prefix": prefix, "limit": 200})
        response.raise_for_status()
        return response.json()

    def remove(self, paths: list):
        url = f"{self.base_url}/storage/v1/object/{self.bucket_name}"
        response = requests.delete(url, headers=self.headers, json={"prefixes": paths})
        response.raise_for_status()
        return response.json()


class SupabaseStorage:
    def __init__(self, base_url: str, headers: dict):
        self.base_url = base_url
        self.headers = headers

    def from_(self, bucket_name: str):
        return SupabaseStorageBucket(self.base_url, self.headers, bucket_name)


# Konfigurasi
SUPABASE_URL = "https://gqeylubpnjewpqkswmqs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdxZXlsdWJwbmpld3Bxa3N3bXFzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg0NTg1MTQsImV4cCI6MjA5NDAzNDUxNH0._sP5xrp_uodpvEqUps7lvQooO4TRWFyw_9Z9Wo5maS8"

# Inisialisasi client global
supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client() -> SupabaseClient:
    return supabase

def get_storage_bucket() -> str:
    return "foto-dokumentasi"