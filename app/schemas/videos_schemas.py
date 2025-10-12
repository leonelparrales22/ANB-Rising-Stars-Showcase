from pydantic import BaseModel


class CreateVideoRequest(BaseModel):
    title: str
    