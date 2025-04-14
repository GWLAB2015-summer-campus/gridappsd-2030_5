from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from ieee_2030_5.db.tables import tableClass, DefaultDERControlTable
from ieee_2030_5.config import InvalidConfigFile, ServerConfiguration
import yaml
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class DBInfo:
    host: str
    user: str
    password: str
    db_name: str

engine = None

def init_db(config: ServerConfiguration):
    file = Path(config.db_info_file)
    if not file.exists():
        raise InvalidConfigFile(f"DB Information File does not exist: {file}")
    yaml_dict = yaml.safe_load(file.read_text())
    try:
        db_info = DBInfo(
            host = yaml_dict["host"],
            user = yaml_dict["user"],
            password = yaml_dict["password"],
            db_name = yaml_dict["db_name"]
        )
        SQLALCHEMY_DATABASE_URL = f"mariadb+pymysql://{db_info.user}:{db_info.password}@{db_info.host}/{db_info.db_name}"
        
        global engine
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        for tc in tableClass:
            tc.metadata.create_all(engine)

        if config.default_der_control:
            DefaultDERControlTable.set_server_default(config.default_der_control)
    except Exception as e:
        raise InvalidDBInfoFile(e)

def get_db_session():
    if engine is None:
        raise InvalidDBInfoFile("DB engine is None")
    else:
        with Session(engine, expire_on_commit=False) as session:
            return session