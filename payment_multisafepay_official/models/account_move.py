from odoo import models, fields
from odoo.exceptions import UserError
import logging
import pprint

from ..const import E_INVOICING_PAYMENT_METHOD, PAY_AFTER_DELIVERY_PAYMENT_METHOD

_logger = logging.getLogger(__name__)


class MultiSafepayAccountMove(models.Model):
    _inherit = 'account.move'

    can_be_refund_with_multisafepay = fields.Boolean(compute='_compute_can_be_refund_with_multisafepay')
    multisafepay_refund_id = fields.Char(string='MultiSafepay refund id')
    payment_refund_id = fields.Char(string='Payment refund id')

    def _compute_can_be_refund_with_multisafepay(self):
        for invoice in self:
            invoice.can_be_refund_with_multisafepay = False
            if not invoice.__can_be_refund():
                continue

            multisafepay_tx_ids = invoice.__get_multisafepay_tx_ids()
            if not multisafepay_tx_ids:
                continue

            multisafepay_client = multisafepay_tx_ids[0].provider_id.get_multisafepay_client()
            for multisafepay_tx_id in multisafepay_tx_ids:
                order = multisafepay_client.order.get(multisafepay_tx_id.multisafepay_order_id)

                if not order.get('success', False):
                    continue
                if not self.__multisafepay_tx_can_be_refund(order):
                    continue
                invoice.can_be_refund_with_multisafepay = True
                break

    def refund_with_multisafepay(self):
        self.ensure_one()

        if not self.__can_be_refund():
            return

        multisafepay_tx_ids = self.__get_multisafepay_tx_ids()
        if not multisafepay_tx_ids:
            return

        multisafepay_client = multisafepay_tx_ids[0].provider_id.get_multisafepay_client()
        order = multisafepay_client.order.get(multisafepay_tx_ids[0].multisafepay_order_id)
        _logger.info(pprint.pformat(order))

        if not order.get('success', False):
            return

        if not self.__multisafepay_tx_can_be_refund(order):
            return

        gateway = order.get('data', {}).get('payment_details', {}).get('type', '')

        refund_with_shopping_cart = gateway in ['KLARNA',
                                                'AFTERPAY',
                                                'PAYAFTER',
                                                'EINVOICE', ]
        refund_body = self.__get_refund_body(refund_with_shopping_cart, order)
        _logger.info(refund_body)
        response = multisafepay_client.order.refund(multisafepay_tx_ids[0].multisafepay_order_id, refund_body)
        if not response.get('success', False):
            raise UserError('MultiSafepay response: ' +
                            str(response.get('error_code', '0')) +
                            ' ' +
                            response.get('error_info', 'unknown'))
        self.multisafepay_refund_id = response.get('data').get('refund_id')
        self.create_refund_payment()
        self.payment_state = 'in_payment'
        self.message_post(body='Refund was requested with MultiSafepay')

        if refund_with_shopping_cart:
            order = multisafepay_client.order.get(multisafepay_tx_ids[0].multisafepay_order_id)
            if gateway in [E_INVOICING_PAYMENT_METHOD, PAY_AFTER_DELIVERY_PAYMENT_METHOD]\
                    and order.get('data', {}).get('status', '') == 'void':
                self.set_refund_paid()
                return
            costs = sorted(order.get('data', {}).get('costs', []), key=lambda cost: cost['created'])
            refund_cost = costs[len(costs) - 1]
            self.multisafepay_refund_id = refund_cost['transaction_id']
            if order.get('data', {}).get('status', '') in ['completed', 'refunded']:
                self.set_refund_paid()

    def __can_be_refund(self):
        self.ensure_one()

        if self.move_type != 'out_refund':
            return False
        if self.state != 'posted':
            return False
        if self.payment_state == 'paid' or self.payment_state == 'in_payment':
            return False
        return True

    @staticmethod
    def __multisafepay_tx_can_be_refund(order):
        return order.get('data').get('status') in ['completed', 'shipped', 'partial_refunded'] \
            and order.get('data').get('amount_refunded') < order.get('data').get('amount')

    def __get_multisafepay_tx_ids(self):
        self.ensure_one()

        tx_ids = self.reversed_entry_id.transaction_ids
        if not tx_ids:
            tx_ids = self.env['payment.transaction'].sudo().search(
                [('invoice_ids', 'in', self.reversed_entry_id.id)])
        return list(filter(lambda tx: tx.provider_code == 'multisafepay', tx_ids))

    def set_refund_paid(self):
        self.ensure_one()
        if self.payment_state != 'in_payment':
            return
        payment = self.env['account.payment'].sudo().browse(int(self.payment_refund_id))
        context = self.env.context.copy()
        context.update({'mail_create_nosubscribe': True})
        payment.with_context(context).post()
        self.payment_state = 'paid'
        self.message_post(body='Refund was paid with MultiSafepay')

    def create_refund_payment(self):
        self.ensure_one()
        multisafepay_provider = self.env.ref('payment_multisafepay_official.payment_acquirer_multisafepay')
        if multisafepay_provider:
            journal_id = multisafepay_provider[0].journal_id
        account_payment_register = self.env['account.payment.register'].with_context(active_ids=self.ids,
                                                                                     active_model='account.move')
        payment_obj = account_payment_register.create({
            'journal_id': journal_id.id,
        })
        payment_obj.action_create_payments()

    def __get_refund_body(self, refund_with_shopping_cart, original_order):
        order_currency = original_order.get('data').get('currency', self.currency_id.name)

        if self.ref.find(',') != -1:
            reason = self.ref[self.ref.find(',') + 1:].strip()
        else:
            reason = 'Refund Description'

        if not refund_with_shopping_cart:
            amount = round(self.amount_total * 100)
            if order_currency != self.currency_id.name:
                amount = round(self.currency_id._convert(
                    amount,
                    self.env.ref('base.EUR'),
                    self.company_id,
                    fields.Date.today()
                ))
            return {
                'currency': order_currency,
                'amount': amount,  # depends on invoice amount
                'description': reason,
                'gateway_info': {
                    'extvar11': '00',
                },
            }

        items = self.__get_items_for_refund_with_shopping_cart(original_order, order_currency)
        return {
            'description': reason,
            'checkout_data': {
                'items': items,
            }
        }

    def __get_items_for_refund_with_shopping_cart(self, original_order, order_currency):
        shopping_cart = original_order.get('data', {}).get('shopping_cart', {}).get('items', [])
        if not shopping_cart:
            raise UserError('Cannot refund with MultiSafepay. Empty shopping cart')

        discount_items = list(filter(lambda item: float(item['unit_price']) < 0, shopping_cart))
        if discount_items:
            raise UserError('Cannot refund with MultiSafepay. Discount items in original order')

        items = shopping_cart.copy()

        for invoice_line_id in self.invoice_line_ids:
            merchant_item_id = invoice_line_id.product_id.id
            shopping_cart_items = list(filter(
                lambda item: item.get('merchant_item_id', 0) == merchant_item_id,
                shopping_cart))

            if not shopping_cart_items or len(shopping_cart_items) > 1:
                raise UserError('Cannot refund with MultiSafepay. Invalid shopping cart')

            if invoice_line_id.quantity > shopping_cart_items[0].get('quantity', 0):
                raise UserError('Cannot refund with MultiSafepay. Invalid shopping cart: product quantity')

            unit_price = invoice_line_id.price_unit
            if order_currency != self.currency_id.name:
                unit_price = round(self.currency_id._convert(
                    unit_price,
                    self.env.ref('base.EUR'),
                    self.company_id,
                    fields.Date.today()
                ), 2)

            if unit_price != float(shopping_cart_items[0].get('unit_price', False)):
                raise UserError('Cannot refund with MultiSafepay. Invalid shopping cart: product price')

            refund_item = shopping_cart_items[0].copy()
            if float(refund_item.get('unit_price', -1)) > 0:
                refund_item['unit_price'] = refund_item.get('unit_price') * -1
                refund_item['quantity'] = invoice_line_id.quantity
                items.append(refund_item)

        return items
