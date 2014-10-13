.. _restful_api:

===========
RESTFul API
===========

About
-----

FireFox OS Store Recommendation webservice is a way to get apps recommendations
considering some user experience. The system is simple, the user send some data
its experience and receive a set of recommended apps to his profile. This
experience can be apps already installed, apps rejected, user location, time,
season, etc...

This new version has little difference from his previous one. Mainly now you can
use a bunch of formats for response. JSON is maintained as the default but you
always get XML and YAML. HTML format and other just depend on plugins. I will
research witch may needed an write them on the requirements.txt on the repo.
In the back-end there was a huge change. All the ReST API system was imported to
TastyPie Framework. That's way so many things are possible now.

Recommendation API
------------------

Just a brief note about the documentation. The ReST description tables here on
this document always start with a response or request field in the first entry.
That's not a name of an actual field. It's is the type of the response. Usually
a object or list. The entries following the first describe the elements that
are used in it.

Just to make things more clear, a example is provided following the table.


Data Types
----------

Every field data type used in the request and response are described in the
following table.

+----------------+------------+-----------------------------------------------+
|                |            |                                               |
| Type           | Data Type  | Description                                   |
|                |            |                                               |
+================+============+===============================================+
|                |            |                                               |
| Text           | String     | Common text like names or descriptions. Ex:   |
|                |            | This description.                             |
|                |            |                                               |
+----------------+------------+-----------------------------------------------+
|                |            |                                               |
| Natural Number | Integer    | Numbers commonly used to count things. Ex:    |
|                |            | How many times something.                     |
|                |            |                                               |
+----------------+------------+-----------------------------------------------+
|                |            |                                               |
| Real Number    | Float      | Number used to measure things like distances, |
|                |            | latitude, etc...                              |
|                |            |                                               |
+----------------+------------+-----------------------------------------------+
|                |            |                                               |
| Date & Time    | String     | Date in format 'YYYY-MM-DDTHH:MI:SS'. Note    |
|                |            | that its the date followed by a capital T and |
|                |            | then the time.                                |
|                |            |                                               |
+----------------+------------+-----------------------------------------------+
|                |            |                                               |
| List<type>     | Array      | List of some data type elements. The type     |
|                |            | in the List is the type of data of the        |
|                |            | elements in the list. If type is not provided |
|                |            | in the documentation you should consider      |
|                |            | multiple data types among the elements in the |
|                |            | the list. But that would never happen because |
|                |            | we are really good and will never do such     |
|                |            | nonsense.                                     |
|                |            |                                               |
+----------------+------------+-----------------------------------------------+
|                |            |                                               |
| Object         | Dictionary | A JSON Dictionary with some fields mapping    |
|                |            | some values. This Values can be of any data   |
|                |            | type described in this table.                 |
|                |            |                                               |
+----------------+------------+-----------------------------------------------+


Request Recommendations
-----------------------

The request recommendation method work over ReST request in a JSON or XML.
The response come as has a list of app IDS.


*URL*::

    http://domain.com/api/v2/recommend/<recommendation_number>/<user_id>.<format>
    http://domain.com/api/v2/recommend/<recommendation_number>/<user_id>/<format>/
    http://domain.com/api/v2/recommend/<recommendation_number>/<user_id>/  # Default format is JSON


GET Request
+++++++++++

Example::

    http://domain.com/api/v2/recommend/120/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173.xml


Response:

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| Response       | Object        |                                           |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| external_id    | String        | The identifier of the user                |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| recommendations| List<String>  | A list with suggested items ids.          |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Example::

    XML Response:
        <root>
            <user>
                0033597455692156e68dfdc2fc3936595b560834d1a0d68d8606e23779f454e1
            </user>
            <recommendations>
                <list-item>457282</list-item>
                <list-item>469837</list-item>
                <list-item>472640</list-item>
                <list-item>455346</list-item>
            </recommendations>
        </root>

    JSON Response:
        {
            user: "0033597455692156e68dfdc2fc3936595b560834d1a0d68d8606e23779f454e1",
            recommendations: [
                "453746",
                "463842",
                "461344",
                "408212"
            ]
        }

Go to the Application place in FF Store
---------------------------------------

This functionality allow to record useful information about a specific app. It can record a simple click, a click from
a recommendation, and a click from anonymous users.


*URL*::

    http://domain.com/apu/v2/<click or recommended>/<user external id or anonymous>/<app external id>/


GET Request
+++++++++++

If the source is *recommended* it has to have a GET parameter called rank. This parameter is used to classify the
position were the app had in that recommendation.

+----------------+---------------+------------------------------------------------+
|                |               |                                                |
| Parameter Name | Type          | Description                                    |
|                |               |                                                |
+================+===============+================================================+
|                |               |                                                |
| rank           | Integer       | The position of the app in the recommendation. |
|                |               |                                                |
+----------------+---------------+------------------------------------------------+

Example::

    http://domain.com/api/v2/recommended/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173/457282/?rank=4


Item/App Detail
---------------

To retrieve information about a specific application.


*URL*::

    http://domain.com/api/v2/item/<app external id>.<format>
    http://domain.com/api/v2/item/<app external id>/<format>/
    http://domain.com/api/v2/item/<app external id>/  # Default format is JSON


GET Request
+++++++++++

