using System;
using OpenERPClient;
using CookComputing.XmlRpc;

namespace register_picking_incidence
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
			
			Object[] domain = new Object[3]; // Albaranes de salida ya asignados y sin incidencias
			domain[0] = new Object[3] {"picking_type_id.code", "=", "outgoing"};
			domain[1] = new Object[3] {"state", "=", "assigned"};
			domain[2] = new Object[3] {"with_incidences", "=", false};
			long[] picking_ids = connection.Search("stock.picking", domain);
			Console.WriteLine("Albaranes encontrados: {0}", picking_ids.Length);
			
			//Los recorremos y les escribimos a todos la misma incidencia
			foreach(long picking_id in picking_ids)
			{
				XmlRpcStruct vals = new XmlRpcStruct();
				vals.Add("with_incidences", true); //Lo marcamos como bajo incidencia
				connection.Write("stock.picking", new long[] {picking_id}, vals);
				
				//Escribimos el motivo de la incidencia
				connection.MessagePost("stock.picking", new long[] {picking_id}, "Stock Incorrecto");
			}
			
			Console.ReadLine();
		}
	}
}
