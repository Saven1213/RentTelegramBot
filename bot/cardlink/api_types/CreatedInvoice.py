from pydantic import BaseModel


class CreatedInvoice(BaseModel):
    link_url: str | None = None
    link_page_url: str | None = None
    bill_id: str | None = None
