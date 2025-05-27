from typing import Callable, Type, Tuple, Any


def expo(*_args: Any, **_kwargs: Any) -> float:
    return 0.0


def on_exception(
    wait_gen: Callable[..., Any],
    exceptions: Tuple[Type[BaseException], ...],
    max_tries: int = 1,
):
    def decorator(func: Callable[..., Any]):
        async def wrapper(*args: Any, **kwargs: Any):
            tries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions:
                    tries += 1
                    if tries >= max_tries:
                        raise

        return wrapper

    return decorator
