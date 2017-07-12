# -*- coding: utf-8 -*-

from openerp import models, fields, api
import winrm,pdb

from openerp import SUPERUSER_ID
#from openerp.osv import orm, fields
from openerp.tools.translate import _
import json


class cmd_execute_history(models.Model):

    _name = 'cmd_execute.history'
    _order = 'date_create desc'
    name = fields.Char()
    command_id=fields.Many2one('cmd_execute.command')
    cmd_line=fields.Char()
    std_out=fields.Char()
    std_err=fields.Char()


class command(models.Model):

    _name = 'cmd_execute.command'

    name = fields.Char()
    history_ids=fields.One2many('cmd_execute.history','command_id')
    cmd_type = fields.Selection([("ws","Web service"),("wcmd", "Windows command"),("wps","Windows powershell")], required=True)
    endpoints_id=fields.Many2one('cmd_execute.endpoints')
    model_id=fields.Many2one('ir.model', zrequired=True)
    method=fields.Boolean(help="Tick if there is a method cmd_execute_method defined on the model")
    ref_ir_act_window=fields.Many2one(
            'ir.actions.act_window', 'Sidebar Action', readonly=True,
            help="Sidebar action to make this template available on records \
                 of the related document model")
    ref_ir_value =fields.Many2one(
            'ir.values', 'Sidebar Button', readonly=True,
            help="Sidebar button to open the sidebar action")
    parameter_ids=fields.One2many('cmd_execute.parameters',"command_id")
    return_values_ids=fields.One2many('cmd_execute.return_values',"command_id")

    ps_command_line=fields.Char(string="Powershell command line", help="Complete powershell as it will be executed on the server")
    
    def create_action(self, cr, uid, ids, context=None):
        vals = {}
        action_obj = self.pool['ir.actions.act_window']
        ir_values_obj = self.pool['ir.values']
        for data in self.browse(cr, uid, ids, context=context):
            src_obj = data.model_id.model
            button_name = _('Execute CMD (%s)') % data.name
            vals['ref_ir_act_window'] = action_obj.create(
                cr, SUPERUSER_ID,
                {
                    'name': button_name,
                    'type': 'ir.actions.act_window',
                    'res_model': 'cmd.execute.wizard',
                    'src_model': src_obj,
                    'view_type': 'form',
                    'context': "{'cmd_execute_object' : %d}" % (data.id),
                    'view_mode': 'form,tree',
                    'target': 'new',
                    #'auto_refresh': 1,
                },
                context)
            vals['ref_ir_value'] = ir_values_obj.create(
                cr, SUPERUSER_ID,
                {
                    'name': button_name,
                    'model': src_obj,
                    'key2': 'client_action_multi',
                    'value': (
                        "ir.actions.act_window," +
                        str(vals['ref_ir_act_window'])),
                    'object': True,
                },
                context)
        self.write(
            cr, uid, ids,
            {
                'ref_ir_act_window': vals.get('ref_ir_act_window', False),
                'ref_ir_value': vals.get('ref_ir_value', False),
            },
            context)
        return True

    def unlink_action(self, cr, uid, ids, context=None):
        for template in self.browse(cr, uid, ids, context=context):
            try:
                if template.ref_ir_act_window:
                    act_window_obj = self.pool['ir.actions.act_window']
                    act_window_obj.unlink(
                        cr, SUPERUSER_ID, [template.ref_ir_act_window.id],
                        context=context)
                if template.ref_ir_value:
                    ir_values_obj = self.pool['ir.values']
                    ir_values_obj.unlink(
                        cr, SUPERUSER_ID, template.ref_ir_value.id,
                        context=context)
            except:
                raise orm.except_orm(
                    _("Warning"),
                    _("Deletion of the action record failed."))
        return True

    def unlink(self, cr, uid, ids, context=None):
        self.unlink_action(cr, uid, ids, context=context)
        return super(command, self).unlink(cr, uid, ids, context=context)

    @api.multi    
    def run_method(self):
        if hasattr(self.env[self.model_id.model],'cmd_execute_method'):
            self.env[self.model_id.model].cmd_execute_method(self)

    def execute(self,vals):
        result={}
        cmd_line=self.ps_command_line
        for param in vals.keys():
            cmd_line += " -%s" % param
            cmd_line += " '%s'" %  vals[param]
        url=self.endpoints_id.url
        user=self.endpoints_id.credential_id.user
        passwd=self.endpoints_id.credential_id.decrypt()[0]
        s = winrm.Session(url, auth=(user, passwd),server_cert_validation='ignore' , transport='credssp')
        r = s.run_ps(cmd_line)
        try:
            result=json.loads(r.std_out)
            data_rec=self.env[self.model_id.model].browse(self.env.context['active_id'])
            for return_value in self.return_values_ids:
                if return_value.name in result.keys():
                    data_rec[return_value.field_id.name]=result[return_value.name]
                    if return_value.return_type == 'int' and return_value.factor !=0:
                        data_rec[return_value.field_id.name]=int(result[return_value.name] * return_value.factor)
            self.env['cmd_execute.history'].create({
                'command_id': self.id,
                'cmd_line': cmd_line,
                'std_out': r.std_out,
                'std_err':r.std_err
                })

        except:
            pass

        return result
                    

        







class parameters(models.Model):
     _name = 'cmd_execute.parameters'

     name= fields.Char()
     command_id=fields.Many2one('cmd_execute.command')
     sequence=fields.Integer()
     @api.one
     def _get_parent_model(self):
     	self.model_id=self.command_id.model_id.id

     model_id=fields.Integer(calculate=_get_parent_model)
     field_id=fields.Many2one('ir.model.fields',help="Field to use for this parameter")

class return_values(models.Model):
     _name = 'cmd_execute.return_values'

     name= fields.Char()
     command_id=fields.Many2one('cmd_execute.command')
     sequence=fields.Integer()
     return_type=fields.Selection([('int','Integer'),('str','String')])
     factor=fields.Float()

     @api.one
     def _get_parent_model(self):
        self.model_id=self.command_id.model_id.id

     model_id=fields.Integer(calculate=_get_parent_model)
     field_id=fields.Many2one('ir.model.fields',help="Field to use for this parameter")


class endpoints(models.Model):
     _name = 'cmd_execute.endpoints'

     name = fields.Char()
     url=fields.Char()
     cmd_type = fields.Selection( [("ws","Web service"),("wcmd", "Windows command"),("wps","Windows powershell")], required=True)
     credential_id=fields.Many2one('lubon_credentials.credentials',  string='credential' )
     #domain=lambda self: [('model', '=', self._name),('related_id', '=', self.id)],auto_join=True,


     ps_root_path=fields.Char(help="Root path of the powershell files")