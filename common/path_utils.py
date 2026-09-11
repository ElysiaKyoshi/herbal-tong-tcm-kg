import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 兼容别名：部分节点模块（如 nodes/generate_markdown_node.py）按 root_path 名称导入
root_path = root_dir


# print(root_dir)


def get_file_path(relative_path):
    return os.path.join(root_dir, relative_path)


if __name__ == '__main__':
    print(get_file_path('aa/test.py'))
