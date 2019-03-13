# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import winrm,pdb,logging

from openerp import SUPERUSER_ID
#from openerp.osv import orm, fields
from openerp.tools.translate import _
import json

logger = logging.getLogger(__name__)

class cmd_execute_history(models.Model):

    _name = 'cmd_execute.history'
    _order = 'create_date desc'
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
    ps_test_command_line_options=fields.Char(string="Test command line options")

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

    @api.multi        
    def execute(self,vals):
        result={}
        cmd_line=self.ps_command_line
        for param in vals.keys():
            cmd_line += " -%s" % param
            cmd_line += " '%s'" %  vals[param]

        ep=self.endpoints_id    
        url=ep.url
        user=ep.credential_id.user
        passwd=ep.credential_id.decrypt()[0]
        s = winrm.Session(url, auth=(user, passwd),server_cert_validation='ignore' , transport='credssp')
        r = s.run_ps(cmd_line)
        self.env['cmd_execute.history'].create({
                 'command_id': self.id,
                 'cmd_line': cmd_line,
                 'std_out': r.std_out,
                 'std_err':r.std_err
                })

        try:
            result=json.loads(r.std_out.replace('\x07','').replace('\x15',''))
            data_rec=self.env[self.model_id.model].browse(self.env.context['active_id'])
            for return_value in self.return_values_ids:
                if return_value.name in result.keys():
                    data_rec[return_value.field_id.name]=result[return_value.name]
                    if return_value.return_type == 'int' and return_value.factor !=0:
                        data_rec[return_value.field_id.name]=int(result[return_value.name] * return_value.factor)
        except:
            pass
        #pdb.set_trace()
        return result


    @api.multi
    def ps_test_command(self):
        cmd=self.ps_command_line
        if self.ps_test_command_line_options:
            cmd+= " " + self.ps_test_command_line_options
        r=self.endpoints_id.execute(cmd)
        raise exceptions.Warning(r)

    @api.multi
    def execute_custom(self,cmd_line=None,endpoints_id=None):
        endpoints_id.execute(cmd_line)
        pdb.set_trace()


    @api.multi
    def run_command(self,obj,vals=None,debug=False): 
        #context = self.env.context.copy()
        context={}
        context['cmd_execute_object'] = self.id
        action = {
                    'name': self.name,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'cmd.execute.wizard',
                    'context': context,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'domain': [],
                }
        return action

        # return {'name': _('Asset candidates'),'context': context,
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'add_quant_to_site.wizard',
        #     'views': [(model_datas[0].res_id, 'form')],
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        #     }
        # line_

#         return {
#                'name': 'Dispatch Wizard',
#                'view_type': 'form',
#                'view_mode': 'form',
#                'res_model': 'vehicle.dispatch.wizard',
#                'domain': [],
#                'context': self.env.context,
#                'res_id': dispatch_wizard.id,
#                'type': 'ir.actions.act_window',
#                'target': 'new',
# #               'nodestroy': True,
#             }





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
     mandatory=fields.Boolean(help="Parameter required?")

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
    test_cmd=fields.Char(default='$env:computername')

    ps_root_path=fields.Char(help="Root path of the powershell files")

    @api.multi
    def test_endpoint(self):
        r=self.execute(self.test_cmd)
        raise exceptions.Warning(r)

    @api.multi
    def execute(self,cmd_line,debug=False):
        url=self.url
        user=self.credential_id.user
        passwd=self.credential_id.decrypt()[0]
        s = winrm.Session(url, auth=(user, passwd),server_cert_validation='ignore' , transport='credssp')
        r = s.run_ps(cmd_line)
        if r.status_code != 0:
            logger.error("Execute failed: %s" % r.std_err)
            if debug:
                raise exceptions.Warning(r.std_err)
        try:
#            result=json.loads(unicode(r.std_out, errors='replace'),strict=False)
            #result=json.loads(repr(r.std_out).decode('unicode-escape').encode('utf8'),strict=False)
            result=json.loads(r.std_out,strict=False,encoding='ISO-8859-1')
            #result=json.loads(r.std_out,strict=False,encoding='cp1257')
        except:
            logging.error("Error occured during json loads")
            result=r.std_out
        #pdb.set_trace()

        return result

    @api.multi
    def execute_json(self,cmd,debug=False):
        cmd_line=cmd['cmd'] + " "
        for key in cmd['parameters'].keys():
            cmd_line += "-" + key + " " + cmd['parameters'][key] +  " "
        result=self.execute(cmd_line,debug=True)
        if debug:
            pdb.set_trace()

