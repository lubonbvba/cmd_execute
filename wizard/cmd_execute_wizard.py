# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C):
#        2012-Today Serpent Consulting Services (<http://www.serpentcs.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp.osv import orm
import openerp.tools as tools

from openerp import api,models

from lxml import etree
import pdb

class cmd_execute_wizard(models.TransientModel):
    _name = 'cmd.execute.wizard'

    @api.model
    def fields_view_get(
            self, view_id=None, view_type='form', toolbar=False, submenu=False):
        
        result = super(cmd_execute_wizard, self).fields_view_get()
        context=self.env.context
        #pdb.set_trace()
        #if len(context['active_ids'])>1:
        #    pdb.set_trace()
         #   return {'type': 'ir.actions.act_window_close'}

        if context.get('cmd_execute_object'):
            cmd_object = self.pool['cmd_execute.command']
 #           editing_data = cmd_object.browse(
 #              cr, uid, context.get('cmd_execute_object'), context)
            editing_data = self.env['cmd_execute.command'].browse( context['cmd_execute_object'])
            all_fields = {}
            xml_form = etree.Element('form', {
                'string': tools.ustr(editing_data.name), 'version': '8.0'})
            xml_group = etree.SubElement(xml_form, 'group', {'colspan': '2'})
            etree.SubElement(xml_group, 'label', {
                'string': '', 'colspan': '2'})
            #pdb.set_trace()
            for parameter in editing_data.parameter_ids:
                all_fields[parameter.name] = {
#                    'type': parameter.field_id.ttype or u'char', 
                    'type': u'char', 
                    'string': parameter.name,
                    'size': parameter.field_id.size or 256,
                    'default': '1234'}
                etree.SubElement(xml_group, 'field', {
                    'name': parameter.name, 'nolabel': '0',
                    'attrs': (
                        "{'invisible':[('selection__" +
                        parameter.name  + "','=','remove')]}"),
                    'colspan': '2'}) 
            #pdb.set_trace()                       
            etree.SubElement(
                xml_form, 'separator', {'string': '', 'colspan': '4'})
            xml_group3 = etree.SubElement(xml_form, 'footer', {})
            etree.SubElement(xml_group3, 'button', {
                'string': 'Run', 'icon': "gtk-execute",
                'type': 'object', 'name': "action_run",
                'class': "oe_highlight"})
            etree.SubElement(xml_group3, 'button', {
                'string': 'Close', 'icon': "gtk-close", 'special': 'cancel'})
            root = xml_form.getroottree()
            result['arch'] = etree.tostring(root)
            result['fields'] = all_fields
       
        return result

# class old_cmd_execute_wizard(orm.TransientModel):
# #class cmd_execute_wizard(models.TransientModel):
#     _name = 'cmd.execute.wizard'

#     def fields_view_get(
#             self, cr, uid, view_id=None, view_type='form', context=None,
#             toolbar=False, submenu=False):
# #    @api.multi
# #    def fields_view_get(
# #            self, view_id=None, view_type='form', toolbar=False, submenu=False):
# #        result={}
#         #result = super(cmd_execute_wizard, self).fields_view_get(view_id, view_type, toolbar, submenu)
#         result = super(cmd_execute_wizard, self).fields_view_get(
#             cr, uid, view_id, view_type, context, toolbar, submenu)
#  #       context=self.env.context
#         pdb.set_trace()
#         if context.get('cmd_execute_object'):
#             cmd_object = self.pool['cmd_execute.command']
#             editing_data = cmd_object.browse(
#                cr, uid, context.get('cmd_execute_object'), context)
#         #editing_data = self.env['cmd_execute_object'].browse( context['cmd_execute_object'])
#             all_fields = {}
#             xml_form = etree.Element('form', {
#                 'string': tools.ustr(editing_data.name), 'version': '8.0'})
#             xml_group = etree.SubElement(xml_form, 'group', {'colspan': '2'})
#             etree.SubElement(xml_group, 'label', {
#                 'string': '', 'colspan': '2'})
#             for parameter in editing_data.parameter_ids:
#                 all_fields[parameter.name] = {
#                     'type': parameter.field_id.ttype, 'string': parameter.name,
#                     'size': parameter.field_id.size or 256,
#                     'default': '1234'}
#                 etree.SubElement(xml_group, 'field', {
#                     'name': parameter.name, 'nolabel': '0',
#                     'attrs': (
#                         "{'invisible':[('selection__" +
#                         parameter.name + "','=','remove')]}"),
#                     'colspan': '2'})                
#             etree.SubElement(
#                 xml_form, 'separator', {'string': '', 'colspan': '4'})
#             xml_group3 = etree.SubElement(xml_form, 'footer', {})
#             etree.SubElement(xml_group3, 'button', {
#                 'string': 'Run', 'icon': "gtk-execute",
#                 'type': 'object', 'name': "action_run",
#                 'class': "oe_highlight"})
#             etree.SubElement(xml_group3, 'button', {
#                 'string': 'Close', 'icon': "gtk-close", 'special': 'cancel'})
#             root = xml_form.getroottree()
#             result['arch'] = etree.tostring(root)
#             result['fields'] = all_fields
#         pdb.set_trace()
#         return result



    @api.model
    def default_get(self, fields_list):
        res=super(cmd_execute_wizard,self).default_get(fields_list)
 #       pdb.set_trace()
        for field in fields_list:
            fname=self.env['cmd_execute.parameters'].search([('name','=',field),('command_id','=',self.env.context['cmd_execute_object'])]).field_id.name
            ftype=self.env['cmd_execute.parameters'].search([('name','=',field),('command_id','=',self.env.context['cmd_execute_object'])]).field_id.ttype
 #           fname=self.env['cmd_execute.command'].browse(self.env.context['cmd_execute_object']).parameter_ids.search([('name','=',field)]).field_id.name
 #           ftype=self.env['cmd_execute.command'].browse(self.env.context['cmd_execute_object']).parameter_ids.search([('name','=',field)]).field_id.ttype
            record=self.env[self.env.context['active_model']].browse(self.env.context['active_id'])
            res[field]=''
            #pdb.set_trace()
            if fname:
                if ftype == 'many2one':
                    res[field]=record[fname].display_name
                else:    
                    res[field]=record[fname]

        #pdb.set_trace()
        return res
    @api.model
    def create(self,vals=None):    
    #def create(self, cr, uid, vals, context=None):
        # if context.get('active_model') and context.get('active_ids'):
        #     model_obj = self.pool.get(context.get('active_model'))
        #     dict = {}
        #     for key, val in vals.items():
        #         if key.startswith('selection__'):
        #             split_key = key.split('__', 1)[1]
        #             if val == 'set':
        #                 dict.update({split_key: vals.get(split_key, False)})
        #             elif val == 'remove':
        #                 dict.update({split_key: False})
        #             elif val == 'remove_m2m':
        #                 dict.update({split_key: [
        #                     (3, id) for id in vals.get(
        #                         split_key, False)[0][2]]})
        #             elif val == 'add':
        #                 m2m_list = []
        #                 for m2m_id in vals.get(split_key, False)[0][2]:
        #                     m2m_list.append((4, m2m_id))
        #                 dict.update({split_key: m2m_list})
        #     if dict:
        #         model_obj.write(
        #             cr, uid, context.get('active_ids'), dict, context)
        #pdb.set_trace()
        result = super(cmd_execute_wizard, self).create({})
        command_line=self.env['cmd_execute.command'].browse(self.env.context['cmd_execute_object']).execute(vals)

        return result
    @api.multi    
    def action_run(self):
    #def action_apply(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
