from langchain_core.runnables import Runnable
from playwright.sync_api import sync_playwright

from __000__demo.xiaohongshu.agent_state import AgentState
import os


class XiaohongshuUploader:
    COOKIE_PATH = "xiaohongshu_state.json"
    PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=image&source=official"

    def __init__(self, image_paths, title="", content=""):
        self.image_paths = image_paths if isinstance(image_paths, list) else [image_paths]
        self.title = title
        self.content = content
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def launch(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)

        if os.path.exists(self.COOKIE_PATH):
            print("[√] 加载已保存的登录状态...")
            self.context = self.browser.new_context(
                storage_state=self.COOKIE_PATH,
                permissions=["geolocation"],
                geolocation={"latitude": 31.2304, "longitude": 121.4737}
            )
        else:
            print("[!] 未检测到登录状态，创建新上下文...")
            self.context = self.browser.new_context(
                permissions=["geolocation"],
                geolocation={"latitude": 31.2304, "longitude": 121.4737}
            )

        self.page = self.context.new_page()
        self.page.goto(self.PUBLISH_URL)

        if not os.path.exists(self.COOKIE_PATH):
            input("请手动登录后按回车继续...")
            self.context.storage_state(path=self.COOKIE_PATH)
            print("[√] 登录状态已保存")
        self.wait_seconds(1)

    def switch_to_image_post(self):
        print("🔀 正在切换到【上传图文】Tab...")

        try:
            # 等待所有 tab 出现
            self.page.wait_for_selector('.creator-tab .title', timeout=10000)

            # 获取所有包含“上传图文”的 tab
            tabs = self.page.query_selector_all('.creator-tab .title')
            target_tab = None

            for tab in tabs:
                text = tab.inner_text().strip()
                if "上传图文" in text:
                    box = tab.bounding_box()
                    # 过滤掉隐藏的节点（box=None 或者位置过于极端）
                    if box and box["x"] > 0 and box["y"] > 0:
                        target_tab = tab
                        break

            if target_tab:
                target_tab.click()
                print("[√] 已成功切换到【上传图文】Tab")
            else:
                print("[x] 未找到可点击的【上传图文】Tab")

        except Exception as e:
            print(f"[X] 切换失败: {e}")

    def upload_images(self, images=None):
        print("📤 正在上传图片...")

        try:
            # 如果外部没传，默认用初始化时的 self.image_paths
            if images is None:
                images = self.image_paths

            # 等待上传框出现
            self.page.wait_for_selector('input.upload-input[type="file"]', timeout=10000)

            # 定位上传图片的 input
            file_input = self.page.query_selector('input.upload-input[type="file"]')

            if file_input:
                file_input.set_input_files(images)
                print(f"[√] 已上传 {len(images)} 张图片")
            else:
                print("[x] 未找到图片上传输入框")

        except Exception as e:
            print(f"[X] 图片上传失败: {e}")

    def fill_title_and_content(self):
        print("📝 正在填写标题和正文...")

        # 填写标题
        try:
            title_input = self.page.wait_for_selector('input.d-text[placeholder*="填写标题"]', timeout=10000)
            title_input.fill(self.title)
            print(f"[√] 标题已填写：{self.title}")
        except:
            print("[x] 未找到标题输入框")

        # 填写正文
        try:
            editor = self.page.wait_for_selector('.tiptap[contenteditable="true"]', timeout=10000)
            editor.click()
            editor.type(self.content)
            print(f"[√] 正文已填写：{self.content}")
        except:
            print("[x] 未找到正文编辑器")

    def submit_post(self):
        self.wait_seconds(3)
        print("🚀 正在尝试点击发布按钮...")

        try:
            # 等待“发布”按钮出现并可点击
            self.page.wait_for_selector('button:has-text("发布")', timeout=10000)
            publish_button = self.page.query_selector('button:has-text("发布")')

            if publish_button:
                publish_button.click()
                print("[√] 发布按钮已点击")
            else:
                print("[!] 未找到发布按钮")
        except Exception as e:
            print(f"[X] 发布失败: {e}")

    def close(self):
        # 等待4秒
        self.wait_seconds(4)
        self.browser.close()
        self.playwright.stop()

    def wait_seconds(self, seconds):
        print(f"⏳ 等待 {seconds} 秒...")
        self.page.wait_for_timeout(seconds * 1000)


def auto_publish_xiaohongshu(images, title, content):
    print("🚀 开始上传小红书...")
    xhs = XiaohongshuUploader(images, title, content)
    # 启动浏览器，加载发布页面
    xhs.launch()
    # 切换到上传图文 Tab
    xhs.switch_to_image_post()
    # 上传图片
    xhs.upload_images()
    # 填写标题和正文
    xhs.fill_title_and_content()
    # # 最后点击发布
    xhs.submit_post()
    # 结束浏览器
    xhs.close()


class XiaohongshuAutoPublishAgent(Runnable):
    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        """根据用户输入生成中医养生类的小红书文案（包括标题、内容、策略）"""
        title = agent_state['xiaohongshu_tcm_post_title']
        content = agent_state['xiaohongshu_tcm_post_content']
        images = [agent_state['xiaohongshu_tcm_post_image_path']]
        print("🚀 开始发布小红书")
        # print(f"标题：{title}")
        # print(f"内容：{content}")
        # print(f"图片：{images}")
        auto_publish_xiaohongshu(images, title, content)
        agent_state['xiaohongshu_tcm_tip'] = "小红书发布成功！"
        return agent_state


if __name__ == '__main__':
    auto_publish_xiaohongshu(
        images=["picture/20250913182017吃荔枝有什.png"],
        title="中医养生",
        content="中医养生hahha"
    )
