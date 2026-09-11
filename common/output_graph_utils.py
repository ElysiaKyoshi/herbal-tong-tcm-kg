"""兼容垫片（补跑通所需，未改动原文件）。

`__004__langgraph_more_nodes/langgraph_more_nodes.py` 里写的是
    from common.output_graph_utils import output_pic_graph
而仓库中实际文件名为 `common/ouput_graph_utils.py`（原拼写少了一个 t）。
这里做一次重导出，使两种名称都能正常导入，原文件保持不变。
"""

from common.ouput_graph_utils import output_pic_graph  # noqa: F401

__all__ = ["output_pic_graph"]
