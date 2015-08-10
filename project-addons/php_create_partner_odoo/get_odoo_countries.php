<?php
require_once('odoo.php');

$connection = new OdooConnect();
$domain_filter = array ();
$country_ids = $connection->search("res.country", $domain_filter, "name asc");
$id_list = array();

for($i = 0; $i < count($country_ids); $i++){
    $id_list[]= new xmlrpcval($country_ids[$i]->me['int'], 'int');
}
$field_list = array(
        new xmlrpcval("name", "string"),
        new xmlrpcval("code", "string")
    );
$country_data = $connection->read("res.country", $id_list, $field_list);

for($i = 0; $i < count($country_data); $i++){
    echo "<option value='" . $country_data[$i]->me['struct']['code']->me['string'] . "'>" . $country_data[$i]->me['struct']['name']->me['string'] . "</option>";
}

?>
