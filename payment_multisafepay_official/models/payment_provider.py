# Copyright 2024 Eezee-IT (<http://www.eezee-it.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api
from odoo.exceptions import UserError
from multisafepay.client import Client
import logging

from ..const import DEFAULT_VALUES, E_INVOICING_PAYMENT_METHOD


_logger = logging.getLogger(__name__)

AFTERPAY_PAYMENT_METHOD = 'AFTERPAY'
PAY_AFTER_DELIVERY_PAYMENT_METHOD = 'PAYAFTER'


class MultiSafepayPaymentAcquirer(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[("multisafepay", "MultiSafepay")],
        ondelete={"multisafepay": "set default"},
    )
    multisafepay_api_key_test = fields.Char('MultiSafepay test api key', size=40)
    multisafepay_api_key_live = fields.Char('MultiSafepay live api key', size=40)

    @api.onchange('multisafepay_api_key_test')
    def _onchange_multisafepay_api_key_test(self):
        if self.multisafepay_api_key_test and len(self.multisafepay_api_key_test) != 40:
            raise UserError('An API key must be 40 characters long')

    @api.onchange('multisafepay_api_key_live')
    def _onchange_multisafepay_api_key_live(self):
        if self.multisafepay_api_key_live and len(self.multisafepay_api_key_live) != 40:
            raise UserError('An API key must be 40 characters long')

    def pull_merchant_payment_methods(self):
        if self.state == 'disabled' or self.code != 'multisafepay':
            pass

        payment_method_ids = []
        payment_method_obj = self.env['payment.method']
        multisafepay_client = self.get_multisafepay_client()
        payment_methods = multisafepay_client.gateways.allgateways()

        if not payment_methods.get('success', False):
            error_message = payment_methods.get('error_info', 'Request failed')
            raise UserError(error_message)

        for payment_method in self.payment_method_ids:
            payment_methods_ids = list(map(lambda method: method.get('id'), payment_methods.get('data', [])))
            if payment_method.title not in payment_methods_ids:
                self.write({'payment_method_ids': [(3, payment_method.id)]})

        for payment_method in payment_methods.get('data', []):
            existed_method = payment_method_obj.search(
                [('title', '=', payment_method.get('id', '').upper())],
                limit=1)

            if existed_method:
                payment_method_ids.append(existed_method.id)
                continue

            payment_method = payment_method_obj.create_multisafepay_method(
                payment_method.get('id', ''),
                self.env,
                self.code
            )
            payment_method_ids.append(payment_method.id)

        existing_generic_method = payment_method_obj.search(
            [('is_generic_gateway', '=', True)], limit=1)

        if existing_generic_method:
            payment_method_ids.append(existing_generic_method.id)
        else:
            generic_payment_method = payment_method_obj.create_multisafepay_method(
                'GENERIC',
                self.env,
                self.code
            )
            payment_method_ids.append(generic_payment_method.id)

        self.write({'payment_method_ids': payment_method_ids})

        return self.action_view_payment_methods()

    def get_api_key_by_state(self):
        if self.state == 'test':
            return self.multisafepay_api_key_test
        return self.multisafepay_api_key_live

    def get_modus_by_state(self):
        if self.state == 'test':
            return 'TEST'
        return 'LIVE'

    def get_ideal_issuers(self):
        multisafepay_client = self.get_multisafepay_client()
        ideal_issuers = multisafepay_client.ideal_issuers.get()

        if not ideal_issuers.get('success', False):
            return []

        return ideal_issuers.get('data', [])

    def build_order_body(self, data):
        gateway = self.get_gateway(payment_method_id=data['payment_method'])
        website = self.env['website'].search([('id', '=', data['website'])], limit=1) if data['website'] else False
        sale_order = invoice = False
        if data['sale_order_id']:
            sale_order = self.env['sale.order'].sudo().browse(int(data['sale_order_id']))
        if data['invoice_id']:
            invoice = self.env['account.move'].sudo().browse(int(data['invoice_id']))

        currency = self.__check_currency(gateway=gateway, current_currency=data['currency'])
        shopping_cart = self.__get_shopping_cart_with_checkout_options(sale_order, invoice, gateway, data['currency'])
        amount = self.__check_amount(gateway=gateway, current_amount=data['amount'], shopping_cart=shopping_cart)

        order_body = {
            'type': self.__get_order_type(gateway=gateway),
            'order_id': data['order_reference'].split('-')[0],
            'custom_info': {
                'transaction_reference': data['order_reference']
            },
            'currency': currency,
            'amount': round(amount) if isinstance(amount, (int, float)) else amount,
            'gateway': gateway,
            'description': 'Odoo Order Payment',
            'google_analytics': {
                'account': 'UA-XXXXXXXXX',
            },
            'manual': False,
            'gateway_info': {
                'birthday': '1970-07-10',
                'gender': 'female',
                'phone': data['phone'],
                'email': data['email'],
            },
            'payment_options': {
                'notification_url': data['base_url'] + '/payment/multisafepay/notification?type=notification',
                'redirect_url': data['base_url'] + '/payment/multisafepay/notification?type=redirect',
                'cancel_url': data['base_url'] + '/payment/multisafepay/notification?type=cancel',
                'close_window': True
            },
            'customer': {
                'locale': data['lang'],
                'ip_address': data['ip_address'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'address1': data['address'],
                'zip_code': data['zip_code'],
                'city': data['city'],
                'country': data['country'],
                'phone': data['phone'],
                'email': data['email'],
                'referrer': data['base_url'],
                'user_agent': data['user_agent'] if gateway != E_INVOICING_PAYMENT_METHOD else '',
                'house_number': data['address2'] if data['address2'] else '1A',
            },
            'plugin_info': {
                'shop': website.name if website else self.company_id.name,
                'plugin_version': '1.0',
                'shop_version': 'odoo 17.0',
                'shop_root_url': website.domain if website and website.domain else data['base_url'],
            },
        }
        if data['issuer']:
            order_body['gateway_info'] = {
                'issuer_id': data['issuer'],
            }
        return {**order_body, **shopping_cart}

    def get_gateway(self, payment_method_id):
        payment_method = self.env['payment.method'].search([('id', '=', payment_method_id)], limit=1)
        if payment_method.title != 'MultiSafepay':
            return payment_method.title
        return ''

    def __check_currency(self, gateway, current_currency):
        if not DEFAULT_VALUES.get(gateway, {}).get('convert_to_eur', False):
            return current_currency
        return self.env.ref('base.EUR').name

    def __check_amount(self, gateway, current_amount, shopping_cart):
        if not DEFAULT_VALUES.get(gateway, {}).get('convert_to_eur', False):
            return current_amount

        items = shopping_cart.get('shopping_cart', {}).get('items', [])

        amount = 0
        for item in items:
            amount += item.get('quantity', 1.0) * item.get('unit_price', 0.00)
        return amount * 100

    def __check_unit_price(self, gateway, current_currency, current_price):
        if not DEFAULT_VALUES.get(gateway, {}).get('convert_to_eur', False):
            return current_price

        eur = self.env.ref('base.EUR')
        initial_currency = self.env.ref('base.' + current_currency.upper())
        return initial_currency._convert(float(current_price), eur, self.company_id, fields.Date.today(), round=False)

    @staticmethod
    def __get_order_type(gateway):
        if not gateway:
            return 'redirect'
        if DEFAULT_VALUES.get(gateway, {}).get('direct_supported', False):
            return 'direct'
        return 'redirect'

    def __get_shopping_cart_with_checkout_options(self, sale_order, invoice, gateway, current_currency):
        if not sale_order and not invoice:
            return []

        items = []
        alternate = [
            {
                'name': 'none',
                'rules': [
                    {
                        'rate': 0.00,
                    },
                ],
            }
        ]
        lines = sale_order.order_line if sale_order else invoice.invoice_line_ids
        for line in lines:
            quantity = line.product_uom_qty if sale_order else line.quantity
            price_unit = line.price_total / quantity
            # tax_percentage = MultiSafepayPaymentAcquirer.__get_tax_percentage(line, price_unit)
            # tax_table_selector_name = 'TAX' + str(int(tax_percentage * 100)) if tax_percentage != 0 else 'none'
            price_unit = self.__check_unit_price(
                gateway=gateway,
                current_currency=current_currency,
                current_price=price_unit
            )

            items.append({
                'name': line.product_id.name,
                'description': line.name,
                'unit_price': price_unit,
                'quantity': quantity,
                'merchant_item_id': line.product_id.id,
                # 'tax_table_selector': tax_table_selector_name,
                'weight': {
                    'unit': line.product_id.weight_uom_name.upper(),
                    'value': line.product_id.weight,
                }
            })
        return {
            'shopping_cart': {
                'items': items,
            },
            'checkout_options': {
                'tax_tables': {
                    'alternate': alternate,
                },
            },
        }

    def get_multisafepay_client(self):
        multisafepay_client = Client()
        multisafepay_client.set_modus(self.get_modus_by_state())
        multisafepay_client.set_api_key(self.get_api_key_by_state())

        return multisafepay_client
