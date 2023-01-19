import uuid
from typing import List


def get_uuid(uuid_list: List[str]) -> str:
    while True:
        id = str(uuid.uuid4())
        if id not in uuid_list:
            break
    return id
