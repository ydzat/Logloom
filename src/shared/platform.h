/**
 * @file platform.h
 * @brief 平台检测和条件编译宏定义
 * 
 * 此文件定义了用于区分内核态和用户态环境的宏，以及平台相关的配置。
 */

#ifndef LOGLOOM_PLATFORM_H
#define LOGLOOM_PLATFORM_H

/*
 * 环境检测宏
 */
#ifdef __KERNEL__
    #define LOGLOOM_KERNEL_MODE 1
#else
    #define LOGLOOM_KERNEL_MODE 0
#endif

/*
 * 内存分配相关宏
 */
#if LOGLOOM_KERNEL_MODE
    /* 内核态内存分配 */
    #include <linux/slab.h>
    #include <linux/string.h>
    
    #define LOGLOOM_MALLOC(size) kmalloc(size, GFP_KERNEL)
    #define LOGLOOM_FREE(ptr) kfree(ptr)
    #define LOGLOOM_STRDUP(str) kstrdup(str, GFP_KERNEL)
#else
    /* 用户态内存分配 */
    #include <stdlib.h>
    #include <string.h>
    
    #define LOGLOOM_MALLOC(size) malloc(size)
    #define LOGLOOM_FREE(ptr) free(ptr)
    #define LOGLOOM_STRDUP(str) strdup(str)
#endif

/*
 * 同步原语相关宏
 */
#if LOGLOOM_KERNEL_MODE
    /* 内核态同步原语 */
    #include <linux/spinlock.h>
    #include <linux/mutex.h>
    
    typedef spinlock_t LOGLOOM_SPINLOCK_T;
    #define LOGLOOM_SPIN_INIT(lock) spin_lock_init(lock)
    #define LOGLOOM_SPIN_LOCK(lock) spin_lock(lock)
    #define LOGLOOM_SPIN_UNLOCK(lock) spin_unlock(lock)
    
    typedef struct mutex LOGLOOM_MUTEX_T;
    #define LOGLOOM_MUTEX_INIT(mutex) mutex_init(mutex)
    #define LOGLOOM_MUTEX_LOCK(mutex) mutex_lock(mutex)
    #define LOGLOOM_MUTEX_UNLOCK(mutex) mutex_unlock(mutex)
    #define LOGLOOM_MUTEX_DESTROY(mutex) /* 内核mutex不需要显式销毁 */
#else
    /* 用户态同步原语 */
    #include <pthread.h>
    
    typedef pthread_spinlock_t LOGLOOM_SPINLOCK_T;
    #define LOGLOOM_SPIN_INIT(lock) pthread_spin_init(lock, PTHREAD_PROCESS_PRIVATE)
    #define LOGLOOM_SPIN_LOCK(lock) pthread_spin_lock(lock)
    #define LOGLOOM_SPIN_UNLOCK(lock) pthread_spin_unlock(lock)
    
    typedef pthread_mutex_t LOGLOOM_MUTEX_T;
    #define LOGLOOM_MUTEX_INIT(mutex) pthread_mutex_init(mutex, NULL)
    #define LOGLOOM_MUTEX_LOCK(mutex) pthread_mutex_lock(mutex)
    #define LOGLOOM_MUTEX_UNLOCK(mutex) pthread_mutex_unlock(mutex)
    #define LOGLOOM_MUTEX_DESTROY(mutex) pthread_mutex_destroy(mutex)
#endif

/*
 * 输出相关宏
 */
#if LOGLOOM_KERNEL_MODE
    /* 内核态输出 */
    #include <linux/kernel.h>
    
    #define LOGLOOM_DEBUG(fmt, ...) pr_debug(fmt, ##__VA_ARGS__)
    #define LOGLOOM_INFO(fmt, ...) pr_info(fmt, ##__VA_ARGS__)
    #define LOGLOOM_WARN(fmt, ...) pr_warn(fmt, ##__VA_ARGS__)
    #define LOGLOOM_ERROR(fmt, ...) pr_err(fmt, ##__VA_ARGS__)
#else
    /* 用户态输出 */
    #include <stdio.h>
    
    #define LOGLOOM_DEBUG(fmt, ...) fprintf(stdout, "[DEBUG] " fmt "\n", ##__VA_ARGS__)
    #define LOGLOOM_INFO(fmt, ...) fprintf(stdout, "[INFO] " fmt "\n", ##__VA_ARGS__)
    #define LOGLOOM_WARN(fmt, ...) fprintf(stdout, "[WARN] " fmt "\n", ##__VA_ARGS__)
    #define LOGLOOM_ERROR(fmt, ...) fprintf(stderr, "[ERROR] " fmt "\n", ##__VA_ARGS__)
#endif

/*
 * 文件操作相关宏
 */
#if LOGLOOM_KERNEL_MODE
    /* 内核态文件操作 */
    #include <linux/fs.h>
    
    typedef struct file* LOGLOOM_FILE_T;
    #define LOGLOOM_FILE_OPEN(path, mode) filp_open(path, mode, 0)
    #define LOGLOOM_FILE_CLOSE(file) filp_close(file, NULL)
    #define LOGLOOM_FILE_WRITE(file, buf, size) kernel_write(file, buf, size, &file->f_pos)
#else
    /* 用户态文件操作 */
    #include <stdio.h>
    
    typedef FILE* LOGLOOM_FILE_T;
    #define LOGLOOM_FILE_OPEN(path, mode) fopen(path, mode)
    #define LOGLOOM_FILE_CLOSE(file) fclose(file)
    #define LOGLOOM_FILE_WRITE(file, buf, size) fwrite(buf, 1, size, file)
#endif

#endif /* LOGLOOM_PLATFORM_H */