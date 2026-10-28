import json
import os
from datetime import datetime
from typing import Optional

import aiofiles
from aiofiles import os as aio_os

from app.core.logger_handler import logger
from app.utils.config import chroma_config
from app.utils.path_tool import get_abstract_path


class MD5Store:
    def __init__(self):
        self.base_dir = os.path.dirname(get_abstract_path(chroma_config["md5_hex_store"]))

    def _get_md5_store_dir(
        self,
        user_id: Optional[str] = None,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> str:
        if user_id:
            if knowledge_base_scope_id:
                return os.path.join(self.base_dir, "user_md5", user_id, knowledge_base_scope_id)
            return os.path.join(self.base_dir, "user_md5", user_id)
        return os.path.join(self.base_dir, "public_md5")

    async def check_md5_hex(
        self,
        md5_for_check: str,
        user_id: Optional[str] = None,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> bool:
        md5_dir = self._get_md5_store_dir(user_id, knowledge_base_scope_id)
        md5_path = os.path.join(md5_dir, "md5_hex_store.txt")

        if not await aio_os.path.exists(md5_dir):
            await aio_os.makedirs(md5_dir, exist_ok=True)
            async with aiofiles.open(md5_path, "w", encoding="utf-8"):
                pass
            return False

        if not await aio_os.path.exists(md5_path):
            async with aiofiles.open(md5_path, "w", encoding="utf-8"):
                pass
            return False

        try:
            async with aiofiles.open(md5_path, "r", encoding="utf-8") as file_obj:
                async for line in file_obj:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("{"):
                        try:
                            data = json.loads(line)
                            if data.get("md5") == md5_for_check:
                                return True
                        except Exception:
                            if line == md5_for_check:
                                return True
                    elif line == md5_for_check:
                        return True
            return False
        except Exception as exc:
            logger.error(f"【MD5存储】检查 MD5 失败: {exc}")
            return False

    async def save_md5_hex(
        self,
        md5_hex: str,
        filename: Optional[str] = None,
        original_filename: Optional[str] = None,
        user_id: Optional[str] = None,
        knowledge_base_scope_id: Optional[str] = None,
    ):
        md5_dir = self._get_md5_store_dir(user_id, knowledge_base_scope_id)
        md5_path = os.path.join(md5_dir, "md5_hex_store.txt")

        if not await aio_os.path.exists(md5_dir):
            await aio_os.makedirs(md5_dir, exist_ok=True)

        data = {
            "md5": md5_hex,
            "filename": filename,
            "original_filename": original_filename,
            "upload_time": datetime.now().isoformat(),
        }

        async with aiofiles.open(md5_path, "a", encoding="utf-8") as file_obj:
            await file_obj.write(json.dumps(data, ensure_ascii=False) + "\n")

    def save_md5_hex_sync(
        self,
        md5_hex: str,
        filename: Optional[str] = None,
        original_filename: Optional[str] = None,
        user_id: Optional[str] = None,
        knowledge_base_scope_id: Optional[str] = None,
    ):
        md5_dir = self._get_md5_store_dir(user_id, knowledge_base_scope_id)
        md5_path = os.path.join(md5_dir, "md5_hex_store.txt")

        if not os.path.exists(md5_dir):
            os.makedirs(md5_dir, exist_ok=True)

        data = {
            "md5": md5_hex,
            "filename": filename,
            "original_filename": original_filename,
            "upload_time": datetime.now().isoformat(),
        }

        with open(md5_path, "a", encoding="utf-8") as file_obj:
            file_obj.write(json.dumps(data, ensure_ascii=False) + "\n")

    async def _read_md5_records(
        self,
        user_id: Optional[str] = None,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> tuple[str, list]:
        md5_dir = self._get_md5_store_dir(user_id, knowledge_base_scope_id)
        md5_path = os.path.join(md5_dir, "md5_hex_store.txt")

        if not await aio_os.path.exists(md5_path):
            return md5_path, []

        records = []
        async with aiofiles.open(md5_path, "r", encoding="utf-8") as file_obj:
            async for line in file_obj:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("{"):
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        records.append(
                            {
                                "md5": line,
                                "filename": None,
                                "original_filename": None,
                                "upload_time": None,
                            }
                        )
                else:
                    records.append(
                        {
                            "md5": line,
                            "filename": None,
                            "original_filename": None,
                            "upload_time": None,
                        }
                    )
        return md5_path, records

    async def _write_md5_records(self, md5_path: str, records: list):
        if not records:
            md5_dir = os.path.dirname(md5_path)
            if await aio_os.path.exists(md5_path):
                await aio_os.remove(md5_path)
            if await aio_os.path.exists(md5_dir):
                try:
                    await aio_os.rmdir(md5_dir)
                except OSError:
                    pass
            return

        async with aiofiles.open(md5_path, "w", encoding="utf-8") as file_obj:
            for record in records:
                await file_obj.write(json.dumps(record, ensure_ascii=False) + "\n")

    async def delete_user_md5(
        self,
        user_id: str,
        knowledge_base_scope_id: Optional[str] = None,
    ):
        md5_dir = self._get_md5_store_dir(user_id, knowledge_base_scope_id)
        md5_path = os.path.join(md5_dir, "md5_hex_store.txt")
        if await aio_os.path.exists(md5_path):
            await aio_os.remove(md5_path)
        if await aio_os.path.exists(md5_dir):
            try:
                await aio_os.rmdir(md5_dir)
            except OSError:
                pass
        logger.info(f"【MD5存储】已清理用户 {user_id} 的 MD5 记录")

    async def delete_by_filename(
        self,
        user_id: str,
        filename: str,
        knowledge_base_scope_id: Optional[str] = None,
    ):
        md5_path, records = await self._read_md5_records(user_id, knowledge_base_scope_id)
        if not records:
            return None

        found_md5 = None
        remaining = []
        for record in records:
            record_filename = record.get("filename", record.get("original_filename"))
            if record_filename == filename:
                found_md5 = record.get("md5")
            else:
                remaining.append(record)

        if found_md5 is None:
            return None

        await self._write_md5_records(md5_path, remaining)
        logger.info(f"【MD5存储】已删除文件 {filename} 的 MD5 记录")
        return found_md5

    async def delete_single_md5(
        self,
        user_id: str,
        md5_to_delete: str,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> bool:
        md5_path, records = await self._read_md5_records(user_id, knowledge_base_scope_id)
        if not records:
            return False

        remaining = [record for record in records if record.get("md5") != md5_to_delete]
        if len(remaining) == len(records):
            return False

        await self._write_md5_records(md5_path, remaining)
        logger.info(f"【MD5存储】已删除 MD5 记录: {md5_to_delete}")
        return True

    async def get_md5_info(
        self,
        user_id: str,
        md5_value: str,
        knowledge_base_scope_id: Optional[str] = None,
    ):
        _, records = await self._read_md5_records(user_id, knowledge_base_scope_id)
        for record in records:
            if record.get("md5") == md5_value:
                return record
        return None

    async def get_all_md5_records(
        self,
        user_id: str,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> list:
        _, records = await self._read_md5_records(user_id, knowledge_base_scope_id)
        return records
