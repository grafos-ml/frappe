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

     $ siege -c60 -t1m -b -i -f frappe/mozzila/user_reco_url.txt

     Lifting the server siege...      done.
     Transactions:		       31867 hits
     Availability:		       100.00 %
     Elapsed time:		       59.41 secs
     Data transferred:	               4.47 MB
     Response time:		       0.11 secs
     Transaction rate:	               536.39 trans/sec
     Throughput:		       0.08 MB/sec
     Concurrency:		       59.90
     Successful transactions:          31867
     Failed transactions:	       0
     Longest transaction:	       0.32
     Shortest transaction:	       0.01
