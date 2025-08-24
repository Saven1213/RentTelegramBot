from abc import ABC
from bot.cardlink.error import APIError


class BaseSession(ABC):
    """
    Abstract session class.

    If you want to implement your own session class,
    you should inherit this class.
    """

    def _check_response(self, return_type, code, data):
        if data.get('success'):
            data.pop('success')
            if 'data' in data:
                data = data['data']
            return return_type(**data)
        raise APIError(message=data.get('message'), code=code)
