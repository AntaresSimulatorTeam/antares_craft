from pydantic import BaseModel


class CraftBaseModel(BaseModel):
    pass
    # def __init__(self, /, **data: Any):
    #    super().__init__(**data)
    #    self.model_dump(warnings=False)
