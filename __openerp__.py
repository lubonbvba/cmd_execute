# -*- coding: utf-8 -*-
{
    'name': "cmd_execute",

    'summary': """
        Execute all kinds of commands on remote servers""",

    'description': """
        Execute commands on remote servers
        - Web services
        - Windows commands (WinRM)
        - Powershell commands (WinRM) 
    """,

    'author': "Lubon bvba",
    'website': "http://www.lubon.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.4',

    # any module necessary for this one to work correctly
    'depends': ['base','lubon_credentials'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
        'views/cmd_execute.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}