.. _results

Results
=======

Some results over computing performance and result accuracy.

Performance
-----------

Tests on performance were made with Mozilla data set deployed on uwsgi with 4 processes and nginx proxy. The script
run to get the performance is under the project on directory folders and the user_reco_url.txt is a file with all users
url for recommend 5 items with the Frappe rest api.

Data
____

**Items**: 5279

**Users**: 91946

**Entries**: 1470331

Machine
_______

**OS**: Ubuntu 12.04 Server

**Processor**: Intel(R) Xeon(R) CPU E5-2680 0 @ 2.70GHz x 2

**Memory**: 16GB

Results
_______

.. code-block:: bash
   :linenos:

     # 2014-Oct-15

     $ sb -f ~/frappe/mozzila/user_reco_url.txt 10000 -c 32 -p 32

     N					10000
     Mean(time)				99.982 ms
     Standard deviation(time)		24.486 ms
     Percentile 50%(time)		116 ms
     Percentile 66%(time)		116 ms
     Percentile 75%(time)		117 ms
     Percentile 90%(time)		118 ms
     Percentile 95%(time)		119 ms
     Percentile 96%(time)		120 ms
     Percentile 97%(time)		120 ms
     Percentile 98%(time)		122 ms
     Percentile 99%(time)		134 ms
     Percentile 100%(time)		219 ms

     $ siege [-c4 -c8 -c16 -c32 -c64] -t1m -b -i -f user_reco_url.txt

            Date & Time,  Trans,  Elap Time,  Data Trans,  Resp Time,  Trans Rate,  Throughput,  Concurrent,    OKAY,   Failed
    2014-10-21 06:02:29,   2343,      29.24,           0,       0.05,       80.13,        0.00,        4.00,    2343,       0
    2014-10-21 06:03:25,   2087,      29.35,           0,       0.11,       71.11,        0.00,        7.98,    2087,       0
    2014-10-21 06:04:42,   2388,      29.90,           0,       0.20,       79.87,        0.00,       15.93,    2388,       0
    2014-10-21 06:00:36,   2321,      29.70,           0,       0.41,       78.15,        0.00,       31.77,    2321,       0
    2014-10-21 06:07:32,   2286,      29.08,           0,       0.80,       78.61,        0.00,       63.03,    2286,       0
