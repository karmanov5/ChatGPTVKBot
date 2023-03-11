from os import environ
from dotenv import load_dotenv
import openai, vk_api, random, re, requests
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api import VkUpload
from io import BytesIO
from PIL import Image


load_dotenv()
api_key = environ.get('API_KEY')
engine = 'text-davinci-003'
api_key_vk = environ.get('API_KEY_VK')

vk_session = vk_api.VkApi(token=api_key_vk)
vk = vk_session.get_api()
openai.api_key = api_key

    
def send_message(chat_id, message):
    vk.messages.send(
        chat_id=chat_id,
        message=message,
        random_id=random.randint(1, 1000)
    )



def send_image(chat_id, image_url):
    upload = VkUpload(vk_session)
    photo = upload.photo_messages(photos=image_url)[0]
    attachments = []
    attachments.append('photo{}_{}'.format(photo['owner_id'], photo['id']))
    vk.messages.send(
        chat_id=chat_id,
        message='Вот ваш результат',
        random_id=random.randint(1, 1000),
        attachment=','.join(attachments)
    )



def main():

    while True:
        longpool = VkBotLongPoll(vk_session, 219298440)
        try:
            for event in longpool.listen():
                if event.type == VkBotEventType.MESSAGE_NEW and event.from_chat:
                    message_text = event.message['text']
                    attachments = event.message['attachments'][0] if len(event.message['attachments']) > 0 else []
                    chat_id = event.chat_id
                    print(chat_id, message_text)
                    promt = re.search(r'[Аа]нтон[\S]*[\s]*(?P<promt>[\w\s\S]*)', message_text)
                    promt = '' if promt is None else promt.group('promt')
                    if promt != '':
                        image = re.search(r'[Нн]арисуй\s*(?P<image>[\w\s\S]*)', promt)
                        edit_image = re.search(r'[Ии]змени\s*[фотографияюкартинкау]*', promt)
                        if edit_image is not None and len(attachments) > 0 and attachments['type'] == 'photo':
                            image_url = attachments['photo']['sizes'][-1]['url']
                            image_source = requests.get(image_url)
                            with open('image.png', 'wb') as f:
                                f.write(image_source.content)
                            
                            image = Image.open('image.png')
                            image = image.resize((256, 256))

                            byte_stream = BytesIO()
                            image.save(byte_stream, format='PNG')
                            byte_array = byte_stream.getvalue()
                            completion = openai.Image.create_variation(
                                    image=byte_array,
                                    n=1,
                                    size='1024x1024'
                                )
                            image_url = completion['data'][0]['url']
                            filename = 'image.png'
                            response = requests.get(image_url)
                            with open(filename, 'wb') as f:
                                f.write(response.content)
                            completion_text = 'Ваше изображение находится по ссылке: ' + image_url
                            # print('Ответ бота:', completion_text)
                            send_image(chat_id, filename)

                        elif image is not None:
                            image = image.group('image')
                            completion = openai.Image.create(
                                prompt=image,
                                n=1,
                                size='1024x1024'
                            )
                            image_url = completion['data'][0]['url']
                            filename = 'image.png'
                            response = requests.get(image_url)
                            with open(filename, 'wb') as f:
                                f.write(response.content)
                            completion_text = 'Ваше изображение находится по ссылке: ' + image_url
                            # print('Ответ бота:', completion_text)
                            send_image(chat_id, filename)
                        else:   
                            completion = openai.Completion.create(
                                        engine=engine,
                                        prompt=promt,
                                        temperature=0.5,
                                        max_tokens=1000
                                    )
                            completion_text = completion.choices[0]['text']
                            print('Ответ бота:', completion_text)
                            send_message(chat_id, completion_text)

        except Exception as ex:
            print('Ошибка:', ex)





if __name__ == '__main__':
    main()