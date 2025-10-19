import matplotlib.pyplot as plt
import networkx as nx


def draw_state_diagram():
    # 创建有向图
    G = nx.DiGraph()

    # 定义状态和状态之间的转移关系
    edges = [
        ("s0", "s1", "ina=1"), ("s0", "s3", "ina=0"),
        ("s1", "s2", "ina=1"), ("s1", "s0", "ina=0"),
        ("s2", "s3", "ina=1"), ("s2", "s1", "ina=0"),
        ("s3", "s0", "ina=1"), ("s3", "s2", "ina=0")
    ]

    # 添加边到图中
    for edge in edges:
        G.add_edge(edge[0], edge[1], label=edge[2])

    # 使用 spring 布局绘制状态图
    pos = nx.spring_layout(G)

    # 绘制节点和边
    nx.draw(G, pos, with_labels=True, node_size=2000, node_color='lightblue', font_size=10, font_weight='bold',
            arrows=True)

    # 绘制边的标签
    edge_labels = {(edge[0], edge[1]): edge[2] for edge in edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, font_color='red')

    # 显示图形
    plt.title("State Diagram for Verilog HDL State Machine")
    plt.show()


# 调用函数绘制状态图
draw_state_diagram()
