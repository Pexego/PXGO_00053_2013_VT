/*
    Copyright (c) 2014 Pexego. <http://pexego.es>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

using System;
using OpenERPClient;
using System.Collections;
using CookComputing.XmlRpc;

namespace odoo_interface
{
	
	class MainClass
	{
		public static void Main (string[] args)
		{
			// Datos de conexión
			String Url = "http://localhost:8069";
			String Dbname = "test_db";
			String Login = "admin";
			String Password = "admin";
			
			// Login
			OpenERPConnect connection = new OpenERPConnect(Url, Dbname, Login, Password);
			connection.Login();
			Console.WriteLine(connection.UserId);
			
			// Nos devuelve todos los ids de empresas
			ArrayList filters = new ArrayList();
			long[] partner_ids = connection.Search("res.partner", filters.ToArray());
			ArrayList fields = new ArrayList();
			fields.Add("name");
			
			// Leemos para todos los ids de empresas obtenidos arriba el campo nombre. Read siempre nos devuelve el id y los campos pedidos.
			var partner_data = connection.Read("res.partner", partner_ids, (string[]) fields.ToArray(typeof(string)));
			foreach(var partner in partner_data)
			{
				Console.WriteLine("Partner {0} with Id {1}", partner["name"], partner["id"]);	
			}
			
			//Comprobarmos que no existe un partner con nombre Prueba
			Object[] domain = new Object[1];
			domain[0] = new Object[3] {"name", "=like", "Prueba%"};
			long[] prueba_partner_ids = connection.Search("res.partner", domain);
			if (prueba_partner_ids.Length > 0) {
				// El partner ya existe lo borramos
				Console.WriteLine("Partnes exists");
				bool deleted = connection.Unlink("res.partner", prueba_partner_ids);
				Console.WriteLine("Deleted: {0}", deleted);
			}
			else {
				// El partner no existe lo creamos	
				Console.WriteLine("Partnes not exists");
				XmlRpcStruct vals = new XmlRpcStruct();
				vals.Add("name", "Prueba");
				vals.Add("is_company", true);
				vals.Add("vat", "ES33552390J");
				long new_partner_id = connection.Create("res.partner", vals);
				Console.WriteLine("New Partner created {0}", new_partner_id);
				
				// Le cambiamos el nombre
				XmlRpcStruct vals2 = new XmlRpcStruct();
				vals2.Add("name", "Prueba2");
				long[] ids_to_update = new long[1];
				ids_to_update[0] = new_partner_id;
				bool updated = connection.Write("res.partner", ids_to_update, vals2);
				Console.WriteLine("Updated: {0}", updated);
				
				//Mostramos el nuevo nombre
				var new_partner_data = connection.Read("res.partner", ids_to_update, new string[] {"name"});
				foreach(var partner in new_partner_data)
				{
					Console.WriteLine("Partner {0} with Id {1}", partner["name"], partner["id"]);	
				}
				
				// Como ejemplo del método execute comprobamos si el cif es válido
				var result = connection.Execute ("res.partner", "button_check_vat", ids_to_update);
				Console.WriteLine("VAT valid: {0}", Convert.ToBoolean(result));
			}
			
			
			Console.ReadLine();
		}
	}
}
