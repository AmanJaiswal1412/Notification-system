from ..constants import Channel
from .email import EmailProvider
from .webpush import WebPushProvider
from .whatsapp import WhatsAppProvider

PROVIDERS = {
    Channel.WHATSAPP: WhatsAppProvider(),
    Channel.EMAIL: EmailProvider(),
    Channel.PUSH: WebPushProvider(),
}


def get_provider(channel):
    return PROVIDERS[channel]
