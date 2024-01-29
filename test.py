from argparse import ArgumentParser
from pydantic import BaseModel, Field
from conflate import Conflater


class NestedConfig(BaseModel):
    retries: int = 3
    timeout: int = Field(10, description="Timeout in seconds.", gt=0, alias='timeout')
    url: str = 'http://example.com'
    

class Config(BaseModel):
    user_key: str = Field('xxx', description="User API key or bearer token used for authorization.") # alias, description
    user_email: str
    user_password: str = Field('abc', alias='pwd')
    api : NestedConfig = NestedConfig()



parser = ArgumentParser()

result = Conflater("polytope", Config, parser).load()


print(result)
