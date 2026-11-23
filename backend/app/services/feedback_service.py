from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select

from app.db.db_config import AsyncSessionLocal
from app.models.chat_history import AnswerFeedback
from app.services.knowledge_base_service import KnowledgeBaseService


class FeedbackService:
    @staticmethod
    def serialize(record: AnswerFeedback) -> dict:
        return {
            "id": record.id,
            "session_id": record.session_id,
            "knowledge_base_id": record.knowledge_base_id,
            "knowledge_base_name": record.knowledge_base_name,
            "question": record.question,
            "answer": record.answer,
            "feedback_type": record.feedback_type,
            "comment": record.comment,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }

    @classmethod
    async def save_feedback(
        cls,
        user_id: str,
        question: str,
        answer: str,
        feedback_type: str,
        session_id: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> dict:
        normalized_type = (feedback_type or "").strip().lower()
        if normalized_type not in {"up", "down"}:
            raise HTTPException(status_code=400, detail="反馈类型仅支持 up 或 down")

        normalized_question = (question or "").strip()
        normalized_answer = (answer or "").strip()
        if not normalized_question or not normalized_answer:
            raise HTTPException(status_code=400, detail="问题和回答不能为空")

        if knowledge_base_id:
            knowledge_base = await KnowledgeBaseService.get_user_base(user_id, knowledge_base_id)
        else:
            knowledge_base = await KnowledgeBaseService.ensure_default_base(user_id)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AnswerFeedback)
                .where(
                    AnswerFeedback.user_id == user_id,
                    AnswerFeedback.session_id == session_id,
                    AnswerFeedback.knowledge_base_id == knowledge_base.id,
                    AnswerFeedback.question == normalized_question,
                    AnswerFeedback.answer == normalized_answer,
                )
                .order_by(AnswerFeedback.id.desc())
                .limit(1)
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                existing = AnswerFeedback(
                    user_id=user_id,
                    session_id=session_id,
                    knowledge_base_id=knowledge_base.id,
                    knowledge_base_name=knowledge_base.name,
                    question=normalized_question,
                    answer=normalized_answer,
                    feedback_type=normalized_type,
                    comment=(comment or "").strip() or None,
                )
                db.add(existing)
            else:
                existing.knowledge_base_id = knowledge_base.id
                existing.knowledge_base_name = knowledge_base.name
                existing.feedback_type = normalized_type
                existing.comment = (comment or "").strip() or None

            await db.commit()
            await db.refresh(existing)

        return cls.serialize(existing)

    @classmethod
    async def list_feedback(
        cls,
        user_id: str,
        knowledge_base_id: Optional[str] = None,
        limit: int = 50,
    ) -> dict:
        normalized_limit = max(1, min(limit, 200))

        async with AsyncSessionLocal() as db:
            query = (
                select(AnswerFeedback)
                .where(AnswerFeedback.user_id == user_id)
                .order_by(AnswerFeedback.updated_at.desc(), AnswerFeedback.id.desc())
                .limit(normalized_limit)
            )
            if knowledge_base_id:
                query = query.where(AnswerFeedback.knowledge_base_id == knowledge_base_id)

            result = await db.execute(query)
            items = result.scalars().all()

        serialized_items = [cls.serialize(item) for item in items]
        positive_count = sum(1 for item in items if item.feedback_type == "up")
        negative_count = sum(1 for item in items if item.feedback_type == "down")

        return {
            "items": serialized_items,
            "total_count": len(serialized_items),
            "positive_count": positive_count,
            "negative_count": negative_count,
        }

    @classmethod
    async def get_feedback_stats(
        cls,
        user_id: str,
        knowledge_base_id: Optional[str] = None,
    ) -> dict:
        async with AsyncSessionLocal() as db:
            base_filters = [AnswerFeedback.user_id == user_id]
            if knowledge_base_id:
                base_filters.append(AnswerFeedback.knowledge_base_id == knowledge_base_id)

            total_count = await db.scalar(
                select(func.count()).select_from(AnswerFeedback).where(*base_filters)
            )
            positive_count = await db.scalar(
                select(func.count())
                .select_from(AnswerFeedback)
                .where(*base_filters, AnswerFeedback.feedback_type == "up")
            )
            negative_count = await db.scalar(
                select(func.count())
                .select_from(AnswerFeedback)
                .where(*base_filters, AnswerFeedback.feedback_type == "down")
            )

        total_count = total_count or 0
        positive_count = positive_count or 0
        negative_count = negative_count or 0
        positive_rate = round((positive_count / total_count) * 100, 1) if total_count else 0.0

        return {
            "total_count": total_count,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "positive_rate": positive_rate,
        }
