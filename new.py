import requests
import json

class VKProfilePhotos:
    vk_api_base_url = 'https://api.vk.com/method/'

    def __init__(self, user_id, access_token):
        self.user_id = user_id
        self.access_token = access_token

    def fetch_photos(self):
        method = 'photos.get'
        params = {
            'owner_id': self.user_id,
            'album_id': 'profile',
            'access_token': self.access_token,
            'v': '5.131',
            'extended': 1,
            'photo_sizes': 1
        }
        response = requests.get(self.vk_api_base_url + method, params=params)
        response.raise_for_status()
        return response.json()['response']['items']

class YandexDiskAPI:
    yandex_api_base_url = 'https://cloud-api.yandex.net/v1/disk/'

    def __init__(self, oauth_token):
        self.oauth_token = oauth_token
        self.headers = {
            "Authorization": f"OAuth {self.oauth_token}"
        }

    def create_directory(self, directory_path):
        params = {
            'path': directory_path
        }
        response = requests.put(self.yandex_api_base_url + "resources", headers=self.headers, params=params)
        if response.status_code == 201:
            print(f"Папка '{directory_path}' успешно создана.")
        elif response.status_code == 409:
            print(f"Папка '{directory_path}' уже существует.")
        else:
            response.raise_for_status()

    def upload_file(self, file_url, file_name, directory_path):
        params = {
            'url': file_url,
            'path': f"{directory_path}/{file_name}",
            'overwrite': 'true'
        }
        response = requests.post(self.yandex_api_base_url + "resources/upload", headers=self.headers, params=params)
        if response.status_code == 202:
            print(f"Файл '{file_name}' успешно загружен в папку '{directory_path}'.")
        else:
            response.raise_for_status()
        return response.json()

class PhotoBackupManager:
    def __init__(self, vk_user_id, vk_access_token, yandex_oauth_token, photo_limit=5):
        self.vk_photos_manager = VKProfilePhotos(vk_user_id, vk_access_token)
        self.yandex_disk_manager = YandexDiskAPI(yandex_oauth_token)
        self.photo_limit = photo_limit
        self.directory_path = "/vk_photos"

    def backup_photos(self):
        photos = self.vk_photos_manager.fetch_photos()
        self.yandex_disk_manager.create_directory(self.directory_path)
        photos.sort(key=lambda x: x["likes"]["count"], reverse=True)
        saved_photos_info = []
        for photo in photos[:self.photo_limit]:
            largest_photo = max(photo["sizes"], key=lambda size: size["width"] * size["height"])
            file_url = largest_photo["url"]
            file_name = f"{photo['likes']['count']}.jpg"
            if any(p["file_name"] == file_name for p in saved_photos_info):
                file_name = f"{photo['likes']['count']}_{photo['date']}.jpg"
            self.yandex_disk_manager.upload_file(file_url, file_name, self.directory_path)
            saved_photos_info.append({
                "file_name": file_name,
                "size": largest_photo["type"]
            })

        with open("saved_photos.json", "w") as f:
            json.dump(saved_photos_info, f, indent=4)
        print("Резервное копирование завершено.")

if __name__ == "__main__":
    vk_user_id = input("Введите ID VK: ")
    vk_access_token = input("Введите токен VK: ")
    yandex_oauth_token = input("Введите токен Ya.Disk: ")
    app = PhotoBackupManager(vk_user_id, vk_access_token, yandex_oauth_token)
    app.backup_photos()