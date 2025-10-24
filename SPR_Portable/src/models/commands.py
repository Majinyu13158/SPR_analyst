# -*- coding: utf-8 -*-
"""
命令模式（Command Pattern）实现

提供可撤销的操作命令
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from .provenance import OperationLog, ProvenanceManager


class ICommand(ABC):
    """命令接口"""
    
    def __init__(self):
        self.error: Optional[str] = None
    
    @abstractmethod
    def execute(self) -> bool:
        """
        执行操作
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """
        撤销操作
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        返回操作描述，用于UI显示
        
        Returns:
            人类可读的操作描述
        """
        pass
    
    @abstractmethod
    def to_operation_log(self) -> OperationLog:
        """
        转换为操作日志
        
        Returns:
            OperationLog对象
        """
        pass


class CommandManager:
    """管理可撤销的命令"""
    
    def __init__(self, provenance_mgr: ProvenanceManager, max_history: int = 50):
        """
        Args:
            provenance_mgr: 血缘管理器
            max_history: 最多保留的历史步数
        """
        self._undo_stack: List[ICommand] = []
        self._redo_stack: List[ICommand] = []
        self._provenance = provenance_mgr
        self._max_history = max_history
    
    def execute(self, command: ICommand) -> bool:
        """
        执行命令并记录
        
        Args:
            command: 要执行的命令
        
        Returns:
            True if successful
        """
        success = command.execute()
        if success:
            self._undo_stack.append(command)
            self._redo_stack.clear()  # 执行新命令后，清空redo栈
            
            # 限制历史大小
            if len(self._undo_stack) > self._max_history:
                self._undo_stack.pop(0)
            
            # 自动记录到血缘
            try:
                op_log = command.to_operation_log()
                self._provenance.record_operation(op_log)
            except Exception as e:
                print(f"[CommandManager] 记录操作日志失败: {e}")
        
        return success
    
    def undo(self) -> bool:
        """
        撤销最近一次操作
        
        Returns:
            True if successful
        """
        if not self._undo_stack:
            return False
        
        cmd = self._undo_stack.pop()
        success = cmd.undo()
        
        if success:
            self._redo_stack.append(cmd)
            
            # 标记操作已被撤销
            try:
                op_log = cmd.to_operation_log()
                self._provenance.mark_reverted(op_log.op_id)
            except Exception as e:
                print(f"[CommandManager] 标记撤销失败: {e}")
        else:
            # 撤销失败，恢复到undo栈
            self._undo_stack.append(cmd)
        
        return success
    
    def redo(self) -> bool:
        """
        重做最近一次撤销
        
        Returns:
            True if successful
        """
        if not self._redo_stack:
            return False
        
        cmd = self._redo_stack.pop()
        success = cmd.execute()
        
        if success:
            self._undo_stack.append(cmd)
            
            # 重新记录操作
            try:
                op_log = cmd.to_operation_log()
                op_log.op_id = op_log.op_id + "_redo"  # 标记为重做
                self._provenance.record_operation(op_log)
            except Exception as e:
                print(f"[CommandManager] 记录重做失败: {e}")
        else:
            # 重做失败，恢复到redo栈
            self._redo_stack.append(cmd)
        
        return success
    
    def can_undo(self) -> bool:
        """是否可以撤销"""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """是否可以重做"""
        return len(self._redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        """获取下一个可撤销操作的描述"""
        return self._undo_stack[-1].get_description() if self._undo_stack else None
    
    def get_redo_description(self) -> Optional[str]:
        """获取下一个可重做操作的描述"""
        return self._redo_stack[-1].get_description() if self._redo_stack else None
    
    def get_history(self) -> List[str]:
        """
        获取历史操作列表
        
        Returns:
            操作描述列表（最新的在最后）
        """
        return [cmd.get_description() for cmd in self._undo_stack]
    
    def clear(self):
        """清空所有历史"""
        self._undo_stack.clear()
        self._redo_stack.clear()

