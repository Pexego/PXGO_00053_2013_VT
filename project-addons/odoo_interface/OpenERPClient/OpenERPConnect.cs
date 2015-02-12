/*
    OpenERP, Open Source Business Applications
    Copyright (c) 2011 OpenERP S.A. <http://openerp.com>
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
using System.Collections;
using CookComputing.XmlRpc;

namespace OpenERPClient
{	
	public class ServiceUrl : System.Attribute
    {
        string _url;
        public ServiceUrl(string url)
        {
            this._url = url;
        }
        public string Url
        {
            get
            {
                return _url;
            }
        }
        public override string ToString()
        {
            return this._url;
        }
    }
	
	public enum OpenERPService
    {
        [ServiceUrl("/xmlrpc/object")]
        Object = 1,
        [ServiceUrl("/xmlrpc/db")]
        DB = 2,
        [ServiceUrl("/xmlrpc/common")]
        Common = 3
    }
	
	public class OpenERPConnect
    {
        int uid;
        string url;
        string dbname;
        string login;
        string password;
		XMLRPCClient rpcclient; 
        public string URL
        {
            /*
            It will get and set the value of the url.
            
            :return : String
            */

            get
            {
                return url;
            }
            set
            {
                url = value;
            }
        }
        public string DBName
        {
            /*
            It will get and set the value of the Database Name.
            
            :return : String
            */

            get
            {
                return dbname;
            }
            set
            {
                dbname = value;
            }
        }
        public int UserId
        {
            /*
            It will get and set the value of the UserId.
            
            :return : String
            */

            get
            {
				if (uid == 0){
					Console.WriteLine("Error, you are not authenticated.");
					Console.ReadLine();
				}
                return uid;
            }
            set
            {
                uid = value;
            }
        }
		public string UserName
        {
            /*
            It will get and set the value of the UserId.
            
            :return : String
            */

            get
            {
                return login;
            }
            set
            {
                login = value;
            }
        }
        public string pswrd
        {
            /*
            It will get and set the value of the Password.
            
            :return : String
            */

            get
            {
                return password;
            }
            set
            {
                password = value;
            }
        }
		
		void Open(Enum service)
        {
            string url = null;
            Type type = service.GetType();
			
			ServiceUrl[] _urls =
               type.GetField(service.ToString()).GetCustomAttributes(typeof(ServiceUrl),
                                       false) as ServiceUrl[];
			if (_urls.Length > 0)
            {
                url = _urls[0].Url;
            }

            this.Open(url);

        }
		
		void Open(string service_url)
        {
            /*
            It opens rpcclient by service url.
            :param service_url : service url
            */

            this.rpcclient = new XMLRPCClient(this.url + service_url);

        }
		
		void Close()
        {
            /*
            It closes rpcclient.
            */

            this.rpcclient = null;

        }
		
		public OpenERPConnect(string url, string dbname, string login, string pwd)
        {
            /*
             It will do the connection with OpenERP server.
             :param url : url with the server and port.
             :param dbname : the list of database.
             :param login : user name.
             :param pwd : password.
            */

            this.url = url;
            this.dbname = dbname;
            this.login = login;
            this.password = pwd;
        }
		
		public Boolean isLoggedIn
        {
            /*
            It will check whether successfully login to OpenERP is done or not.
            
            :return : True or False.
            */

            get
            {
                if (this.uid > 0) { return true; }
                return false;
            }
        }
		
		public void Login()
        {
            /*
             It will check whether the entered dbname, userid and password are correct or not
             and on that basis it will allow the user for connecting to OpenERP.
            */

            this.Open(OpenERPClient.OpenERPService.Common);
            int isLogin = this.rpcclient.Login(this.dbname, this.login, this.password);
            this.uid = 0;
            if (Convert.ToBoolean(isLogin))
            {
                this.uid = Convert.ToInt32(isLogin);
            }

            if (this.uid <= 0)
            {
                Console.WriteLine("Authentication Error!\nBad username or password.");
				Console.ReadLine();
            }
            this.Close();

        }
		
		public long Create(string model, XmlRpcStruct fieldValues)
		{
			/* 
			 It inserts new registry in OpenERP
			 :param model : _name of model where you insert
             :param fieldValues : struct with data to insert [key, value] 
             
             :return : Long (new is created)
			*/
			this.Open(OpenERPClient.OpenERPService.Object);	
			var new_id = this.rpcclient.Create(this.dbname, this.UserId, this.password, model, "create", fieldValues);
			this.Close();
			return Convert.ToInt32(new_id);
		}
		
		public long[] Search(string model, Object[] filters)
		{
			/* 
			 It searches in OpenERP's models
			 :param model : _name of model where you search
             :param filters : openerp's domain [[field, operator, value],[...]]
             
             :return : Long[] (ids found)
			*/
			this.Open(OpenERPClient.OpenERPService.Object);	
			var ids_obj = this.rpcclient.Search(this.dbname, this.UserId, this.password, model, "search", filters);
			this.Close();
			return Array.ConvertAll(ids_obj, ids => Convert.ToInt64(ids));
		}
		
		public XmlRpcStruct[] Read(string model, long[] ids, string[] fields)
		{
			/* 
			 It obtains data from OpenERP registries
			 :param model : _name of model where you request
			 :param ids : ids of registries whose you can obtain data
             :param fields : names of models's fields you want to obtain
             
             :return : XmlRpcStruct[] (data [[("id", 1), ("name", "Test")]])
			*/
			this.Open(OpenERPClient.OpenERPService.Object);
			var data = this.rpcclient.Read (this.dbname, this.UserId, this.password, model, "read", ids, fields);
			this.Close();
			ArrayList records = new ArrayList(data);
			return records.ToArray(typeof(XmlRpcStruct)) as XmlRpcStruct[];
		}
		
		public XmlRpcStruct[] Read(string model, long[] ids, string[] fields, XmlRpcStruct context)
		{
			/* 
			 It obtains data from OpenERP registries
			 :param model : _name of model where you request
			 :param ids : ids of registries whose you can obtain data
             :param fields : names of models's fields you want to obtain
             :param context : Odoo's context
             
             :return : XmlRpcStruct[] (data [[("id", 1), ("name", "Test")]])
			*/
			this.Open(OpenERPClient.OpenERPService.Object);
			var data = this.rpcclient.Read (this.dbname, this.UserId, this.password, model, "read", ids, fields, context);
			this.Close();
			ArrayList records = new ArrayList(data);
			return records.ToArray(typeof(XmlRpcStruct)) as XmlRpcStruct[];
		}
		
		public bool Unlink(string model, long[] ids)
		{
			/* 
			 It removes OpenERP registries
			 :param model : _name of model where you remove
			 :param ids: ids of registries to remove
             
             :return : Boolean
			*/
			this.Open(OpenERPClient.OpenERPService.Object);
			bool result = this.rpcclient.Unlink(this.dbname, this.UserId, this.password, model, "unlink", ids);
			this.Close();
			return result;
		}
		
		public bool Unlink(string model, long[] ids, XmlRpcStruct context)
		{
			/* 
			 It removes OpenERP registries
			 :param model : _name of model where you remove
			 :param ids: ids of registries to remove
			 :param context : Odoo's context
             
             :return : Boolean
			*/
			this.Open(OpenERPClient.OpenERPService.Object);
			bool result = this.rpcclient.Unlink(this.dbname, this.UserId, this.password, model, "unlink", ids, context);
			this.Close();
			return result;
		}
		
		public bool Write(string model, long[] ids, XmlRpcStruct fieldValues)
		{
			/* 
			 It updates OpenERp's registries
			 :param model : _name of model where you update
			 :param ids : Ids of registries whose you can update
             :param fieldValues : struct with data to update [key, value] 
             
             :return : Boolean
			*/
			this.Open(OpenERPClient.OpenERPService.Object);
			bool result = this.rpcclient.Write(this.dbname, this.UserId, this.password, model, "write", ids, fieldValues);
			this.Close();
			return result;
		}
		
		public bool Write(string model, long[] ids, XmlRpcStruct fieldValues, XmlRpcStruct context)
		{
			/* 
			 It updates OpenERp's registries
			 :param model : _name of model where you update
			 :param ids : Ids of registries whose you can update
             :param fieldValues : struct with data to update [key, value]
             :param context : Odoo's context 
             
             :return : Boolean
			*/
			this.Open(OpenERPClient.OpenERPService.Object);
			bool result = this.rpcclient.Write(this.dbname, this.UserId, this.password, model, "write", ids, fieldValues, context);
			this.Close();
			return result;
		}
		
		public Object Execute(string model, string method, long[] ids)
		{
			/* 
			 It allows to execute any OpenERP's method
			 :param model : _name of model where method is defined
			 :param method : name of method to execute
			 :param ids : ids of registries whose you can update
             
             :return : Object (depends on method)
			*/
			this.Open(OpenERPClient.OpenERPService.Object);
			Object res = this.rpcclient.Execute(this.dbname, this.UserId, this.password, model, method, ids);
			this.Close();
			return res;
		}
		
		public Object Execute(string model, string method, long[] ids, XmlRpcStruct context)
		{
			/* 
			 It allows to execute any OpenERP's method
			 :param model : _name of model where method is defined
			 :param method : name of method to execute
			 :param ids : ids of registries whose you can update
			 :param context : Odoo's context
             
             :return : Object (depends on method)
			*/
			this.Open(OpenERPClient.OpenERPService.Object);
			Object res = this.rpcclient.Execute(this.dbname, this.UserId, this.password, model, method, ids, context);
			this.Close();
			return res;
		}
		
		public void MessagePost(string model, long[] ids, string message)
		{
			/* 
			 It allows to create a message in any OpenERP's record
			 :param model : _name of model where method is defined
			 :param ids : ids of registries whose you can update
			 :param message : message to send
             
             :return : long (Id of message)
			*/
			this.Open(OpenERPClient.OpenERPService.Object);
			this.rpcclient.MessagePost(this.dbname, this.UserId, this.password, model, "message_post", ids, message);
			this.Close();
		}
		
	}

}
