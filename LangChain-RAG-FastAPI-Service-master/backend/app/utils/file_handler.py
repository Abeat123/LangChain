import asyncio
import hashlib
import os
import shutil
import sys

import aiofiles
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
    UnstructuredPowerPointLoader,
)
from langchain_core.documents import Document

from app.core.logger_handler import logger
from app.utils.path_tool import get_abstract_path


class FontBBoxStreamFilter:
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        if "FontBBox from font descriptor" not in data:
            self.stream.write(data)

    def flush(self):
        self.stream.flush()


sys.stderr = FontBBoxStreamFilter(sys.stderr)


def _resolve_abs_path(path: str) -> str:
    return get_abstract_path(path) if not os.path.isabs(path) else path


def _has_poppler() -> bool:
    return shutil.which("pdfinfo") is not None or shutil.which("pdftoppm") is not None


async def get_file_md5_hex(file_path: str) -> str:
    abs_file_path = _resolve_abs_path(file_path)

    if not os.path.exists(abs_file_path):
        logger.error(f"MD5 source file does not exist: {abs_file_path}")
        return ""

    if not os.path.isfile(abs_file_path):
        logger.error(f"MD5 source path is not a file: {abs_file_path}")
        return ""

    md5_object = hashlib.md5()
    try:
        async with aiofiles.open(abs_file_path, "rb") as f:
            while chunk := await f.read(1024):
                md5_object.update(chunk)
    except Exception as exc:
        logger.error(f"Failed to read file for MD5: {abs_file_path}, error: {exc}")
        return ""

    return md5_object.hexdigest()


async def listdir_allowed_type(path: str, allowed_types: tuple[str]) -> tuple:
    abs_path = _resolve_abs_path(path)

    if not os.path.exists(abs_path):
        logger.error(f"Directory does not exist: {abs_path}")
        return ()

    if not os.path.isdir(abs_path):
        logger.error(f"Path is not a directory: {abs_path}")
        return ()

    file_list = []
    for filename in await asyncio.to_thread(os.listdir, abs_path):
        if filename.endswith(allowed_types):
            file_list.append(os.path.join(abs_path, filename))

    return tuple(file_list)


async def pdf_loader(file_path: str, password: str = None) -> list[Document]:
    abs_file_path = _resolve_abs_path(file_path)

    if password:
        loader = PyPDFLoader(abs_file_path, password=password)
        return await asyncio.to_thread(loader.load)

    if _has_poppler():
        try:
            loader = UnstructuredPDFLoader(abs_file_path)
            docs = await asyncio.to_thread(loader.load)
            if docs and any(doc.page_content.strip() for doc in docs):
                return docs
        except Exception as exc:
            logger.warning(f"UnstructuredPDFLoader failed, fallback to PyPDFLoader: {exc}")
    else:
        logger.info("Poppler not found, using PyPDFLoader directly")

    loader = PyPDFLoader(abs_file_path)
    return await asyncio.to_thread(loader.load)


async def txt_loader(file_path: str) -> list[Document]:
    abs_file_path = _resolve_abs_path(file_path)

    for encoding in ("utf-8", "gbk"):
        try:
            loader = TextLoader(abs_file_path, encoding=encoding)
            return await asyncio.to_thread(loader.load)
        except Exception as exc:
            logger.error(f"Failed to load text file with encoding {encoding}: {abs_file_path}, error: {exc}")

    return []


async def word_loader(file_path: str) -> list[Document]:
    abs_file_path = _resolve_abs_path(file_path)
    try:
        loader = TextLoader(abs_file_path, encoding="utf-8")
        return await asyncio.to_thread(loader.load)
    except Exception as exc:
        logger.error(f"Failed to load word file: {abs_file_path}, error: {exc}")
        return []


async def markdown_loader(file_path: str) -> list[Document]:
    abs_file_path = _resolve_abs_path(file_path)
    try:
        loader = UnstructuredMarkdownLoader(abs_file_path, mode="single")
        return await asyncio.to_thread(loader.load)
    except Exception as exc:
        logger.error(f"Failed to load markdown file: {abs_file_path}, error: {exc}")
        return []


async def ppt_loader(file_path: str) -> list[Document]:
    abs_file_path = _resolve_abs_path(file_path)
    try:
        loader = UnstructuredPowerPointLoader(abs_file_path, mode="single")
        return await asyncio.to_thread(loader.load)
    except Exception as exc:
        logger.error(f"Failed to load powerpoint file: {abs_file_path}, error: {exc}")
        return []


def get_file_md5_hex_sync(file_path: str) -> str:
    abs_file_path = _resolve_abs_path(file_path)

    if not os.path.exists(abs_file_path):
        logger.error(f"MD5 source file does not exist: {abs_file_path}")
        return ""

    if not os.path.isfile(abs_file_path):
        logger.error(f"MD5 source path is not a file: {abs_file_path}")
        return ""

    md5_object = hashlib.md5()
    try:
        with open(abs_file_path, "rb") as f:
            while chunk := f.read(1024):
                md5_object.update(chunk)
    except Exception as exc:
        logger.error(f"Failed to read file for MD5: {abs_file_path}, error: {exc}")
        return ""

    return md5_object.hexdigest()


def pdf_loader_sync(file_path: str, password: str = None) -> list[Document]:
    abs_file_path = _resolve_abs_path(file_path)

    if password:
        loader = PyPDFLoader(abs_file_path, password=password)
        return loader.load()

    if _has_poppler():
        try:
            loader = UnstructuredPDFLoader(abs_file_path)
            docs = loader.load()
            if docs and any(doc.page_content.strip() for doc in docs):
                return docs
        except Exception as exc:
            logger.warning(f"UnstructuredPDFLoader failed, fallback to PyPDFLoader: {exc}")
    else:
        logger.info("Poppler not found, using PyPDFLoader directly")

    loader = PyPDFLoader(abs_file_path)
    return loader.load()


def txt_loader_sync(file_path: str) -> list[Document]:
    abs_file_path = _resolve_abs_path(file_path)

    for encoding in ("utf-8", "gbk"):
        try:
            loader = TextLoader(abs_file_path, encoding=encoding)
            return loader.load()
        except Exception as exc:
            logger.error(f"Failed to load text file with encoding {encoding}: {abs_file_path}, error: {exc}")

    return []


def word_loader_sync(file_path: str) -> list[Document]:
    abs_file_path = _resolve_abs_path(file_path)
    try:
        loader = TextLoader(abs_file_path, encoding="utf-8")
        return loader.load()
    except Exception as exc:
        logger.error(f"Failed to load word file: {abs_file_path}, error: {exc}")
        return []


def markdown_loader_sync(file_path: str) -> list[Document]:
    abs_file_path = _resolve_abs_path(file_path)
    try:
        loader = UnstructuredMarkdownLoader(abs_file_path, mode="single")
        return loader.load()
    except Exception as exc:
        logger.error(f"Failed to load markdown file: {abs_file_path}, error: {exc}")
        return []


def ppt_loader_sync(file_path: str) -> list[Document]:
    abs_file_path = _resolve_abs_path(file_path)
    try:
        loader = UnstructuredPowerPointLoader(abs_file_path, mode="single")
        return loader.load()
    except Exception as exc:
        logger.error(f"Failed to load powerpoint file: {abs_file_path}, error: {exc}")
        return []
