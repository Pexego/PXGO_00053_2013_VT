using System;
using OpenERPClient;
using System.Collections;
using CookComputing.XmlRpc;

namespace picking_management_example
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
			
			// Tengo dos albaranes reconocidos en estado Esperando disponibilidad, en concreto son el id 40 y el id 48, que son sobre los que voy a hacer el ejemplo
			// Vstock tendrá que tener guardado en algún sitio el identificador del albarán en Odoo para poder mapearlos. En mi caso el 40 y 48, se pueden cambiar para ver el ejemplo.
			
			//Ejemplo de lectura para estos dos albaranes de los datos de dirección y de los datos de transportista
			ArrayList fields = new ArrayList();
			fields.Add("name"); // Núm. albaran
			fields.Add("partner_id"); // Empresa asociada al albarán
			fields.Add("state"); // Estado del albarán
			fields.Add("carrier_id"); // Transportista asociado
			long[] picking_ids = new long[] {40,48};
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
				if (!picking["carrier_id"].Equals(false)) {
					Console.WriteLine("- Datos de transporte:");
					XmlRpcStruct[] carrier_data = connection.Read("delivery.carrier", new long[] {Convert.ToInt64(((object[]) picking["carrier_id"])[0])}, new string[] {"name"}); // Leemos el nombre del transportista
					Console.WriteLine("Transportista: {0}", carrier_data[0]["name"]);
				}
				Console.WriteLine("###########################"); // Separación
				Console.WriteLine("###########################"); // Separación
			}
			
			Console.WriteLine("\n\n");
			
			// Siguiendo con el ejemplo, voy a decirle a Odoo que compruebe disponibilidad. Quizás Vstock ya consultaría sólo albaranes disponibles o parcialmente disponibles
			// El botón de comprobar disponibilidad llama a un método de nombre action_assign
			connection.Execute("stock.picking", "action_assign", picking_ids);
			// Volvemos a imprimir los estados de estos albaranes para ver si ya los tenemos diponibles o parcialmente disponibles.
			XmlRpcStruct[] picking_data = connection.Read("stock.picking", picking_ids, new string[] {"name", "state", "move_lines"});
			foreach(var picking in picking_data)
			{
				Console.WriteLine("Albarán {0} en estado {1}. Id: {2}", picking["name"], picking["state"], picking["id"]);
				// En mi caso uno queda parcialmente diponible y otro totalmente disponible
				
				if (picking["state"].Equals("partially_available")) { // En el caso de que esté parcialmente disponible listamos sus movimientos con la cantidad pedida y la cantidad que consiguió reservar del stock.
					int[] moves = (int[]) picking["move_lines"];
					foreach(var move in moves)
					{
						XmlRpcStruct[] move_data = connection.Read("stock.move", new long[] {(long) move}, new string[] {"product_id", "product_uom_qty", "availability"});
						XmlRpcStruct[] product_data = connection.Read("product.product", new long[] {Convert.ToInt64(((object[]) move_data[0]["product_id"])[0])}, new string[] {"default_code", "name"});
						Console.WriteLine("[{0}] {1}, {2} Unidades pedidas. {3} unidades disponibles", product_data[0]["default_code"], product_data[0]["name"], move_data[0]["product_uom_qty"], move_data[0]["availability"]);
						// En el caso de que las unidades disponibles no coincidan con las de Vstock habrá que generar una incidencia desde Vstock a Odoo para informar de este hecho
						// La gestión de incidencias en albaranes no está desarrollada en este momento de la integración, por lo que para seguir con el ejemplo supongamos que coincide.
					}
				}
			}
			
			Console.WriteLine("\n\n");
			
			// Como ejemplo vamos a cancelar el albarán que está parcialmente disponible, porque al final por lo que se no lo enviamos. Este albarán es el id: 40
			// El botón de Cancelar transferencia llama a un método de nombre action_cancel. Una vez cancelado el albarán no hay forma de recuperarlo para envío. Hay que irse al pedido asociado y crear uno nuevo.
			connection.Execute("stock.picking", "action_cancel", new long[] {40});
			// Comprobamos de nuevo su estado para ver que realmente se canceló bien.
			XmlRpcStruct[] cancel_picking_data = connection.Read("stock.picking", new long[] {40}, new string[] {"name", "state"});
			Console.WriteLine("Albarán {0} en estado {1}. Id: {2}", cancel_picking_data[0]["name"], cancel_picking_data[0]["state"], cancel_picking_data[0]["id"]);
			
			Console.WriteLine("\n\n");

			// Como último ejemplo vamos a procesar por completo el albarán con id 48. La forma que se expone es la forma sencilla, en la que queremos procesar el albarán integramente
			// Hay un forma más compleja en la que se permite procesar parcialmente pero la definiremos en un segundo paso.
			connection.Execute("stock.picking", "action_done", new long[] {48});
					                                                                                          
			// Una vez hecho el traspaso comprobamos de nuevo el estado del albarán, para ver que efectivamente se ha puesto como Realizado.		                                                                                          
			XmlRpcStruct[] done_picking_data = connection.Read("stock.picking", new long[] {48}, new string[] {"name", "state"});
			Console.WriteLine("Albarán {0} en estado {1}. Id: {2}", done_picking_data[0]["name"], done_picking_data[0]["state"], done_picking_data[0]["id"]);
			
			Console.ReadLine();
		}
	}
}
