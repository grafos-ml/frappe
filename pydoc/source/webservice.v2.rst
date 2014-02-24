App Recommendation Webservice Version 1.2
=========================================

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

The request recommendation method work over ReST request in a JSON, XML or YAML.
The response come as has a list of app IDS.


GET Request
+++++++++++

*URL*::

    http://domain.com/api/v2/recommend/<recommendation_number>/<user_id>.<format>
    http://domain.com/api/v2/recommend/<recommendation_number>/<user_id>/<format>/
    http://domain.com/api/v2/recommend/<recommendation_number>/<user_id>/  # Default format is JSON


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
| Request.       | String        | Identifier number for the user.           |
|  user_id       |               |                                           |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Request.       | Number        | Number of recommendation you want.        |
|  recommendation|               |                                           |
|  _number       |               |                                           |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Request.format | String        | The format of the response (json, xml or  |
|                |               | yaml.                                     |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Example::

    http://domain.com/api/v2/recommend/120/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173.xml


GET Response
++++++++++++

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
| recommendations| List<Number>  | A list with suggested apps ids.           |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Example::

    Response:
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



Go to the Application place in FF Store
---------------------------------------

This functionality allow to record useful information about a specific app. It can record a simple click, a click from
a recommendation, and a click from anonymous users.


GET Request
+++++++++++

*URL*::

    http://domain.com/apu/v2/<click or recommended>/<user external id or anonymous>/<app external id>/


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


GET Request
+++++++++++

*URL*::

    http://domain.com/api/v2/item/<app external id>.<format>
    http://domain.com/api/v2/item/<app external id>/<format>/
    http://domain.com/api/v2/item/<app external id>/  # Default format is JSON

The request may have a set of extra GET parameters.

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


GET Response
++++++++++++

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
| name           | String        | The name of the app.                      |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| external_id    | Integer       | The external id of the app.               |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| icon           | URL           | The URL for the 64x64 icon.               |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| icon_small     | URL           | The URL for the 16x16 icon.               |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| icon_large     | URL           | The URL for the 128x128 icon.             |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| store          | URI           | The URI to the "go to store"              |
|                |               | functionality.                            |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Example::

    {
        name: "Urban Dictionary",
        external_id: 462103,
        icon_small: "https://marketplace.cdn.mozilla.net/img/uploads/addon_icons/462/462103-32.png?modified=1377861637",
        icon_large: "https://marketplace.cdn.mozilla.net/img/uploads/addon_icons/462/462103-128.png?modified=1377861637",
        store: "/api/v2/click/anonymous/462103/",
        icon: "https://marketplace.cdn.mozilla.net/img/uploads/addon_icons/462/462103-64.png?modified=1377861637"
    }