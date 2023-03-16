import os

from dotenv import load_dotenv
import vk_api


def create_post(post_text, post_image=None, group_id=None):
    load_dotenv('.env')
    if not group_id:
        group_id = os.environ['VK_GROUP_ID']

    vk_login = os.environ['VK_LOGIN']
    vk_password = os.environ['VK_PASSWORD']
    vk_session = vk_api.VkApi(vk_login, vk_password)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return False

    vk = vk_session.get_api()
    if not post_image:
        vk.wall.post(message=post_text, owner_id=f'-{group_id}')
        return True
    upload = vk_api.VkUpload(vk_session)
    with open(os.path.join('images', post_image), 'rb') as image:
        uploaded_image = upload.photo_wall(image, user_id=group_id, caption=post_text)
        image_for_post = f'photo{uploaded_image[0]["owner_id"]}_{uploaded_image[0]["id"]}'
        vk.wall.post(message=post_text, owner_id=f'-{group_id}', attachments=image_for_post)
        return True
