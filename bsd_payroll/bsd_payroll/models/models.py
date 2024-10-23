# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import requests
import json
import hashlib
import hmac
import time
from dateutil.relativedelta import relativedelta
import xlsxwriter
import os
import base64
import tempfile

class bsdPayroll(models.Model):
    _name = 'bsd.payroll'
    _description = 'BSD Payroll'

    insentif = fields.Float(string="Insentif Tahunan")

class BSDTransport(models.Model):
    _name = 'bsd.transport'
    _description='BSD Transport'

    tanggal = fields.Date(string='Tanggal', required=True)
    km_awal = fields.Integer(string='KM Awal', required=True)
    km_akhir = fields.Integer(string='KM Akhir', required=True)
    jarak = fields.Integer(string='Jarak (KM)', compute="_jarak_km", store=True)

    @api.depends('km_awal', 'km_akhir')
    def _jarak_km(self):
        for record in self:
            _hit_jarak = record.km_akhir - record.km_awal
            if _hit_jarak <= 80:
                record.jarak = _hit_jarak
            else:
                record.jarak = 80

class BSDPosting(models.Model):
    _name = 'bsd.posting'
    _description = 'BSD Posting'

    nama = fields.Char(string='Nama Transaksi', required=True)
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    posting_date = fields.Datetime(required=True, string='Waktu Mulai')

    @api.depends('date_from', 'date_to')
    def action_schedule_posting(self):
        code_model = "env['bsd.posting'].search([('id','=',%s)]).action_posting_gaji()" % (self.id)
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'bsd.posting')], limit=1).id
        self.env['ir.cron'].sudo().create({
            'name': self.nama,
            'model_id': model_id,
            'state': 'code',
            'code': code_model,
            'nextcall': self.posting_date,
            'numbercall': 1,  # Hanya sekali
            'active': True,
        })

    def action_schedule_tht(self):
        code_model = "env['bsd.posting'].search([('id', '=', %s)]).action_tht()" % (self.id)
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'bsd.posting')], limit=1).id
        self.env['ir.cron'].sudo().create({
            'name': self.nama,
            'model_id': model_id,
            'state': 'code',
            'code': code_model,
            'nextcall': self.posting_date,
            'numbercall': 1,  # Hanya sekali
            'active': True,
        })

    def action_schedule_teller(self):
        code_model = "env['bsd.posting'].search([('id', '=', %s)]).action_teller()" % (self.id)
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'bsd.posting')], limit=1).id
        self.env['ir.cron'].sudo().create({
            'name': self.nama,
            'model_id': model_id,
            'state': 'code',
            'code': code_model,
            'nextcall': self.posting_date,
            'numbercall': 1,  # Hanya sekali
            'active': True,
        })

    def action_schedule_nonkas(self):
        code_model = "env['bsd.posting'].search([('id', '=', %s)]).action_nonkas()" % (self.id)
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'bsd.posting')], limit=1).id
        self.env['ir.cron'].sudo().create({
            'name': self.nama,
            'model_id': model_id,
            'state': 'code',
            'code': code_model,
            'nextcall': self.posting_date,
            'numbercall': 1,  # Hanya sekali
            'active': True,
        })
        
    def action_schedule_angsuran(self):
        code_model = "env['bsd.posting'].search([('id', '=', %s)]).action_angsuran()" % (self.id)
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'bsd.posting')], limit=1).id
        self.env['ir.cron'].sudo().create({
            'name': self.nama,
            'model_id': model_id,
            'state': 'code',
            'code': code_model,
            'nextcall': self.posting_date,
            'numbercall': 1,  # Hanya sekali
            'active': True,
        })

    def action_posting_gaji(self):
        client_secret = "b23584024228150612849f806bfae35e1185bfe2"
        api = "https://apimbs.msodc.co.id/los/"
        path = [
                "api/auth",
                "api/tabungan/info",
                "api/trans/setoran/coa",
                "api/trans/penarikan/coa",
                "api/trans/setoran/tab"
            ]

        endpoint = f'{api}{path[0]}'
        endpoint_setoran_coa = f'{api}{path[2]}'

        date_from_ = self.date_from
        date_to_ = self.date_to

        date_from_formatted = fields.Date.from_string(date_from_)
        date_to_formatted = fields.Date.from_string(date_to_)

        domain = [('struct_id', '=', 5),('net_wage','!=',0), ('date_from', '>=', date_from_formatted), ('date_to', '<=', date_to_formatted)]
        get_net_wage_by_periode = self.env['hr.payslip'].search_read(domain, fields=['x_norek', 'net_wage'])

        #Get Net Wage
        def get_net_wage_by_employee(get_net_wage_by_periode):
            net_wage_by_employee = {}
            for payslip in get_net_wage_by_periode:
                norek = payslip.get('x_norek')
                net_wage = payslip.get('net_wage')
                if norek and net_wage:
                    net_wage_str = str(net_wage).rstrip('0').rstrip('.')
                    net_wage_by_employee[norek] = net_wage_str
                    net_wage_int = int(net_wage_str)
                    net_wage_by_employee[norek] = net_wage_int

            return net_wage_by_employee

        # Membuat string JSON untuk data permintaan
        auth = {"username": "sinthadaya_oddo", "password": "sinthadayaoddof@Gfk$7W"}
        json_data = json.dumps(auth)

        # Menghasilkan HMAC-SHA256 dari data JSON menggunakan client_secret
        payload = f"{auth['username']}:{auth['password']}".encode()
        signature = hmac.new(client_secret.encode(), payload, hashlib.sha256).hexdigest()

        # Header untuk permintaan
        headers = {
            "x-signature": signature,
            "Content-Type": "application/json"
        }

        # Melakukan permintaan POST
        response = requests.post(endpoint, data=json_data, headers=headers)

        # # Menampilkan hasil
        print(response.status_code)
        print(response.text)

        # # Mengonversi teks respons ke dalam format JSON
        response_json = json.loads(response.text)

        # Mengambil nilai token dari JSON
        bearer_token = response_json.get('token')

        print("=============================================================")

        # Melakukan permintaan POST Setoran COA
        # Panggil fungsi untuk mendapatkan informasi net wage
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y")
        net_wage_by_employee = get_net_wage_by_employee(get_net_wage_by_periode)
        delay_seconds = 10
        excel_file_name = f"ReportTakeHomePay{timestamp}.xlsx"
        excel_file_path = os.path.join(tempfile.gettempdir(), excel_file_name)
        
        workbook = xlsxwriter.Workbook(excel_file_path)
        worksheet = workbook.add_worksheet()

        # Menulis judul kolom
        header = ["Code", "Message","TransID", "Amount", "Norek", "RekeningName", "SumberNorek"]
        for col, title in enumerate(header):
            worksheet.write(0, col, title)

        # Counter untuk menentukan baris pertama
        row_counter = 0
        for norek, net_wage in net_wage_by_employee.items():
            request_coa = { "no_tabungan":norek,
                            "rek_sumber":"2.201.03",
                            "amount":net_wage
                            }
            json_data_ = json.dumps(request_coa)
            message = f"{request_coa['no_tabungan']}:{request_coa['rek_sumber']}:{request_coa['amount']}".encode()
            signature_ = hmac.new(client_secret.encode(), message, hashlib.sha256).hexdigest()
            headers_nasabah = {
                                "x-signature":signature_,
                                "Content-Type":"application/json",
                                "Authorization":"Bearer " + bearer_token}
            response_2 = requests.post(endpoint_setoran_coa, data=json_data_, headers=headers_nasabah, timeout=35)
            time.sleep(delay_seconds)
            print(response_2.status_code)
            print("-------------------------------------------------------------")
            print(response_2.text)
            print("-------------------------------------------------------------")
            response_json = json.loads(response_2.text)
            row_counter += 1
            worksheet.write(row_counter, 0, response_json["code"])
            worksheet.write(row_counter, 1, response_json["message"])
            worksheet.write(row_counter, 2, response_json["transid"])
            worksheet.write(row_counter, 3, response_json["amount"])
            worksheet.write(row_counter, 4, response_json["rekening"]["norek"])
            worksheet.write(row_counter, 5, response_json["rekening"]["name"])
            worksheet.write(row_counter, 6, response_json["sumber"]["norek"])
        workbook.close()
        print("Posting Selesai!")

        if os.path.exists(excel_file_path):
                # Membaca konten file untuk attachment
            with open(excel_file_path, 'rb') as file:
                file_content = file.read()

                # Mengubah data biner menjadi string base64
            file_content_base64 = base64.b64encode(file_content).decode('utf-8')

                # Membuat attachment di Odoo
            attachment = self.env['ir.attachment'].create({
                    'name': excel_file_name,
                    'type': 'binary',
                    'datas': file_content_base64,
                    'store_fname': excel_file_name,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                })

            user_partner_id = self.env.user.partner_id.id
            message = "File Excel berhasil disimpan."

            self.env['mail.message'].create({
                    'subject': "Notification",
                    'partner_ids': [(4, user_partner_id)],
                    'body': message,
                    'message_type': 'notification',
                })

    def action_download_report(self):
        attachment = self.env['ir.attachment'].search([('res_model', '=', self._name), ('res_id', '=', self.id)], limit=1)
        if attachment:
            file_url = f"/web/content/{attachment.id}?download=true"
            file_url_with_mime = f"{file_url}&mimetype=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            return {
                'type': 'ir.actions.act_url',
                'name': 'Download Excel File',
                'url': file_url_with_mime,
                'target': 'self',
            }
        else:
            raise UserError('No report available for download.')
    @api.depends('date_from', 'date_to')
    def action_post_weekly(self):
        # Informasi autentikasi API
        client_secret = "b23584024228150612849f806bfae35e1185bfe2"
        api = "https://apimbs.msodc.co.id/los/"
        path = [
                "api/auth",
                "api/tabungan/info",
                "api/trans/setoran/coa",
                "api/trans/penarikan/coa",
                "api/trans/setoran/tab"
            ]

        endpoint = f'{api}{path[0]}'
        endpoint_setoran_coa = f'{api}{path[2]}'

        auth = {"username": "sinthadaya_oddo", "password": "sinthadayaoddof@Gfk$7W"}
        json_data = json.dumps(auth)

        # Menghasilkan HMAC-SHA256 dari data JSON menggunakan client_secret
        payload = f"{auth['username']}:{auth['password']}".encode()
        signature = hmac.new(client_secret.encode(), payload, hashlib.sha256).hexdigest()

        # Header untuk permintaan
        headers = {
            "x-signature": signature,
            "Content-Type": "application/json"
        }

        # Melakukan permintaan POST
        response = requests.post(endpoint, data=json_data, headers=headers)

        # Mengonversi teks respons ke dalam format JSON
        response_json = json.loads(response.text)

        # Mengambil nilai token dari JSON
        bearer_token = response_json.get('token')

        print("Proses Posting...")
        print("=============================================================")

        date_from_ = self.date_from
        date_to_ = self.date_to

        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y")

        date_from_formatted = fields.Date.from_string(date_from_)
        date_to_formatted = fields.Date.from_string(date_to_)

        domain_makan = [('struct_id', '=', 4),('net_wage', '!=', '0'), ('date_from', '>=', date_from_formatted), ('date_to', '<=', date_to_formatted)]
        get_net_makan = self.env['hr.payslip'].search_read(domain_makan, fields=['x_rek_makan', 'net_wage'])

        #Get Net Makan
        def get_net_makan_per_employee(get_net_makan):
            net_makan_per_employee = {}
            for record in get_net_makan:
                norek_makan = record.get('x_rek_makan')
                net_wage = record.get('net_wage')
                if norek_makan and net_wage:
                    net_wage_str = str(net_wage).rstrip('0').rstrip('.')
                    net_makan_per_employee[norek_makan] = int(net_wage_str)
            return net_makan_per_employee
        
        delay_seconds = 10
        excel_file_name = f"ReportUangMakan{timestamp}.xlsx"
        excel_file_path = os.path.join(tempfile.gettempdir(), excel_file_name)
        
        workbook = xlsxwriter.Workbook(excel_file_path)
        worksheet = workbook.add_worksheet()

        # Menulis judul kolom
        header = ["Code", "Message","TransID", "Amount", "Norek", "RekeningName", "SumberNorek"]
        for col, title in enumerate(header):
            worksheet.write(0, col, title)

        # Counter untuk menentukan baris pertama
        row_counter = 0
        get_makan = get_net_makan_per_employee(get_net_makan)
        try:
            for norek_makan, net_wage in get_makan.items():
                request_coa = {
                    "no_tabungan": norek_makan,
                    "rek_sumber": "2.201.03",
                    "amount": net_wage
                }
                json_data_ = json.dumps(request_coa)
                message = f"{request_coa['no_tabungan']}:{request_coa['rek_sumber']}:{request_coa['amount']}".encode()
                signature_ = hmac.new(client_secret.encode(), message, hashlib.sha256).hexdigest()
                headers_nasabah = {
                    "x-signature": signature_,
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + bearer_token
                }
                response_2 = requests.post(endpoint_setoran_coa, data=json_data_, headers=headers_nasabah, timeout=35)
                time.sleep(delay_seconds)
                
                print(response_2.status_code)
                print("-------------------------------------------------------------")
                print(response_2.text)
                print("-------------------------------------------------------------")
                
                response_json = response_2.json()
                row_counter += 1
                # Menulis data ke dalam file Excel
                worksheet.write(row_counter, 0, response_json.get("code", ""))
                worksheet.write(row_counter, 1, response_json.get("message", ""))
                worksheet.write(row_counter, 2, response_json.get("transid", ""))
                worksheet.write(row_counter, 3, response_json.get("amount", ""))
                worksheet.write(row_counter, 4, response_json.get("rekening", {}).get("norek", ""))
                worksheet.write(row_counter, 5, response_json.get("rekening", {}).get("name", ""))
                worksheet.write(row_counter, 6, response_json.get("sumber", {}).get("norek", ""))
                
            workbook.close()
            print("Posting Selesai!")

            if os.path.exists(excel_file_path):
                # Membaca konten file untuk attachment
                with open(excel_file_path, 'rb') as file:
                    file_content = file.read()

                # Mengubah data biner menjadi string base64
                file_content_base64 = base64.b64encode(file_content).decode('utf-8')

                # Membuat attachment di Odoo
                attachment = self.env['ir.attachment'].create({
                    'name': excel_file_name,
                    'type': 'binary',
                    'datas': file_content_base64,
                    'store_fname': excel_file_name,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                })

                user_partner_id = self.env.user.partner_id.id
                message = "File Excel berhasil disimpan."

                self.env['mail.message'].create({
                    'subject': "Notification",
                    'partner_ids': [(4, user_partner_id)],
                    'body': message,
                    'message_type': 'notification',
                })

                # Konstruksi URL unduhan file
                file_url = f"/web/content/{attachment.id}?download=true"
                file_url_with_mime = f"{file_url}&mimetype=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                # Tindakan unduhan
                download_action = {
                    'type': 'ir.actions.act_url',
                    'name': 'Download Excel File',
                    'url': file_url_with_mime,
                    'target': 'self',  # Buka di tab yang sama
                }

                return download_action
        except requests.exceptions.ConnectTimeout as e:
            print("Koneksi time out:", e)

    @api.depends('date_from', 'date_to')
    def action_post_transport(self):
        date_from_ = self.date_from
        date_to_ = self.date_to
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y")

        date_from_formatted = fields.Date.from_string(date_from_)
        date_to_formatted = fields.Date.from_string(date_to_)

        domain = [('struct_id', '=', 7), ('net_wage', '!=', '0'), ('date_from', '>=', date_from_formatted), ('date_to', '<=', date_to_formatted)]
        get_net_transport = self.env['hr.payslip'].search_read(domain, fields=['x_rek_makan', 'net_wage'])

        def get_transport_by_employee(get_net_transport):
            net_transport = {}
            for payslip in get_net_transport:
                norek = payslip.get('x_rek_makan')
                net_wage = payslip.get('net_wage')
                if norek and net_wage:
                    net_wage_str = str(net_wage).rstrip('0').rstrip('.')
                    net_transport[norek] = net_wage_str
                    net_wage_int = int(net_wage_str)
                    net_transport[norek] = net_wage_int

            return net_transport

        client_secret = "b23584024228150612849f806bfae35e1185bfe2"
        api = "https://apimbs.msodc.co.id/los/"
        path = [
                "api/auth",
                "api/tabungan/info",
                "api/trans/setoran/coa",
                "api/trans/penarikan/coa",
                "api/trans/setoran/tab"
            ]

        endpoint = f'{api}{path[0]}'
        endpoint_setoran_coa = f'{api}{path[2]}'
        # Membuat string JSON untuk data permintaan
        auth = {"username": "sinthadaya_oddo", "password": "sinthadayaoddof@Gfk$7W"}
        json_data = json.dumps(auth)

        # Menghitung HMAC-SHA256 dari data JSON menggunakan client_secret
        payload = f"{auth['username']}:{auth['password']}".encode()
        signature = hmac.new(client_secret.encode(), payload, hashlib.sha256).hexdigest()

        # Header untuk permintaan
        headers = {
            "x-signature": signature,
            "Content-Type": "application/json"
        }

        # Melakukan permintaan POST
        response = requests.post(endpoint, data=json_data, headers=headers)

        # # Mengonversi teks respons ke dalam format JSON
        response_json = json.loads(response.text)

        # Mengambil nilai token dari JSON
        bearer_token = response_json.get('token')

        print("Proses Posting...")
        print("=============================================================")

        transport = get_transport_by_employee(get_net_transport)
        delay_seconds = 10
        excel_file_name = f"ReportUangTransport{timestamp}.xlsx"
        excel_file_path = os.path.join(tempfile.gettempdir(), excel_file_name)
        
        workbook = xlsxwriter.Workbook(excel_file_path)
        worksheet = workbook.add_worksheet()

        # Menulis judul kolom
        header = ["Code", "Message","TransID", "Amount", "Norek", "RekeningName", "SumberNorek"]
        for col, title in enumerate(header):
            worksheet.write(0, col, title)

        # Counter untuk menentukan baris pertama
        row_counter = 0
        try:
            for norek, net_wage in transport.items():
                request_coa = { "no_tabungan":norek,
                                "rek_sumber":"2.201.03",
                                "amount":net_wage
                                }
                json_data_ = json.dumps(request_coa)
                message = f"{request_coa['no_tabungan']}:{request_coa['rek_sumber']}:{request_coa['amount']}".encode()
                signature_ = hmac.new(client_secret.encode(), message, hashlib.sha256).hexdigest()
                headers_nasabah = {
                                "x-signature": signature_,
                                "Content-Type": "application/json",
                                "Authorization": "Bearer " + bearer_token}
                response_2 = requests.post(endpoint_setoran_coa, data=json_data_, headers=headers_nasabah, timeout=35)
                time.sleep(delay_seconds)
                print(response_2.status_code)
                print("-------------------------------------------------------------")
                print(response_2.text)
                print("-------------------------------------------------------------")
                response_json = json.loads(response_2.text)
                row_counter += 1
                worksheet.write(row_counter, 0, response_json["code"])
                worksheet.write(row_counter, 1, response_json["message"])
                worksheet.write(row_counter, 2, response_json["transid"])
                worksheet.write(row_counter, 3, response_json["amount"])
                worksheet.write(row_counter, 4, response_json["rekening"]["norek"])
                worksheet.write(row_counter, 5, response_json["rekening"]["name"])
                worksheet.write(row_counter, 6, response_json["sumber"]["norek"])
            workbook.close()
            print("Posting Selesai!")

            if os.path.exists(excel_file_path):
                # Membaca konten file untuk attachment
                with open(excel_file_path, 'rb') as file:
                    file_content = file.read()

                # Mengubah data biner menjadi string base64
                file_content_base64 = base64.b64encode(file_content).decode('utf-8')

                # Membuat attachment di Odoo
                attachment = self.env['ir.attachment'].create({
                    'name': excel_file_name,
                    'type': 'binary',
                    'datas': file_content_base64,
                    'store_fname': excel_file_name,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                })

                user_partner_id = self.env.user.partner_id.id
                message = "File Excel berhasil disimpan."

                self.env['mail.message'].create({
                    'subject': "Notification",
                    'partner_ids': [(4, user_partner_id)],
                    'body': message,
                    'message_type': 'notification',
                })

                # Konstruksi URL unduhan file
                file_url = f"/web/content/{attachment.id}?download=true"
                file_url_with_mime = f"{file_url}&mimetype=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                # Tindakan unduhan
                download_action = {
                    'type': 'ir.actions.act_url',
                    'name': 'Download Excel File',
                    'url': file_url_with_mime,
                    'target': 'self',  # Buka di tab yang sama
                }

                return download_action
        except requests.exceptions.ConnectTimeout as e:
            print("Koneksi time out:", e)
    
    @api.depends('date_from', 'date_to')
    def action_post_insentif(self):
        date_from_ = self.date_from
        date_to_ = self.date_to

        date_from_formatted = fields.Date.from_string(date_from_)
        date_to_formatted = fields.Date.from_string(date_to_)

        domain = [('struct_id', '=', 8), ('date_from', '>=', date_from_formatted), ('date_to', '<=', date_to_formatted)]
        get_net_insentif = self.env['hr.payslip'].search_read(domain, fields=['x_norek', 'net_wage'])

        def get_insentif_by_employee(get_net_insentif):
            net_insentif = {}
            for payslip in get_net_insentif:
                norek = payslip.get('x_norek')
                net_wage = payslip.get('net_wage')
                if norek and net_wage:
                    net_wage_str = str(net_wage).rstrip('0').rstrip('.')
                    net_insentif[norek] = net_wage_str
                    net_wage_int = int(net_wage_str)
                    net_insentif[norek] = net_wage_int

            return net_insentif

        # Informasi autentikasi API
        client_secret = "b23584024228150612849f806bfae35e1185bfe2"
        api = "https://apimbs.msodc.co.id/los/"
        path = [
                "api/auth",
                "api/tabungan/info",
                "api/trans/setoran/coa",
                "api/trans/penarikan/coa",
                "api/trans/setoran/tab"
            ]

        endpoint = f'{api}{path[0]}'
        endpoint_setoran_coa = f'{api}{path[2]}'
        # Membuat string JSON untuk data permintaan
        auth = {"username": "sinthadaya_oddo", "password": "sinthadayaoddof@Gfk$7W"}
        json_data = json.dumps(auth)

        # Menghitung HMAC-SHA256 dari data JSON menggunakan client_secret
        payload = f"{auth['username']}:{auth['password']}".encode()
        signature = hmac.new(client_secret.encode(), payload, hashlib.sha256).hexdigest()

        # Header untuk permintaan
        headers = {
            "x-signature": signature,
            "Content-Type": "application/json"
        }

        # Melakukan permintaan POST
        response = requests.post(endpoint, data=json_data, headers=headers)

        # # Mengonversi teks respons ke dalam format JSON
        response_json = json.loads(response.text)

        # Mengambil nilai token dari JSON
        bearer_token = response_json.get('token')

        print("Proses Posting...")
        print("=============================================================")

        insentif = get_insentif_by_employee(get_net_insentif)
        delay_seconds = 10
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y")
        excel_file_name = f"ReportInsentif{timestamp}.xlsx"
        excel_file_path = os.path.join(tempfile.gettempdir(), excel_file_name)
        
        workbook = xlsxwriter.Workbook(excel_file_path)
        worksheet = workbook.add_worksheet()

        # Menulis judul kolom
        header = ["Code", "Message","TransID", "Amount", "Norek", "RekeningName", "SumberNorek"]
        for col, title in enumerate(header):
            worksheet.write(0, col, title)

        # Counter untuk menentukan baris pertama
        row_counter = 0
        try:
            for norek, net_wage in insentif.items():
                request_coa = { "no_tabungan":norek,
                                "rek_sumber":"2.201.03",
                                "amount":net_wage
                                }
                json_data_ = json.dumps(request_coa)
                message = f"{request_coa['no_tabungan']}:{request_coa['rek_sumber']}:{request_coa['amount']}".encode()
                signature_ = hmac.new(client_secret.encode(), message, hashlib.sha256).hexdigest()
                headers_nasabah = {
                                "x-signature": signature_,
                                "Content-Type": "application/json",
                                "Authorization": "Bearer " + bearer_token}
                response_2 = requests.post(endpoint_setoran_coa, data=json_data_, headers=headers_nasabah, timeout=35)
                time.sleep(delay_seconds)
                print(response_2.status_code)
                print("-------------------------------------------------------------")
                print(response_2.text)
                print("-------------------------------------------------------------")
                response_json = json.loads(response_2.text)
                row_counter += 1
                worksheet.write(row_counter, 0, response_json["code"])
                worksheet.write(row_counter, 1, response_json["message"])
                worksheet.write(row_counter, 2, response_json["transid"])
                worksheet.write(row_counter, 3, response_json["amount"])
                worksheet.write(row_counter, 4, response_json["rekening"]["norek"])
                worksheet.write(row_counter, 5, response_json["rekening"]["name"])
                worksheet.write(row_counter, 6, response_json["sumber"]["norek"])
            workbook.close()
            print("Posting Selesai!")

            if os.path.exists(excel_file_path):
                # Membaca konten file untuk attachment
                with open(excel_file_path, 'rb') as file:
                    file_content = file.read()

                # Mengubah data biner menjadi string base64
                file_content_base64 = base64.b64encode(file_content).decode('utf-8')

                # Membuat attachment di Odoo
                attachment = self.env['ir.attachment'].create({
                    'name': excel_file_name,
                    'type': 'binary',
                    'datas': file_content_base64,
                    'store_fname': excel_file_name,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                })

                user_partner_id = self.env.user.partner_id.id
                message = "File Excel berhasil disimpan."

                self.env['mail.message'].create({
                    'subject': "Notification",
                    'partner_ids': [(4, user_partner_id)],
                    'body': message,
                    'message_type': 'notification',
                })

                # Konstruksi URL unduhan file
                file_url = f"/web/content/{attachment.id}?download=true"
                file_url_with_mime = f"{file_url}&mimetype=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                # Tindakan unduhan
                download_action = {
                    'type': 'ir.actions.act_url',
                    'name': 'Download Excel File',
                    'url': file_url_with_mime,
                    'target': 'self',  # Buka di tab yang sama
                }

                return download_action
        except requests.exceptions.ConnectTimeout as e:
            print("Koneksi time out:", e)

    @api.depends('date_from', 'date_to')
    def action_post_thr(self):
        date_from_ = self.date_from
        date_to_ = self.date_to

        date_from_formatted = fields.Date.from_string(date_from_)
        date_to_formatted = fields.Date.from_string(date_to_)

        domain = [('struct_id', '=', 9), ('date_from', '>=', date_from_formatted), ('date_to', '<=', date_to_formatted)]
        get_net_thr = self.env['hr.payslip'].search_read(domain, fields=['x_norek', 'net_wage'])

        def get_net_thr_per_employee(get_net_thr):
            thr = {}
            for record in get_net_thr:
                norek = record.get('x_norek')
                net_thr = record.get('net_wage')
                if norek and net_thr:
                    net_thr_str = str(net_thr).rstrip('0').rstrip('.')
                    thr[norek] = int(net_thr_str)
            return thr
        
        # Informasi autentikasi API
        client_secret = "b23584024228150612849f806bfae35e1185bfe2"
        api = "https://apimbs.msodc.co.id/los/"
        path = [
                "api/auth",
                "api/tabungan/info",
                "api/trans/setoran/coa",
                "api/trans/penarikan/coa",
                "api/trans/setoran/tab"
            ]

        endpoint = f'{api}{path[0]}'
        endpoint_setoran_coa = f'{api}{path[2]}'
        # Membuat string JSON untuk data permintaan
        auth = {"username": "sinthadaya_oddo", "password": "sinthadayaoddof@Gfk$7W"}
        json_data = json.dumps(auth)

        # Menghitung HMAC-SHA256 dari data JSON menggunakan client_secret
        payload = f"{auth['username']}:{auth['password']}".encode()
        signature = hmac.new(client_secret.encode(), payload, hashlib.sha256).hexdigest()

        # Header untuk permintaan
        headers = {
            "x-signature": signature,
            "Content-Type": "application/json"
        }

        # Melakukan permintaan POST
        response = requests.post(endpoint, data=json_data, headers=headers)

        # # Mengonversi teks respons ke dalam format JSON
        response_json = json.loads(response.text)

        # Mengambil nilai token dari JSON
        bearer_token = response_json.get('token')

        print("Proses Posting...")
        print("=============================================================")

        get_thr = get_net_thr_per_employee(get_net_thr)
        delay_seconds = 10

        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y")
        excel_file_name = f"ReportTHR{timestamp}.xlsx"
        excel_file_path = os.path.join(tempfile.gettempdir(), excel_file_name)
        
        workbook = xlsxwriter.Workbook(excel_file_path)
        worksheet = workbook.add_worksheet()

        # Menulis judul kolom
        header = ["Code", "Message","TransID", "Amount", "Norek", "RekeningName", "SumberNorek"]
        for col, title in enumerate(header):
            worksheet.write(0, col, title)

        # Counter untuk menentukan baris pertama
        row_counter = 0
        try:
            for norek, net_thr in get_thr.items():
                request_coa = { "no_tabungan": norek,
                                "rek_sumber":"1.180.99.99",
                                "amount":net_thr
                                }
                json_data_ = json.dumps(request_coa)
                message = f"{request_coa['no_tabungan']}:{request_coa['rek_sumber']}:{request_coa['amount']}".encode()
                signature_ = hmac.new(client_secret.encode(), message, hashlib.sha256).hexdigest()
                headers_nasabah = {
                                "x-signature": signature_,
                                "Content-Type": "application/json",
                                "Authorization": "Bearer " + bearer_token}
                response_2 = requests.post(endpoint_setoran_coa, data=json_data_, headers=headers_nasabah, timeout=35)
                time.sleep(delay_seconds)
                print(response_2.status_code)
                print("-------------------------------------------------------------")
                print(response_2.text)
                print("-------------------------------------------------------------")
                response_json = json.loads(response_2.text)
                row_counter += 1
                worksheet.write(row_counter, 0, response_json["code"])
                worksheet.write(row_counter, 1, response_json["message"])
                worksheet.write(row_counter, 2, response_json["transid"])
                worksheet.write(row_counter, 3, response_json["amount"])
                worksheet.write(row_counter, 4, response_json["rekening"]["norek"])
                worksheet.write(row_counter, 5, response_json["rekening"]["name"])
                worksheet.write(row_counter, 6, response_json["sumber"]["norek"])
            workbook.close()
            print("Posting Selesai!")

            if os.path.exists(excel_file_path):
                # Membaca konten file untuk attachment
                with open(excel_file_path, 'rb') as file:
                    file_content = file.read()

                # Mengubah data biner menjadi string base64
                file_content_base64 = base64.b64encode(file_content).decode('utf-8')

                # Membuat attachment di Odoo
                attachment = self.env['ir.attachment'].create({
                    'name': excel_file_name,
                    'type': 'binary',
                    'datas': file_content_base64,
                    'store_fname': excel_file_name,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                })

                user_partner_id = self.env.user.partner_id.id
                message = "File Excel berhasil disimpan."

                self.env['mail.message'].create({
                    'subject': "Notification",
                    'partner_ids': [(4, user_partner_id)],
                    'body': message,
                    'message_type': 'notification',
                })

                # Konstruksi URL unduhan file
                file_url = f"/web/content/{attachment.id}?download=true"
                file_url_with_mime = f"{file_url}&mimetype=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                # Tindakan unduhan
                download_action = {
                    'type': 'ir.actions.act_url',
                    'name': 'Download Excel File',
                    'url': file_url_with_mime,
                    'target': 'self',  # Buka di tab yang sama
                }

                return download_action
        except requests.exceptions.ConnectTimeout as e:
            print("Koneksi time out:", e)

    def get_tht_by_employee(self):
        domain = [('x_tab_tht', '!=', False)]
        get_tht1 = self.env['hr.contract'].search_read(domain, fields=['x_rek_tht1', 'x_tab_tht'])
        get_tht2 = self.env['hr.contract'].search_read(domain, fields=['x_rek_tht2', 'x_tab_tht2'])
        tht ={}
        def convert_to_int(tab_tht):
            tab_tht_str = str(tab_tht).rstrip('0').rstrip('.')
            return int(tab_tht_str)
        
        for contract in get_tht1:
            no_tht = contract.get('x_rek_tht1')
            tab_tht = contract.get('x_tab_tht')
            if no_tht and tab_tht:
                tab_tht = convert_to_int(tab_tht)
                tht[no_tht] = {
                    'tab_tht': tab_tht
                }

        for contract in get_tht2:
            no_tht = contract.get('x_rek_tht2')
            tab_tht = contract.get('x_tab_tht2')
            if no_tht and tab_tht:
                tab_tht = convert_to_int(tab_tht)
                tht[no_tht] = {
                    'tab_tht': tab_tht
                }

        return tht

    def action_tht(self):
        tht_all = self.get_tht_by_employee()
        client_secret = "b23584024228150612849f806bfae35e1185bfe2"
        api = "https://apimbs.msodc.co.id/los/"
        path = [
            "api/auth",
            "api/tabungan/info",
            "api/trans/setoran/coa",
            "api/trans/penarikan/coa",
            "api/trans/setoran/tab",
            "api/trans/kredit/angsuran-coa"
        ]

        endpoint = f'{api}{path[0]}'
        endpoint_setoran_coa = f'{api}{path[2]}'

        auth = {"username": "sinthadaya_oddo", "password": "sinthadayaoddof@Gfk$7W"}
        json_data = json.dumps(auth)

        payload = f"{auth['username']}:{auth['password']}".encode()
        signature = hmac.new(client_secret.encode(), payload, hashlib.sha256).hexdigest()

        headers = {
            "x-signature": signature,
            "Content-Type": "application/json"
        }

        response = requests.post(endpoint, data=json_data, headers=headers)
        response_json = json.loads(response.text)
        bearer_token = response_json.get('token')

        print('Proses Posting...')

        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y")
        excel_file_name = f"ReportTabTHT{timestamp}.xlsx"
        excel_file_path = os.path.join(tempfile.gettempdir(), excel_file_name)
        
        workbook = xlsxwriter.Workbook(excel_file_path)
        worksheet = workbook.add_worksheet()

        # Menulis judul kolom
        header = ["Code", "Message","TransID", "Amount", "Norek", "RekeningName", "SumberNorek"]
        for col, title in enumerate(header):
            worksheet.write(0, col, title)

        # Counter untuk menentukan baris pertama
        row_counter = 0
        delay_seconds = 10
        for no_tht, tab_tht in tht_all.items():
            tht = tab_tht['tab_tht']
            request_coa = {"no_tabungan": no_tht,
                        "rek_sumber":"2.201.03",
                        "amount":tht
                        }
            json_data_ = json.dumps(request_coa)
            message = f"{request_coa['no_tabungan']}:{request_coa['rek_sumber']}:{request_coa['amount']}".encode()
            signature_ = hmac.new(client_secret.encode(), message, hashlib.sha256).hexdigest()
            headers_nasabah = {
                            "x-signature": signature_,
                            "Content-Type": "application/json",
                            "Authorization": "Bearer " + bearer_token}
            response_2 = requests.post(endpoint_setoran_coa, data=json_data_, headers=headers_nasabah, timeout=35)
            time.sleep(delay_seconds)
            print(response_2.status_code)
            print("-------------------------------------------------------------")
            print(response_2.text)
            print("-------------------------------------------------------------")
            response_json = json.loads(response_2.text)

            # Menulis data ke dalam file Excel
            row_counter += 1
            worksheet.write(row_counter, 0, response_json["code"])
            worksheet.write(row_counter, 1, response_json["message"])
            worksheet.write(row_counter, 2, response_json["transid"])
            worksheet.write(row_counter, 3, response_json["amount"])
            worksheet.write(row_counter, 4, response_json["rekening"]["norek"])
            worksheet.write(row_counter, 5, response_json["rekening"]["name"])
            worksheet.write(row_counter, 6, response_json["sumber"]["norek"])
        workbook.close()
        print("Posting Selesai!")

        if os.path.exists(excel_file_path):
                # Membaca konten file untuk attachment
            with open(excel_file_path, 'rb') as file:
                file_content = file.read()

                # Mengubah data biner menjadi string base64
            file_content_base64 = base64.b64encode(file_content).decode('utf-8')

                # Membuat attachment di Odoo
            attachment = self.env['ir.attachment'].create({
                    'name': excel_file_name,
                    'type': 'binary',
                    'datas': file_content_base64,
                    'store_fname': excel_file_name,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                })

            user_partner_id = self.env.user.partner_id.id
            message = "File Excel berhasil disimpan."

            self.env['mail.message'].create({
                    'subject': "Notification",
                    'partner_ids': [(4, user_partner_id)],
                    'body': message,
                    'message_type': 'notification',
                })

                # Konstruksi URL unduhan file
            file_url = f"/web/content/{attachment.id}?download=true"
            file_url_with_mime = f"{file_url}&mimetype=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                # Tindakan unduhan
            download_action = {
                    'type': 'ir.actions.act_url',
                    'name': 'Download Excel File',
                    'url': file_url_with_mime,
                    'target': 'self',  # Buka di tab yang sama
                }

            return download_action

    def get_teller_by_employee(self):
        domain = [('x_tab_teller', '!=', False)]
        get_teller = self.env['hr.contract'].search_read(domain, fields=['x_norek_teller','x_tab_teller'])
        teller ={}
        for contract in get_teller:
            no_teller = contract.get('x_norek_teller')
            tab_teller = contract.get('x_tab_teller')
            if no_teller and tab_teller:
                tab_teller_str = str(tab_teller).rstrip('0').rstrip('.')
                teller[no_teller] = int(tab_teller_str)

        return teller
    
    def action_teller(self):
        tab_teller = self.get_teller_by_employee()
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y")
        client_secret = "b23584024228150612849f806bfae35e1185bfe2"
        api = "https://apimbs.msodc.co.id/los/"
        path = [
            "api/auth",
            "api/tabungan/info",
            "api/trans/setoran/coa",
            "api/trans/penarikan/coa",
            "api/trans/setoran/tab",
            "api/trans/kredit/angsuran-coa"
        ]

        endpoint = f'{api}{path[0]}'
        endpoint_setoran_coa = f'{api}{path[2]}'

        auth = {"username": "sinthadaya_oddo", "password": "sinthadayaoddof@Gfk$7W"}
        json_data = json.dumps(auth)

        payload = f"{auth['username']}:{auth['password']}".encode()
        signature = hmac.new(client_secret.encode(), payload, hashlib.sha256).hexdigest()

        headers = {
            "x-signature": signature,
            "Content-Type": "application/json"
        }

        response = requests.post(endpoint, data=json_data, headers=headers)
        response_json = json.loads(response.text)
        bearer_token = response_json.get('token')

        print('Proses Posting...')
        excel_file_name = f"ReportTabTeller{timestamp}.xlsx"
        excel_file_path = os.path.join(tempfile.gettempdir(), excel_file_name)
        
        workbook = xlsxwriter.Workbook(excel_file_path)
        worksheet = workbook.add_worksheet()
        
        # Menulis judul kolom
        header = ["Code", "Message", "TransID", "Amount", "Norek", "RekeningName", "SumberNorek"]
        for col, title in enumerate(header):
            worksheet.write(0, col, title)

        row_counter = 0  # Baris pertama setelah header
        delay_seconds = 5
        for no_teller, tab_teller in tab_teller.items():
            request_coa = {
                "no_tabungan": no_teller,
                "rek_sumber": "2.201.03",
                "amount": tab_teller
            }
            json_data_ = json.dumps(request_coa)
            message = f"{request_coa['no_tabungan']}:{request_coa['rek_sumber']}:{request_coa['amount']}".encode()
            signature_ = hmac.new(client_secret.encode(), message, hashlib.sha256).hexdigest()
            headers_nasabah = {
                "x-signature": signature_,
                "Content-Type": "application/json",
                "Authorization": "Bearer " + bearer_token
            }
            response_2 = requests.post(endpoint_setoran_coa, data=json_data_, headers=headers_nasabah, timeout=25)
            time.sleep(delay_seconds)
            
            print(response_2.status_code)
            print("-------------------------------------------------------------")
            print(response_2.text)
            print("-------------------------------------------------------------")
            
            response_json = response_2.json()
            row_counter += 1
            # Menulis data ke dalam file Excel
            worksheet.write(row_counter, 0, response_json.get("code", ""))
            worksheet.write(row_counter, 1, response_json.get("message", ""))
            worksheet.write(row_counter, 2, response_json.get("transid", ""))
            worksheet.write(row_counter, 3, response_json.get("amount", ""))
            worksheet.write(row_counter, 4, response_json.get("rekening", {}).get("norek", ""))
            worksheet.write(row_counter, 5, response_json.get("rekening", {}).get("name", ""))
            worksheet.write(row_counter, 6, response_json.get("sumber", {}).get("norek", ""))

        workbook.close()
        print("Posting Selesai!")

        if os.path.exists(excel_file_path):
            # Membaca konten file untuk attachment
            with open(excel_file_path, 'rb') as file:
                file_content = file.read()

            # Mengubah data biner menjadi string base64
            file_content_base64 = base64.b64encode(file_content).decode('utf-8')

            # Membuat attachment di Odoo
            attachment = self.env['ir.attachment'].create({
                'name': excel_file_name,
                'type': 'binary',
                'datas': file_content_base64,
                'store_fname': excel_file_name,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            user_partner_id = self.env.user.partner_id.id
            message = "File Excel berhasil disimpan."

            self.env['mail.message'].create({
                'subject': "Notification",
                'partner_ids': [(4, user_partner_id)],
                'body': message,
                'message_type': 'notification',
            })

            # Konstruksi URL unduhan file
            file_url = f"/web/content/{attachment.id}?download=true"
            file_url_with_mime = f"{file_url}&mimetype=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            # Tindakan unduhan
            download_action = {
                'type': 'ir.actions.act_url',
                'name': 'Download Excel File',
                'url': file_url_with_mime,
                'target': 'self',  # Buka di tab yang sama
            }

            return download_action
        
    def get_all_angsuran_by_employee(self):
        domain = [('employee_id', '!=', False)]
        get_angsuran1 = self.env['hr.contract'].search_read(domain, fields=['x_no_kredit1', 'x_angsuran_kredit', 'x_bunga1'])
        get_angsuran2 = self.env['hr.contract'].search_read(domain, fields=['x_no_kredit2', 'x_kredit_2', 'x_bunga2'])
        get_angsuran3 = self.env['hr.contract'].search_read(domain, fields=['x_no_kredit3', 'x_kredit_3', 'x_bunga3'])
        get_angsuran4 = self.env['hr.contract'].search_read(domain, fields=['x_no_kredit4', 'x_kredit_4', 'x_bunga4'])
        
        kredit = {}
        
        # Fungsi untuk mengkonversi nominal
        def convert_nominal(pokok, bunga):
            pokok_str = str(pokok).rstrip('0').rstrip('.')
            bunga_str = str(bunga).rstrip('0').rstrip('.')
            pokok_int = int(float(pokok_str))
            bunga_int = int(float(bunga_str))
            return pokok_int, bunga_int

        # Proses angsuran 1
        for contract in get_angsuran1:
            no_kredit = contract.get('x_no_kredit1')
            pokok = contract.get('x_angsuran_kredit')
            bunga = contract.get('x_bunga1')
            if no_kredit and pokok and bunga:
                pokok, bunga = convert_nominal(pokok, bunga)
                kredit[no_kredit] = {
                    'angsuran': pokok,
                    'bunga': bunga
                }

        # Proses angsuran 2
        for contract in get_angsuran2:
            no_kredit = contract.get('x_no_kredit2')
            pokok = contract.get('x_kredit_2')
            bunga = contract.get('x_bunga2')
            if no_kredit and pokok and bunga:
                pokok, bunga = convert_nominal(pokok, bunga)
                kredit[no_kredit] = {
                    'angsuran': pokok,
                    'bunga': bunga
                }

        # Proses angsuran 3
        for contract in get_angsuran3:
            no_kredit = contract.get('x_no_kredit3')
            pokok = contract.get('x_kredit_3')
            bunga = contract.get('x_bunga3')
            if no_kredit and pokok and bunga:
                pokok, bunga = convert_nominal(pokok, bunga)
                kredit[no_kredit] = {
                    'angsuran': pokok,
                    'bunga': bunga
                }

        # Proses angsuran 4
        for contract in get_angsuran4:
            no_kredit = contract.get('x_no_kredit4')
            pokok = contract.get('x_kredit_4')
            bunga = contract.get('x_bunga4')
            if no_kredit and pokok and bunga:
                pokok, bunga = convert_nominal(pokok, bunga)
                kredit[no_kredit] = {
                    'angsuran': pokok,
                    'bunga': bunga
                }

        return kredit

    def action_angsuran(self):
        kredit_all = self.get_all_angsuran_by_employee()
        client_secret = "b23584024228150612849f806bfae35e1185bfe2"
        api = "https://apimbs.msodc.co.id/los/"
        path = [
            "api/auth",
            "api/tabungan/info",
            "api/trans/setoran/coa",
            "api/trans/penarikan/coa",
            "api/trans/setoran/tab",
            "api/trans/kredit/angsuran-coa"
        ]

        endpoint = f'{api}{path[0]}'
        endpoint_angsuran = f'{api}{path[5]}'
        auth = {"username": "sinthadaya_oddo", "password": "sinthadayaoddof@Gfk$7W"}
        json_data = json.dumps(auth)
        payload = f"{auth['username']}:{auth['password']}".encode()
        signature = hmac.new(client_secret.encode(), payload, hashlib.sha256).hexdigest()
        headers = {
            "x-signature": signature,
            "Content-Type": "application/json"
        }

        response = requests.post(endpoint, data=json_data, headers=headers)
        response_json = json.loads(response.text)
        bearer_token = response_json.get('token')

        delay_seconds = 10
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y")
        excel_file_name = f"ReportAngsuran{timestamp}.xlsx"
        excel_file_path = os.path.join(tempfile.gettempdir(), excel_file_name)
        
        workbook = xlsxwriter.Workbook(excel_file_path)
        worksheet = workbook.add_worksheet()

        # Menulis judul kolom
        header = ["Code", "Message","TransID", "No Kredit", "Total"]
        for col, title in enumerate(header):
            worksheet.write(0, col, title)

        # Counter untuk menentukan baris pertama
        row_counter = 0
        for no_kredit, kredit_info in kredit_all.items():
            bunga = kredit_info['bunga']
            pokok = kredit_info['angsuran']
            request_coa = {
                "kantor": "01",
                "no_kredit": no_kredit,
                "pokok": pokok,
                "bunga": bunga,
                "denda": 0,
            }
            json_data_ = json.dumps(request_coa)
            message = f"{request_coa['kantor']}:{request_coa['no_kredit']}:{request_coa['pokok']}:{request_coa['bunga']}:{request_coa['denda']}".encode()
            signature_ = hmac.new(client_secret.encode(), message, hashlib.sha256).hexdigest()
            headers_nasabah = {
                "x-signature": signature_,
                "Content-Type": "application/json",
                "Authorization": "Bearer " + bearer_token
            }
            response_2 = requests.post(endpoint_angsuran, data=json_data_, headers=headers_nasabah, timeout=35)
            time.sleep(delay_seconds)
            print(response_2.status_code)
            print("-------------------------------------------------------------")
            print(response_2.text)
            print("-------------------------------------------------------------")
            response_json = json.loads(response_2.text)
            row_counter += 1
            worksheet.write(row_counter, 0, response_json["code"])
            worksheet.write(row_counter, 1, response_json["message"])
            worksheet.write(row_counter, 2, response_json["transid"])
            worksheet.write(row_counter, 3, response_json["no_kredit"])
            worksheet.write(row_counter, 4, response_json["total"])

        workbook.close()
        print("Posting Angsuran success!!")
        if os.path.exists(excel_file_path):
                # Membaca konten file untuk attachment
            with open(excel_file_path, 'rb') as file:
                file_content = file.read()

                # Mengubah data biner menjadi string base64
            file_content_base64 = base64.b64encode(file_content).decode('utf-8')

                # Membuat attachment di Odoo
            attachment = self.env['ir.attachment'].create({
                    'name': excel_file_name,
                    'type': 'binary',
                    'datas': file_content_base64,
                    'store_fname': excel_file_name,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                })

            user_partner_id = self.env.user.partner_id.id
            message = "File Excel berhasil disimpan."

            self.env['mail.message'].create({
                    'subject': "Notification",
                    'partner_ids': [(4, user_partner_id)],
                    'body': message,
                    'message_type': 'notification',
                })

                # Konstruksi URL unduhan file
            file_url = f"/web/content/{attachment.id}?download=true"
            file_url_with_mime = f"{file_url}&mimetype=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                # Tindakan unduhan
            download_action = {
                    'type': 'ir.actions.act_url',
                    'name': 'Download Excel File',
                    'url': file_url_with_mime,
                    'target': 'self',  # Buka di tab yang sama
                }

            return download_action

    def action_nonkas(self):
        # bulan_ini = datetime.now().month
        # bulan_formatted = f'{int(bulan_ini):02d}'
        date_from_ = self.date_from
        date_to_ = self.date_to

        date_from_formatted = fields.Date.from_string(date_from_)
        date_to_formatted = fields.Date.from_string(date_to_)

        domain = [('date_from', '>=', date_from_formatted), ('date_to', '<=', date_to_formatted)]
        get_ded_kredit1 = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id', 'x_l10n_id_ded_kredit'])
        get_ded_kredit2 = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id', 'x_l10n_id_ded_kredit2'])
        get_ded_kredit3 = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id', 'x_l10n_id_ded_kredit3'])
        get_bpjs = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id', 'x_l10n_id_alw_bpjs'])
        get_pot_bpjs = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id','x_l10n_id_ded_bpjs'])
        get_pph21 = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id','x_l10n_id_alw_pph21'])        
        get_bpjs = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id', 'x_l10n_id_alw_bpjs'])
        get_pot_bpjs = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id','x_l10n_id_ded_bpjs'])
        get_jamsostek = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id', 'x_l10n_id_alw_jamsostek'])
        get_pot_jamsostek = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id','x_l10n_id_ded_jamsostek'])
        get_yadapen = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id','x_l10n_id_alw_yadapen'])
        get_pot_yadapen = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id','x_l10n_id_ded_yadapen'])
        get_lembur = self.env['hr.payroll.report'].search_read(domain, fields=['employee_id','x_l10n_id_alw_lembur'])

        def total_kredit1(get_ded_kredit1):
            total_k = 0
            for record in get_ded_kredit1:
                kredit1 = record.get('x_l10n_id_ded_kredit', 0)
                total_k += kredit1
            return int(total_k)
        nonkas_kredit1 = total_kredit1(get_ded_kredit1)

        def total_kredit2(get_ded_kredit2):
            total_k = 0
            for record in get_ded_kredit2:
                kredit2 = record.get('x_l10n_id_ded_kredit2', 0)
                total_k += kredit2
            return int(total_k)
        nonkas_kredit2 = total_kredit2(get_ded_kredit2)

        def total_kredit3(get_ded_kredit3):
            total_k = 0
            for record in get_ded_kredit3:
                kredit3 = record.get('x_l10n_id_ded_kredit3', 0)
                total_k += kredit3
            return int(total_k)
        nonkas_kredit3 = total_kredit3(get_ded_kredit3)

        def total_pph(get_pph21):
            total_p = 0
            for record in get_pph21:
                pph = record.get('x_l10n_id_alw_pph21', 0)
                total_p += pph
            return int(total_p)
        nonkas_pph21 = total_pph(get_pph21)

        def total_alw_lembur(get_lembur):
            total_lembur = 0
            for record in get_lembur:
                lembur = record.get("x_l10n_id_alw_lembur", 0)
                total_lembur += lembur
            return int(total_lembur)
        nonkas_lembur = total_alw_lembur(get_lembur)

        def total_bpjs(get_bpjs):
            total_b = 0
            for record in get_bpjs:
                bpjs = record.get('x_l10n_id_alw_bpjs', 0)
                total_b += bpjs
            return int(total_b)
        nonkas_bpjs = total_bpjs(get_bpjs)

        def total_pot_bpjs(get_pot_bpjs):
            total_pb = 0
            for record in get_pot_bpjs:
                pot_bpjs = record.get('x_l10n_id_ded_bpjs', 0)
                total_pb += pot_bpjs
            return int(total_pb)

        total_ded_bpjs = total_pot_bpjs(get_pot_bpjs) - total_bpjs(get_bpjs)

        def total_jamsostek(get_jamsostek):
            total = 0
            for record in get_jamsostek:
                jamsostek = record.get('x_l10n_id_alw_jamsostek', 0)
                total += jamsostek
            return int(total)
        nonkas_jamsostek = total_jamsostek(get_jamsostek)

        def total_pot_jamsostek(get_pot_jamsostek):
            total_pj = 0
            for record in get_pot_jamsostek:
                pot_jamsostek = record.get('x_l10n_id_ded_jamsostek', 0)
                total_pj += pot_jamsostek
            return int(total_pj)

        total_ded_jamsostek = total_pot_jamsostek(get_pot_jamsostek) - total_jamsostek(get_jamsostek)

        def total_yadapen(get_yadapen):
            total_y = 0
            for record in get_yadapen:
                yadapen = record.get('x_l10n_id_alw_yadapen', 0)
                total_y += yadapen
            return int(total_y)

        total_yadapen_value = total_yadapen(get_yadapen)

        def total_pot_yadapen(get_pot_yadapen):
            total_py = 0
            for record in get_pot_yadapen:
                pot_yadapen = record.get('x_l10n_id_ded_yadapen', 0)
                total_py += pot_yadapen
            return int(total_py)

        total_ded_yadapen = total_pot_yadapen(get_pot_yadapen) - total_yadapen(get_yadapen)
        
        client_secret = "b23584024228150612849f806bfae35e1185bfe2"
        api = "https://apimbs.msodc.co.id/los/"
        path = [
                "api/auth",
                "api/trans/akuntansi/nonkas"
            ]

        endpoint = f'{api}{path[0]}'
        endpoint_akuntansi_nonkas = f'{api}{path[1]}'

        # Membuat string JSON untuk data permintaan
        auth = {"username": "sinthadaya_oddo", "password": "sinthadayaoddof@Gfk$7W"}
        json_data = json.dumps(auth)

        # Menghasilkan HMAC-SHA256 dari data JSON menggunakan client_secret
        payload = f"{auth['username']}:{auth['password']}".encode()
        signature = hmac.new(client_secret.encode(), payload, hashlib.sha256).hexdigest()

        # Header untuk permintaan
        headers = {
            "x-signature": signature,
            "Content-Type": "application/json"
        }

        # Melakukan permintaan POST
        response = requests.post(endpoint, data=json_data, headers=headers)

        # Menampilkan hasil
        print(response.status_code)
        print(response.text)

        # # Mengonversi teks respons ke dalam format JSON
        response_json = json.loads(response.text)

        # Mengambil nilai token dari JSON
        bearer_token = response_json.get('token')
        # Menampilkan token
        print('Proses Posting...')
        print("=============================================================")
        delay_seconds = 5

        transactions = [
            {"kantor": "01", "perk_debet": "2.201.03", "perk_kredit": "1.200.30.14", "amount": nonkas_kredit1},
            {"kantor": "01", "perk_debet": "2.201.03", "perk_kredit": "1.200.30.14", "amount": nonkas_kredit2},
            {"kantor": "01", "perk_debet": "2.201.03", "perk_kredit": "1.200.30.14", "amount": nonkas_kredit3},
            {"kantor": "01", "perk_debet": "2.201.12", "perk_kredit": "1.200.10.08", "amount": nonkas_pph21},
            {"kantor": "01", "perk_debet": "2.201.18", "perk_kredit": "2.201.03", "amount": nonkas_lembur},
            {"kantor": "01", "perk_debet": "2.201.03", "perk_kredit": "1.200.90.93", "amount": total_ded_bpjs},
            {"kantor": "01", "perk_debet": "2.201.19", "perk_kredit": "1.200.90.93", "amount": nonkas_bpjs},
            {"kantor": "01", "perk_debet": "2.201.03", "perk_kredit": "1.200.90.94", "amount": total_ded_jamsostek},
            {"kantor": "01", "perk_debet": "2.201.20", "perk_kredit": "1.200.90.94", "amount": nonkas_jamsostek},
            {"kantor": "01", "perk_debet": "2.201.03", "perk_kredit": "1.200.90.02.02", "amount": total_yadapen_value},
            {"kantor": "01", "perk_debet": "2.201.16", "perk_kredit": "1.200.90.02.02", "amount": total_ded_yadapen}
        ]

        # Create an Excel file with the responses
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y")
        excel_file_name = f"ReportNonkas{timestamp}.xlsx"
        excel_file_path = os.path.join(tempfile.gettempdir(), excel_file_name)

        workbook = xlsxwriter.Workbook(excel_file_path)
        worksheet = workbook.add_worksheet()

        # Write header
        header = ["Code", "Message", "TransID", "Total"]
        for col, title in enumerate(header):
            worksheet.write(0, col, title)

        row_counter = 0
        for transaction in transactions:
            json_data = json.dumps(transaction)
            message = f"{transaction['kantor']}:{transaction['perk_debet']}:{transaction['perk_kredit']}:{transaction['amount']}".encode()
            signature = hmac.new(client_secret.encode(), message, hashlib.sha256).hexdigest()
            headers = {
                "x-signature": signature,
                "Content-Type": "application/json",
                "Authorization": "Bearer " + bearer_token
            }

            response = requests.post(endpoint_akuntansi_nonkas, data=json_data, headers=headers)
            time.sleep(delay_seconds)
            print(response.status_code)
            print(response.text)
            response_json = json.loads(response.text)

            # Menulis data ke dalam file Excel
            row_counter += 1
            worksheet.write(row_counter, 0, response_json["code"])
            worksheet.write(row_counter, 1, response_json["message"])
            worksheet.write(row_counter, 2, response_json["transid"])
            worksheet.write(row_counter, 3, response_json["total"])

        workbook.close()
        print("Posting Jurnal selesai.")

        if os.path.exists(excel_file_path):
            with open(excel_file_path, 'rb') as file:
                file_content = file.read()

            file_content_base64 = base64.b64encode(file_content).decode('utf-8')

            attachment = self.env['ir.attachment'].create({
                'name': excel_file_name,
                'type': 'binary',
                'datas': file_content_base64,
                'store_fname': excel_file_name,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            user_partner_id = self.env.user.partner_id.id
            message = "File Excel berhasil disimpan."

            self.env['mail.message'].create({
                'subject': "Notification",
                'partner_ids': [(4, user_partner_id)],
                'body': message,
                'message_type': 'notification',
            })
            file_url = f"/web/content/{attachment.id}?download=true"
            file_url_with_mime = f"{file_url}&mimetype=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                # Tindakan unduhan
            download_action = {
                    'type': 'ir.actions.act_url',
                    'name': 'Download Excel File',
                    'url': file_url_with_mime,
                    'target': 'self',  # Buka di tab yang sama
                }

            return download_action
        
    

        