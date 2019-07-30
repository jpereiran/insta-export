import shutil, os
import json
import requests
from random import choice
from appJar import gui
from bs4 import BeautifulSoup
from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageFile


ImageFile.LOAD_TRUNCATED_IMAGES = True
USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64)','AppleWebKit/537.36 (KHTML, like Gecko)','Chrome/65.0.3325.181','Safari/537.36']
percentComplete = 0

class InstagramScraper:
    def __init__(self, url, user_agents=None):
        self.url = url
        self.user_agents = user_agents

    def __random_agent(self):
        if self.user_agents and isinstance(self.user_agents, list):
            return choice(self.user_agents)
        return choice(USER_AGENTS)

    def __request_url(self):
        try:
            response = requests.get(
                        self.url,
                        headers={'User-Agent': self.__random_agent()})
            response.raise_for_status()
        except requests.HTTPError:
            raise requests.HTTPError('Received non-200 status code.')
        except requests.RequestException:
            raise requests.RequestException
        else:
            return response.text
    
    @staticmethod
    def extract_json(html):
        soup = BeautifulSoup(html, 'html.parser')
        body = soup.find('body')
        script_tag = body.find('script')
        raw_string = script_tag.text.strip().replace('window._sharedData =', '').replace(';', '')
        return json.loads(raw_string)
    
    def post_metrics(self):
        results = []
        try:
            response = self.__request_url()
            json_data = self.extract_json(response)
            metrics = json_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']
        except Exception as e:
            raise e
        else:
            for node in metrics:
                node = node.get('node')
                if node and isinstance(node,dict):
                    results.append(node)
        return results


def formatText(description, font, final_size):
    max_text = final_size - 20
    max_text_o = final_size - 20        
    final_text  = ''
    contador = 0
    text = description.replace('\n',' ').split('#')[0]
    words = text.split(' ')

    for word in words:
        if contador == 0:
            text_size = font.getsize(final_text + word)
        else:
            text_size = font.getsize(final_text + ' ' + word)
        if text_size[0] < max_text:
            if contador == 0:
                final_text = word
            else:
                final_text = final_text + ' ' + word
        else:
            final_text = final_text + '\n' + word
            max_text = max_text_o + max_text
            if max_text > max_text_o*3:
                return (final_text + '...')

        contador = contador + 1
    return final_text



def getImages(url, path):
    # Initiate a scraper object and call one of the methods.
    instagram = InstagramScraper(url)
    post_metrics = instagram.post_metrics()
    app.setMeter("progress", 10)

    for post in post_metrics:
        thumbnail = post['thumbnail_src']
        id_thumb = post['id']
        description = post['edge_media_to_caption']['edges'][0]['node']['text']

        response = requests.get(thumbnail, stream=True)

        with open(path + '/' + id_thumb +  '.png', 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
            out_file.close()

            final_size = 500
            font = ImageFont.truetype("fonts/" + "zombie checklist alpha.ttf",int(final_size*0.06))
            final_text = formatText(description,font,final_size)

            # set button size + 10px margins
            button_size = (final_size, int(final_size*0.22))
            name_img = Image.new('RGB', button_size, '#ebeadf')
            name_draw = ImageDraw.Draw(name_img)
            name_draw.text((10, int(final_size*0.04)), final_text, font=font, fill='black')

            # set image size + 10px margins
            color_img = Image.open(path + '/' + id_thumb +  '.png')
            color_img = color_img.resize((final_size, final_size)) 

            # add images
            total_height = color_img.size[1] + name_img.size[1]
            new_im = Image.new('RGB', (final_size, total_height))
            new_im.paste(color_img, (0,0))
            new_im.paste(name_img, (0,final_size))
            new_im = ImageOps.expand(new_im,border=int(final_size*0.05),fill='#ebeadf')
            new_im = ImageOps.expand(new_im,border=2,fill='black')

            # save in new file
            new_im.save(path + '/' + id_thumb +  '.png', "PNG")
            app.setMeter("progress", app.getMeter("progress")[0]*100 + int(90/len(post_metrics)))

    app.setMeter("progress", 100)


def press(btnName):
    if btnName == "Cancel":
        app.stop()

    elif app.getEntry("urlEnt") != "" and app.getEntry("folderEnt") != "":
        try:
            getImages(app.getEntry("urlEnt"), app.getEntry("folderEnt"))
            app.infoBox("Processing", "Finished downloading pictures")
            app.setMeter("progress", 0)
        except Exception as e:
            print(e)
            app.setMeter("progress", 0)
            app.errorBox("Internal Error", "Please check your internet connection and if the parameters are valid")  
    else:
        app.errorBox("Error", "Invalid parameters")


# create the GUI & set a title
app = gui("Pola-Filter",'400x200')
app.addLabel("urlLab", "URL:", 0, 0)
app.addEntry("urlEnt", 0, 1)
app.addLabel("folderLab", "Directory:", 1,0)
app.addDirectoryEntry("folderEnt", 1,1)

# progress bar
app.addMeter("progress", colspan=2)
app.setMeterFill("progress", "green")

# set the function to the buttons
app.addButtons( ["Submit", "Cancel"], press, colspan=2)
app.setFocus("urlEnt")
app.enableEnter(press)

# start the GUI
app.go()