from odoo import models, fields, api, _
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
import logging
import psycopg2
from datetime import datetime
from dateutil import relativedelta
from urllib.parse import quote

_logger = logging.getLogger(__name__)


class MultiSafepayPaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    multisafepay_order_id = fields.Char(string='Order ID in MultiSafepay')

    def _get_specific_rendering_values(self, values):
        res = super()._get_specific_rendering_values(values)
        if self.provider_code != 'multisafepay':
            return res

        self.ensure_one()

        amount = values.get("amount")
        multisafepay_tx_values = dict(values)
        multisafepay_tx_values.update(
            {
                'tx_url': '/payment/multisafepay/init',
                'sale_order_id': self.sale_order_ids[0].id if self.sale_order_ids else False,
                'invoice_id': self.invoice_ids[0].id if self.invoice_ids else False,
                'order_reference': values.get('reference'),
                'currency': self.currency_id.name,
                'amount': int(round(amount * 100)),
                'lang': self.partner_id and self.partner_id.lang or 'en_US',
                'first_name': self.partner_name,
                'last_name': self.partner_name,
                'address': self.partner_address,
                'address2': self.partner_address,
                'zip_code': self.partner_zip,
                'city': self.partner_city,
                'country': self.partner_country_id and self.partner_country_id.code or "",
                'phone': self.partner_phone,
                'email': self.partner_email,
                'provider_id': self.provider_id.id,
                'payment_method': self.payment_method_id.id,
                'website': values.get('website', False),
                # 'issuer_id': self.env.context.get('issuer', False),
                'base_url': self.get_base_url(),
            }
        )
        return multisafepay_tx_values

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Multisafepay data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if inconsistent data were received
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "multisafepay":
            return tx

        multisafepay_order_id = notification_data.get("transactionid")
        if not multisafepay_order_id:
            error_msg = _("MultiSafepay: received data with missing reference (%s)") % (
                multisafepay_order_id
            )
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        txs = self.search(['|', ('reference', '=', multisafepay_order_id),
                           ('reference', '=like', multisafepay_order_id + '-%')], order="id desc", limit=1)
        if not txs or len(txs) > 1:
            error_msg = "MultiSafepay: received data for reference %s" % (multisafepay_order_id)
            if not txs:
                error_msg += "; no order found"
            else:
                error_msg += "; multiple order found"
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return txs[0]

    def _process_notification_data(self, data):
        """Override of payment to process the transaction based on MultiSafePay data.

        Note: self.ensure_one()

        :param dict data: The feedback data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_notification_data(data)
        if self.provider_code != "multisafepay":
            return
        reference = quote(data.get("transactionid"), safe='')

        multisafepay_client = self.provider_id.get_multisafepay_client()
        order = multisafepay_client.order.get(reference)

        if self.handle_refund_transactions(order):
            return

        if self.state == 'done':
            return True

        if not order.get('success', False):
            error_message = order.get('error_info', 'Request failed')
            _logger.info(error_message)
            self.write({"state_message": error_message})
            self.with_user(SUPERUSER_ID)._set_error("Multisafepay: " + _(error_message))
            return True

        if not order.get('data').get('order_id'):
            self.with_user(SUPERUSER_ID)._set_canceled()
            return True

        order_status = order.get('data').get('status', False)
        self.write({
            'provider_reference': order.get('data').get('transaction_id', 'undefined'),
            'multisafepay_order_id': order.get('data').get('order_id', 'undefined'),
        })

        if order_status in ['void', 'declined', ] and data.get('type') == 'cancel':
            self.with_user(SUPERUSER_ID)._set_canceled()
            return True

        if order_status in ['completed', 'shipped']:
            self.with_user(SUPERUSER_ID)._set_done()
            return True

        if order_status in ['initialized', 'uncleared', ]:
            self.with_user(SUPERUSER_ID)._set_pending()
            return True

        self.with_user(SUPERUSER_ID)._set_error('Transaction status: ' + order_status)
        return True

    def update_order(self):
        if not self.invoice_ids:
            return

        multisafepay_client = self.provider_id.get_multisafepay_client()
        multisafepay_client.order.update(self.multisafepay_order_id, {
            'invoice_id': self.invoice_ids[0].id
        })

    def _cron_update_transaction_state_from_msp(self, client_limit_time, max_days_retry, states_to_process):
        """ Retry to process unconfirmed transactions by checking them in MSP.

        :return: None
        """
        # Let the client confirm transactions so that they remain available in the portal
        client_handling_limit_date = datetime.now() - relativedelta.relativedelta(minutes=client_limit_time)
        # Don't try forever to process a transaction that doesn't go through. Set a retry_limit_date limit
        retry_limit_date = datetime.now() - relativedelta.relativedelta(days=max_days_retry)
        # Retrieve all transactions matching the criteria for post-processing
        txs_to_post_process = self.search([
            ('state', 'in', states_to_process),
            ('last_state_change', '<=', client_handling_limit_date),
            ('last_state_change', '>=', retry_limit_date),
        ])
        for tx in txs_to_post_process:
            try:
                if tx.state in states_to_process:
                    tx.update_tx_from_msp()
                    self.env.cr.commit()
            except psycopg2.OperationalError:
                self.env.cr.rollback()  # Rollback and try later.
            except Exception as e:
                _logger.exception(
                    "encountered an error while processing transaction with reference %s:\n%s",
                    tx.reference, e
                )
                self.env.cr.rollback()

    def update_tx_from_msp(self, order_id=False):
        if self.reference:
            order_id = self.reference.split('-')[0]

        if not order_id:
            return

        txs = self.search(['|', ('reference', '=', order_id), ('reference', '=like', order_id + '-%')])
        if any(t.state == 'done' for t in txs):
            for tx in txs.filtered(lambda record: record.state == 'draft'):
                tx._set_canceled()
        else:
            post = {'transactionid': order_id, 'type': 'notification'}
            self.sudo()._handle_notification_data('multisafepay', post)

            txs.filtered(lambda record: record.state == 'done')._cron_finalize_post_processing()

    def handle_refund_transactions(self, order):
        if order.get('data', {}).get('payment_details', {}).get('type', '') in ['PAYPAL', 'AFTERPAY']:
            costs = order.get('data').get('costs', [])
            if not costs or order.get('data').get('status', False) != 'completed':
                return False
            for cost in costs:
                if cost.get('status', 'void') == 'void':
                    continue
                invoice = self.env['account.move'].sudo().search(
                    [('multisafepay_refund_id', '=', cost.get('transaction_id'))], limit=1)
                if not invoice:
                    continue
                invoice.set_refund_paid()
            return True
        else:
            related_transactions = order.get('data').get('related_transactions', [])
            if not related_transactions:
                return False
            for related_tx in related_transactions:
                if related_tx.get('status', False) == 'completed':
                    invoice = self.env['account.move'].sudo().search(
                        [('multisafepay_refund_id', '=', related_tx.get('transaction_id'))], limit=1)
                    if not invoice:
                        continue
                    invoice.set_refund_paid()
            return True


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def send_to_shipper(self):
        super(StockPicking, self).send_to_shipper()

        order = self.env['sale.order'].sudo().search([('name', 'ilike', self.origin)], limit=1)
        multisafepay_transactions = list(
            filter(lambda tx: tx.provider_code == 'multisafepay', order.transaction_ids))
        if not multisafepay_transactions:
            return

        multisafepay_client = multisafepay_transactions[0].provider_id.get_multisafepay_client()
        for multisafepay_tx in multisafepay_transactions:
            multisafepay_client.order.update(multisafepay_tx.multisafepay_order_id, {
                "status": "shipped",
                "tracktrace_code": self.carrier_tracking_ref,
                "tracktrace_url": self.carrier_tracking_url,
                "ship_date": datetime.now().strftime("%d-%m-%Y"),
                "carrier": self.carrier_id.name,
            })