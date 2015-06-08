using System;
using OpenERPClient;
using System.Collections;
using CookComputing.XmlRpc;

namespace odoo_production
{
	class MainClass
	{
		public static void Main (string[] args)
		{
			// Datos de conexión
			String Url = "http://localhost:8069";
			String Dbname = "visiotech_devel";
			String Login = "admin";
			String Password = "admin";

			// Login
			OpenERPConnect connection = new OpenERPConnect(Url, Dbname, Login, Password);
			connection.Login();
			Console.WriteLine(connection.UserId);

			Object[] domain = new Object[3];
			domain[0] = "|"; //OR
			domain[1] = new Object[3] {"state", "=", "confirmed"}; //Esperando materias primas
			domain[2] = new Object[3] {"state", "=", "ready"}; //Lista para producir
			long[] production_ids = connection.Search("mrp.production", domain);
			var prods_data = connection.Read("mrp.production", production_ids, new string[] {"state", "move_lines", "move_created_ids", "name", "product_id"});


			foreach(var prod in prods_data)
			{
				Console.WriteLine ("Procesando: {0}", prod ["name"]);
				if ((string) prod ["state"] == "confirmed") {
					connection.Execute("mrp.production", "force_production", new long[] {Convert.ToInt64(((int) prod["id"]))}); //Confirmado -> Listo para producir
				}

				// Recorremos las lineas a consumir y les ponemos nº serie
				int[] moves = (int[]) prod["move_lines"];
				foreach (long move in moves) {
					XmlRpcStruct[] move_data = connection.Read("stock.move", new long[] {(long) move}, new string[] {"product_id"});
					//buscamos si hay un lote ya creado con el código 0001 para el producto del movimiento
					Object[] lot_domain = new Object[2];

					lot_domain[0] = new Object[3] {"product_id", "=", Convert.ToInt64(((object[]) move_data[0]["product_id"])[0])};
					lot_domain[1] = new Object[3] {"name", "=", "0001"};
					long[] lot_ids = connection.Search ("stock.production.lot", lot_domain);
					long lot_id = 0;
					if (lot_ids.Length > 0) {
						lot_id = lot_ids [0];
					}
					else {
						XmlRpcStruct vals = new XmlRpcStruct();
						vals.Add("name", "0001");
						vals.Add("product_id", Convert.ToInt64(((object[]) move_data[0]["product_id"])[0]));
						lot_id = connection.Create("stock.production.lot", vals);
					}
					XmlRpcStruct w_vals = new XmlRpcStruct();
					w_vals.Add("restrict_lot_id", lot_id);
					connection.Write("stock.move", new long[] {(long) move}, w_vals);
				}

				// Recorremos los productos finales y les ponemos nº serie
				int[] final_moves = (int[]) prod["move_created_ids"];
				foreach (long fmove in final_moves) {
					XmlRpcStruct[] fmove_data = connection.Read("stock.move", new long[] {(long) fmove}, new string[] {"product_id"});
					//buscamos si hay un lote ya creado con el código 0001 para el producto del movimiento
					Object[] flot_domain = new Object[2];

					flot_domain[0] = new Object[3] {"product_id", "=", Convert.ToInt64(((object[]) fmove_data[0]["product_id"])[0])};
					flot_domain[1] = new Object[3] {"name", "=", "0001"};
					long[] flot_ids = connection.Search ("stock.production.lot", flot_domain);
					long flot_id = 0;
					if (flot_ids.Length > 0) {
						flot_id = flot_ids [0];
					}
					else {
						XmlRpcStruct fvals = new XmlRpcStruct();
						fvals.Add("name", "0001");
						fvals.Add("product_id", Convert.ToInt64(((object[]) fmove_data[0]["product_id"])[0]));
						flot_id = connection.Create("stock.production.lot", fvals);
					}
					XmlRpcStruct wf_vals = new XmlRpcStruct();
					wf_vals.Add("restrict_lot_id", flot_id);
					connection.Write("stock.move", new long[] {(long) fmove}, wf_vals);
				}

				connection.Execute("mrp.production", "action_production_end", new long[] {Convert.ToInt64(((int) prod["id"]))});
			}
		}
	}
}
