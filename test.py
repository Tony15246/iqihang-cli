import json
import queue
import re
import subprocess
import sys
from datetime import datetime

import requests


def get_cookie(phone, password):
    url = "https://www.iqihang.com/api/ark/sso/login"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    data = {"loginType": 2, "clientType": 2, "registerPlatform": 2, "account": phone, "password": password}
    response = requests.post(url, headers=headers, json=data, timeout=5)
    return response.json()["data"]["token"]


# def get_user_id(cookie):
#     url = "https://www.iqihang.com/api/ark/web/v1/user/info"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
#         "Authorization": f"Bearer {cookie}",
#     }
#     response = requests.get(url, headers=headers, timeout=5)
#     data = response.json()["data"]
#     return data["id"]


def get_course_list(cookie):
    url = "https://www.iqihang.com/api/ark/web/v1/user/course/course-list?isMarketingCourse=0&type=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Authorization": f"Bearer {cookie}",
    }
    response = requests.get(url, headers=headers, timeout=5)
    data = response.json()["data"]
    course_list = []
    for course in data:
        course_dict = {
            "id": course["id"],
            "name": course["productName"],
            "progress_id": course["lastLearningChapterId"] or None,
            "progress_name": course["lastLearningChapterName"] or None,
            "user_id": course["userId"],
            "product_id": course["productId"],
            "skuId": course["skuId"],
            "catalog": course["productCurriculumId"],
        }
        course_list.append(course_dict)
    return course_list


def get_lesson_tree(course_catalog, cookie):
    url = f"https://www.iqihang.com/api/ark/web/v1/course/catalog/{course_catalog}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Authorization": f"Bearer {cookie}",
    }
    response = requests.get(url, headers=headers, timeout=5)
    data = response.json()["data"]
    lesson_tree = []
    for tree in data["courseNodes"]:
        root = {
            "id": tree["id"],
            "name": tree["name"],
            "children": tree["children"],
            "vid": tree["resourceList"][0]["vid"] if tree["resourceList"] else None,
        }
        node_queue = queue.Queue()
        node_queue.put(root)
        while not node_queue.empty():
            parent = node_queue.get()
            children = parent["children"]
            parent["children"] = []
            if not children:
                continue
            for node in children:
                child = {
                    "id": node["id"],
                    "name": node["name"],
                    "children": node["children"],
                    "vid": (
                        node["resourceList"][0]["vid"] if node["resourceList"] else None
                    ),
                }
                node_queue.put(child)
                parent["children"].append(child)
        lesson_tree.append(root)
    return lesson_tree


def choose_lesson(children):
    for index, lesson in enumerate(children):
        if len(lesson["children"]) == 0 and not lesson["vid"]:
            print(f"Index: {index}, Name: {lesson['name']}, 暂不支持处理直播回放")
            continue
        print(f"Index: {index}, Name: {lesson['name']}")
    lesson_index = int(input("选择课程："))
    print()
    lesson = children[lesson_index]
    if len(lesson["children"]) == 0 and not lesson["vid"]:
        return None
    if len(lesson["children"]) == 0:
        return lesson
    return choose_lesson(lesson["children"])


def get_video_url(vid, cookie):
    url = "https://p.bokecc.com/servlet/getvideofile"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Authorization": f"Bearer {cookie}",
    }
    params = {
        "vid": vid,
        "siteid": "A183AC83A2983CCC",
    }
    response = requests.get(url, headers=headers, params=params, timeout=5)
    match = re.search(r"\((.*)\)", response.text)
    if not match:
        return None
    json_str = match.group(1)
    data = json.loads(json_str)
    copies = data["copies"]
    for copy in copies:
        if copy["desp"] == "1080P":
            return copy["playurl"]
    return None


def finish_progress(course, lesson, cookie):
    url = "https://www.iqihang.com/api/ark/report/v1/user/course/user/learn/new/report"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Authorization": f"Bearer {cookie}",
    }
    data = {
        "userId": course["user_id"],
        "productId": course["product_id"],
        "productSkuId": course["skuId"],
        "userProductId": course["id"],
        "curriculumId": course["catalog"],
        "chapterId": lesson["id"],
        "chapterName": lesson["name"],
        "sourceType": 3,
        "position": 0,
        "learnProgress": "1.00",
        "reportTime": 0,
        "isDrag": 1,
        "source": 4,
        "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    requests.post(url, headers=headers, json=data, timeout=5)


if __name__ == "__main__":
    with open("config.json", "r", encoding="utf8") as file:
        config = json.load(file)
    cookie = get_cookie(config["phone"], config["password"])
    course_list = get_course_list(cookie)
    for index, course in enumerate(course_list):
        print(
            f"Index: {index}, Name: {course['name']}, 上次学到：{course['progress_name'] or '无'}"
        )
    course_index = int(input("选择课程："))
    print()
    course_catalog = course_list[course_index]["catalog"]
    lesson_tree = get_lesson_tree(course_catalog, cookie)
    lesson = choose_lesson(lesson_tree)
    if lesson is None:
        print("暂不支持处理直播回放")
        sys.exit()
    video_url = get_video_url(lesson["vid"], cookie)
    if not video_url:
        print("获取视频源出错")
        sys.exit()
    print("Index: 0, 使用mpv播放课程")
    print("Index: 1, 下载课程")
    print("Index: 2, 标记课程为已学习")
    user_option = int(input("选择要进行的操作："))
    print()
    match user_option:
        case 0:
            print("调用mpv播放器中...")
            subprocess.run(
                [
                    str(config["mpv_path"]),
                    str(video_url),
                    f"--force-media-title={lesson['name']}",
                ],
                check=False,
            )
        case 1:
            print("调用ffmpeg中...")
            subprocess.run(
                [
                    str(config["ffmpeg_path"]),
                    "-i",
                    str(video_url),
                    "-c",
                    "copy",
                    f"{lesson['name']}.mp4",
                ],
                check=False,
            )
        case 2:
            finish_progress(course_list[course_index], lesson, cookie)
            print("标记完成")
        case _:
            pass
