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
			String Url = "http://localhost:8069";
			String Dbname = "pcog80";
			String Login = "admin";
			String Password = "admin";
			
			OpenERPConnect connection = new OpenERPConnect(Url, Dbname, Login, Password);
			connection.Login();
			Console.WriteLine(connection.UserId);
			
			ArrayList filters = new ArrayList();
			long[] partner_ids = connection.Search("res.partner", filters.ToArray());
			ArrayList fields = new ArrayList();
			fields.Add("name");
			var partner_data = connection.Read("res.partner", partner_ids, (string[]) fields.ToArray(typeof(string)));
			foreach(var partner in partner_data)
			{
				Console.WriteLine("Partner {0} with Id {1}", partner["name"], partner["id"]);	
			}
			
			Console.ReadLine();
		}
	}
}
