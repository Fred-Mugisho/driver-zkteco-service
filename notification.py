from config import config
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def format_html_message(message: str, subject: str) -> str:
    """
    Formate un message texte en HTML avec un style professionnel

    Args:
        message: Message en texte brut
        subject: Sujet de l'email (pour déterminer le style)

    Returns:
        Message formaté en HTML
    """
    # Déterminer le type d'alerte (erreur, warning, info)
    if "Échec" in subject or "Erreur" in subject or "échec" in message.lower():
        alert_color = "#dc3545"  # Rouge
        alert_icon = "⚠️"
        alert_type = "ALERTE"
    elif "Warning" in subject or "Attention" in subject:
        alert_color = "#ffc107"  # Jaune
        alert_icon = "⚡"
        alert_type = "ATTENTION"
    else:
        alert_color = "#28a745"  # Vert
        alert_icon = "✓"
        alert_type = "INFO"

    # Convertir les sauts de ligne en <br> et extraire les informations
    lines = message.strip().split('\n')
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Si la ligne contient un ":", la formater comme un champ clé-valeur
        if ':' in line and not line.startswith('http'):
            parts = line.split(':', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            formatted_lines.append(f'<tr><td style="padding: 8px; font-weight: bold; color: #555;">{key}:</td><td style="padding: 8px; color: #333;">{value}</td></tr>')
        else:
            formatted_lines.append(f'<tr><td colspan="2" style="padding: 8px; color: #333;">{line}</td></tr>')

    html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- En-tête -->
                    <tr>
                        <td style="background-color: {alert_color}; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px;">
                                {alert_icon} {alert_type}
                            </h1>
                        </td>
                    </tr>

                    <!-- Sujet -->
                    <tr>
                        <td style="padding: 20px; background-color: #f8f9fa;">
                            <h2 style="margin: 0; color: #333; font-size: 18px; text-align: center;">
                                {subject}
                            </h2>
                        </td>
                    </tr>

                    <!-- Corps du message -->
                    <tr>
                        <td style="padding: 20px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                {''.join(formatted_lines)}
                            </table>
                        </td>
                    </tr>

                    <!-- Pied de page -->
                    <tr>
                        <td style="padding: 20px; background-color: #f8f9fa; text-align: center; border-radius: 0 0 8px 8px; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0; color: #6c757d; font-size: 12px;">
                                Service de synchronisation ZKTeco<br>
                                Message automatique - Ne pas répondre
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''
    return html_content


def send_email_notification(subject: str, message: str, html: bool = True):
    """
    Envoie une notification email

    Args:
        subject: Sujet de l'email
        message: Message (texte brut ou HTML)
        html: Si True, le message sera formaté en HTML automatiquement si ce n'est pas déjà du HTML
    """
    try:
        API_ENDPOINT_SEND_MAIL = config.API_ENDPOINT_SEND_MAIL
        if not API_ENDPOINT_SEND_MAIL or API_ENDPOINT_SEND_MAIL == "API_ENDPOINT_SEND_MAIL":
            logger.warning("Aucune API de notification n'a été configurée.")
            return False

        # Filtrer les destinataires valides
        recipients = [r.strip() for r in config.RECEIVERS_EMAILS if r.strip()]

        if not recipients:
            logger.warning("Aucun destinataire valide trouvé.")
            return False

        # Convertir le message en HTML si nécessaire
        if html and not message.strip().startswith('<'):
            message = format_html_message(message, subject)

        data = {
            "email_host": config.EMAIL_HOST,
            "email_host_user": config.EMAIL_HOST_USER,
            "email_host_password": config.EMAIL_HOST_PASSWORD,
            "entity": "ZKTECO_SERVICE",
            "subject": subject,
            "message": message,
            "destinateurs": ",".join(recipients),
        }

        logger.debug(f"Envoi email vers {API_ENDPOINT_SEND_MAIL}")
        logger.debug(f"Destinataires: {recipients}")

        response = requests.post(API_ENDPOINT_SEND_MAIL, json=data, timeout=30, verify=False)

        if response.status_code != 200:
            logger.error(f"Erreur API ({response.status_code}): {response.text}")
            return False

        logger.info(f"Email envoyé avec succès à {len(recipients)} destinataire(s)")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur réseau lors de l'envoi de l'email: {e}")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email: {e}")
        return False
    
# Exemple d'utilisation dans le processus de synchronisation
if __name__ == "__main__":
    subject = "Sync ZKTeco"
    message = "Sync ZKTeco"
    send_email_notification(subject, message)