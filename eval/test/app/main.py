import os
import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    text,
)
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


mysql_host = required_env("MYSQL_HOST")
mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
mysql_user = required_env("MYSQL_USER")
mysql_password = required_env("MYSQL_PASSWORD")
mysql_database = required_env("MYSQL_DATABASE")

# Log connection details without exposing the password in pod logs.
print(
    "MySQL configuration loaded: "
    f"host={mysql_host}, port={mysql_port}, database={mysql_database}, "
    f"user={mysql_user}, password=<redacted>"
)

mysql_url = URL.create(
    drivername="mysql+mysqldb",
    username=mysql_user,
    password=mysql_password,
    host=mysql_host,
    port=mysql_port,
    database=mysql_database,
)
mysql_engine = create_engine(mysql_url, pool_pre_ping=True, pool_recycle=1800)
metadata = MetaData()
app = FastAPI(title="Kubernetes evaluation API")


class TableSchema(BaseModel):
    table_name: str
    columns: dict[str, str]


_identifier = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_type_spec = re.compile(
    r"^(Integer|String|Text|Boolean|Float|Date|DateTime)(?:\(([1-9][0-9]{0,4})\))?$"
)
_column_types = {
    "Integer": Integer,
    "String": String,
    "Text": Text,
    "Boolean": Boolean,
    "Float": Float,
    "Date": Date,
    "DateTime": DateTime,
}


def parse_column_type(type_spec: str):
    """Parse the supported SQL types without evaluating request-provided code."""
    match = _type_spec.fullmatch(type_spec)
    if match is None:
        raise ValueError(f"Unsupported column type: {type_spec}")

    type_name, length = match.groups()
    if length is not None:
        if type_name != "String":
            raise ValueError(f"A length is only supported for String, got {type_name}")
        return String(int(length))
    return _column_types[type_name]()


@app.get("/health")
def health():
    try:
        with mysql_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="MySQL is unavailable") from exc
    return {"status": "ok", "database": mysql_database}


@app.get("/tables")
def get_tables():
    try:
        with mysql_engine.connect() as connection:
            results = connection.execute(text("SHOW TABLES;"))
            return {"database": [str(result[0]) for result in results.fetchall()]}
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Could not list database tables") from exc


@app.put("/table")
def create_table(schema: TableSchema):
    if not _identifier.fullmatch(schema.table_name):
        raise HTTPException(status_code=422, detail="Invalid table name")
    if not schema.columns:
        raise HTTPException(status_code=422, detail="At least one column is required")

    columns = []
    for column_name, type_spec in schema.columns.items():
        if not _identifier.fullmatch(column_name):
            raise HTTPException(status_code=422, detail=f"Invalid column name: {column_name}")
        try:
            column_type = parse_column_type(type_spec)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        columns.append(Column(column_name, column_type))

    table = Table(schema.table_name, metadata, *columns, extend_existing=True)
    try:
        metadata.create_all(mysql_engine, tables=[table], checkfirst=True)
        return f"{schema.table_name} successfully created"
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Could not create database table") from exc
