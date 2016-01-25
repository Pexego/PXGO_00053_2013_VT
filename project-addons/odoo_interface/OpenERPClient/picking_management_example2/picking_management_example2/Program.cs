using System;
using OpenERPClient;
using System.Collections;
using CookComputing.XmlRpc;

namespace picking_management_example2
{
	class MainClass
	{
		public static void Main (string[] args)
		{
			// Datos de conexión
			String Url = "http://localhost:8069";
			String Dbname = "demo_db";
			String Login = "admin";
			String Password = "admin";

			// Login
			OpenERPConnect connection = new OpenERPConnect(Url, Dbname, Login, Password);
			connection.Login();
			Console.WriteLine(connection.UserId);

			// Tengo un albarán en estado asignado, en concreto el id 280, sobre el que voy a hacer el ejemplo

			ArrayList fields = new ArrayList();
			fields.Add("name"); // Núm. albaran
			fields.Add("partner_id"); // Empresa asociada al albarán
			fields.Add("state"); // Estado del albarán
			fields.Add("internal_notes"); // Notas internas
			fields.Add("move_lines"); // Lineas del albarán
			long[] picking_ids = new long[] {280};
			XmlRpcStruct[] pickings_data = connection.Read("stock.picking", picking_ids, (string[]) fields.ToArray(typeof(string)));
			XmlRpcStruct context = new XmlRpcStruct();
			context.Add("lang", "es_ES");

			foreach(var picking in pickings_data)
			{
				Console.WriteLine("Albaran {0} en estado {1}", picking["name"], picking["state"]);	
				if (!picking["partner_id"].Equals(false)) { // Si tiene una empresa asociada, obtenemos los datos que nos interesan
					Console.WriteLine("- Dirección de envío:");
					XmlRpcStruct[] partner_data = connection.Read("res.partner", new long[] {Convert.ToInt64(((object[]) picking["partner_id"])[0])}, new string[] {"name","street","zip","city","state_id","country_id"}); //Pedimos que nos devuelva los campos que nos interesan
					Console.WriteLine("Nombre cliente: {0}", partner_data[0]["name"]);
					Console.WriteLine("Dirección: {0}", partner_data[0]["street"]);
					Console.WriteLine("Población: {0}", partner_data[0]["city"]);
					Console.WriteLine("Cód. Postal: {0}", partner_data[0]["zip"]);
					if (!partner_data[0]["state_id"].Equals(false)) { // Si tiene provincia
						XmlRpcStruct[] state_data = connection.Read("res.country.state", new long[] {Convert.ToInt64(((object[]) partner_data[0]["state_id"])[0])}, new string[] {"name"}, context);
						Console.WriteLine("Provincia: {0}", state_data[0]["name"]);
					}
					if (!partner_data[0]["country_id"].Equals(false)) { // Si tiene país
						XmlRpcStruct[] country_data = connection.Read("res.country", new long[] {Convert.ToInt64(((object[]) partner_data[0]["country_id"])[0])}, new string[] {"name"}, context);
						Console.WriteLine("País: {0}", country_data[0]["name"]);
					}
				}
				if (!picking["internal_notes"].Equals(false)) {
					Console.WriteLine("Observaciones: {0}", picking["name"]);
				}
				Console.WriteLine("###########################"); // Separación
				Console.WriteLine("###########################"); // Separación

				int[] moves = (int[]) picking["move_lines"];
				foreach(var move in moves)
				{
					XmlRpcStruct[] move_data = connection.Read("stock.move", new long[] {(long) move}, new string[] {"product_id", "product_uom_qty", "availability"});
					XmlRpcStruct[] product_data = connection.Read("product.product", new long[] {Convert.ToInt64(((object[]) move_data[0]["product_id"])[0])}, new string[] {"default_code", "name", "track_outgoing"});
					Console.WriteLine("[{0}] {1}, {2} Unidades pedidas. {3} unidades disponibles. Seriable; {4}", product_data[0]["default_code"], product_data[0]["name"], move_data[0]["product_uom_qty"], move_data[0]["availability"], product_data[0]["track_outgoing"]);

					// Si es seriable hay que crearle numeros de serie
					if (!product_data[0]["track_outgoing"].Equals(false))
					{
						// Nº de número de serie a crear
						int serialNo = Convert.ToInt32(move_data[0]["product_uom_qty"]);
						XmlRpcStruct move_vals = new XmlRpcStruct();
						string lots = "";
						int cont = 1;
						// While hasta que no haya que crear ninguno más
						while (serialNo > 0)
						{
							string serial = cont.ToString("000000");
							if (lots.Equals("")){
								lots = serial;
							} else {
								lots += "," + serial; // Separamos por comas los números de serie
							}
							serialNo--;
							cont++;
						}
						move_vals.Add("lots_text", lots); //Informamos de los número de serie del movimiento a Odoo
						connection.Write("stock.move", new long[] {(long) move}, move_vals);
					}
				}
			}
			// Procesamos el albarán como siempre pero el sistema debió de separarlo en tantas peraciones como números de serie.
			connection.Execute("stock.picking", "action_done", new long[] {280});
		}
	}
}
