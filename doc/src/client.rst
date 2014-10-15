.. _frappe_flient:

===========
Demo Client
===========

This is an implementation of a rest client for the recommendation system. It will list all users in your system and
provide a unique page for each with all the items the user possess and a list of recommended items for that user in
specific.

It is a html5/javascript app and you can use it in any modern browser. All the dependencies are in the same directory
as the client.html and everything is in the folder client in the project repository.

.. note::

    Because the client access resources from the machine some browsers like chrome will block it by default. If you
    want to use the client with one of this browsers you have to manual allow cross origin request for file system.

.. note::

   This client was created to communicate to Mozilla Firefox OS marketplace. So the interface look that same icons
   should appear with the items and some more info. With the Mozilla data those things happen.


Getting Started
---------------

Go to /project/directory/client and open client.html with your browser (if you are using chrome you have to pass
--allow-file-access-from-files). The page open should have a textbox to introduce the webservice url.

In this stage you should have a frappe service up and running. If the server domain is **example.net**, the port where
it is serving is **8080** and you have configured the url mapping to the service has **api** you should introduce in the
textfield **http://example.com:8080/api/** and click go.

After you introduce the service url a list of the first 15 users in the database should appear in a table. The first
column is the id in the database for the user, the second the external_id and third the number of owned items.

By clicking in the external_id you should jump to a page with two sections. The first a list with owned items for that
user. The second a list of items recommended for that user. A refresh button is available to request for a new
recommendation.

TODO
----

In the next stage a functionality to acquire a new item and drop items.