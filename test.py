from functools import wraps  # 别忘了导入它


def my_good_decorator(func):
    # 重点：把 @wraps(func) 放在 wrapper 上
    @wraps(func)
    def wrapper(*args, **kwargs):
        """我是 wrapper 函数的文档 (但这个文档会被覆盖)"""
        print("--- 装饰器运行 ---")
        return func(*args, **kwargs)

    return wrapper


@my_good_decorator
def say_hello():
    """我是一个简单的问候函数"""
    print("你好!")


# ----------------------------------------
# 让我们再次“审问”一下 say_hello 函数
say_hello()
print(f"函数的名字是: {say_hello.__name__}")
print(f"函数的文档是: {say_hello.__doc__}")