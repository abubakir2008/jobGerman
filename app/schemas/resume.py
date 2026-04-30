from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    title: str
    company: str | None = None
    period: str | None = None
    description: str | None = None


class ProjectEntry(BaseModel):
    name: str
    link: str | None = None
    description: str | None = None


class EducationEntry(BaseModel):
    institution: str
    degree: str | None = None
    period: str | None = None


class LanguageEntry(BaseModel):
    name: str
    level: str | None = None


class ExtraEntry(BaseModel):
    title: str
    description: str | None = None


class ResumeBase(BaseModel):
    full_name: str | None = None
    phone: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    linkedin_url: str | None = Field(None, max_length=500)
    github_url: str | None = Field(None, max_length=500)
    desired_position: str | None = Field(None, max_length=255)
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)
    extras: list[ExtraEntry] = Field(default_factory=list)


class ResumeUpsert(ResumeBase):
    pass


class ResumeResponse(ResumeBase):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
