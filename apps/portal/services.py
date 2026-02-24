import base64
import hashlib

from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

MAGIC_LINK_SALT = "portal-magic-link"
MAGIC_LINK_MAX_AGE = 900  # 15 minutes

SESSION_KEY = "portal_student_id"

ALLOWED_EMAIL_DOMAINS = [".edu.tr"]


def generate_token(student_id):
    signer = signing.TimestampSigner(salt=MAGIC_LINK_SALT)
    signed = signer.sign(student_id)
    return base64.urlsafe_b64encode(signed.encode()).decode()


def verify_token(token):
    from .models import UsedToken

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if UsedToken.objects.filter(token_hash=token_hash).exists():
        return None

    try:
        signed = base64.urlsafe_b64decode(token.encode()).decode()
    except Exception:
        return None
    signer = signing.TimestampSigner(salt=MAGIC_LINK_SALT)
    try:
        student_id = signer.unsign(signed, max_age=MAGIC_LINK_MAX_AGE)
    except (signing.BadSignature, signing.SignatureExpired):
        return None

    UsedToken.objects.create(token_hash=token_hash)
    return student_id


def send_magic_link(request, student):
    token = generate_token(student.student_id)
    url = request.build_absolute_uri(reverse("portal:magic_login", args=[token]))
    try:
        send_mail(
            subject="Your Attendance Portal Login Link",
            message=f"Hi {student.name},\n\nClick the link below to view your attendance:\n\n{url}\n\nThis link expires in 15 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
        )
        return True
    except Exception:
        return False


def login_student(request, student_id):
    request.session[SESSION_KEY] = student_id


def logout_student(request):
    request.session.pop(SESSION_KEY, None)


def get_logged_in_student_id(request):
    return request.session.get(SESSION_KEY)


def validate_email_domain(email):
    if not email or "@" not in email:
        return False
    domain = email.rsplit("@", 1)[1].lower()
    return any(domain.endswith(allowed) for allowed in ALLOWED_EMAIL_DOMAINS)


def mask_email(email):
    if not email or "@" not in email:
        return ""
    local, domain = email.rsplit("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"
