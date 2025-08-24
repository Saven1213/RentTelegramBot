from pydantic import BaseModel


class Item(BaseModel):
    name: str
    price: str
    quantity: str
    category: str
    extra_phone: str
