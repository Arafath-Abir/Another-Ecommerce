import requests
from django.conf import settings
import json
from django.core.mail import EmailMultiAlternatives

def generate_ssl_commerz_payment(request, order):
    post_body = {}
    post_body['store_id'] = settings.SSL_COMMERZE_STORE_ID
    post_body['total_amount'] = float(order.get_total_cost())
    post_body['trans_id'] = str(order.id)
    post_body['trans_id'] = str(order.id)
    post_body['cus_name'] = f'{order.first_name} {order.last_name}'
    post_body['cus_email'] = order.email
    post_body['marchant_name'] = 'Mallava'
    post_body['currency'] = 'BDT'
    post_body['succes_url'] = request.build_absolute_uri('/shop/payment-success/')
    post_body['fail_url'] = request.build_absolute_uri('/shop/payment-failed/')
    post_body['cancel_url'] = request.build_absolute_uri('/shop/payment-cancelled/')
    response = requests.post(settings.SSL_COMMERZE_PAYMENT_URL, data=post_body)
    return json.loads(response.text)

def send_order_confirmation_email(order):
    subject = f'Order Confirmation - Order #{order.id}'
    message = render_to_string('', {'order': order})
    to = order.email
    email = EmailMultiAlternatives(subject, message, to=[to])
    email.attach_alternative(message, "text/html")
    email.send()