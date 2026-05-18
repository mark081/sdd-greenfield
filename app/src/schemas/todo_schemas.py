from typing import Annotated

from pydantic import BaseModel, Field, StrictBool, field_validator


class TodoCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1, max_length=1000)

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v.strip()


class TodoUpdateSchema(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1, max_length=1000)
    completed: StrictBool | None = None

    @field_validator("title")
    @classmethod
    def update_title_not_whitespace(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title must not be blank")
        return v.strip() if v else v

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("title must not be blank")
        return v.strip() if v else v
