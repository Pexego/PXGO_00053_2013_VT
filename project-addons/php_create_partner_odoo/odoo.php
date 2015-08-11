<?php

require_once('lib/xmlrpc.inc');
require_once('lib/xmlrpcs.inc');

$GLOBALS['xmlrpc_internalencoding']='UTF-8';
class OdooConnect {

    private $uid;
    const dbname = 'demo';
    const user = 'admin';
    const password = 'admin';
    const server_url = 'http://localhost:8069';
    const lang = "es_ES";

    public function __construct()
    {
        $connexion = new xmlrpc_client(self::server_url . "/xmlrpc/common");
        $connexion->setSSLVerifyPeer(0);

        $c_msg = new xmlrpcmsg('login');
        $c_msg->addParam(new xmlrpcval(self::dbname, "string"));
        $c_msg->addParam(new xmlrpcval(self::user, "string"));
        $c_msg->addParam(new xmlrpcval(self::password, "string"));
        $c_response = $connexion->send($c_msg);

        if ($c_response->errno != 0){
            echo  '<p>error : ' . $c_response->faultString() . '</p>';
        }
        else{
            $this->uid = $c_response->value()->scalarval();
        }
    }

    public function getUid()
    {
        return $this->uid;
    }

    public function create($model, $val)
    {
        $client = new xmlrpc_client(self::server_url . "/xmlrpc/object");
        $client->setSSLVerifyPeer(0);

        $msg = new xmlrpcmsg('execute');
        $msg->addParam(new xmlrpcval(self::dbname, "string"));
        $msg->addParam(new xmlrpcval($this->uid, "int"));
        $msg->addParam(new xmlrpcval(self::password, "string"));
        $msg->addParam(new xmlrpcval($model, "string"));
        $msg->addParam(new xmlrpcval("create", "string"));
        $msg->addParam(new xmlrpcval($val, "struct"));
        return $client->send($msg);
    }

    public function search($model, $domain_filter, $order="")
    {
        $client = new xmlrpc_client(self::server_url . "/xmlrpc/object");
        $client->setSSLVerifyPeer(0);

        $msg = new xmlrpcmsg('execute');
        $msg->addParam(new xmlrpcval(self::dbname, "string"));
        $msg->addParam(new xmlrpcval($this->uid, "int"));
        $msg->addParam(new xmlrpcval(self::password, "string"));
        $msg->addParam(new xmlrpcval($model, "string"));
        $msg->addParam(new xmlrpcval("search", "string"));
        $msg->addParam(new xmlrpcval($domain_filter, "array"));
        $msg->addParam(new xmlrpcval(0, "int"));
        $msg->addParam(new xmlrpcval(0, "int"));
        $msg->addParam(new xmlrpcval($order, "string"));
        $context = array (
            "lang" => new xmlrpcval(self::lang, "string")
        );
        $msg->addParam(new xmlrpcval($context, "struct"));
        $response = $client->send($msg);


        $result = $response->value();
        return $result->scalarval();
    }

    public function read($model, $id_list, $field_list)
    {
        $client = new xmlrpc_client(self::server_url . "/xmlrpc/object");
        $client->setSSLVerifyPeer(0);

        $msg = new xmlrpcmsg('execute');
        $msg->addParam(new xmlrpcval(self::dbname, "string"));
        $msg->addParam(new xmlrpcval($this->uid, "int"));
        $msg->addParam(new xmlrpcval(self::password, "string"));
        $msg->addParam(new xmlrpcval($model, "string"));
        $msg->addParam(new xmlrpcval("read", "string"));
        $msg->addParam(new xmlrpcval($id_list, "array"));
        $msg->addParam(new xmlrpcval($field_list, "array"));

        $context = array (
            "lang" => new xmlrpcval(self::lang, "string")
        );
        $msg->addParam(new xmlrpcval($context, "struct"));

        $resp = $client->send($msg);

        if ($resp->faultCode()){
            echo $resp->faultString();
        }

        return $resp->value()->scalarval();
    }
}
?>
