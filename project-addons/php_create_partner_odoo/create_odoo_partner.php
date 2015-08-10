<?php

require_once('odoo.php');

$connection = new OdooConnect();

$country_id = null;
try {
     $country_code = $_POST['country'];
     $domain_filter = array (
        new xmlrpcval(
            array(new xmlrpcval('code' , "string"),
                  new xmlrpcval('=',"string"),
                  new xmlrpcval($country_code,"string")
                  ),"array"),
        );
     $country_ids = $connection->search("res.country", $domain_filter);
     $country_id = $country_ids[0]->me['int'];

     $pos = strpos($_POST["vat"], $country_code);
     if ($pos !== 0 || $pos === false){
        throw new Exception('El código del país debe figurar en el NIF.');
     }

     $val = array (
        "name"    => new xmlrpcval($_POST["name"], "string"),
        "city" => new xmlrpcval($_POST["city"], "string"),
        "zip" => new xmlrpcval($_POST["zip"], "string"),
        "street" => new xmlrpcval($_POST["street"], "string"),
        "vat" => new xmlrpcval($_POST["vat"], "string"),
        "email" => new xmlrpcval($_POST["email"], "string"),
        "country_id" => new xmlrpcval($country_id, "int"),
        "customer" => new xmlrpcval(1, "int"),
        "is_company" => new xmlrpcval(1, "int"),
    );

    $connection->create("res.partner", $val);
    echo json_encode("");

} catch (Exception $e) {
    $data = array('type' => 'error', 'message' => $e->getMessage());
    header('HTTP/1.1 400 Bad Request');
    header('Content-Type: application/json; charset=UTF-8');
    echo json_encode($data);
}

?>
