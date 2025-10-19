# -*- coding: utf-8 -*-
"""
链接管理器 - 管理对象之间的关联关系

功能：
1. 创建和删除链接
2. 查询正向/反向链接
3. 追踪数据血缘
4. 序列化/反序列化支持
"""
from PySide6.QtCore import QObject, Signal
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime
import json


class LinkManager(QObject):
    """
    链接管理器
    
    管理所有对象之间的关联关系，支持数据血缘追踪
    
    信号：
        link_created: 链接创建 (source_type, source_id, target_type, target_id)
        link_removed: 链接删除 (source_type, source_id, target_type, target_id)
        dependency_changed: 依赖关系改变
    """
    
    # 信号定义
    link_created = Signal(str, object, str, object)  # source_type, source_id, target_type, target_id
    link_removed = Signal(str, object, str, object)
    dependency_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 正向链接：source → [targets]
        self.forward_links: Dict[str, List[str]] = defaultdict(list)
        
        # 反向链接：target → [sources]
        self.backward_links: Dict[str, List[str]] = defaultdict(list)
        
        # 链接元数据：存储额外信息
        self.link_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 链接ID计数器
        self._link_id_counter = 0
    
    # ========== 核心功能 ==========
    
    def create_link(self, source_type: str, source_id: Any, 
                    target_type: str, target_id: Any, 
                    link_type: str = "default",
                    metadata: Optional[Dict] = None) -> str:
        """
        创建链接
        
        参数：
            source_type: 源对象类型 ('file', 'data', 'result', 'figure', 'project')
            source_id: 源对象ID（可以是int或str）
            target_type: 目标对象类型
            target_id: 目标对象ID
            link_type: 链接类型 ('import', 'plot_source', 'fitting_output', 'visualization', 'default')
            metadata: 额外的元数据
        
        返回：
            link_id: 链接ID
        
        示例：
            create_link('file', '/path/data.json', 'data', 1, 'import')
            create_link('data', 1, 'result', 3, 'fitting_output')
            create_link('result', 3, 'figure', 6, 'visualization')
        """
        # 生成键
        source_key = self._make_key(source_type, source_id)
        target_key = self._make_key(target_type, target_id)
        
        # 检查是否已存在
        if target_key in self.forward_links[source_key]:
            print(f"[LinkManager] 链接已存在: {source_key} → {target_key}")
            return self._find_link_id(source_key, target_key)
        
        # 生成链接ID
        link_id = f"link_{self._link_id_counter:06d}"
        self._link_id_counter += 1
        
        # 创建正向链接
        self.forward_links[source_key].append(target_key)
        
        # 创建反向链接
        self.backward_links[target_key].append(source_key)
        
        # 存储元数据
        link_data = {
            'id': link_id,
            'source': source_key,
            'target': target_key,
            'link_type': link_type,
            'created_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.link_metadata[link_id] = link_data
        
        # 发射信号
        self.link_created.emit(source_type, source_id, target_type, target_id)
        self.dependency_changed.emit()
        
        print(f"[LinkManager] 创建链接: {source_key} --[{link_type}]--> {target_key}")
        
        return link_id
    
    def remove_link(self, source_type: str, source_id: Any, 
                    target_type: str, target_id: Any) -> bool:
        """
        删除链接
        
        返回：
            bool: 是否成功删除
        """
        source_key = self._make_key(source_type, source_id)
        target_key = self._make_key(target_type, target_id)
        
        # 检查链接是否存在
        if target_key not in self.forward_links.get(source_key, []):
            print(f"[LinkManager] 链接不存在: {source_key} → {target_key}")
            return False
        
        # 删除正向链接
        self.forward_links[source_key].remove(target_key)
        if not self.forward_links[source_key]:
            del self.forward_links[source_key]
        
        # 删除反向链接
        self.backward_links[target_key].remove(source_key)
        if not self.backward_links[target_key]:
            del self.backward_links[target_key]
        
        # 删除元数据
        link_id = self._find_link_id(source_key, target_key)
        if link_id and link_id in self.link_metadata:
            del self.link_metadata[link_id]
        
        # 发射信号
        self.link_removed.emit(source_type, source_id, target_type, target_id)
        self.dependency_changed.emit()
        
        print(f"[LinkManager] 删除链接: {source_key} → {target_key}")
        
        return True
    
    def get_targets(self, source_type: str, source_id: Any, 
                    link_type: Optional[str] = None) -> List[Tuple[str, Any]]:
        """
        获取某对象链接的所有目标
        
        参数：
            source_type: 源对象类型
            source_id: 源对象ID
            link_type: 可选，过滤特定类型的链接
        
        返回：
            List[Tuple[type, id]]: 目标对象列表
        
        示例：
            targets = get_targets('data', 1)
            # 返回: [('result', 3), ('figure', 5)]
        """
        source_key = self._make_key(source_type, source_id)
        target_keys = self.forward_links.get(source_key, [])
        
        results = []
        for target_key in target_keys:
            # 如果指定了link_type，需要过滤
            if link_type:
                link_id = self._find_link_id(source_key, target_key)
                if link_id:
                    link_data = self.link_metadata.get(link_id, {})
                    if link_data.get('link_type') != link_type:
                        continue
            
            # 解析target_key
            target_type, target_id = self._parse_key(target_key)
            results.append((target_type, target_id))
        
        return results
    
    def get_sources(self, target_type: str, target_id: Any,
                    link_type: Optional[str] = None) -> List[Tuple[str, Any]]:
        """
        获取链接到某对象的所有源（反向查询）
        
        参数：
            target_type: 目标对象类型
            target_id: 目标对象ID
            link_type: 可选，过滤特定类型的链接
        
        返回：
            List[Tuple[type, id]]: 源对象列表
        
        示例：
            sources = get_sources('result', 3)
            # 返回: [('data', 1)]
        """
        target_key = self._make_key(target_type, target_id)
        source_keys = self.backward_links.get(target_key, [])
        
        results = []
        for source_key in source_keys:
            # 如果指定了link_type，需要过滤
            if link_type:
                link_id = self._find_link_id(source_key, target_key)
                if link_id:
                    link_data = self.link_metadata.get(link_id, {})
                    if link_data.get('link_type') != link_type:
                        continue
            
            # 解析source_key
            source_type, source_id = self._parse_key(source_key)
            results.append((source_type, source_id))
        
        return results
    
    def get_dependency_chain(self, obj_type: str, obj_id: Any, 
                            direction: str = 'forward') -> List[List[Tuple[str, Any]]]:
        """
        获取完整的依赖链
        
        参数：
            obj_type: 对象类型
            obj_id: 对象ID
            direction: 'forward' (正向：找所有派生对象) 或 'backward' (反向：找所有源对象)
        
        返回：
            List[List[Tuple]]: 依赖链列表（可能有多条路径）
        
        示例：
            # 正向：data:1 → result:3 → figure:6
            chain = get_dependency_chain('data', 1, 'forward')
            # 返回: [[('data', 1), ('result', 3), ('figure', 6)]]
        """
        visited = set()
        chains = []
        
        def dfs(current_type, current_id, path):
            current_key = self._make_key(current_type, current_id)
            
            if current_key in visited:
                return  # 避免循环
            
            visited.add(current_key)
            path.append((current_type, current_id))
            
            # 获取下一级
            if direction == 'forward':
                next_objs = self.get_targets(current_type, current_id)
            else:
                next_objs = self.get_sources(current_type, current_id)
            
            if not next_objs:
                # 到达终点
                chains.append(list(path))
            else:
                for next_type, next_id in next_objs:
                    dfs(next_type, next_id, path)
            
            path.pop()
            visited.remove(current_key)
        
        dfs(obj_type, obj_id, [])
        return chains
    
    def has_link(self, source_type: str, source_id: Any,
                 target_type: str, target_id: Any) -> bool:
        """检查两个对象之间是否存在链接"""
        source_key = self._make_key(source_type, source_id)
        target_key = self._make_key(target_type, target_id)
        return target_key in self.forward_links.get(source_key, [])
    
    def get_link_info(self, source_type: str, source_id: Any,
                     target_type: str, target_id: Any) -> Optional[Dict]:
        """获取链接的详细信息"""
        source_key = self._make_key(source_type, source_id)
        target_key = self._make_key(target_type, target_id)
        link_id = self._find_link_id(source_key, target_key)
        
        if link_id:
            return self.link_metadata.get(link_id)
        return None
    
    # ========== 序列化支持 ==========
    
    def to_dict(self) -> Dict:
        """
        导出为字典（用于保存到文件）
        
        返回：
            Dict: 包含所有链接信息的字典
        """
        return {
            'version': '1.0',
            'forward_links': dict(self.forward_links),
            'backward_links': dict(self.backward_links),
            'link_metadata': self.link_metadata,
            'link_id_counter': self._link_id_counter
        }
    
    def from_dict(self, data: Dict):
        """
        从字典导入（用于从文件加载）
        
        参数：
            data: to_dict() 返回的字典
        """
        version = data.get('version', '1.0')
        
        # 清空现有数据
        self.forward_links.clear()
        self.backward_links.clear()
        self.link_metadata.clear()
        
        # 加载数据
        self.forward_links = defaultdict(list, data.get('forward_links', {}))
        self.backward_links = defaultdict(list, data.get('backward_links', {}))
        self.link_metadata = data.get('link_metadata', {})
        self._link_id_counter = data.get('link_id_counter', 0)
        
        print(f"[LinkManager] 加载完成：{len(self.link_metadata)}个链接")
    
    def clear(self):
        """清空所有链接"""
        self.forward_links.clear()
        self.backward_links.clear()
        self.link_metadata.clear()
        self._link_id_counter = 0
        self.dependency_changed.emit()
        print("[LinkManager] 已清空所有链接")
    
    # ========== 统计和调试 ==========
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'total_links': len(self.link_metadata),
            'total_sources': len(self.forward_links),
            'total_targets': len(self.backward_links),
            'link_types': self._count_link_types()
        }
    
    def print_summary(self):
        """打印链接摘要（用于调试）"""
        stats = self.get_stats()
        print(f"\n{'='*50}")
        print(f"链接管理器统计")
        print(f"{'='*50}")
        print(f"总链接数: {stats['total_links']}")
        print(f"源对象数: {stats['total_sources']}")
        print(f"目标对象数: {stats['total_targets']}")
        print(f"\n链接类型分布:")
        for link_type, count in stats['link_types'].items():
            print(f"  - {link_type}: {count}")
        print(f"{'='*50}\n")
    
    def print_all_links(self):
        """打印所有链接（用于调试）"""
        print(f"\n{'='*50}")
        print(f"所有链接")
        print(f"{'='*50}")
        for link_id, link_data in self.link_metadata.items():
            print(f"{link_data['source']} --[{link_data['link_type']}]--> {link_data['target']}")
        print(f"{'='*50}\n")
    
    # ========== 私有辅助方法 ==========
    
    def _make_key(self, obj_type: str, obj_id: Any) -> str:
        """生成对象键: type:id"""
        return f"{obj_type}:{obj_id}"
    
    def _parse_key(self, key: str) -> Tuple[str, Any]:
        """
        解析对象键
        
        返回：
            (type, id): 类型和ID的元组
        """
        parts = key.split(':', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid key format: {key}")
        
        obj_type, obj_id_str = parts
        
        # 尝试转换ID为整数
        try:
            obj_id = int(obj_id_str)
        except ValueError:
            obj_id = obj_id_str
        
        return obj_type, obj_id
    
    def _find_link_id(self, source_key: str, target_key: str) -> Optional[str]:
        """查找链接ID"""
        for link_id, link_data in self.link_metadata.items():
            if link_data['source'] == source_key and link_data['target'] == target_key:
                return link_id
        return None
    
    def _count_link_types(self) -> Dict[str, int]:
        """统计各类型链接的数量"""
        counts = defaultdict(int)
        for link_data in self.link_metadata.values():
            counts[link_data['link_type']] += 1
        return dict(counts)

