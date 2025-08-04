# -*- coding: utf-8 -*-
from odoo import models, fields

class MiModuloHolaMundo(models.Model):
    _name = 'mi_modulo_hola_mundo.mensaje'
    _description = 'Mensaje de Hola Mundo'

    name = fields.Char(string='Mensaje', default='Hola Mundo desde Odoo 17!', readonly=True)
    fecha_creacion = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now, readonly=True)
