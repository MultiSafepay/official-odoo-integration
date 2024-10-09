IDEAL_PAYMENT_METHOD = 'IDEAL'
SOFORT_PAYMENT_METHOD = 'DIRECTBANK'
PAYPAL_PAYMENT_METHOD = 'PAYPAL'
BELFIUS_PAYMENT_METHOD = 'BELFIUS'
ING_HOME_PAYMENT_METHOD = 'INGHOME'
KBC_PAYMENT_METHOD = 'KBC'
ALIPAY_PAYMENT_METHOD = 'ALIPAY'
BETAAPLAN_PAYMENT_METHOD = 'SANTANDER'
DBRTP_PAYMENT_METHOD = 'DBRTP'
AFTERPAY_PAYMENT_METHOD = 'AFTERPAY'
PAY_AFTER_DELIVERY_PAYMENT_METHOD = 'PAYAFTER'
E_INVOICING_PAYMENT_METHOD = 'EINVOICE'
MAESTRO_PAYMENT_METHOD = 'MAESTRO'
EPS_PAYMENT_METHOD = 'EPS'
GIROPAY_PAYMENT_METHOD = 'GIROPAY'
JCB_PAYMENT_METHOD = 'JCB'
BANKTRANS_PAYMENT_METHOD = 'BANKTRANS'
APPLEPAY_PAYMENT_METHOD = 'APPLEPAY'
BANCONTACT_PAYMENT_METHOD = 'MISTERCASH'
TRUSTLY_PAYMENT_METHOD = 'TRUSTLY'
PAY_IN_ADVANCE_PAYMENT_METHOD = 'PAYINADV'
KLARNA_PAYMENT_METHOD = 'KLARNA'
DIRECT_DEBIT_PAYMENT_METHOD = 'DIRDEB'
MASTERCARD_PAYMENT_METHOD = 'MASTERCARD'
VISA_PAYMENT_METHOD = 'VISA'
AMEX_PAYMENT_METHOD = 'AMEX'
MULTISAFEPAY_PAYMENT_METHOD = 'MultiSafepay'
DOTPAY_PAYMENT_METHOD = 'DOTPAY'
IDEAL_QR_PAYMENT_METHOD = 'IDEALQR'
MCACQ_MS_PAYMENT_METHOD = 'MCACQMS'
GENERIC_PAYMENT_METHOD = 'GENERIC'
IN3_PAYMENT_METHOD = 'IN3'
FIETSENBON_PAYMENT_METHOD = 'FIETSENBON'
PSAFECARD_PAYMENT_METHOD = 'PSAFECARD'
PAYAFTB2B_PAYMENT_METHOD = 'PAYAFTB2B'

