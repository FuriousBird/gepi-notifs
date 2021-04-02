from bs4 import BeautifulSoup
import requests
import urllib3
import os, json
import operator

class WorkTile():
    def __init__(self, uuid, title, text, done=False):
        self.id = uuid
        self.title = title
        self.text = text
        self.done = done
    def __str__(self):
        return self.title+"\n"+self.text

class User():
    def __init__(self, name, password): #use create function instead, it will only return an object if the password is correct
        self.name = name
        self.password = password
        self.connected = False
        self.lastid = 0
    @staticmethod
    def create(name, password): #correct method for creating a user
        newuser = User(name, password)
        test = newuser.connect()
        if test:
            newuser.groupname = test[1]
            newuser.disconnect()
            return newuser
        else:
            newuser.disconnect()
            return False

    def connect(self):
        if self.connected:
            self.connected = False
            self.disconnect()
            return self.connect()
        else:
            self.session = requests.Session()
            payload = {
                'login':self.name, 
                'no_anti_inject_password':self.password
            }
            request = self.session.post("http://lfabuc.fr/ac/login.php", data=payload)
            requestContent = request.text.encode("utf-8")
            soup = BeautifulSoup(requestContent, features="html.parser")
            if "Échec de la connexion à Gepi" in soup.title.text:
                return False
            else:
                self.connected = True
                self.token = self.get_token()
                classdiv = soup.find("div",attrs={"id":"bd_colonne_droite"})
                classname = classdiv.find_all("p")[1].text.replace("\n","").split(" ")[-1]
                return True, classname
    def disconnect(self):
        self.session.close()
        self.connected = False
        return True
    
    def get(self, url, text=True):
        if not self.connected:
            self.connect()
            print("Did you forget to connect before making a request? Just did it for you.")
            return self.get(url, text)
        else:
            request = self.session.get(url)
            if request.ok:
                requestContent = request.content.decode("utf-8")
                if text:
                    return requestContent
                else:
                    return requestContent, request
            else:
                print("Your request didn't succeed.")
                return False
    
    def fetch_work(self, auto_set_read=False):
        response = self.get("http://lfabuc.fr/ac/cahier_texte/consultation.php")
        if response:
            soup = BeautifulSoup(response, features="html.parser")
            rawtiles = soup.find_all("div", attrs={"class":"matiere_a_faire"})
            tiles = []
            for rawtile in rawtiles:
                uuid = int(rawtile["id"][len("div_travail_"):])
                title = rawtile.find("h4").text
                text = "\n".join([x.text for x in rawtile.find_all('p')])
                isdone = 'color_fond_notices_t_fait' in rawtile.attrs["class"]
                tile = WorkTile(uuid, title, text, done=isdone)
                tiles.append(tile)
            return tiles
        else:
            print("Sorry we couldn't get the work for this user: {} .".format(self.name))
            return False
    def fetch_undone_work(self):
        tofilter = self.fetch_work()
        return [x for x in tofilter if not x.done]
        # only erase if already done
    def fetch_unseen_work(self):
        tofilter = self.fetch_work()
        work = []
        for i in tofilter:
            if i.id > self.lastid:
                work.append(i)
                self.lastid = i.id
        return work
        # erase if id is lower than lastid
    def get_token(self):
        if self.connected:
            response = self.get("http://lfabuc.fr/ac/cahier_texte/consultation.php")
            if response:
                soup = BeautifulSoup(response, features="html.parser")
                script_text = str(soup.find("div", attrs={"id":"container"}).find_all("script")[0])
                token = script_text[476:][:-670].split("',{")[0]
                return token
            else:
                return False
        else:
            self.connect()
            return self.get_token()
    def done_status(self, tile):
        if self.connected:
            if type(tile) == WorkTile:
                tile_id = tile.id
            else:
                print("Unvalid format for tile id.")
                return False
            token = self.token
            if token:
                tile.done = not tile.done
                self.get("http://lfabuc.fr/ac/cahier_texte_2/ajax_cdt.php?login_eleve={}&id_ct_devoir={}&mode=changer_etat&csrf_alea={}".format(self.name, tile_id, token))
                # we can check here if it suceeded by looking for the "unauthorized action" text at the top of the page. 
                return True
            else:
                return False
        else:
            self.connect()
            return self.done_status(tile)

