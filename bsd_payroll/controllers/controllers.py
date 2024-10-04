# -*- coding: utf-8 -*-
# from odoo import http
# from odoo.http import request, route

# class BsdPayroll(http.Controller):
#     @route('/bsd_payroll/bsd_payroll/download_excel', type='http', auth='user')
#     def download_excel(self, **post):
#         result = request.env['bsd.posting'].sudo().action_teller()
#         return request.env['ir.http'].send_file(result['url'])
#     @http.route('/bsd_payroll/bsd_payroll', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bsd_payroll/bsd_payroll/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bsd_payroll.listing', {
#             'root': '/bsd_payroll/bsd_payroll',
#             'objects': http.request.env['bsd_payroll.bsd_payroll'].search([]),
#         })

#     @http.route('/bsd_payroll/bsd_payroll/objects/<model("bsd_payroll.bsd_payroll"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bsd_payroll.object', {
#             'object': obj
#         })
