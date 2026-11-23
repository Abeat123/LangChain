import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select

from app.db.db_config import AsyncSessionLocal
from app.models.chat_history import KnowledgeBase
from app.rag.vector_store import VectorStoreService


DEFAULT_KNOWLEDGE_BASE_NAME = "默认知识库"
DEFAULT_KNOWLEDGE_BASE_DESCRIPTION = "系统默认知识库，兼容当前已有文档。"


class KnowledgeBaseService:
    @staticmethod
    def serialize(knowledge_base: KnowledgeBase, document_count: int = 0) -> dict:
        return {
            "id": knowledge_base.id,
            "name": knowledge_base.name,
            "description": knowledge_base.description or "",
            "is_default": bool(knowledge_base.is_default),
            "document_count": document_count,
            "created_at": knowledge_base.created_at.isoformat() if knowledge_base.created_at else None,
            "updated_at": knowledge_base.updated_at.isoformat() if knowledge_base.updated_at else None,
        }

    @classmethod
    async def ensure_default_base(cls, user_id: str) -> KnowledgeBase:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.user_id == user_id,
                    KnowledgeBase.is_default.is_(True),
                )
            )
            knowledge_base = result.scalar_one_or_none()
            if knowledge_base:
                return knowledge_base

            knowledge_base = KnowledgeBase(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=DEFAULT_KNOWLEDGE_BASE_NAME,
                description=DEFAULT_KNOWLEDGE_BASE_DESCRIPTION,
                is_default=True,
            )
            db.add(knowledge_base)
            await db.commit()
            await db.refresh(knowledge_base)
            return knowledge_base

    @classmethod
    async def get_user_base(cls, user_id: str, knowledge_base_id: str) -> KnowledgeBase:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.id == knowledge_base_id,
                    KnowledgeBase.user_id == user_id,
                )
            )
            knowledge_base = result.scalar_one_or_none()

        if knowledge_base is None:
            raise HTTPException(status_code=404, detail="知识库不存在")

        return knowledge_base

    @classmethod
    async def resolve_scope_id(cls, user_id: str, knowledge_base_id: Optional[str]) -> Optional[str]:
        if not knowledge_base_id:
            await cls.ensure_default_base(user_id)
            return None

        knowledge_base = await cls.get_user_base(user_id, knowledge_base_id)
        return None if knowledge_base.is_default else knowledge_base.id

    @classmethod
    async def get_base_info(cls, user_id: str, knowledge_base_id: Optional[str]) -> dict:
        if knowledge_base_id:
            knowledge_base = await cls.get_user_base(user_id, knowledge_base_id)
        else:
            knowledge_base = await cls.ensure_default_base(user_id)

        document_count = await cls._count_documents(user_id, knowledge_base)
        return cls.serialize(knowledge_base, document_count=document_count)

    @classmethod
    async def list_user_bases(cls, user_id: str) -> list[dict]:
        await cls.ensure_default_base(user_id)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeBase)
                .where(KnowledgeBase.user_id == user_id)
                .order_by(KnowledgeBase.is_default.desc(), KnowledgeBase.updated_at.desc())
            )
            knowledge_bases = result.scalars().all()

        items = []
        for knowledge_base in knowledge_bases:
            document_count = await cls._count_documents(user_id, knowledge_base)
            items.append(cls.serialize(knowledge_base, document_count=document_count))
        return items

    @classmethod
    async def create_base(cls, user_id: str, name: str, description: Optional[str] = "") -> dict:
        normalized_name = (name or "").strip()
        if not normalized_name:
            raise HTTPException(status_code=400, detail="知识库名称不能为空")

        await cls.ensure_default_base(user_id)

        async with AsyncSessionLocal() as db:
            duplicate = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.user_id == user_id,
                    KnowledgeBase.name == normalized_name,
                )
            )
            if duplicate.scalar_one_or_none() is not None:
                raise HTTPException(status_code=400, detail="知识库名称已存在")

            knowledge_base = KnowledgeBase(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=normalized_name,
                description=(description or "").strip(),
                is_default=False,
            )
            db.add(knowledge_base)
            await db.commit()
            await db.refresh(knowledge_base)

        return cls.serialize(knowledge_base, document_count=0)

    @classmethod
    async def update_base(
        cls,
        user_id: str,
        knowledge_base_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.id == knowledge_base_id,
                    KnowledgeBase.user_id == user_id,
                )
            )
            knowledge_base = result.scalar_one_or_none()
            if knowledge_base is None:
                raise HTTPException(status_code=404, detail="知识库不存在")

            if name is not None:
                normalized_name = name.strip()
                if not normalized_name:
                    raise HTTPException(status_code=400, detail="知识库名称不能为空")

                duplicate = await db.execute(
                    select(KnowledgeBase).where(
                        KnowledgeBase.user_id == user_id,
                        KnowledgeBase.name == normalized_name,
                        KnowledgeBase.id != knowledge_base_id,
                    )
                )
                if duplicate.scalar_one_or_none() is not None:
                    raise HTTPException(status_code=400, detail="知识库名称已存在")

                knowledge_base.name = normalized_name

            if description is not None:
                knowledge_base.description = description.strip()

            await db.commit()
            await db.refresh(knowledge_base)

        document_count = await cls._count_documents(user_id, knowledge_base)
        return cls.serialize(knowledge_base, document_count=document_count)

    @classmethod
    async def delete_base(cls, user_id: str, knowledge_base_id: str) -> None:
        knowledge_base = await cls.get_user_base(user_id, knowledge_base_id)
        if knowledge_base.is_default:
            raise HTTPException(status_code=400, detail="默认知识库不能删除")

        scope_id = knowledge_base.id
        store = VectorStoreService(knowledge_base_scope_id=scope_id)
        await store.delete_user_documents(user_id)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.id == knowledge_base_id,
                    KnowledgeBase.user_id == user_id,
                )
            )
            current = result.scalar_one_or_none()
            if current is not None:
                await db.delete(current)
                await db.commit()

    @classmethod
    async def _count_documents(cls, user_id: str, knowledge_base: KnowledgeBase) -> int:
        scope_id = None if knowledge_base.is_default else knowledge_base.id
        store = VectorStoreService(knowledge_base_scope_id=scope_id)
        documents = await store.get_user_documents(user_id)
        return len(documents)
