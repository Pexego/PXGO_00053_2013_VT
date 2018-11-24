# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, tools


class mood(models.Model):
    _name = 'mood'
    _descrition = 'Moods'

    def _get_image(self):
        for obj in self:
            obj.image_small = tools.image_get_resized_images(obj.image)

    def _set_image(self):
        for obj in self:
            obj.write({'image': tools.image_resize_image_big(obj.image_small)})

    name = fields.Char('Name', size=128, required=True, index=True)
    image = fields.Binary("Image",
                          help="This field contains the image used to \
                                set the mood, limited to 1024x1024px")
    image_small = fields.Binary(compute="_get_image", inverse="_set_image",
                                string="Small-sized image", store=True)
