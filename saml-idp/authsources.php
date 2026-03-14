<?php

$config = array(

    'admin' => array(
        'core:AdminPassword',
    ),

    'example-userpass' => array(
        'exampleauth:UserPass',
        'user1:user1pass' => array(
            'uid'                  => array('1'),
            'cn'                   => array('user1'),
            'givenName'            => array('User'),
            'sn'                   => array('One'),
            'mail'                 => array('user1@example.com'),
            'eduPersonAffiliation' => array('group1'),
        ),
        'user2:user2pass' => array(
            'uid'                  => array('2'),
            'cn'                   => array('user2'),
            'givenName'            => array('User'),
            'sn'                   => array('Two'),
            'mail'                 => array('user2@example.com'),
            'eduPersonAffiliation' => array('group2'),
        ),
    ),

);
