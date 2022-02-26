
import json
import hashlib
import time
import urllib
import requests
from datetime import datetime
import os
import PySimpleGUI as sg


class photo_backup():
    def __init__(self,vk_id, ok_fid):
        self.vk_id = vk_id
        self.ok_fid = ok_fid
        self.ya_token = self.upload_tokens('ya_token')
        self.vk_token = self.upload_tokens('vk_token')
        self.insta_token = self.upload_tokens('insta_token')
        self.ok_application_key = self.upload_tokens('ok_application_key')
        self.ok_access_token = self.upload_tokens('ok_access_token')
        self.ok_secret_token = self.upload_tokens('ok_secret_token')
        self.gd_token = self.upload_tokens('gd_token')
        self.json = []
        self.check_vars()

    def check_vars(self):
        if self.ya_token == '':
            self.vars_writing('ya_token')
            self.ya_token = self.upload_tokens('ya_token')
        if self.gd_token == '':
            self.vars_writing('gd_token')
            self.gd_token = self.upload_tokens('gd_token')
        if self.insta_token == '':
            self.vars_writing('insta_token')
            self.insta_token = self.upload_tokens('insta_token')

    def vars_writing(self,token):
        value = input(f'Введите ваш {token}: ')
        with open(f'tokens\\{token}.txt', 'w') as file:
            file.write(value)
            file.close()

    def general_func (self):
        for i in self.get_vk_albums():
            self.upload_to_ya(self.vk_downloads(i))
        self.upload_to_ya(self.insta_download())
        self.upload_to_ya(self.ok_photo_download())
        self.upload_to_gdrive()
        self.write_json(self.json)
        print("Download finish!")



    def vk_downloads(self,album):
        jsn = []
        url = f"https://api.vk.com/method/photos.get"
        params = {'user_id': self.vk_id, 'access_token': self.vk_token, 'v': '5.131', 'album_id': album, 'extended': '1'}
        respon = requests.get(url, params=params)
        for items in respon.json()['response']['items']:
            for url in reversed(items['sizes']):
                if self._check_entery(jsn, f"{items['likes']['count']}.jpg"):
                    jsn.extend([{'file_name': f'{str(datetime.date(datetime.now()))}_{str(items["likes"]["count"])}.jpg', 'size': url['type'], 'url': url['url'], 'From': f"VK{params['album_id']}"}])
                    break
                else:
                    jsn.extend([{'file_name': f"{items['likes']['count']}.jpg", 'size': url['type'], 'url': url['url'], 'From': f"VK{params['album_id']}"}])
                    break
        self.json.append(jsn)
        return jsn

    def _check_entery (self, jsn, item):
        for i in jsn:
            if item == i['file_name']:
                return True

    def get_vk_albums(self):
        albums_lst = ["profile","wall"]
        url = f"https://api.vk.com/method/photos.getAlbums"
        params = {'user_id': self.vk_id, 'access_token': self.vk_token, 'v': '5.131'}
        response = requests.get(url=url, params=params)
        for i in response.json()['response']['items']:
            if i != None:
                albums_lst.append(i['id'])
        return albums_lst



    def insta_download(self):
        jsn_ids = self._insta_photo_ids()
        jsn = []
        params = {"fields": "media_url", "access_token": self.insta_token}
        for i in jsn_ids:
            url = 'https://graph.instagram.com/'+i['file_name']
            response = requests.get(url=url, params=params)
            jsn.append({'file_name': i['file_name'] + '.jpg', 'size': 'max', 'url': response.json()['media_url'], 'From': 'Instagram'})
        self.json.append(jsn)
        return jsn

    def _insta_photo_ids(self):
        jsn = []
        url_ids = f'https://graph.instagram.com/me/media?fields=id,caption&access_token={self.insta_token}'
        while True:
            response = requests.get(url_ids)
            for i in response.json()['data']:
                jsn.append({'file_name': i['id'], 'size': 'max', 'url': '', 'From': 'Instagram'})
            try:
                url_ids = response.json()['paging']['next']
            except:
                break
        return jsn



    def ok_photo_download(self):
        jsn = []
        url = 'https://api.ok.ru/fb.do?'
        params = {'application_key': self.ok_application_key, 'fid': self.ok_fid, 'format': 'json', 'method': 'photos.getUserPhotos', 'sig': self._get_ok_sig(), 'access_token': self.ok_access_token}
        response = requests.get(url=url, params=params)
        result = response.json()
        for items in result['photos']:
            jsn.append({'file_name': items['fid']+'.jpg', 'size': 'max', 'url': items['standard_url'], 'From': 'Ok'})
        self.json.append(jsn)
        return jsn

    def _get_ok_sig(self):
        sig_str = f'application_key={self.ok_application_key}fid={self.ok_fid}format=jsonmethod=photos.getUserPhotos{self.ok_secret_token}'
        sig = hashlib.md5(sig_str.encode())
        return sig.hexdigest()



    def upload_to_ya(self,value):
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', "Authorization": f"OAuth {self.ya_token}"}
        response_path = requests.put(f"https://cloud-api.yandex.net/v1/disk/resources?path={value[0]['From']}", headers=headers,)
        iteration = 0
        for i in value:
            sg.one_line_progress_meter(f'Download', iteration, len(value), f'file: {i["file_name"]} from {i["From"]}')
            iteration +=1
            params = {'url': i['url'], 'path': f"{value[0]['From']}/{i['file_name']}", 'overwrite': 'false'}
            time.sleep(1)
            response = requests.post(url=url,headers=headers,params=params)



    def upload_file_to_gdrive (self, folder_id, file_name,path_to_file):
        headers = {"Authorization": f"Bearer {self.gd_token}"}
        para = {"name": file_name, "parents": [folder_id]}
        files = {'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'), 'file': ('application/jpeg', open(path_to_file, "rb"))}
        r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart", headers=headers, files=files)

    def create_Folder_in_gdrive(self,folderName):
        url = 'https://www.googleapis.com/drive/v3/files'
        headers = {'Authorization': f"Bearer {self.gd_token}", 'Content-Type': 'application/json'}
        metadata = {'name': folderName,'mimeType': 'application/vnd.google-apps.folder'}
        response = requests.post(url, headers=headers, data=json.dumps(metadata))
        return response.json()

    def upload_to_gdrive(self):
        way_list = self.download_to_pc(self.json)
        previos_folder = ''
        iteration = 0
        for items in way_list:
            sg.one_line_progress_meter(f'Download', iteration, len(way_list),f'file: {items.values()} from {items.keys()}')
            iteration += 1
            if str(items.keys())[12:-3] != previos_folder:
                previos_folder = str(items.keys())[12:-3]
                path_name = str(items.keys())[12:-3]
                folder_id = self.create_Folder_in_gdrive(path_name)['id']
            path_to_file = str(items.values())[14:-3]
            index = str(items.values()).rfind(r'\\')+2
            file_name = str(items.values())[index:-3]
            self.upload_file_to_gdrive(folder_id, file_name, path_to_file)


    def write_json (self, data):
        write_list = []
        iteration = 0
        for lst in data:

            sg.one_line_progress_meter(f'Download', iteration, len(data),f'Write json')
            iteration += 1
            for dict in lst:
                write_list.append({'From': dict['From'], 'file_name': dict['file_name'], 'size': dict['size']})
        with open('data.json', 'w') as f:
            json.dump(write_list, f)

    def upload_tokens(self,token):
        f = open(f'tokens\\{token}.txt')
        return f.read()

    def download_to_pc(self, jsn):
        way_list = []
        iteration = 0
        for lists in jsn:
            for item in lists:
                sg.one_line_progress_meter(f'Download', iteration, len(lists), f'download to pc')
                iteration += 1
                url = item['url']
                img = urllib.request.urlopen(url).read()
                if os.path.exists("photos\\"+ str(item['From'])):
                    path = "photos\\" + str(item['From'])
                else:
                    os.mkdir("photos\\"+ str(item['From']))
                    path = "photos\\"+ str(item['From'])
                time.sleep(1)
                photo = open(path + "\\" + str(item['file_name']), "wb")
                photo.write(img)
                photo.close
                way_list.append({str(item['From']): path + "\\" + str(item['file_name'])})
        return way_list


vkid = input('Введите ID страницы "ВКонтакте": ')
ok_fid = input('Введите ID страницы "Одноклассники": ')
one = photo_backup(vkid,ok_fid)
one.general_func()