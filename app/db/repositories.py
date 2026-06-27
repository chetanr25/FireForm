from uuid import UUID

from sqlmodel import Session, select

from app.models import Template, FormSubmission, FormTemplate, Job, Input

# Templates (legacy fill pipeline - read-only lookup, consumed by forms/jobs/tasks)
def get_template(session: Session, template_id: int) -> Template | None:
    return session.get(Template, template_id)


# Form templates (contract Layer 6 registry)
def create_form_template(session: Session, template: FormTemplate) -> FormTemplate:
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def get_form_template(session: Session, template_id: UUID) -> FormTemplate | None:
    return session.get(FormTemplate, template_id)


def get_form_template_by_form_type(session: Session, form_type: str) -> FormTemplate | None:
    statement = select(FormTemplate).where(FormTemplate.form_type == form_type)
    return session.exec(statement).first()


def list_form_templates(session: Session) -> list[FormTemplate]:
    statement = select(FormTemplate).order_by(
        FormTemplate.created_at.desc(), FormTemplate.template_id
    )
    return list(session.exec(statement))


def update_form_template(session: Session, template: FormTemplate) -> FormTemplate:
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


# Forms
def create_form(session: Session, form: FormSubmission) -> FormSubmission:
    session.add(form)
    session.commit()
    session.refresh(form)
    return form


# Jobs
def create_job(session: Session, job: Job) -> Job:
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_job(session: Session, job_id: int) -> Job | None:
    return session.get(Job, job_id)


def get_job_by_uuid(session: Session, job_uuid: str) -> Job | None:
    statement = select(Job).where(Job.job_id == job_uuid)
    return session.exec(statement).first()


def get_job_by_celery_id(session: Session, celery_task_id: str) -> Job | None:
    statement = select(Job).where(Job.celery_task_id == celery_task_id)
    return session.exec(statement).first()


def update_job(session: Session, job: Job) -> Job:
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_form_submission(session: Session, submission_id: int) -> FormSubmission | None:
    return session.get(FormSubmission, submission_id)


def delete_form_submission(session: Session, submission: FormSubmission) -> None:
    session.delete(submission)
    session.commit()


# Inputs
def create_input(session: Session, input_obj: Input) -> Input:
    session.add(input_obj)
    session.commit()
    session.refresh(input_obj)
    return input_obj


def get_input(session: Session, input_id: UUID) -> Input | None:
    return session.get(Input, input_id)

