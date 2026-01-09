"""
Email Service Module
ماژول ارسال ایمیل
"""
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import aiosmtplib
import os

from app.core.config import settings


class EmailService:
    """
    سرویس ارسال ایمیل
    پشتیبانی از HTML و پیوست‌ها
    """

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.from_name = settings.EMAIL_FROM_NAME
        self.from_address = settings.EMAIL_FROM_ADDRESS or settings.SMTP_USER

    async def send_email(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ارسال ایمیل

        Args:
            to: آدرس گیرنده یا لیست آدرس‌ها
            subject: موضوع
            body: متن ساده
            html: متن HTML (اختیاری)
            cc: Carbon Copy
            bcc: Blind Carbon Copy
            attachments: لیست مسیر فایل‌های پیوست
            reply_to: آدرس پاسخ

        Returns:
            دیکشنری حاوی نتیجه ارسال
        """
        # ایجاد پیام
        if html:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html, 'html', 'utf-8'))
        else:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # تنظیم هدرها
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.from_address}>"

        if isinstance(to, list):
            msg['To'] = ', '.join(to)
            recipients = to
        else:
            msg['To'] = to
            recipients = [to]

        if cc:
            msg['Cc'] = ', '.join(cc)
            recipients.extend(cc)

        if bcc:
            recipients.extend(bcc)

        if reply_to:
            msg['Reply-To'] = reply_to

        # افزودن پیوست‌ها
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    await self._attach_file(msg, file_path)

        # ارسال
        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=self.use_tls,
                recipients=recipients
            )

            return {
                'success': True,
                'recipients': recipients,
                'subject': subject
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'recipients': recipients
            }

    async def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """افزودن پیوست به پیام"""
        filename = os.path.basename(file_path)

        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            msg.attach(part)

    async def send_notification(
        self,
        to: str,
        title: str,
        message: str,
        action_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """ارسال اعلان ایمیلی"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; border-radius: 4px; margin-top: 20px; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{settings.APP_NAME}</h1>
                </div>
                <div class="content">
                    <h2>{title}</h2>
                    <p>{message}</p>
                    {f'<a href="{action_url}" class="button">View Details</a>' if action_url else ''}
                </div>
                <div class="footer">
                    <p>This is an automated message from {settings.APP_NAME}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to=to,
            subject=f"[{settings.APP_NAME}] {title}",
            body=f"{title}\n\n{message}",
            html=html
        )

    async def send_reminder(
        self,
        to: str,
        reminder_title: str,
        reminder_details: str,
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """ارسال یادآوری"""
        due_text = f"\n\nDue Date: {due_date}" if due_date else ""

        return await self.send_notification(
            to=to,
            title=f"Reminder: {reminder_title}",
            message=f"{reminder_details}{due_text}"
        )

    async def send_expiry_alert(
        self,
        to: str,
        document_type: str,
        customer_name: str,
        account_no: str,
        expiry_date: str,
        days_remaining: int
    ) -> Dict[str, Any]:
        """ارسال هشدار انقضا"""
        urgency = "URGENT" if days_remaining <= 7 else "Warning"

        return await self.send_notification(
            to=to,
            title=f"{urgency}: {document_type} Expiring",
            message=f"""
            Document expiry alert:

            Customer: {customer_name}
            Account: {account_no}
            Document: {document_type}
            Expiry Date: {expiry_date}
            Days Remaining: {days_remaining}

            Please take necessary action.
            """
        )

    async def send_personal_notes(
        self,
        to: str,
        notes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """ارسال یادداشت‌های شخصی به ایمیل"""
        notes_html = ""
        notes_text = ""

        for note in notes:
            notes_html += f"""
            <div style="margin-bottom: 15px; padding: 10px; background: white; border-left: 4px solid #2563eb;">
                <strong>{note.get('title', 'Note')}</strong>
                <p>{note.get('content', '')}</p>
                <small style="color: #666;">{note.get('created_at', '')}</small>
            </div>
            """
            notes_text += f"\n---\n{note.get('title', 'Note')}\n{note.get('content', '')}\n"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Personal Notes</h1>
                </div>
                <div class="content">
                    {notes_html}
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to=to,
            subject=f"[{settings.APP_NAME}] Your Personal Notes",
            body=f"Your Personal Notes\n{notes_text}",
            html=html
        )


# Singleton instance
email_service = EmailService()
