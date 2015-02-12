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
using System.Text;
using CookComputing.XmlRpc;

namespace OpenERPClient
{
	
    public interface IOpenERPCommon : IXmlRpcProxy
    {
        [XmlRpcMethod("login")]
        int Login(string dbname, string username, string pwd);
		
		[XmlRpcMethod("logout")]
        int Logout(string dbname, string username, string pwd);

    }
    public interface IOpenERPObject : IXmlRpcProxy
    {

		[XmlRpcMethod("execute")]
        object Create(string dbName, int userId, string pwd, string model, string method, XmlRpcStruct fieldValues);
		
		[XmlRpcMethod("execute")]
        object Create(string dbName, int userId, string pwd, string model, string method, XmlRpcStruct fieldValues, XmlRpcStruct context);
		
		[XmlRpcMethod("execute")]
        Object[] Search(string dbName, int userId, string pwd, string model, string method, Object[] filters);
		
		[XmlRpcMethod("execute")]
        bool Write(string dbName, int userId, string pwd, string model, string method, long[] ids, XmlRpcStruct fieldValues);
		
		[XmlRpcMethod("execute")]
        bool Write(string dbName, int userId, string pwd, string model, string method, long[] ids, XmlRpcStruct fieldValues, XmlRpcStruct context);
		
		[XmlRpcMethod("execute")]
        bool Unlink(string dbName, int userId, string pwd, string model, string method, long[] ids);
		
		[XmlRpcMethod("execute")]
        bool Unlink(string dbName, int userId, string pwd, string model, string method, long[] ids, XmlRpcStruct context);
		
		[XmlRpcMethod("execute")]
        Object[] Read(string dbName, int userId, string pwd, string model, string method, long[] ids, string[] fieldNames);
		
		[XmlRpcMethod("execute")]
        Object[] Read(string dbName, int userId, string pwd, string model, string method, long[] ids, string[] fieldNames, XmlRpcStruct context);
		
		[XmlRpcMethod("execute")]
        Object Execute(string dbName, int userId, string pwd, string model, string method, long[] ids);
		
		[XmlRpcMethod("execute")]
        Object Execute(string dbName, int userId, string pwd, string model, string method, long[] ids, XmlRpcStruct context);
		
		[XmlRpcMethod("execute")]
        void MessagePost(string dbName, int userId, string pwd, string model, string method, long[] ids, string message);

    }
	
	public interface Ixmlrpcconnect : IOpenERPCommon, IOpenERPObject
    {
    }
	
	public class XMLRPCClient : Ixmlrpcconnect
	{
		Ixmlrpcconnect rpcclient = XmlRpcProxyGen.Create<Ixmlrpcconnect>();
		public XMLRPCClient(string ServiceUrl)
        {
            rpcclient.Url = ServiceUrl;
        }
		
		public int Login(string dbname, string username, string pwd)
		{
			return rpcclient.Login(dbname, username, pwd);
		}
		
		public int Logout(string dbname, string username, string pwd)
		{
			return rpcclient.Logout(dbname, username, pwd);
		}
		
		public object Create(string dbName, int userId, string pwd, string model, string method, XmlRpcStruct fieldValues)
		{
			return rpcclient.Create(dbName, userId, pwd, model, method, fieldValues);
		}
		
		public object Create(string dbName, int userId, string pwd, string model, string method, XmlRpcStruct fieldValues, XmlRpcStruct context)
		{
			return rpcclient.Create(dbName, userId, pwd, model, method, fieldValues, context);
		}
		
		public Object[] Search(string dbName, int userId, string pwd, string model, string method, Object[] filters)
		{
			return rpcclient.Search(dbName, userId, pwd, model, method, filters);
		}
		
		public bool Write(string dbName, int userId, string pwd, string model, string method, long[] ids, XmlRpcStruct fieldValues)
		{
			return rpcclient.Write(dbName, userId, pwd, model, method, ids, fieldValues);
		}
		
		public bool Write(string dbName, int userId, string pwd, string model, string method, long[] ids, XmlRpcStruct fieldValues, XmlRpcStruct context)
		{
			return rpcclient.Write(dbName, userId, pwd, model, method, ids, fieldValues, context);
		}
		
		public bool Unlink(string dbName, int userId, string pwd, string model, string method, long[] ids)
		{
			return rpcclient.Unlink(dbName, userId, pwd, model, method, ids);
		}
		
		public bool Unlink(string dbName, int userId, string pwd, string model, string method, long[] ids, XmlRpcStruct context)
		{
			return rpcclient.Unlink(dbName, userId, pwd, model, method, ids, context);
		}
		
		public Object[] Read(string dbName, int userId, string pwd, string model, string method, long[] ids, string[] fieldNames)
		{
			return rpcclient.Read(dbName, userId, pwd, model, method, ids, fieldNames);
		}
		
		public Object[] Read(string dbName, int userId, string pwd, string model, string method, long[] ids, string[] fieldNames, XmlRpcStruct context)
		{
			return rpcclient.Read(dbName, userId, pwd, model, method, ids, fieldNames, context);
		}
		
		public Object Execute(string dbName, int userId, string pwd, string model, string method, long[] ids)
		{
			return rpcclient.Execute(dbName, userId, pwd, model, method, ids);
		}
		
		public Object Execute(string dbName, int userId, string pwd, string model, string method, long[] ids, XmlRpcStruct context)
		{
			return rpcclient.Execute(dbName, userId, pwd, model, method, ids, context);
		}
		
		public void MessagePost(string dbName, int userId, string pwd, string model, string method, long[] ids, string message)
		{
			rpcclient.MessagePost(dbName, userId, pwd, model, method, ids, message);
		}
		
		#region NotImplemanted
		
		public bool AllowAutoRedirect
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }
		
		public System.Security.Cryptography.X509Certificates.X509CertificateCollection ClientCertificates
        {
            get { throw new NotImplementedException(); }
        }
		
		public string ConnectionGroupName
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }
		
		public System.Net.CookieContainer CookieContainer
        {
            get { throw new NotImplementedException(); }
        }
		
		public System.Net.ICredentials Credentials
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }
		
		public bool EnableCompression
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }
		
		public bool Expect100Continue
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }
		
		public System.Net.WebHeaderCollection Headers
        {
            get { throw new NotImplementedException(); }
        }
		
		public Guid Id
        {
            get { throw new NotImplementedException(); }
        }
		
		public int Indentation
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }
		
		public bool KeepAlive
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }
		
		public XmlRpcNonStandard NonStandard
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public bool PreAuthenticate
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public Version ProtocolVersion
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public System.Net.IWebProxy Proxy
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public System.Net.CookieCollection ResponseCookies
        {
            get { throw new NotImplementedException(); }
        }

        public System.Net.WebHeaderCollection ResponseHeaders
        {
            get { throw new NotImplementedException(); }
        }

        public int Timeout
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public string Url
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public bool UseEmptyParamsTag
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public bool UseIndentation
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public bool UseIntTag
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public bool UseStringTag
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public string UserAgent
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public Encoding XmlEncoding
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public string XmlRpcMethod
        {
            get
            {
                throw new NotImplementedException();
            }
            set
            {
                throw new NotImplementedException();
            }
        }

        public string[] SystemListMethods()
        {
            throw new NotImplementedException();
        }

        public object[] SystemMethodSignature(string MethodName)
        {
            throw new NotImplementedException();
        }

        public string SystemMethodHelp(string MethodName)
        {
            throw new NotImplementedException();
        }
		
		public event XmlRpcRequestEventHandler RequestEvent;

        public event XmlRpcResponseEventHandler ResponseEvent;
		
		#endregion
		
	}
    
}
