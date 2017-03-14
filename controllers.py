# -*- coding: utf-8 -*-
from openerp import http

# class CmdExecute(http.Controller):
#     @http.route('/cmd_execute/cmd_execute/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cmd_execute/cmd_execute/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cmd_execute.listing', {
#             'root': '/cmd_execute/cmd_execute',
#             'objects': http.request.env['cmd_execute.cmd_execute'].search([]),
#         })

#     @http.route('/cmd_execute/cmd_execute/objects/<model("cmd_execute.cmd_execute"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cmd_execute.object', {
#             'object': obj
#         })