import threading
import queue
import logging
from typing import Callable, Any
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.task_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._start_worker()

    def _start_worker(self):
        def worker():
            while True:
                try:
                    task, args = self.task_queue.get()
                    if task is None:
                        break
                    
                    logger.info(f"[BACKGROUND] Starting task with args: {args}")
                    try:
                        self.executor.submit(task, *args)
                    except Exception as e:
                        logger.error(f"[BACKGROUND] Error executing task: {str(e)}")
                    
                    self.task_queue.task_done()
                except Exception as e:
                    logger.error(f"[BACKGROUND] Worker error: {str(e)}")

        threading.Thread(target=worker, daemon=True).start()

    def add_task(self, task: Callable, *args: Any):
        """Add a task to be executed in background"""
        logger.info(f"[BACKGROUND] Queueing task with args: {args}")
        self.task_queue.put((task, args))

    def shutdown(self):
        """Shutdown the task manager"""
        self.task_queue.put((None, None))
        self.executor.shutdown()
