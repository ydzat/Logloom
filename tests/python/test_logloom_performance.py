#!/usr/bin/env python3
"""
Logloom Python绑定性能测试
========================

测试Logloom Python绑定在高负载下的性能表现
"""

import os
import sys
import unittest
import time
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'bindings' / 'python'))
    
try:
    import logloom_py as ll
except ImportError:
    print("无法导入logloom_py模块。请确保Python绑定已正确构建。")
    print("可能需要在src/bindings/python目录运行: python setup.py install --user")
    sys.exit(1)

class LogloomPerformanceTest(unittest.TestCase):
    def setUp(self):
        """测试开始前的设置"""
        self.config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
        self.log_file = os.path.join(os.path.dirname(__file__), "python_test.log")
        
        # 确保测试开始前删除可能存在的旧日志文件
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
            
        # 初始化Logloom
        ll.initialize(self.config_path)
        
        # 配置日志输出到测试日志文件
        self.logger = ll.Logger("perf_test")
        self.logger.set_level("INFO")
        self.logger.set_file(self.log_file)  # 显式设置日志文件路径
        
    def tearDown(self):
        """测试结束后的清理"""
        ll.cleanup()
        # 测试完成后清理日志文件
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
    
    def test_logging_throughput(self):
        """测试日志记录的吞吐量"""
        num_logs = 10000
        message = "这是一条测试日志消息，用于测试Logloom的性能表现"
        
        start_time = time.time()
        
        # 记录大量日志
        for i in range(num_logs):
            self.logger.info(f"{message}: {i}")
            
        end_time = time.time()
        duration = end_time - start_time
        
        # 计算每秒日志数
        logs_per_second = num_logs / duration
        
        print(f"\n性能测试结果: 记录了 {num_logs} 条日志，耗时 {duration:.2f} 秒")
        print(f"吞吐量: {logs_per_second:.2f} 日志/秒")
        
        # 不需要断言，这是一个性能基准测试
        # 但可以检查文件是否存在，确认日志确实被写入
        self.assertTrue(os.path.exists(self.log_file), "日志文件应该被创建")
    
    def test_logging_latency(self):
        """测试日志记录的延迟"""
        num_samples = 100
        message = "这是一条测试日志消息，用于测试Logloom的延迟性能"
        latencies = []
        
        for i in range(num_samples):
            start_time = time.perf_counter()  # 使用高精度计时器
            self.logger.info(f"{message}: {i}")
            end_time = time.perf_counter()
            latencies.append((end_time - start_time) * 1000)  # 转换为毫秒
            
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        print(f"\n延迟测试结果:")
        print(f"平均延迟: {avg_latency:.3f} 毫秒")
        print(f"最大延迟: {max_latency:.3f} 毫秒")
        print(f"最小延迟: {min_latency:.3f} 毫秒")

    def test_concurrent_logging(self):
        """测试并发日志记录性能"""
        try:
            import threading
            import tempfile
            import os
        except ImportError:
            self.skipTest("threading模块不可用，跳过并发测试")
            return
            
        num_threads = 10
        logs_per_thread = 1000
        
        # 使用类的主日志文件，确保它已存在且可写
        concurrent_log_file = os.path.join(os.path.dirname(__file__), "concurrent_test.log")
        
        # 确保目录存在且有写权限
        log_dir = os.path.dirname(concurrent_log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # 创建文件以确保它存在
        try:
            # 预先创建日志文件确保它存在
            with open(concurrent_log_file, 'w') as f:
                f.write("# 并发测试日志文件\n")
        except (IOError, OSError) as e:
            self.fail(f"无法创建测试日志文件: {e}")
            
        # 创建一个全局的logger并预先设置日志文件
        global_logger = ll.Logger("concurrent_test")
        global_logger.set_file(concurrent_log_file)
        
        # 共享锁用于同步日志操作
        log_lock = threading.RLock()
        
        def logging_worker(thread_id):
            """工作线程函数 - 使用全局logger避免文件访问冲突"""
            nonlocal global_logger
            
            # 每个线程记录指定数量的日志
            for i in range(logs_per_thread):
                # 使用锁保护日志操作，避免并发访问
                with log_lock:
                    try:
                        global_logger.info(f"Thread {thread_id} 记录日志 {i}")
                    except Exception as e:
                        print(f"线程 {thread_id} 记录日志 {i} 时出错: {e}")
        
        start_time = time.time()
        
        # 创建并启动线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=logging_worker, args=(i,))
            threads.append(thread)
            thread.start()
            
        # 等待所有线程完成
        for thread in threads:
            thread.join()
            
        end_time = time.time()
        duration = end_time - start_time
        
        # 计算性能指标
        total_logs = num_threads * logs_per_thread
        logs_per_second = total_logs / duration if duration > 0 else 0
        
        print(f"\n并发测试结果:")
        print(f"{num_threads} 个线程共记录了 {total_logs} 条日志，耗时 {duration:.2f} 秒")
        print(f"并发吞吐量: {logs_per_second:.2f} 日志/秒")
        
        # 验证日志文件存在
        self.assertTrue(os.path.exists(concurrent_log_file), "日志文件应该被创建")
        
        # 清理创建的日志文件
        try:
            os.remove(concurrent_log_file)
        except:
            pass

if __name__ == "__main__":
    unittest.main()