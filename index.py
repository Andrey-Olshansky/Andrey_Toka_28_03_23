from random import randrange

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from config import token, user_token
from database import save_vk_user, find_vk_user_by_id, get_users, \
    find_history_couples_id_by_user_id, add_couple_in_history

vk = vk_api.VkApi(token=token)
user_vk = vk_api.VkApi(token=user_token)
long_poll = VkLongPoll(vk)

START_COMMAND = "/поиск"


def send_msg(user_id, message):
    vk.method("messages.send", {"user_id": user_id, "message": message, "random_id": randrange(10 ** 7), })


def send_msg_with_photo(user_id, message, photo_id):
    print(photo_id)
    vk.method("messages.send", {"user_id": user_id, "message": message, "random_id": randrange(10 ** 7),
                                "attachment": f"photo{photo_id}", })


def user_profile_is_closed(user_id):
    response = vk.method("users.get", {"user_id": user_id, "fields": "is_closed"})
    return response[0].get("is_closed")


def get_user_data_by_id(user_id):
    response = vk.method("users.get", {"user_id": user_id, "fields": "sex,bdate,city,relation"})[0]
    try:
        return {user_id: response.get("id"), "sex": response.get("sex"), "age": response.get("age"),
                "city_id": response.get("city").get("id"), "relation": response.get("relation")}
    except AttributeError:
        return None


def get_user_photos_id_by_user_id(user_id):
    try:
        response = user_vk.method("photos.get", {"owner_id": user_id, "album_id": "profile"})
        id_list = []
        for i in response.get("items"):
            id_list.append(i.get("id"))
        return id_list[:3]
    except vk_api.exceptions.ApiError:
        pass


def get_domain_by_user_id(user_id):
    response = vk.method("users.get", {"user_id": user_id, "fields": "domain"})
    return f"vk.com/{response[0].get('domain')}"


def get_photo_url_by_user_id(user_id):
    response = vk.method("users.get", {"user_id": user_id, "fields": "photo_400_orig"})
    return f"{response[0].get('photo_400_orig')}"


def get_photo_id_by_user_id(user_id):
    response = vk.method("users.get", {"user_id": user_id, "fields": "photo_id"})
    return response[0].get('photo_id')


def find_couple_for_vk_user(user_id):
    possible_relations = [1, 5, 6]
    user = find_vk_user_by_id(user_id)
    user_data = get_user_data_by_id(user.user_id)
    other_users = [other_user for other_user in get_users() if
                   other_user.user_id not in find_history_couples_id_by_user_id(user.user_id)]
    for other_user in other_users:
        other_user_data = get_user_data_by_id(other_user.user_id)
        if other_user_data is not None and other_user_data.get("sex") != user_data.get("sex") and \
                (other_user_data.get("relation") in possible_relations or other_user_data.get("relation") is None):
            add_couple_in_history(user_id, other_user.user_id)
            return other_user
    return None


def is_start_request(text):
    if text.lower() == START_COMMAND:
        return True
    else:
        return False


for event in long_poll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            msg_text = event.text
            client_user_id = event.user_id
            if is_start_request(msg_text):
                if user_profile_is_closed(client_user_id):
                    send_msg(client_user_id, "Ваш профиль закрыт, для работы VKinder откройте профиль")
                else:
                    save_vk_user(client_user_id)
                    couple = find_couple_for_vk_user(client_user_id)
                    if couple is None:
                        send_msg(event.user_id, "Мы не смогли подобрать вам пару, загляните позже")
                    else:
                        send_msg(event.user_id,
                                 f"Мы подобрали вам пару! Чтобы продолжить поиск введите {START_COMMAND}")
                        send_msg_with_photo(event.user_id, f"{get_domain_by_user_id(couple.user_id)}",
                                            get_photo_id_by_user_id(couple.user_id))
                        for photo_id in get_user_photos_id_by_user_id(couple.user_id):
                            send_msg_with_photo(event.user_id, f"",
                                                f"{couple.user_id}_{photo_id}")

            else:
                send_msg(event.user_id, f"Привет, для поиска необходимо написать {START_COMMAND}")
