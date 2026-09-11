import os
import json
import base64
import requests

from typing import Optional
from langchain_core.runnables import Runnable
import datetime

from volcengine.visual.VisualService import VisualService
from __000__demo.xiaohongshu.agent_state import AgentState
from __000__demo.xiaohongshu.common import JIMENG_AK, JIMENG_SK


def sanitize_title_for_filename(title: str, max_length: int = 10) -> str:
    """
    将标题字符串清洗成适合作为文件名的格式（去除不合法字符，只保留前max_length个字符）

    :param title: 原始标题
    :param max_length: 截取的最大字符数
    :return: 清洗后的文件名部分
    """
    # 获取现在的时间
    now = datetime.datetime.now()
    # 格式化时间
    time_str = now.strftime("%Y%m%d%H%M%S")
    return time_str + title[:5] + ".png"


def generate_jimeng_prompt(title: str, content: str) -> str:
    return (
        f"一幅围绕中医养生主题创作的图像，画面展现与标题内容相关的场景，"
        f"构图中包含人物或物品与养生行为（如冥想、泡脚、煮药、食疗、经络按摩等），"
        f"整体氛围温和、宁静、有疗愈感，色调自然柔和，背景可融入自然或居家环境，"
        f"表达健康、平衡与舒缓的情绪。"
        f"图片内容主题为:{title}"
        f"图片中不能有任何文字。"
        f"整体画面和谐、美观，符合图片质量要求。"
        f"图片中包含与中医养生主题相关的元素，如中药、穴位、食物、运动等。"
        f"文字与画面协调，不影响整体美感。允许画风自由表达，可现代、写意、插画、水彩或其他形式。"
    )


def download_image_from_url(url: str, output_path: str):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        print(f"图片已保存：{output_path}")
    except requests.exceptions.RequestException as e:
        print(f"下载失败：{e}")


def generate_image(prompt: str, output_path: str):
    visual_service = VisualService()
    visual_service.set_ak(JIMENG_AK)  # 替换为你自己的 AK
    visual_service.set_sk(JIMENG_SK)  # 替换为你自己的 SK

    form = {
        "req_key": "jimeng_high_aes_general_v21_L",
        "prompt": prompt,
        "return_url": True
    }

    resp = visual_service.cv_process(form)
    image_urls = resp.get('data', {}).get('image_urls', [])
    if image_urls:
        download_image_from_url(image_urls[0], output_path)
        return output_path
    else:
        raise RuntimeError("图像生成失败，无有效图片链接返回")


def xiaohongshu_image_generator(title, content):
    # 生成提示词
    prompt = generate_jimeng_prompt(title, content)

    # 建了一个文件夹，用于保存图片
    os.makedirs('picture', exist_ok=True)
    file_name = sanitize_title_for_filename(title)
    output_path = os.path.join('picture', file_name)

    image_path = generate_image(prompt, output_path)
    return image_path


class XiaohongshuImageGeneratorAgent(Runnable):
    def invoke(self, agent_state: AgentState, config: Optional[dict] = None) -> AgentState:
        """根据标题和内容生成中医养生风格的小红书配图"""
        title = agent_state.get('xiaohongshu_tcm_post_title')
        content = agent_state.get('xiaohongshu_tcm_post_content')

        image_path = xiaohongshu_image_generator(title, content)

        agent_state['xiaohongshu_tcm_post_image_path'] = image_path
        print(f"图片生成成功: {image_path}")
        agent_state['xiaohongshu_tcm_tip'] = "图片生成成功"
        return agent_state


if __name__ == '__main__':
    xiaohongshu_image_generator("吃荔枝有什么好处呢？姐妹们！", "很多好处")
