App Recommendation Webservice Version 1.1
=============================

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

    http://domain.com/api/v1/recommendation/<external_id>_<recommendation_number>.<format>


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
|  external_id   |               |                                           |
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

    http://domain.com/api/v1/recommendation/006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173_120.xml

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
        <object>
            <external_id>
                006a508fe63e87619db5c3db21da2c536f24e296c29d885e4b48d0b5aa561173
            </external_id>
            <recommendations type="list">
                <value type="integer">371208</value>
                ...
                <value type="integer">372579</value>
            </recommendations>
        </object>

