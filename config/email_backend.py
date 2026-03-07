"""
Custom Django email backend using the Forward Email REST API.
https://forwardemail.net/en/email-api
"""
import logging

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

_API_URL = 'https://api.forwardemail.net/v1/emails'


class ForwardEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        api_key = getattr(settings, 'FORWARDEMAIL_API_KEY', '')
        if not api_key:
            logger.error('ForwardEmailBackend: FORWARDEMAIL_API_KEY not configured')
            return 0

        sent = 0
        for msg in email_messages:
            try:
                data = {
                    'from': msg.from_email,
                    'to': ', '.join(msg.to),
                    'subject': msg.subject,
                    'text': msg.body,
                }
                if msg.cc:
                    data['cc'] = ', '.join(msg.cc)
                if msg.bcc:
                    data['bcc'] = ', '.join(msg.bcc)
                if msg.reply_to:
                    data['replyTo'] = ', '.join(str(a) for a in msg.reply_to)

                # HTML alternative (EmailMultiAlternatives)
                for content, mimetype in getattr(msg, 'alternatives', []):
                    if mimetype == 'text/html':
                        data['html'] = content
                        break

                resp = requests.post(
                    _API_URL,
                    data=data,
                    auth=(api_key, ''),
                    timeout=15,
                )
                resp.raise_for_status()
                sent += 1
                logger.debug('ForwardEmailBackend: sent to %s (status %s)', msg.to, resp.status_code)

            except requests.HTTPError as exc:
                logger.error(
                    'ForwardEmailBackend: HTTP %s sending to %s — %s',
                    exc.response.status_code, msg.to, exc.response.text,
                )
                if not self.fail_silently:
                    raise
            except Exception as exc:
                logger.exception('ForwardEmailBackend: failed sending to %s: %s', msg.to, exc)
                if not self.fail_silently:
                    raise

        return sent
