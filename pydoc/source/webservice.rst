App Recommendation Webservice
=============================

About
-----

FireFox OS Store Recommendation webservice is a way to get apps recommendations
considering some user experience. The system is simple, the user send some data
its experience and receive a set of recommended apps to his profile. This
experience can be apps already installed, apps rejected, user location, time,
season, etc...

For the first implementation its something simple , just installed apps and few
more.

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

The request recommendation method work over ReST request in a JSON. The
response come as a JSON list of app IDS.


GET Request
+++++++++++

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
| Request.user   | Number        | Identifier number for the user.           |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Request.n      | Number        | Number of recommendation you want.        |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Example::

    http://domain.com/api/recommendation/?user=12345&n=10

GET Response
++++++++++++

+----------------+---------------+-------------------------------------------+
|                |               |                                           |
| Parameter Name | Type          | Description                               |
|                |               |                                           |
+================+===============+===========================================+
|                |               |                                           |
| Response       | List<Number>  | A list with suggested apps ids.           |
|                |               |                                           |
+----------------+---------------+-------------------------------------------+

Example::

    Response:
        [334644,000002,576868,775332,244250,218923,534475]

