import enum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base , TimestampMixin



class DocumentType(str, enum.Enum):
    passport = "passport"
    cv = "cv"
    diploma = "diploma"
    translation = "translation"
    visa = "visa"
    other = "other"


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False
    )
    doc_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int | None] = mapped_column()
    mime_type: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    candidate: Mapped["CandidateProfile"] = relationship(back_populates="documents")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Document {self.doc_type} candidate={self.candidate_id}>" 