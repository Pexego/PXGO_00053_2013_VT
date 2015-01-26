using System;
using OpenERPClient;
using System.Collections;
using CookComputing.XmlRpc;

namespace odoo_inventory
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
			
			//Listamos todos los productos almacenables con su stock inicial
			Object[] domain = new Object[1]; // [('type.code', '=', 'product')]
			domain[0] = new Object[3] {"type", "=", "product"};
			long[] product_ids = connection.Search("product.product", domain);
			Console.WriteLine("Productos encontrados: {0}", product_ids.Length);
			
			XmlRpcStruct context = new XmlRpcStruct();
			context.Add("lang", "es_ES"); // cargamos en contexto el idioma español
			XmlRpcStruct[] products_data = connection.Read ("product.product", product_ids, new string[] {"name", "qty_available", "uom_id"}, context);
			
			Console.WriteLine("STOCK INICIAL");
			foreach(var product in products_data)
			{
				Console.WriteLine("Producto: {0} - Stock actual: {1} unidades", product["name"], product["qty_available"]);
			}
			
			Console.WriteLine("\n\n");
			// Con un inventario vamos a aumentarle una unidad a cada uno siempre que el stock no sea en negativo, si es negativo ponemos 0.
			
			//Creamos un inventario nuevo.
			XmlRpcStruct vals = new XmlRpcStruct();
			vals.Add("name", "Inventario de prueba"); //Motivo de inventario
			long inv_id = connection.Create("stock.inventory", vals); // se crea
			// Necesitamos recuperar el id de la ubicación de stock del inventario
			XmlRpcStruct[] inv_data = connection.Read("stock.inventory", new long[] {inv_id}, new string[] {"location_id"});
			long location_id = Convert.ToInt64(((object[]) inv_data[0]["location_id"])[0]);
			
			foreach(var product in products_data) //Para cada producto creamos una linea en el inventario
			{
				XmlRpcStruct line_vals = new XmlRpcStruct();
				line_vals.Add("inventory_id", inv_id);
				line_vals.Add("product_id", product["id"]);
				line_vals.Add("location_id", location_id);
				if (Convert.ToDouble(product["qty_available"]) >= 0){
					line_vals.Add("product_qty", Convert.ToDouble(product["qty_available"]) + 1.0); // cantidad actual + 1
				}
				else{
					line_vals.Add("product_qty", 0); // cantidad actual <= 0 entonces 0
				}
				
				line_vals.Add("product_uom_id", Convert.ToInt64(((object[]) product["uom_id"])[0])); //unidad de medida
				connection.Create("stock.inventory.line", line_vals);
			}
			
			//Una vez rellenado lo confirmamos
			connection.Execute("stock.inventory", "prepare_inventory", new long[] {inv_id});
			connection.Execute("stock.inventory", "action_done", new long[] {inv_id});
			
			//Para comprobar el cambio volvemso a leer productos y mostrarlos por pantalla.
			long[] product_ids2 = connection.Search("product.product", domain);
			Console.WriteLine("Productos encontrados: {0}", product_ids2.Length);
			
			XmlRpcStruct[] products_data2 = connection.Read ("product.product", product_ids2, new string[] {"name", "qty_available", "uom_id"}, context);
			
			Console.WriteLine("STOCK ACTUAL");
			foreach(var product in products_data2)
			{
				Console.WriteLine("Producto: {0} - Stock actual: {1} unidades", product["name"], product["qty_available"]);
			}
			
			Console.ReadLine();
		}
	}
}
