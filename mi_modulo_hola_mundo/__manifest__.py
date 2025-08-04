# -*- coding: utf-8 -*-
{
    'name': "Mi Módulo Hola Mundo",
    'summary': """
        Un módulo simple para mostrar "Hola Mundo" en Odoo 17.
    """,
    'description': """
        Este es un módulo de ejemplo básico para demostrar la creación de un módulo en Odoo 17.
        Muestra un mensaje "Hola Mundo" en una nueva entrada de menú.
    """,
    'author': "Tu Nombre",
    'website': "http://www.tudominio.com",
    'category': 'Uncategorized',
    'version': '17.0.1.0.0',
    'depends': ['base'], # 'base' es el módulo mínimo necesario.
    'data': [
        'views/mi_modulo_hola_mundo_views.xml', # Vistas y acción
        'views/menu.xml', # Definición del menú principal
    ],
    'installable': True,
    'application': True, # Esto hace que aparezca en el menú de Aplicaciones.
    'auto_install': False,
    'license': 'LGPL-3',
}
