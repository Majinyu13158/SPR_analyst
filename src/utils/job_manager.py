# -*- coding: utf-8 -*-
"""
JobManager - 统一后台任务调度（线程/进程）、进度、取消与结果回传。

最小可用实现：
- 线程池执行（I/O密集）
- 进程池执行（CPU密集）
- 提供 submit(func, *args, **kwargs, use_process=False) → job_id
- 取消/信号：started/progress/finished/failed/cancelled

后续可扩展：优先级、超时、批量任务、阶段化进度。
"""
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
from PySide6.QtWidgets import QApplication
import uuid
import traceback
from concurrent.futures import ProcessPoolExecutor


class _Runnable(QRunnable):
    def __init__(self, job_id, func, args, kwargs, mgr):
        super().__init__()
        self.job_id = job_id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.mgr = mgr

    def run(self):
        try:
            self.mgr.job_started.emit(self.job_id)
            result = self.func(*self.args, **self.kwargs)
            self.mgr.job_finished.emit(self.job_id, result)
        except Exception as e:
            tb = traceback.format_exc()
            self.mgr.job_failed.emit(self.job_id, f"{e}\n{tb}")


class JobManager(QObject):
    job_started = Signal(str)
    job_progress = Signal(str, float)
    job_finished = Signal(str, object)
    job_failed = Signal(str, str)
    job_cancelled = Signal(str)

    _instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread_pool = QThreadPool.globalInstance()
        self._proc_pool = ProcessPoolExecutor(max_workers=None)
        self._futures = {}  # job_id -> future (for process jobs)

    @classmethod
    def instance(cls):
        if cls._instance is None or getattr(cls._instance, 'destroyed', False):
            app = QApplication.instance()
            cls._instance = JobManager(parent=app)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """强制重置JobManager实例,清除所有旧任务和回调"""
        if cls._instance is not None:
            try:
                # 关闭进程池
                cls._instance._proc_pool.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass
            try:
                # ⭐ 清空线程池中的所有待执行任务
                cls._instance._thread_pool.clear()
                cls._instance._thread_pool.waitForDone(100)  # 等待100ms让正在执行的任务完成
            except Exception:
                pass
            cls._instance = None

    def new_job_id(self) -> str:
        return str(uuid.uuid4())

    def submit(self, func, *args, use_process=False, **kwargs) -> str:
        job_id = self.new_job_id()
        return self.submit_with_id(job_id, func, *args, use_process=use_process, **kwargs)

    def submit_with_id(self, job_id: str, func, *args, use_process=False, **kwargs) -> str:
        if use_process:
            # 进程池执行
            self.job_started.emit(job_id)
            fut = self._proc_pool.submit(func, *args, **kwargs)
            self._futures[job_id] = fut
            fut.add_done_callback(lambda f, jid=job_id: self._on_future_done(jid, f))
        else:
            # 线程池执行
            runnable = _Runnable(job_id, func, args, kwargs, self)
            self.job_started.emit(job_id)
            self._thread_pool.start(runnable)
        return job_id

    def cancel(self, job_id: str):
        fut = self._futures.get(job_id)
        if fut is not None:
            cancelled = fut.cancel()
            if cancelled:
                self.job_cancelled.emit(job_id)

    def _on_future_done(self, job_id: str, future):
        try:
            result = future.result()
            self.job_finished.emit(job_id, result)
        except Exception as e:
            tb = traceback.format_exc()
            self.job_failed.emit(job_id, f"{e}\n{tb}")

    def submit_with_callbacks(self, func, *args, 
                             on_started=None, on_done=None, on_fail=None, 
                             use_process=False, **kwargs) -> str:
        """
        提交任务并使用回调函数（而非信号），避免lambda累积问题
        
        Args:
            func: 要执行的函数
            on_started: 回调 fn(job_id)
            on_done: 回调 fn(job_id, result)
            on_fail: 回调 fn(job_id, error_str)
            use_process: 是否使用进程池
        
        Returns:
            job_id
        """
        job_id = self.new_job_id()
        
        if on_started:
            on_started(job_id)
        
        if use_process:
            # 进程池
            def _callback(future):
                try:
                    result = future.result()
                    if on_done:
                        on_done(job_id, result)
                except Exception as e:
                    tb = traceback.format_exc()
                    if on_fail:
                        on_fail(job_id, f"{e}\n{tb}")
            
            fut = self._proc_pool.submit(func, *args, **kwargs)
            self._futures[job_id] = fut
            fut.add_done_callback(_callback)
        else:
            # 线程池 - 需要包装
            class CallbackRunnable(QRunnable):
                def __init__(self, jid, f, a, kw, on_d, on_f):
                    super().__init__()
                    self.jid = jid
                    self.func = f
                    self.args = a
                    self.kwargs = kw
                    self.on_done = on_d
                    self.on_fail = on_f
                
                def run(self):
                    try:
                        result = self.func(*self.args, **self.kwargs)
                        if self.on_done:
                            self.on_done(self.jid, result)
                    except Exception as e:
                        tb = traceback.format_exc()
                        if self.on_fail:
                            self.on_fail(self.jid, f"{e}\n{tb}")
            
            runnable = CallbackRunnable(job_id, func, args, kwargs, on_done, on_fail)
            self._thread_pool.start(runnable)
        
        return job_id

