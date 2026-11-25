# Load libraries
import asyncio
import logging

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notification import Notification, NotificationPreference
from backend.models.settings import Settings

logger = logging.getLogger(__name__)


# Creates a notification and optionally triggers an email
async def create_notification(
    db: AsyncSession,
    type: str,
    title: str,
    message: str,
    severity: str = "info",
    related_fic_id: int | None = None,
) -> Notification | None:
    pref_result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.notification_type == type
        )
    )
    pref = pref_result.scalar_one_or_none()

    if pref is not None and not pref.ui_enabled and not pref.email_enabled:
        return None

    notification = None

    if pref is None or pref.ui_enabled:
        notification = Notification(
            type=type,
            title=title,
            message=message,
            severity=severity,
            related_fic_id=related_fic_id,
        )
        db.add(notification)
        await db.flush()

    if pref is not None and pref.email_enabled:
        settings_result = await db.execute(select(Settings).where(Settings.id == 1))
        settings_row = settings_result.scalar_one_or_none()

        if settings_row and settings_row.smtp_host:
            asyncio.ensure_future(_send_notification_email(db, title, message))

    return notification


# Builds a branded HTML email from notification content
def _build_email_html(title: str, message: str) -> str:
    import html

    safe_title = html.escape(title)
    safe_message = html.escape(message)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f3f4f6;padding:24px 0;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

<tr><td style="background-color:#4f46e5;padding:20px 24px;border-radius:8px 8px 0 0;">
<span style="color:#ffffff;font-size:18px;font-weight:700;">&#128218; Bibliotheca Fabulae</span>
</td></tr>

<tr><td style="background-color:#ffffff;padding:24px;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;">
<h2 style="margin:0 0 12px 0;font-size:18px;color:#111827;">{safe_title}</h2>
<p style="margin:0;font-size:14px;line-height:1.6;color:#374151;">{safe_message}</p>
</td></tr>

<tr><td style="background-color:#f9fafb;padding:16px 24px;border:1px solid #e5e7eb;border-top:0;border-radius:0 0 8px 8px;">
<p style="margin:0;font-size:12px;color:#9ca3af;">Bibliotheca Fabulae &mdash; Your personal fanfiction archive</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


# Sends a notification email in the background
async def _send_notification_email(db: AsyncSession, title: str, message: str) -> None:
    try:
        from backend.services.email_service import send_email

        html_body = _build_email_html(title, message)

        await send_email(
            db,
            subject=title,
            body=message,
            html_body=html_body,
        )

    except Exception:
        logger.exception("Failed to send notification email: %s", title)


# Retrieves a paginated list of notifications with counts
async def get_notifications(
    db: AsyncSession,
    unread_only: bool = False,
    type_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    query = select(Notification)
    count_query = select(func.count(Notification.id))
    unread_query = select(func.count(Notification.id)).where(
        Notification.is_read == False  # noqa: E712
    )

    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712
        count_query = count_query.where(Notification.is_read == False)  # noqa: E712

    if type_filter:
        query = query.where(Notification.type == type_filter)
        count_query = count_query.where(Notification.type == type_filter)

    query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    notifications = result.scalars().all()

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar()

    items = [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "severity": n.severity,
            "is_read": n.is_read,
            "related_fic_id": n.related_fic_id,
            "email_sent": n.email_sent,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]

    return {"items": items, "total": total, "unread_count": unread_count}


# Returns the count of unread notifications
async def get_unread_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.is_read == False  # noqa: E712
        )
    )

    return result.scalar()


# Marks a single notification as read
async def mark_read(db: AsyncSession, notification_id: int) -> dict:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()

    if notification is None:
        raise ValueError("Notification not found")

    notification.is_read = True
    await db.flush()

    return {"success": True}


# Marks all unread notifications as read
async def mark_all_read(db: AsyncSession) -> dict:
    await db.execute(
        update(Notification)
        .where(Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    await db.flush()

    return {"success": True}


# Deletes a notification by its ID
async def delete_notification(db: AsyncSession, notification_id: int) -> dict:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()

    if notification is None:
        raise ValueError("Notification not found")

    await db.delete(notification)
    await db.flush()

    return {"success": True}


# Retrieves all notification delivery preferences
async def get_preferences(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(NotificationPreference).order_by(NotificationPreference.notification_type)
    )
    preferences = result.scalars().all()

    return [
        {
            "id": p.id,
            "notification_type": p.notification_type,
            "ui_enabled": p.ui_enabled,
            "email_enabled": p.email_enabled,
        }
        for p in preferences
    ]


# Updates the delivery settings for a specific notification type
async def update_preference(
    db: AsyncSession,
    notification_type: str,
    ui_enabled: bool | None = None,
    email_enabled: bool | None = None,
) -> dict:
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.notification_type == notification_type
        )
    )
    pref = result.scalar_one_or_none()

    if pref is None:
        raise ValueError(f"Notification preference not found: {notification_type}")

    if ui_enabled is not None:
        pref.ui_enabled = ui_enabled

    if email_enabled is not None:
        pref.email_enabled = email_enabled

    await db.flush()

    return {
        "notification_type": pref.notification_type,
        "ui_enabled": pref.ui_enabled,
        "email_enabled": pref.email_enabled,
    }
