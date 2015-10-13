using System;
using System.IO;
using OpenERPClient;
using System.Collections;
using CookComputing.XmlRpc;

namespace odoo_print_picking
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

			byte[] pdf_content = File.ReadAllBytes("./Properties/prueba.pdf");
			String base64_pdf = Convert.ToBase64String(pdf_content);

			// Se obtendría el id del albarán donde queremos añadir el adjunto
			// Cojo un id de un albarán cualquiera 
			int picking = 209;
			// Creamos el adjunto
			XmlRpcStruct vals = new XmlRpcStruct();
			vals.Add("name", "Pdf prueba"); // Nombre del pdf
			vals.Add("datas", base64_pdf); // base64
			vals.Add("datas_fname", "Pdf prueba"); // Nombre del pdf
			vals.Add("res_model", "stock.picking"); // Valor fijo, modelo al que se asocia el pdf
			vals.Add("res_id", picking); // Id del registro al que se asocia el pdf
			vals.Add("to_print", true);
			long attachment_id = connection.Create("ir.attachment", vals); // se crea
			// stock_custom.report_picking_with_attachments es el nombre del informe, valor fijo
			// 209 vuelve a ser el id del picking
			Object x = connection.Print("report",  "stock_custom.report_picking_with_attachments", new long[] {209});
		}
	}
}
