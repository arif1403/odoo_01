# -*- coding: utf-8 -*-
# from odoo import http


# class BsdPayroll(http.Controller):
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
