#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>
#include <linux/slab.h>
#include <linux/string.h>
#include "lang.h"
#include "log.h"
#include "config.h"

#define PROC_ENTRY_NAME "logloom_test"
#define TEST_LOG_FILE "/tmp/logloom_kernel_test.log"
#define TEST_MODULE_NAME "KTEST"

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Logloom Test");
MODULE_DESCRIPTION("Logloom Kernel Module Test");
// MODULE_DEPENDS("logloom"); /* 此宏在内核中不存在，已移除 */

/* 测试状态跟踪 */
static int tests_run = 0;
static int tests_failed = 0;
static char test_buffer[4096] = ""; // 保存测试结果的缓冲区
static int buffer_pos = 0;

/* proc接口相关 */
static struct proc_dir_entry *proc_entry;

/* 添加测试结果到缓冲区 */
static void add_test_result(const char *format, ...) {
    va_list args;
    int len;

    va_start(args, format);
    len = vsnprintf(test_buffer + buffer_pos, sizeof(test_buffer) - buffer_pos, format, args);
    va_end(args);

    if (len > 0 && buffer_pos + len < sizeof(test_buffer)) {
        buffer_pos += len;
    }
}

/* 断言宏 */
#define ASSERT(condition, message) do { \
    tests_run++; \
    if (!(condition)) { \
        tests_failed++; \
        add_test_result("FAIL: %s - %s (%s:%d)\n", __func__, message, __FILE__, __LINE__); \
        pr_err("LOGLOOM_TEST: FAIL - %s - %s (%s:%d)\n", __func__, message, __FILE__, __LINE__); \
    } else { \
        add_test_result("PASS: %s - %s\n", __func__, message); \
        pr_info("LOGLOOM_TEST: PASS - %s - %s\n", __func__, message); \
    } \
} while (0)

/* 测试日志基本功能 */
static void test_log_basic(void) {
    // 设置日志级别为DEBUG
    log_set_level("DEBUG");
    ASSERT(strcasecmp(log_get_level_string(), "DEBUG") == 0, "Set log level to DEBUG");
    
    // 测试不同级别的日志
    log_debug(TEST_MODULE_NAME, "This is a debug message");
    log_info(TEST_MODULE_NAME, "This is an info message");
    log_warn(TEST_MODULE_NAME, "This is a warning message");
    log_error(TEST_MODULE_NAME, "This is an error message");
    log_fatal(TEST_MODULE_NAME, "This is a fatal message");
    
    // 设置日志级别为WARN，低于此级别的日志不应输出
    log_set_level("WARN");
    ASSERT(strcasecmp(log_get_level_string(), "WARN") == 0, "Set log level to WARN");
    
    // 测试日志文件输出
    log_set_file(TEST_LOG_FILE);
    log_warn(TEST_MODULE_NAME, "This warning should appear in file");
    log_error(TEST_MODULE_NAME, "This error should appear in file");
    
    // 测试控制台输出开关
    log_set_console_enabled(0);
    log_warn(TEST_MODULE_NAME, "This warning should NOT appear in console");
    log_set_console_enabled(1);
    log_error(TEST_MODULE_NAME, "This error should appear in console again");
}

/* 测试国际化功能 */
static void test_lang_basic(void) {
    const char *text;
    char *formatted;
    
    // 测试获取默认语言文本
    text = lang_get("system.welcome");
    ASSERT(text != NULL, "Get default language text");
    add_test_result("Text: %s\n", text);
    
    // 测试格式化文本
    formatted = lang_getf("system.user_login", "test_user");
    if (formatted) {
        add_test_result("Formatted: %s\n", formatted);
        ASSERT(strstr(formatted, "test_user") != NULL, "Format text with parameters");
        kfree(formatted);
    } else {
        ASSERT(0, "Format text with parameters");
    }
    
    // 测试切换语言（如果支持）
    if (lang_set_language("zh")) {
        text = lang_get("system.welcome");
        ASSERT(text != NULL, "Get text after language switch");
        add_test_result("Chinese text: %s\n", text);
        
        // 切回英文
        lang_set_language("en");
    } else {
        add_test_result("Language 'zh' not available, skipping test\n");
    }
}

/* 测试环境设置和清理 */
static int setup_tests(void) {
    // 设置日志输出到临时文件
    log_set_file(TEST_LOG_FILE);
    log_set_console_enabled(1);
    log_set_level("INFO");
    return 0;
}

static void cleanup_tests(void) {
    log_set_file(NULL); // 关闭日志文件
}

/* 运行所有测试 */
static void run_all_tests(void) {
    buffer_pos = 0;
    tests_run = 0;
    tests_failed = 0;
    
    add_test_result("Starting Logloom kernel module tests...\n\n");
    
    if (setup_tests() != 0) {
        add_test_result("Test setup failed!\n");
        return;
    }
    
    test_log_basic();
    test_lang_basic();
    
    cleanup_tests();
    
    add_test_result("\nTests completed: %d run, %d failed\n", tests_run, tests_failed);
}

/* /proc文件操作 */
static int logloom_test_proc_show(struct seq_file *m, void *v) {
    seq_printf(m, "%s", test_buffer);
    return 0;
}

static int logloom_test_proc_open(struct inode *inode, struct file *file) {
    return single_open(file, logloom_test_proc_show, NULL);
}

static ssize_t logloom_test_proc_write(struct file *file, const char __user *buffer, 
                                     size_t count, loff_t *pos) {
    char command[32];
    
    if (count >= sizeof(command))
        return -EINVAL;
        
    if (copy_from_user(command, buffer, count))
        return -EFAULT;
        
    command[count] = '\0';
    
    if (strncmp(command, "run", 3) == 0) {
        run_all_tests();
        return count;
    }
    
    return -EINVAL;
}

static const struct proc_ops logloom_test_proc_fops = {
    .proc_open = logloom_test_proc_open,
    .proc_read = seq_read,
    .proc_write = logloom_test_proc_write,
    .proc_lseek = seq_lseek,
    .proc_release = single_release,
};

static int __init logloom_test_init(void) {
    pr_info("Logloom test module initializing\n");
    
    // 创建proc条目
    proc_entry = proc_create(PROC_ENTRY_NAME, 0666, NULL, &logloom_test_proc_fops);
    if (!proc_entry) {
        pr_err("Failed to create /proc/%s\n", PROC_ENTRY_NAME);
        return -ENOMEM;
    }
    
    // 第一次自动运行所有测试
    run_all_tests();
    
    return 0;
}

static void __exit logloom_test_exit(void) {
    if (proc_entry)
        proc_remove(proc_entry);
        
    pr_info("Logloom test module exited\n");
}

module_init(logloom_test_init);
module_exit(logloom_test_exit);