The request may have a set of extra GET parameters.

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| user           | String        | An external id of the user in case is an  |
|                |               | installed app.                            |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| rank           | Number        | The rank of the application in case of it |
|                |               | source was from a recommendation.         |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Example::

    http://domain.com/api/v2/item/457282.json?rank=4&user=006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173


Response:

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| name           | String        | The name of the app.                      |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| external_id    | String        | The external id of the item.              |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| details        | URL           | The URL for app details.                  |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| store          | URI           | The URI to the "go to store"              |
|                |               | functionality.                            |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Example::

    {
        external_id: "457282",
        name: "Kronometro Vulpa",
        store: "/api/v2/recommended/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173/457282/?rank=4",
        details: "https://marketplace.firefox.com/api/v1/apps/app/457282/"
    }


User Items API
--------------

With this API is possible to check user owned items/installed apps. This API also allow acquire or drop an item (install
or uninstall an app) using the POST and DELETE methods.

.. note::

    All the *unsafe* HTTP methods require a crsf token. But in this case and since the API is not supposed to contact
    with public we will disable this functionality.


*URL*::

    http://domain.com/api/v2/user-items/<user external id>.<format>
    http://domain.com/api/v2/user-items/<user external id>/<format>/
    http://domain.com/api/v2/user-items/<user external id>/  # Default format is JSON

GET Request
+++++++++++

The request *may* have a set of extra GET parameters.

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| Request        | Object        | User information.                         |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| offset         | Number        | The number of items to drop before        |
|                |               | deliver in response.                      |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| items          | Number        | The number of items to be delivered in    |
|                |               | the response.                             |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Example::

    http://domain.com/api/v2/user-items/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173/xml/?offset=10&items=30
    http://domain.com/api/v2/user-items/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173.json



Response:

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| user           | String        | The user external id.                     |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| items          | List          | A list of owned items.                    |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Owned Items:

+-------------------+---------------+-------------------------------------------+
|                   |               |                                           |
| Parameter Name    | Type          | Description                               |
|                   |               |                                           |
+===================+===============+===========================================+
|                   |               |                                           |
| external_id       | String        | The item external id.                     |
|                   |               |                                           |
+-------------------+---------------+-------------------------------------------+
|                   |               |                                           |
| is_dropped        | Boolean       | Is the item was dropped by user.          |
|                   |               |                                           |
+-------------------+---------------+-------------------------------------------+


Example::

    {
        items: [
            {
                is_dropped: false,
                external_id: "413346",
            }
        ],
        user: "006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173"
    }


POST Request
++++++++++++

This method is used to acquire/install a new item/application to the user inventory. It still need a Post parameter.

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| item_to_acquire| String        | The item external id.                     |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Response:

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| status         | Number        | The response status.                      |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| message        | Text          | Some message with information.            |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+


Example::

    {
        "status": 200,
        "message": "done"
    }

DELETE Request
++++++++++++++

This method is used to drop/remove a new item/application from a user inventory. It still need a parameter.

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| item_to_remove | String        | The item external id.                     |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Response:

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| status         | Number        | The response status.                      |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| message        | Text          | Some message with information.            |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+


Example::

    {
        "status": 200,
        "message": "done"
    }

User API
--------

This API implements a way to list the users in system and create a new user.

.. note::

    All the *unsafe* HTTP methods require a crsf token. But in this case and since the API is not supposed to contact
    with public we will disable this functionality.


*URL*::

    http://domain.com/api/v2/users.<format>
    http://domain.com/api/v2/users/<format>/
    http://domain.com/api/v2/users/  # Default format is JSON

GET Request
+++++++++++

The request *may* have a set of extra GET parameters.

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| Request        | Object        | User information.                         |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| offset         | Number        | The number of users to drop before        |
|                |               | deliver in response.                      |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| users          | Number        | The number of users to be delivered in    |
|                |               | the response.                             |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Example::

    http://domain.com/api/v2/users.json?offset=10&users=30
    http://domain.com/api/v2/users/xml/



Response:

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| response       | List          | A list of users items.                    |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

User:

+-------------------+---------------+-------------------------------------------+
|                   |               |                                           |
| Parameter Name    | Type          | Description                               |
|                   |               |                                           |
+===================+===============+===========================================+
|                   |               |                                           |
| external_id       | String        | The user external id.                     |
|                   |               |                                           |
+-------------------+---------------+-------------------------------------------+
|                   |               |                                           |
| id                | Integer       | The user internal id                      |
|                   |               |                                           |
+-------------------+---------------+-------------------------------------------+


Example::

    [
        {
            external_id: "00bff6c3e52abf68501dcd4b9882a76327f6182cf760d33463531bacdd52c53b",
            id: 11
        },
        {
            external_id: "00360cca7ccdb1464cca0e42cef52753698295b4c148f86d2fa74431001477a8",
            id: 12
        },
        {
            external_id: "0000389d24eb79b0970d3baccaff7736fd2aebc7eee5d0615779a2d3dd5824aa",
            id: 13
        }
    ]


POST Request
++++++++++++

This method is used to create a new user in system. It still need a Post parameter.

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| external_id    | String        | The user external id.                     |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Response:

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| status         | Number        | The response status.                      |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| message        | Text          | Some message with information.            |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+


Example::

    {
        "status": 200,
        "message": "done"
    }
