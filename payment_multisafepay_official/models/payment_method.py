from odoo import models, fields
from odoo import modules
import base64

from ..const import DEFAULT_VALUES


class MultiSafepayPaymentMethod(models.Model):
    _inherit = 'payment.method'

    title = fields.Char(string='Title')
    min_amount = fields.Integer(string='Min order amount (EUR)', default=1)
    max_amount = fields.Integer(string='Max order amount (EUR)', default=100000)
    provider = fields.Char(string='Provider')
    customer_group = fields.Selection([
        ('all', 'All users'),
        ('logged-in', 'Logged in users'),
        ('non-logged-in', 'Non logged in users'),
    ], string='Customer group', default='all')
    is_credit_card = fields.Boolean(string='Is credit card', default=False)

    editable_min_amount = fields.Boolean(string='Can be min amount be edit', default=True)
    editable_max_amount = fields.Boolean(string='Can be max amount be edit', default=True)
    is_generic_gateway = fields.Boolean(string='Is generic gateway', default=False)
    requires_shopping_cart = fields.Boolean(string='Does this gateway require a shopping cart', default=False)

    @staticmethod
    def create_multisafepay_method(payment_method_id, env, provider):
        if not payment_method_id:
            return
        path = modules.get_module_resource(
            'payment_multisafepay_official',
            'static/src/img/payment_methods',
            payment_method_id + '.png'
        )
        if not path:
            path = modules.get_module_resource(
                'payment_multisafepay_official',
                'static/src/img/payment_methods',
                'MultiSafepay.png'
            )

        with open(path, 'rb') as file:
            image = base64.b64encode(file.read())

        payment_method_deafult_value = DEFAULT_VALUES.get(payment_method_id, {})
        country_codes = payment_method_deafult_value.get('countries', ())
        countries = [env.ref('base.' + country.lower()).id for country in country_codes]

        min_amount = 1
        if payment_method_deafult_value.get('min_amount', False):
            min_amount = payment_method_deafult_value.get('min_amount')

        max_amount = 100000
        if payment_method_deafult_value.get('max_amount', False):
            max_amount = payment_method_deafult_value.get('max_amount')

        name = payment_method_id
        if payment_method_deafult_value.get('name', False):
            name = payment_method_deafult_value.get('name')

        payment_method = env['payment.method'].create(vals_list={
            'name': name,
            'code': payment_method_id,
            'title': payment_method_id.upper(),
            'provider': provider,
            'is_credit_card': payment_method_deafult_value.get('is_credit_card', False),
            'is_generic_gateway': payment_method_deafult_value.get('is_generic_gateway', False),
            'requires_shopping_cart': payment_method_deafult_value.get('requires_shopping_cart', False),
            'image': image,
            'supported_country_ids': countries,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'editable_min_amount': False if payment_method_deafult_value.get('min_amount', False) else True,
            'editable_max_amount': False if payment_method_deafult_value.get('max_amount', False) else True,
        })

        return payment_method
