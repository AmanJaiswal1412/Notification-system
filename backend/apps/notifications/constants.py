class Channel:
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PUSH = "push"
    CHOICES = [(WHATSAPP, "WhatsApp"), (EMAIL, "Email"), (PUSH, "Web Push")]
    ALL = [WHATSAPP, EMAIL, PUSH]


class ApprovalStatus:
    DRAFT = "draft"          # only stored locally
    PENDING = "pending"      # submitted to Meta, waiting for review
    APPROVED = "approved"
    REJECTED = "rejected"
    CHOICES = [(s, s.title()) for s in (DRAFT, PENDING, APPROVED, REJECTED)]


class LogStatus:
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"
    CHOICES = [(SENT, "Sent"), (FAILED, "Failed"), (SKIPPED, "Skipped")]
