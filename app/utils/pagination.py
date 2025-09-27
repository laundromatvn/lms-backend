import math


def get_total_pages(total: int, page_size: int) -> int:
    return math.ceil(total / page_size)
