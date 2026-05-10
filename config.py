class Config:
    def __init__(self, **kwargs):
        self.db_host = kwargs["DB_HOST"]
        self.db_port = kwargs["DB_PORT"]
        self.db_name = kwargs["DB_NAME"]


config = Config(DB_HOST="localhost", DB_PORT=27017, DB_NAME="ecommerce")
