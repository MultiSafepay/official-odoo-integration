# -*- coding: utf-8 -*-
{
    'name': 'MultiSafepay payments',

    'description': '''
        Accept, manage and stimulate online sales with MultiSafepay.
        Increase conversion rates with MultiSafepay unique solutions,
        create the perfect checkout experience and the best payment method mix.
        ''',

    'summary': '''E-commerce is part of our DNA''',

    'author': 'MultiSafepay',
    'website': 'http://www.multisafepay.com',

    'license': 'Other OSI approved licence',

    # Categories can be used to filter modules in modules listing
    'category': 'eCommerce',
    'version': '17.0.0.0.4',

    # any module necessary for this one to work correctly
    'depends': ['payment', 'sale', 'delivery', 'stock'],
    'external_dependencies': {'python': ['multisafepay']},

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/payment_views.xml',
        'views/payment_templates.xml',
        'views/account_move_views.xml',
        'data/payment_provider.xml',
        'data/ir_cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images': ['static/description/main.png'],
    'installable': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'application': True,
    'auto_install': False,
}
