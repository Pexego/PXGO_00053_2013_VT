using System;
using OpenERPClient;
using System.Collections;
using CookComputing.XmlRpc;

namespace picking_access_example
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
			
			// Obtiene albranes de salida que se hayan cambiado o creado con posterioridad al 01/10/2014
			Object[] domain = new Object[4]; // [('picking_type_id.code', '=', 'outgoing'),'|',('write_date', '=', False),('write_date', '>=', '2014-10-01 00:00:00')]
			domain[0] = new Object[3] {"picking_type_id.code", "=", "outgoing"};
			domain[1] = "|"; // Operador OR
			domain[2] = new Object[3] {"write_date", "=", false};
			domain[3] = new Object[3] {"write_date", ">=", "2014-10-01 00:00:00"}; //%Y-%m-%d %H:%M:%S
			long[] picking_ids = connection.Search("stock.picking", domain);
			Console.WriteLine("Albaranes encontrados: {0}", picking_ids.Length);
			
			XmlRpcStruct context = new XmlRpcStruct();
			context.Add("lang", "es_ES");
			ArrayList fields = new ArrayList();
			fields.Add("name"); // Num. albaran
			fields.Add("partner_id"); // Empresa asociada al albaran
			fields.Add("move_lines"); //Listado de los movimientos del albaran
			fields.Add("state"); // Estado del albarán
			fields.Add("write_date"); // Fecha de última modificación
			fields.Add("create_date"); // Fecha de creación
			XmlRpcStruct[] pickings_data = connection.Read("stock.picking", picking_ids, (string[]) fields.ToArray(typeof(string)));
			foreach(var picking in pickings_data)
			{
				if (picking["write_date"] != null) {
					Console.WriteLine("Albaran: {0} modificado por ultima vez el {1}", picking["name"], picking["write_date"]);
				}
				else {
					Console.WriteLine("Albaran: {0} creado el {1}", picking["name"], picking["create_date"]);
				}
				if (!picking["partner_id"].Equals(false)) {
					XmlRpcStruct[] partner_data = connection.Read("res.partner", new long[] {Convert.ToInt64(((object[]) picking["partner_id"])[0])}, new string[] {"name"}); //Obtenemos el nombre del cliente asociado
					Console.WriteLine("Cliente: {0} || Estado: {1}", partner_data[0]["name"], picking["state"]);
				}
				else {
					Console.WriteLine("Estado: {0}", picking["state"]);	
				}
				
				Console.WriteLine("Movimientos");
				int[] moves = (int[]) picking["move_lines"];
				foreach(var move in moves)
				{
					XmlRpcStruct[] move_data = connection.Read("stock.move", new long[] {(long) move}, new string[] {"product_id", "product_uom_qty"});
					XmlRpcStruct[] product_data = connection.Read("product.product", new long[] {Convert.ToInt64(((object[]) move_data[0]["product_id"])[0])}, new string[] {"default_code", "name"}, context);
					Console.WriteLine("[{0}] {1}, {2} Unidades", product_data[0]["default_code"], product_data[0]["name"], move_data[0]["product_uom_qty"]);	
				}
				
				Console.WriteLine("\n\n");
			}
			
			Console.ReadLine();
		}
	}
}