DEFAULT_VALUES = {
    KLARNA_PAYMENT_METHOD: {
        'name': 'Klarna - Buy now, pay later',
        'countries': ('NL', 'AT', 'DE',),
        'convert_to_eur': True,
        'direct_supported': False,
    },
    AFTERPAY_PAYMENT_METHOD: {
        'name': 'AfterPay',
        'countries': ('NL', 'BE',),
        'convert_to_eur': True,
        'direct_supported': True,
    },
    # gb
    BANKTRANS_PAYMENT_METHOD: {
        'name': 'Bank transfer',
        'countries': ('AT', 'BE', 'CZ', 'FR', 'DE',  'HU', 'IT', 'NL', 'PL', 'PT', 'ES', ),
        'convert_to_eur': True,
    },
    DBRTP_PAYMENT_METHOD: {
        'name': 'Request to Pay powered by Deutsche Bank',
        'countries': ('AT', 'BE', 'FI', 'DE', 'IT', 'NL', 'ES', ),
        'convert_to_eur': True,
        'min_amount': 1,
        'max_amount': 15000,
        'direct_supported': True,
    },
    BETAAPLAN_PAYMENT_METHOD: {
        'name': 'Santander Consumer Finance | Pay per Month',
        'countries': ('NL',),
        'convert_to_eur': True,
        'min_amount': 250,
        'max_amount': 8000,
        'direct_supported': True,
    },
    E_INVOICING_PAYMENT_METHOD: {
        'name': 'E-Invoicing',
        'countries': ('NL',),
        'convert_to_eur': True,
        'min_amount': 200,
        'max_amount': 300,
    },
    PAY_AFTER_DELIVERY_PAYMENT_METHOD: {
        'name': 'Pay After Delivery',
        'countries': ('NL',),
        'convert_to_eur': True,
        'max_amount': 300,
    },
    MAESTRO_PAYMENT_METHOD: {
        'name': 'Maestro',
        'convert_to_eur': True,
    },
    EPS_PAYMENT_METHOD: {
        'name': 'EPS',
        'convert_to_eur': True,
    },
    GIROPAY_PAYMENT_METHOD: {
        'name': 'Giropay',
        'convert_to_eur': True,
    },
    JCB_PAYMENT_METHOD: {
        'convert_to_eur': True,
    },
    APPLEPAY_PAYMENT_METHOD: {
        'name': 'Apple Pay',
        'convert_to_eur': True,
    },
    BANCONTACT_PAYMENT_METHOD: {
        'name': 'Bancontact',
        'countries': ('BE',),
        'convert_to_eur': True,
    },
    # gb
    TRUSTLY_PAYMENT_METHOD: {
        'name': 'Trustly',
        'countries': ('AT', 'BE', 'BG', 'HR', 'CY', 'GR', 'CZ', 'DK', 'EE', 'FI', 'DE', 'HU',
                      'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'SK', 'SI',
                      'ES', 'SE', ),
        'convert_to_eur': True,
    },
    PAY_IN_ADVANCE_PAYMENT_METHOD: {
        'convert_to_eur': True,
    },
    DIRECT_DEBIT_PAYMENT_METHOD: {
        'name': 'SEPA Direct Debit',
        'convert_to_eur': True,
    },
    VISA_PAYMENT_METHOD: {
        'name': 'Visa',
        'is_credit_card': True,
    },
    MASTERCARD_PAYMENT_METHOD: {
        'name': 'Mastercard',
        'is_credit_card': True,
    },
    AMEX_PAYMENT_METHOD: {
        'name': 'American Express',
        'is_credit_card': True,
    },
    SOFORT_PAYMENT_METHOD: {
        'name': 'SOFORT Banking',
        'countries': ('AT', 'BE', 'DE', 'IT', 'ES', 'CH', 'PL',),
        'convert_to_eur': True,
    },
    IDEAL_QR_PAYMENT_METHOD: {
        'name': 'iDEAL QR',
        'direct_supported': True,
    },
    IDEAL_PAYMENT_METHOD: {
        'name': 'iDEAL',
        'direct_supported': True,
    },
    PAYPAL_PAYMENT_METHOD: {
        'name': 'Paypal',
        'direct_supported': True,
    },
    BELFIUS_PAYMENT_METHOD: {
        'name': 'Belfius',
        'direct_supported': True,
    },
    ING_HOME_PAYMENT_METHOD: {
        'name': 'ING Home\'Pay',
        'direct_supported': True,
    },
    KBC_PAYMENT_METHOD: {
        'name': 'KBC',
        'direct_supported': True,
    },
    ALIPAY_PAYMENT_METHOD: {
        'name': 'Alipay',
        'direct_supported': True,
    },
    IN3_PAYMENT_METHOD: {
        'name': 'in3',
        'convert_to_eur': True,
        'direct_supported': False,
    },
    FIETSENBON_PAYMENT_METHOD: {
        'name': 'Fietsenbon',
        'direct_supported': False,
    },
    PSAFECARD_PAYMENT_METHOD: {
        'name': 'Paysafecard',
        'direct_supported': False,
    },
    DOTPAY_PAYMENT_METHOD: {
        'name': 'Dotpay',
        'direct_supported': False,
    },
    PAYAFTB2B_PAYMENT_METHOD: {
        'name': 'Pay after Delivery B2B',
        'direct_supported': False,
    },
    GENERIC_PAYMENT_METHOD: {
        'name': 'Generic gateway',
        'is_generic_gateway': True,
    },
}
